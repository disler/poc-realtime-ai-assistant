import asyncio
import os
import json
import websockets
import base64
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
from websockets.exceptions import ConnectionClosedError
from .modules.logging import log_tool_call, log_error, log_info, log_warning

# Import from modules
from .modules.async_microphone import AsyncMicrophone
from .modules.audio import play_audio
from .modules.tools import (
    function_map,
    tools,
)
from .modules.utils import (
    RUN_TIME_TABLE_LOG_JSON,
    SESSION_INSTRUCTIONS,
    PREFIX_PADDING_MS,
    SILENCE_THRESHOLD,
    SILENCE_DURATION_MS,
)
from .modules.logging import logger, log_ws_event
import sys

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ["OPENAI_API_KEY", "PERSONALIZATION_FILE", "SCRATCH_PAD_DIR"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please set these variables in your .env file.")
    sys.exit(1)

scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

# Ensure the scratch pad directory exists
os.makedirs(scratch_pad_dir, exist_ok=True)

# Load personalization data
with open(os.getenv("PERSONALIZATION_FILE"), "r") as f:
    personalization = json.load(f)


def base64_encode_audio(audio_bytes):
    return base64.b64encode(audio_bytes).decode("utf-8")


def log_runtime(function_or_name: str, duration: float):
    jsonl_file = RUN_TIME_TABLE_LOG_JSON
    time_record = {
        "timestamp": datetime.now().isoformat(),
        "function": function_or_name,
        "duration": f"{duration:.4f}",
    }
    with open(jsonl_file, "a") as file:
        json.dump(time_record, file)
        file.write("\n")

    logger.info(f"⏰ {function_or_name}() took {duration:.4f} seconds")


class RealtimeAPI:
    def __init__(self, prompts=None):
        self.prompts = prompts
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("Please set the OPENAI_API_KEY in your .env file.")
            sys.exit(1)
        self.exit_event = asyncio.Event()
        self.mic = AsyncMicrophone()

        # Initialize state variables
        self.assistant_reply = ""
        self.audio_chunks = []
        self.response_in_progress = False
        self.function_call = None
        self.function_call_args = ""
        self.response_start_time = None

    async def run(self):
        while True:
            try:
                url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "OpenAI-Beta": "realtime=v1",
                }

                async with websockets.connect(
                    url,
                    extra_headers=headers,
                    close_timeout=120,
                    ping_interval=30,
                    ping_timeout=10,
                ) as websocket:
                    log_info("✅ Connected to the server.", style="bold green")

                    await self.initialize_session(websocket)
                    ws_task = asyncio.create_task(self.process_ws_messages(websocket))

                    logger.info(
                        "Conversation started. Speak freely, and the assistant will respond."
                    )

                    if self.prompts:
                        await self.send_initial_prompts(websocket)
                    else:
                        self.mic.start_recording()
                        logger.info("Recording started. Listening for speech...")

                    await self.send_audio_loop(websocket)

                    logger.info("before await ws_task")

                    # Wait for the WebSocket processing task to complete
                    await ws_task

                    logger.info("await ws_task complete")

                # If execution reaches here without exceptions, exit the loop
                break
            except ConnectionClosedError as e:
                if "keepalive ping timeout" in str(e):
                    logger.warning(
                        "WebSocket connection lost due to keepalive ping timeout. Reconnecting..."
                    )
                    await asyncio.sleep(1)  # Wait before reconnecting
                    continue  # Retry the connection
                else:
                    logger.exception("WebSocket connection closed unexpectedly.")
                    break  # Exit the loop on other connection errors
            except Exception as e:
                logger.exception(f"An unexpected error occurred: {e}")
                break  # Exit the loop on unexpected exceptions
            finally:
                self.mic.stop_recording()
                self.mic.close()

    async def initialize_session(self, websocket):
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": SESSION_INSTRUCTIONS,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": SILENCE_THRESHOLD,
                    "prefix_padding_ms": PREFIX_PADDING_MS,
                    "silence_duration_ms": SILENCE_DURATION_MS,
                },
                "tools": tools,
            },
        }
        log_ws_event("Outgoing", session_update)
        await websocket.send(json.dumps(session_update))

    async def process_ws_messages(self, websocket):
        while True:
            try:
                message = await websocket.recv()
                event = json.loads(message)
                log_ws_event("Incoming", event)
                await self.handle_event(event, websocket)
            except websockets.ConnectionClosed:
                log_warning("⚠️ WebSocket connection lost.")
                break

    async def handle_event(self, event, websocket):
        event_type = event.get("type")
        if event_type == "response.created":
            self.mic.start_receiving()
            self.response_in_progress = True
        elif event_type == "response.output_item.added":
            await self.handle_output_item_added(event)
        elif event_type == "response.function_call_arguments.delta":
            self.function_call_args += event.get("delta", "")
        elif event_type == "response.function_call_arguments.done":
            await self.handle_function_call(event, websocket)
        elif event_type == "response.text.delta":
            delta = event.get("delta", "")
            self.assistant_reply += delta
            print(f"Assistant: {delta}", end="", flush=True)
        elif event_type == "response.audio.delta":
            self.audio_chunks.append(base64.b64decode(event["delta"]))
        elif event_type == "response.done":
            await self.handle_response_done()
        elif event_type == "error":
            await self.handle_error(event, websocket)
        elif event_type == "input_audio_buffer.speech_started":
            logger.info("Speech detected, listening...")
        elif event_type == "input_audio_buffer.speech_stopped":
            await self.handle_speech_stopped(websocket)
        elif event_type == "rate_limits.updated":
            self.response_in_progress = False
            self.mic.is_recording = True
            logger.info("Resumed recording after rate_limits.updated")

    async def handle_output_item_added(self, event):
        item = event.get("item", {})
        if item.get("type") == "function_call":
            self.function_call = item
            self.function_call_args = ""

    async def handle_function_call(self, event, websocket):
        if self.function_call:
            function_name = self.function_call.get("name")
            call_id = self.function_call.get("call_id")
            logger.info(
                f"Function call: {function_name} with args: {self.function_call_args}"
            )
            try:
                args = (
                    json.loads(self.function_call_args)
                    if self.function_call_args
                    else {}
                )
            except json.JSONDecodeError:
                args = {}
            await self.execute_function_call(function_name, call_id, args, websocket)

    async def execute_function_call(self, function_name, call_id, args, websocket):
        if function_name in function_map:
            try:
                result = await function_map[function_name](**args)
                log_tool_call(function_name, args, result)
            except Exception as e:
                error_message = f"Error executing function '{function_name}': {str(e)}"
                log_error(error_message)
                result = {"error": error_message}
                await self.send_error_message_to_assistant(error_message, websocket)
        else:
            error_message = f"Function '{function_name}' not found. Add to function_map in tools.py."
            log_error(error_message)
            result = {"error": error_message}
            await self.send_error_message_to_assistant(error_message, websocket)

        function_call_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result),
            },
        }
        log_ws_event("Outgoing", function_call_output)
        await websocket.send(json.dumps(function_call_output))
        await websocket.send(json.dumps({"type": "response.create"}))

        # Reset function call state
        self.function_call = None
        self.function_call_args = ""

    async def send_error_message_to_assistant(self, error_message, websocket):
        error_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "text", "text": error_message}],
            },
        }
        log_ws_event("Outgoing", error_item)
        await websocket.send(json.dumps(error_item))

    async def handle_response_done(self):
        if self.response_start_time is not None:
            response_end_time = time.perf_counter()
            response_duration = response_end_time - self.response_start_time
            log_runtime("realtime_api_response", response_duration)
            self.response_start_time = None

        log_info("Assistant response complete.", style="bold blue")
        if self.audio_chunks:
            audio_data = b"".join(self.audio_chunks)
            logger.info(
                f"Sending {len(audio_data)} bytes of audio data to play_audio()"
            )
            await play_audio(audio_data)
            logger.info("Finished play_audio()")
        self.assistant_reply = ""
        self.audio_chunks = []
        logger.info("Calling stop_receiving()")
        self.mic.stop_receiving()

    async def handle_error(self, event, websocket):
        error_message = event.get("error", {}).get("message", "")
        log_error(f"Error: {error_message}")
        if "buffer is empty" in error_message:
            logger.info("Received 'buffer is empty' error, no audio data sent.")
        elif "Conversation already has an active response" in error_message:
            logger.info("Received 'active response' error, adjusting response flow.")
            self.response_in_progress = True
        else:
            logger.error(f"Unhandled error: {error_message}")

    async def handle_speech_stopped(self, websocket):
        self.mic.stop_recording()
        logger.info("Speech ended, processing...")
        self.response_start_time = time.perf_counter()
        await websocket.send(json.dumps({"type": "input_audio_buffer.commit"}))

    async def send_initial_prompts(self, websocket):
        logger.info(f"Sending {len(self.prompts)} prompts: {self.prompts}")
        content = [{"type": "input_text", "text": prompt} for prompt in self.prompts]
        event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": content,
            },
        }
        log_ws_event("Outgoing", event)
        await websocket.send(json.dumps(event))

        # Trigger the assistant's response
        response_create_event = {"type": "response.create"}
        log_ws_event("Outgoing", response_create_event)
        await websocket.send(json.dumps(response_create_event))

    async def send_audio_loop(self, websocket):
        try:
            while not self.exit_event.is_set():
                await asyncio.sleep(0.1)  # Small delay to accumulate audio data
                if not self.mic.is_receiving:
                    audio_data = self.mic.get_audio_data()
                    if audio_data and len(audio_data) > 0:
                        base64_audio = base64_encode_audio(audio_data)
                        if base64_audio:
                            audio_event = {
                                "type": "input_audio_buffer.append",
                                "audio": base64_audio,
                            }
                            log_ws_event("Outgoing", audio_event)
                            await websocket.send(json.dumps(audio_event))
                        else:
                            logger.debug("No audio data to send")
                else:
                    await asyncio.sleep(0.1)  # Wait while receiving assistant response
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Closing the connection.")
        finally:
            self.exit_event.set()
            self.mic.stop_recording()
            self.mic.close()
            await websocket.close()


def main():
    print(f"Starting realtime API...")
    logger.info(f"Starting realtime API...")
    parser = argparse.ArgumentParser(
        description="Run the realtime API with optional prompts."
    )
    parser.add_argument("--prompts", type=str, help="Prompts separated by |")
    args = parser.parse_args()

    prompts = args.prompts.split("|") if args.prompts else None

    realtime_api_instance = RealtimeAPI(prompts)
    try:
        asyncio.run(realtime_api_instance.run())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    print("Press Ctrl+C to exit the program.")
    main()
