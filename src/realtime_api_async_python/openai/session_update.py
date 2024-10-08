# Constants for turn detection
PREFIX_PADDING_MS = 300
SILENCE_THRESHOLD = 0.5
SILENCE_DURATION_MS = 400

def get_session_update(tool_schema, instructions):
  session_update = {
      "type": "session.update",
      "session": {
          "modalities": ["text", "audio"],
          "instructions": instructions,
          "voice": "alloy",
          "input_audio_format": "pcm16",
          "output_audio_format": "pcm16",
          "turn_detection": {
              "type": "server_vad",
              "threshold": SILENCE_THRESHOLD,
              "prefix_padding_ms": PREFIX_PADDING_MS,
              "silence_duration_ms": SILENCE_DURATION_MS,
          },
          "tools": tool_schema,
      },
  }
  return session_update