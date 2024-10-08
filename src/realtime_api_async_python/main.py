import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError
import os
import json
import base64
import time

from .utils.encode_audio import encode_audio
from .utils.logging import logging, log_ws_event, log_runtime
from .utils.load_config import setup, get_session_instructions
from .audio.bidirectional_audio import BidirectionalAudio, play_audio
from .openai.session_update import get_session_update
from .tools.all_tools import function_map, tool_schema

setup()

# big ideas here, really, this should be db calls. More on this later.
assistant_storage: dict = {}

async def realtime_api():
    while True:
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logging.error("Please set the OPENAI_API_KEY in your .env file.")
                return

            exit_event = asyncio.Event()

            url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "OpenAI-Beta": "realtime=v1",
            }

            mic = BidirectionalAudio()

            async with websockets.connect(url, extra_headers=headers) as websocket:
                logging.info("Connected to the server.")

                # Initialize the session with voice capabilities and tool
                session_update = get_session_update(tool_schema, get_session_instructions())
                
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
                                        logging.info(
                                            f"🛠️ Calling function: {function_name} with args: {args}"
                                        )
                                        logging.info(
                                            f"🛠️ Calling function: {function_map[function_name]}"
                                        )
                                        if args:
                                            result = await function_map[function_name](
                                                **args
                                            )
                                        else:
                                            result = await function_map[function_name]()
                                        logging.info(
                                            f"🛠️ Function call result: {result}"
                                        )
                                    else:
                                        result = {
                                            "error": f"Function '{function_name}' not found."
                                        }
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

                                logging.info("Assistant response complete.")
                                if audio_chunks:
                                    audio_data = b"".join(audio_chunks)
                                    logging.info(
                                        f"Sending {len(audio_data)} bytes of audio data to play_audio()"
                                    )
                                    await play_audio(audio_data)
                                    logging.info("Finished play_audio()")
                                assistant_reply = ""
                                audio_chunks = []
                                logging.info("Calling stop_receiving()")
                                mic.stop_receiving()
                            elif event["type"] == "rate_limits.updated":
                                response_in_progress = False
                                mic.is_recording = True
                                logging.info(
                                    "Resumed recording after rate_limits.updated"
                                )
                                pass
                            elif event["type"] == "error":
                                error_message = event.get("error", {}).get(
                                    "message", ""
                                )
                                logging.error(f"Error: {error_message}")
                                if "buffer is empty" in error_message:
                                    logging.info(
                                        "Received 'buffer is empty' error, no audio data sent."
                                    )
                                    continue
                                elif (
                                    "Conversation already has an active response"
                                    in error_message
                                ):
                                    logging.info(
                                        "Received 'active response' error, adjusting response flow."
                                    )
                                    response_in_progress = True
                                    continue
                                else:
                                    logging.error(f"Unhandled error: {error_message}")
                                    break
                            elif event["type"] == "input_audio_buffer.speech_started":
                                logging.info("Speech detected, listening...")
                            elif event["type"] == "input_audio_buffer.speech_stopped":
                                mic.stop_recording()
                                logging.info("Speech ended, processing...")
                                # await asyncio.sleep(0.5)

                                # start the response timer, on send
                                response_start_time = time.perf_counter()
                                await websocket.send(
                                    json.dumps({"type": "input_audio_buffer.commit"})
                                )

                        except websockets.ConnectionClosed:
                            logging.warning("WebSocket connection closed")
                            break

                ws_task = asyncio.create_task(process_ws_messages())

                logging.info(
                    "Conversation started. Speak freely, and the assistant will respond."
                )
                mic.start_recording()
                logging.info("Recording started. Listening for speech...")

                try:
                    while not exit_event.is_set():
                        await asyncio.sleep(
                            0.1
                        )  # Small delay to accumulate some audio data
                        if not mic.is_receiving:
                            audio_data = mic.get_audio_data()
                            if audio_data and len(audio_data) > 0:
                                base64_audio = encode_audio(audio_data)
                                if base64_audio:
                                    audio_event = {
                                        "type": "input_audio_buffer.append",
                                        "audio": base64_audio,
                                    }
                                    log_ws_event("Outgoing", audio_event)
                                    await websocket.send(json.dumps(audio_event))
                                else:
                                    logging.debug("No audio data to send")
                        else:
                            await asyncio.sleep(
                                0.1
                            )  # Wait while receiving assistant response
                except KeyboardInterrupt:
                    logging.info("Keyboard interrupt received. Closing the connection.")
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
                logging.warning(
                    "WebSocket connection lost due to keepalive ping timeout. Reconnecting..."
                )
                await asyncio.sleep(1)  # Wait before reconnecting
                continue  # Retry the connection
            else:
                logging.exception("WebSocket connection closed unexpectedly.")
                break  # Exit the loop on other connection errors
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            break  # Exit the loop on unexpected exceptions
        finally:
            if "mic" in locals():
                mic.stop_recording()
                mic.close()
            if "websocket" in locals():
                await websocket.close()



def main():
    try:
        asyncio.run(realtime_api())
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    print("Press Ctrl+C to exit the program.")
    main()
