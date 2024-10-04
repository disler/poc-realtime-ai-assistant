import asyncio
import openai
from pydantic import BaseModel
import websockets
import os
import json
import base64
from dotenv import load_dotenv
import pyaudio
import numpy as np
import queue
import logging
import time
import sys

# Add these imports for the functions
from datetime import datetime
import random
import webbrowser
from concurrent.futures import ThreadPoolExecutor

# Constants for turn detection
PREFIX_PADDING_MS = 300
SILENCE_THRESHOLD = 0.5
SILENCE_DURATION_MS = 400

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

# Load environment variables
load_dotenv()

# Check for required environment variables
required_env_vars = ["OPENAI_API_KEY", "PERSONALIZATION_FILE"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logging.error("Please set these variables in your .env file.")
    sys.exit(1)


# Define the functions to be called
async def get_current_time():
    return {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


async def get_random_number():
    return {"random_number": random.randint(1, 100)}


class WebUrl(BaseModel):
    url: str


async def open_browser(prompt: str):
    """
    Open a browser tab with the best-fitting URL based on the user's prompt.

    Args:
        prompt (str): The user's prompt to determine which URL to open.
    """
    personalization_file = os.getenv("PERSONALIZATION_FILE", "./personalization.json")

    # Load personalization settings
    with open(personalization_file, "r") as f:
        personalization = json.load(f)

    # Extract browser URLs and create a comma-separated string
    browser_urls = personalization.get("browser_urls", [])
    browser_urls_str = ", ".join(browser_urls)

    # Extract browser preference
    browser = personalization.get("browser", "chrome")

    # Build the structured prompt
    prompt_structure = f"""
<purpose>
    Select a browser URL from the list of browser URLs based on the user's prompt.
</purpose>

<instructions>
    <instruction>Infer the browser URL that the user wants to open from the user-prompt and the list of browser URLs.</instruction>
    <instruction>If the user-prompt is not related to the browser URLs, return an empty string.</instruction>
</instructions>

<browser-urls>
    {browser_urls_str}
</browser-urls>

<user-prompt>
    {prompt}
</user-prompt>
    """

    logging.info(f"📖 open_browser() Prompt: {prompt_structure}")

    # Call the LLM to select the best-fit URL
    response = structured_output_prompt(prompt_structure, WebUrl)

    logging.info(f"📖 open_browser() Response: {response}")

    # Open the URL if it's not empty
    if response.url:
        logging.info(f"📖 open_browser() Opening URL: {response.url}")
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(
                pool, webbrowser.get(browser).open, response.url
            )
        return {"status": "Browser opened", "url": response.url}
    else:
        return {"status": "No URL found"}


# Map function names to their corresponding functions
function_map = {
    "get_current_time": get_current_time,
    "get_random_number": get_random_number,
    "open_browser": open_browser,
}


# Function to log WebSocket events
def log_ws_event(direction, event):
    event_type = event.get("type", "Unknown")
    icon = "⬆️  -  Out" if direction == "outgoing" else "⬇️  -  In"
    logging.info(f"realtime_api_ws_events: {icon} {event_type}")


def structured_output_prompt(prompt: str, response_format: BaseModel) -> BaseModel:
    """
    Parse the response from the OpenAI API using structured output.

    Args:
        prompt (str): The prompt to send to the OpenAI API.
        response_format (BaseModel): The Pydantic model representing the expected response format.

    Returns:
        BaseModel: The parsed response from the OpenAI API.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "user", "content": prompt},
        ],
        response_format=response_format,
    )

    message = completion.choices[0].message

    if not message.parsed:
        raise ValueError(message.refusal)

    return message.parsed


# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

assistant_storage: dict = {}


class AsyncMicrophone:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            stream_callback=self.callback,
        )
        self.queue = queue.Queue()
        self.is_recording = False
        self.is_receiving = False
        logging.info("AsyncMicrophone initialized")

    def callback(self, in_data, frame_count, time_info, status):
        if self.is_recording and not self.is_receiving:
            self.queue.put(in_data)
        # if self.is_recording:
        #     self.queue.put(in_data)
        return (None, pyaudio.paContinue)

    def start_recording(self):
        self.is_recording = True
        logging.info("Started recording")

    def stop_recording(self):
        self.is_recording = False
        logging.info("Stopped recording")

    def start_receiving(self):
        self.is_receiving = True
        self.is_recording = False
        logging.info("Started receiving assistant response")

    def stop_receiving(self):
        self.is_receiving = False
        logging.info("Stopped receiving assistant response")

    def get_audio_data(self):
        data = b""
        while not self.queue.empty():
            data += self.queue.get()
        return data if data else None

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        logging.info("AsyncMicrophone closed")


def base64_encode_audio(audio_bytes):
    return base64.b64encode(audio_bytes).decode("utf-8")


async def realtime_api():
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

    mic = AsyncMicrophone()

    async with websockets.connect(url, extra_headers=headers) as websocket:
        logging.info("Connected to the server.")

        # Initialize the session with voice capabilities and tool
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful assistant. Respond concisely.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": SILENCE_THRESHOLD,
                    "prefix_padding_ms": PREFIX_PADDING_MS,
                    "silence_duration_ms": SILENCE_DURATION_MS,
                },
                "tools": [
                    {
                        "type": "function",
                        "name": "get_current_time",
                        "description": "Returns the current time.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                    {
                        "type": "function",
                        "name": "get_random_number",
                        "description": "Returns a random number between 1 and 100.",
                        "parameters": {
                            "type": "object",
                            "properties": {},
                            "required": [],
                        },
                    },
                    {
                        "type": "function",
                        "name": "open_browser",
                        "description": "Opens a browser tab with the best-fitting URL based on the user's prompt.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "The user's prompt to determine which URL to open.",
                                },
                            },
                            "required": ["prompt"],
                        },
                    },
                ],
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
                    elif event["type"] == "response.function_call_arguments.delta":
                        delta = event.get("delta", "")
                        function_call_args += delta
                    elif event["type"] == "response.function_call_arguments.done":
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
                                if args:
                                    result = await function_map[function_name](**args)
                                else:
                                    result = await function_map[function_name]()
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
                            await websocket.send(json.dumps(function_call_output))
                            await websocket.send(
                                json.dumps({"type": "response.create"})
                            )
                            function_call = None
                            function_call_args = ""
                    elif event["type"] == "response.text.delta":
                        assistant_reply += event.get("delta", "")
                        print(
                            f"Assistant: {event.get('delta', '')}", end="", flush=True
                        )
                    elif event["type"] == "response.audio.delta":
                        audio_chunks.append(base64.b64decode(event["delta"]))
                    elif event["type"] == "response.done":
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
                        logging.info("Resumed recording after rate_limits.updated")
                        pass
                    elif event["type"] == "error":
                        error_message = event.get("error", {}).get("message", "")
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
                        await asyncio.sleep(0.5)
                        await websocket.send(
                            json.dumps({"type": "input_audio_buffer.commit"})
                        )
                        if not response_in_progress:
                            logging.info("Creating a new response")
                            await websocket.send(
                                json.dumps({"type": "response.create"})
                            )
                        else:
                            logging.info(
                                "Response already in progress, not creating a new response"
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
                await asyncio.sleep(0.1)  # Small delay to accumulate some audio data
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
                            logging.debug("No audio data to send")
                else:
                    await asyncio.sleep(0.1)  # Wait while receiving assistant response
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received. Closing the connection.")
        finally:
            exit_event.set()
            mic.stop_recording()
            mic.close()
            await websocket.close()

        # Wait for the WebSocket processing task to complete
        await ws_task


async def play_audio(audio_data):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
    stream.write(audio_data)

    # Add a small delay (e.g., 100ms) of silence at the end
    silence_duration = 0.1  # 100ms
    silence_frames = int(RATE * silence_duration)
    silence = b"\x00" * (
        silence_frames * CHANNELS * 2
    )  # 2 bytes per sample for 16-bit audio
    stream.write(silence)

    # Add a small pause before closing the stream
    time.sleep(0.5)

    stream.stop_stream()
    stream.close()
    p.terminate()
    logging.debug("Audio playback completed")


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
