import asyncio
import websockets
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


async def test_realtime_api_connection():
    # Retrieve your API key from the environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable in your .env file.")
        return

    # Define the WebSocket URL with the appropriate model
    # Replace 'gpt-4' with the correct model name if necessary
    url = "wss://api.openai.com/v1/realtime?model=gpt-4"

    # Set the required headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }

    # Attempt to establish the WebSocket connection
    try:
        async with websockets.connect(url, extra_headers=headers) as websocket:
            print("Connected to the server.")
    except websockets.InvalidStatusCode as e:
        print(f"Failed to connect: {e}")
        if e.status_code == 403:
            print("HTTP 403 Forbidden: Access denied.")
            print("You may not have access to the Realtime API.")
        else:
            print(f"HTTP {e.status_code}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test_realtime_api_connection())
