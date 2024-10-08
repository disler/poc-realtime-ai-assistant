
# Load environment variables
import json
import os
import sys
from dotenv import load_dotenv

from ..utils import logging

def check_env():
   # Check for required environment variables
  required_env_vars = ["OPENAI_API_KEY", "PERSONALIZATION_FILE", "BROWSER_CUSTOMIZATION_FILE", "SCRATCH_PAD_DIR", "RUN_TIME_TABLE_LOG_JSON"]
  missing_vars = [var for var in required_env_vars if not os.getenv(var)]
  if missing_vars:
      logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
      logging.error("Please set these variables in your .env file.")
      sys.exit(1)

def create_directories():
  scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
  os.makedirs(scratch_pad_dir, exist_ok=True)

def get_session_instructions():
  # Load personalization settings
  personalization_file = os.getenv("PERSONALIZATION_FILE", "./personalization.json")
  with open(personalization_file, "r") as f:
      personalization = json.load(f)

  # Extract names from personalization
  ai_assistant_name = personalization.get("ai_assistant_name", "Assistant")
  human_name = personalization.get("human_name", "User")

  # Define session instructions constant
  SESSION_INSTRUCTIONS = f"You are {ai_assistant_name}, a helpful assistant. Respond concisely to {human_name}."
  return SESSION_INSTRUCTIONS


def setup():
  load_dotenv()
  check_env()
  create_directories()

  
