import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Hello"}]
    )
    print("API Key is valid. Response: ", response.choices[0].message.content)
except Exception as e:
    print(f"Invalid API Key: {e}")
