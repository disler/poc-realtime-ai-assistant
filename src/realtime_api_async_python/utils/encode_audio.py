import base64

def encode_audio(audio_bytes):
    return base64.b64encode(audio_bytes).decode("utf-8")
