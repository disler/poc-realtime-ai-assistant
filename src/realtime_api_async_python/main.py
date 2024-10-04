import asyncio
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

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Function to log WebSocket events
def log_ws_event(direction, event):
    event_type = event.get("type", "Unknown")
    logging.info(f"realtime_api_ws_events: {direction} - {event_type}")


# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000


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
        time.sleep(0.1)  # Small delay before resuming recording
        self.is_recording = True
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
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("Please set the OPENAI_API_KEY in your .env file.")
        return

    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    mic = AsyncMicrophone()

    async with websockets.connect(url, extra_headers=headers) as websocket:
        logging.info("Connected to the server.")

        # Initialize the session with voice capabilities
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
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200,
                },
            },
        }
        log_ws_event("Outgoing", session_update)
        await websocket.send(json.dumps(session_update))

        async def process_ws_messages():
            assistant_reply = ""
            audio_chunks = []
            while True:
                try:
                    message = await websocket.recv()
                    event = json.loads(message)
                    log_ws_event("Incoming", event)

                    if event["type"] == "response.created":
                        mic.start_receiving()
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
                            await play_audio(audio_data)
                            logging.info(f"Finished play_audio()")
                        assistant_reply = ""
                        audio_chunks = []
                        logging.info(f"Calling stop_receiving()")
                        mic.stop_receiving()
                    elif event["type"] == "error":
                        error_message = event.get("error", {}).get("message", "")
                        logging.error(f"Error: {error_message}")
                        if "buffer is empty" in error_message:
                            logging.info(
                                "Ignoring empty buffer error and continuing..."
                            )
                            continue
                        elif (
                            "Conversation already has an active response"
                            in error_message
                        ):
                            logging.info(
                                "Ignoring active response error and continuing..."
                            )
                            continue
                        if "buffer is empty" in error_message:
                            logging.info(
                                "Ignoring empty buffer error and continuing..."
                            )
                            continue
                    elif event["type"] == "input_audio_buffer.speech_started":
                        logging.info("Speech detected, listening...")
                    elif event["type"] == "input_audio_buffer.speech_stopped":
                        mic.stop_recording()
                        logging.info("Speech ended, processing...")
                        # Wait a short time to ensure all audio data has been sent
                        await asyncio.sleep(0.5)
                        await websocket.send(
                            json.dumps({"type": "input_audio_buffer.commit"})
                        )
                        # Generate a response after committing the audio
                        await websocket.send(json.dumps({"type": "response.create"}))
                except websockets.ConnectionClosed:
                    logging.warning("WebSocket connection closed")
                    break

        ws_task = asyncio.create_task(process_ws_messages())

        logging.info("Press Enter to start the ongoing conversation.")
        await asyncio.get_event_loop().run_in_executor(None, input)

        logging.info(
            "Conversation started. Speak freely, and the assistant will respond."
        )
        mic.start_recording()

        try:
            while True:
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
            mic.stop_recording()
            mic.close()
            await websocket.close()


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
    main()
