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
import base64
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


async def realtime_api(prompts=None):
    while True:
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("Please set the OPENAI_API_KEY in your .env file.")
                return

            exit_event = asyncio.Event()

            url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "OpenAI-Beta": "realtime=v1",
            }

            mic = AsyncMicrophone()

            async with websockets.connect(url, extra_headers=headers) as websocket:
                log_info("✅ Connected to the server.", style="bold green")

                # Initialize the session with voice capabilities and tool
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

                async def process_ws_messages():
                    assistant_reply = ""
                    audio_chunks = []
                    response_in_progress = False
                    function_call = None
                    function_call_args = ""
                    response_start_time = None

                    while True:
                        try:
                            message = await websocket.recv()
                            event = json.loads(message)
                            log_ws_event("Incoming", event)

                            if event["type"] == "response.created":
                                mic.start_receiving()
                                response_in_progress = True
                            elif event["type"] == "response.output_item.added":
                                item = event.get("item", {})
                                if item.get("type") == "function_call":
                                    function_call = item
                                    function_call_args = ""
                            elif (
                                event["type"]
                                == "response.function_call_arguments.delta"
                            ):
                                delta = event.get("delta", "")
                                function_call_args += delta
                            elif (
                                event["type"] == "response.function_call_arguments.done"
                            ):
                                if function_call:
                                    function_name = function_call.get("name")
                                    call_id = function_call.get("call_id")
                                    try:
                                        args = (
                                            json.loads(function_call_args)
                                            if function_call_args
                                            else None
                                        )
                                    except json.JSONDecodeError:
                                        args = None
                                    if function_name in function_map:
                                        log_tool_call(function_name, args, None)
                                        if args:
                                            result = await function_map[function_name](
                                                **args
                                            )
                                        else:
                                            result = await function_map[function_name]()
                                        log_tool_call(function_name, args, result)
                                    else:
                                        result = {
                                            "error": f"Function '{function_name}' not found."
                                        }
                                        raise Exception(
                                            f"Function '{function_name}' not found. Add to function_map in tools.py."
                                        )
                                    function_call_output = {
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type": "function_call_output",
                                            "call_id": call_id,
                                            "output": json.dumps(result),
                                        },
                                    }
                                    log_ws_event("Outgoing", function_call_output)
                                    await websocket.send(
                                        json.dumps(function_call_output)
                                    )
                                    await websocket.send(
                                        json.dumps({"type": "response.create"})
                                    )
                                    function_call = None
                                    function_call_args = ""

                            elif event["type"] == "response.text.delta":
                                assistant_reply += event.get("delta", "")
                                print(
                                    f"Assistant: {event.get('delta', '')}",
                                    end="",
                                    flush=True,
                                )
                            elif event["type"] == "response.audio.delta":
                                audio_chunks.append(base64.b64decode(event["delta"]))
                            elif event["type"] == "response.done":
                                if response_start_time is not None:
                                    response_end_time = time.perf_counter()
                                    response_duration = (
                                        response_end_time - response_start_time
                                    )
                                    log_runtime(
                                        "realtime_api_response", response_duration
                                    )
                                    response_start_time = None

                                log_info(
                                    "Assistant response complete.", style="bold blue"
                                )
                                if audio_chunks:
                                    audio_data = b"".join(audio_chunks)
                                    logger.info(
                                        f"Sending {len(audio_data)} bytes of audio data to play_audio()"
                                    )
                                    await play_audio(audio_data)
                                    logger.info("Finished play_audio()")
                                assistant_reply = ""
                                audio_chunks = []
                                logger.info("Calling stop_receiving()")
                                mic.stop_receiving()
                            elif event["type"] == "rate_limits.updated":
                                response_in_progress = False
                                mic.is_recording = True
                                logger.info(
                                    "Resumed recording after rate_limits.updated"
                                )
                                pass
                            elif event["type"] == "error":
                                error_message = event.get("error", {}).get(
                                    "message", ""
                                )
                                log_error(f"Error: {error_message}")
                                if "buffer is empty" in error_message:
                                    logger.info(
                                        "Received 'buffer is empty' error, no audio data sent."
                                    )
                                    continue
                                elif (
                                    "Conversation already has an active response"
                                    in error_message
                                ):
                                    logger.info(
                                        "Received 'active response' error, adjusting response flow."
                                    )
                                    response_in_progress = True
                                    continue
                                else:
                                    logger.error(f"Unhandled error: {error_message}")
                                    break
                            elif event["type"] == "input_audio_buffer.speech_started":
                                logger.info("Speech detected, listening...")
                            elif event["type"] == "input_audio_buffer.speech_stopped":
                                mic.stop_recording()
                                logger.info("Speech ended, processing...")
                                # await asyncio.sleep(0.5)

                                # start the response timer, on send
                                response_start_time = time.perf_counter()
                                await websocket.send(
                                    json.dumps({"type": "input_audio_buffer.commit"})
                                )

                        except websockets.ConnectionClosed:
                            log_warning("⚠️ WebSocket connection lost. Reconnecting...")
                            break

                ws_task = asyncio.create_task(process_ws_messages())

                logger.info(
                    "Conversation started. Speak freely, and the assistant will respond."
                )

                if prompts:
                    logger.info(f"Sending {len(prompts)} prompts: {prompts}")
                    content = [
                        {"type": "input_text", "text": prompt} for prompt in prompts
                    ]
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

                else:
                    mic.start_recording()
                    logger.info("Recording started. Listening for speech...")

                try:
                    while not exit_event.is_set():
                        await asyncio.sleep(
                            0.1
                        )  # Small delay to accumulate some audio data
                        if not mic.is_receiving:
                            audio_data = mic.get_audio_data()
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
                            await asyncio.sleep(
                                0.1
                            )  # Wait while receiving assistant response
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt received. Closing the connection.")
                finally:
                    exit_event.set()
                    mic.stop_recording()
                    mic.close()
                    await websocket.close()

                # Wait for the WebSocket processing task to complete
                await ws_task

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
            if "mic" in locals():
                mic.stop_recording()
                mic.close()
            if "websocket" in locals():
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

    try:
        asyncio.run(realtime_api(prompts))
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    print("Press Ctrl+C to exit the program.")
    main()
