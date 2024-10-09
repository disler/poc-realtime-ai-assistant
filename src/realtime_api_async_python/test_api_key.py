import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

try:
    models = openai.models.list()
    print("API Key is valid")
    print("Available models:")
    for model in models.data:
        print("  -", model.id)
except openai.AuthenticationError:
    print("API Key is invalid")
except Exception as e:
    print(f"Unhandled exception occurred: {str(e)}")
