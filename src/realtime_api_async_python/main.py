import asyncio
import functools
import openai
from pydantic import BaseModel
import websockets
from websockets.exceptions import ConnectionClosedError
import os
import json
import base64
from typing import Optional
from dotenv import load_dotenv
import pyaudio
import numpy as np
import queue
import logging
import time
import sys
from datetime import datetime

# Add these imports for the functions
from datetime import datetime
import random
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from enum import Enum

# Constants for turn detection
PREFIX_PADDING_MS = 300
SILENCE_THRESHOLD = 0.5
SILENCE_DURATION_MS = 400

RUN_TIME_TABLE_LOG_JSON = "runtime_time_table.jsonl"


def timeit_decorator(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)
        print(f"⏰ {func.__name__}() took {duration:.4f} seconds")

        jsonl_file = RUN_TIME_TABLE_LOG_JSON

        # Create new time record
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": func.__name__,
            "duration": f"{duration:.4f}",
        }

        # Append the new record to the JSONL file
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)
        print(f"⏰ {func.__name__}() took {duration:.4f} seconds")

        jsonl_file = RUN_TIME_TABLE_LOG_JSON

        # Create new time record
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": func.__name__,
            "duration": f"{duration:.4f}",
        }

        # Append the new record to the JSONL file
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class ModelName(str, Enum):
    state_of_the_art_model = "state_of_the_art_model"
    reasoning_model = "reasoning_model"
    base_model = "base_model"
    fast_model = "fast_model"


# Mapping from enum options to model IDs
model_name_to_id = {
    ModelName.state_of_the_art_model: "o1-preview",
    ModelName.reasoning_model: "o1-mini",
    ModelName.base_model: "gpt-4o-2024-08-06",
    ModelName.fast_model: "gpt-4o-mini",
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

# Load environment variables
load_dotenv()

# Load personalization settings
personalization_file = os.getenv("PERSONALIZATION_FILE", "./personalization.json")
with open(personalization_file, "r") as f:
    personalization = json.load(f)

# Extract names from personalization
ai_assistant_name = personalization.get("ai_assistant_name", "Assistant")
human_name = personalization.get("human_name", "User")

# Define session instructions constant
SESSION_INSTRUCTIONS = f"You are {ai_assistant_name}, a helpful assistant. Respond concisely to {human_name}."

# Check for required environment variables
required_env_vars = ["OPENAI_API_KEY", "PERSONALIZATION_FILE", "SCRATCH_PAD_DIR"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logging.error("Please set these variables in your .env file.")
    sys.exit(1)

scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

# Ensure the scratch pad directory exists
os.makedirs(scratch_pad_dir, exist_ok=True)


# Define the functions to be called
@timeit_decorator
async def get_current_time():
    return {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@timeit_decorator
async def get_random_number():
    return {"random_number": random.randint(1, 100)}


class WebUrl(BaseModel):
    url: str


class CreateFileResponse(BaseModel):
    file_content: str
    file_name: str


class FileSelectionResponse(BaseModel):
    file: str
    model: ModelName = ModelName.base_model


class FileUpdateResponse(BaseModel):
    updates: str


class FileDeleteResponse(BaseModel):
    file: str
    force_delete: bool


@timeit_decorator
async def open_browser(prompt: str):
    """
    Open a browser tab with the best-fitting URL based on the user's prompt.

    Args:
        prompt (str): The user's prompt to determine which URL to open.
    """
    # Use global 'personalization' variable
    browser_urls = personalization.get("browser_urls", [])
    browser_urls_str = ", ".join(browser_urls)
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
            await loop.run_in_executor(pool, webbrowser.get(browser).open, response.url)
        return {"status": "Browser opened", "url": response.url}
    else:
        return {"status": "No URL found"}


@timeit_decorator
async def create_file(file_name: str, prompt: str) -> dict:
    """
    Generate content for a new file based on the user's prompt and the file name.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    # Ensure the scratch pad directory exists
    os.makedirs(scratch_pad_dir, exist_ok=True)

    # Construct the full file path
    file_path = os.path.join(scratch_pad_dir, file_name)

    # Check if the file already exists
    if os.path.exists(file_path):
        return {"status": "file already exists"}

    # Build the structured prompt
    prompt_structure = f"""
<purpose>
    Generate content for a new file based on the user's prompt and the file name.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the file name, generate content for a new file.</instruction>
    <instruction>The file name is the name of the file that the user wants to create.</instruction>
    <instruction>The user's prompt is the prompt that the user wants to use to generate the content for the new file.</instruction>
</instructions>

<user-prompt>
    {prompt}
</user-prompt>

<file-name>
    {file_name}
</file-name>
    """

    # Call the LLM to generate the file content
    response = structured_output_prompt(prompt_structure, CreateFileResponse)

    # Write the generated content to the file
    with open(file_path, "w") as f:
        f.write(response.file_content)

    return {"status": "file created", "file_name": response.file_name}


@timeit_decorator
async def delete_file(prompt: str, force_delete: bool = False) -> dict:
    """
    Delete a file based on the user's prompt.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    # Ensure the scratch pad directory exists
    os.makedirs(scratch_pad_dir, exist_ok=True)

    # List available files in SCRATCH_PAD_DIR
    available_files = os.listdir(scratch_pad_dir)
    available_files_str = ", ".join(available_files)

    # Build the structured prompt to select the file and determine 'force_delete' status
    select_file_prompt = f"""
    <purpose>
        Select a file from the available files to delete.
    </purpose>

    <instructions>
        <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to delete.</instruction>
        <instruction>If no file matches, return an empty string for 'file'.</instruction>
    </instructions>

    <available-files>
        {available_files_str}
    </available-files>

    <user-prompt>
        {prompt}
    </user-prompt>
    """

    # Call the LLM to select the file and determine 'force_delete'
    file_delete_response = structured_output_prompt(
        select_file_prompt, FileDeleteResponse
    )

    # Check if a file was selected
    if not file_delete_response.file:
        result = {"status": "No matching file found"}
    else:
        selected_file = file_delete_response.file
        file_path = os.path.join(scratch_pad_dir, selected_file)

        # Check if the file exists
        if not os.path.exists(file_path):
            result = {"status": "File does not exist", "file_name": selected_file}
        # If 'force_delete' is False, prompt for confirmation
        elif not force_delete:
            result = {
                "status": "Confirmation required",
                "file_name": selected_file,
                "message": f"Are you sure you want to delete '{selected_file}'? Say force delete if you want to delete.",
            }
        else:
            # Proceed to delete the file
            os.remove(file_path)
            result = {"status": "File deleted", "file_name": selected_file}

    return result


@timeit_decorator
async def update_file(prompt: str, model: ModelName = ModelName.base_model) -> dict:
    """
    Update a file based on the user's prompt.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    # Ensure the scratch pad directory exists
    os.makedirs(scratch_pad_dir, exist_ok=True)

    # List available files in SCRATCH_PAD_DIR
    available_files = os.listdir(scratch_pad_dir)
    available_files_str = ", ".join(available_files)

    # Prepare the available models mapping as JSON
    available_model_map = json.dumps(
        {model.value: model_name_to_id[model] for model in ModelName}
    )

    # Build the structured prompt to select the file and model
    select_file_prompt = f"""
<purpose>
    Select a file from the available files and choose the appropriate model based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to update.</instruction>
    <instruction>Also, select the most appropriate model from the available models mapping.</instruction>
    <instruction>If the user does not specify a model, default to 'base_model'.</instruction>
    <instruction>If no file matches, return an empty string for 'file'.</instruction>
</instructions>

<available-files>
    {available_files_str}
</available-files>

<available-model-map>
    {available_model_map}
</available-model-map>

<user-prompt>
    {prompt}
</user-prompt>
"""

    # Call the LLM to select the file and model
    file_selection_response = structured_output_prompt(
        select_file_prompt, FileSelectionResponse
    )

    # Check if a file was selected
    if not file_selection_response.file:
        return {"status": "No matching file found"}

    selected_file = file_selection_response.file
    selected_model_key = file_selection_response.model
    selected_model = model_name_to_id.get(
        selected_model_key, model_name_to_id[ModelName.base_model]
    )

    file_path = os.path.join(scratch_pad_dir, selected_file)

    # Load the content of the selected file
    with open(file_path, "r") as f:
        file_content = f.read()

    # Build the structured prompt to generate the updates
    update_file_prompt = f"""
<purpose>
    Update the content of the file based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the file content, generate the updated content for the file.</instruction>
    <instruction>The file-name is the name of the file to update.</instruction>
    <instruction>The user's prompt describes the updates to make.</instruction>
    <instruction>Respond exclusively with the updates to the file and nothing else; they will be used to overwrite the file entirely using f.write().</instruction>
    <instruction>Do not include any preamble or commentary or markdown formatting, just the raw updates.</instruction>
    <instruction>Be precise and accurate.</instruction>
</instructions>

<file-name>
    {selected_file}
</file-name>

<file-content>
    {file_content}
</file-content>

<user-prompt>
    {prompt}
</user-prompt>
"""

    # Call the LLM to generate the updates using the selected model
    file_update_response = chat_prompt(update_file_prompt, selected_model)

    # Apply the updates by writing the new content to the file
    with open(file_path, "w") as f:
        f.write(file_update_response)

    return {
        "status": "File updated",
        "file_name": selected_file,
        "model_used": selected_model_key,
    }


# Map function names to their corresponding functions
function_map = {
    "get_current_time": get_current_time,
    "get_random_number": get_random_number,
    "open_browser": open_browser,
    "create_file": create_file,
    "update_file": update_file,
    "delete_file": delete_file,
}


# Function to log WebSocket events
def log_ws_event(direction, event):
    event_type = event.get("type", "Unknown")
    icon = "⬆️  - Out" if direction == "outgoing" else "⬇️  - In"
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


def chat_prompt(prompt: str, model: str) -> str:
    """
    Run a chat model based on the specified model name.

    Args:
        prompt (str): The prompt to send to the OpenAI API.
        model (str): The model ID to use for the API call.

    Returns:
        str: The assistant's response.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    message = completion.choices[0].message

    return message.content


# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000

# big ideas here, really, this should be db calls. More on this later.
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

    logging.info(f"⏰ {function_or_name}() took {duration:.4f} seconds")


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

            mic = AsyncMicrophone()

            async with websockets.connect(url, extra_headers=headers) as websocket:
                logging.info("Connected to the server.")

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
                            {
                                "type": "function",
                                "name": "create_file",
                                "description": "Generates content for a new file based on the user's prompt and file name.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "file_name": {
                                            "type": "string",
                                            "description": "The name of the file to create.",
                                        },
                                        "prompt": {
                                            "type": "string",
                                            "description": "The user's prompt to generate the file content.",
                                        },
                                    },
                                    "required": ["file_name", "prompt"],
                                },
                            },
                            {
                                "type": "function",
                                "name": "update_file",
                                "description": "Updates a file based on the user's prompt.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "prompt": {
                                            "type": "string",
                                            "description": "The user's prompt describing the updates to the file.",
                                        },
                                        "model": {
                                            "type": "string",
                                            "enum": [
                                                "state_of_the_art_model",
                                                "reasoning_model",
                                                "base_model",
                                                "fast_model",
                                            ],
                                            "description": "The model to use for generating the updates. Default to 'base_model' if not specified.",
                                        },
                                    },
                                    "required": ["prompt"],  # 'model' is optional
                                },
                            },
                            {
                                "type": "function",
                                "name": "delete_file",
                                "description": "Deletes a file based on the user's prompt.",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "prompt": {
                                            "type": "string",
                                            "description": "The user's prompt describing the file to delete.",
                                        },
                                        "force_delete": {
                                            "type": "boolean",
                                            "description": "Whether to force delete the file without confirmation. Default to 'false' if not specified.",
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


async def play_audio(audio_data):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)
    stream.write(audio_data)

    # Add a small delay (e.g., 100ms) of silence at the end to prevent popping, and weird cuts off sounds
    silence_duration = 0.2  # 200ms
    silence_frames = int(RATE * silence_duration)
    silence = b"\x00" * (
        silence_frames * CHANNELS * 2
    )  # 2 bytes per sample for 16-bit audio
    stream.write(silence)

    # Add a small pause before closing the stream to make sure the audio is fully played
    await asyncio.sleep(0.5)

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
