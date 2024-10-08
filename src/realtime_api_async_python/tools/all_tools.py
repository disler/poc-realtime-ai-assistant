from .get_current_time import get_current_time
from .get_random_number import get_random_number
from .open_browser import open_browser
from .file_operations import create_file, update_file, delete_file

function_map = {
    "get_current_time": get_current_time,
    "get_random_number": get_random_number,
    "open_browser": open_browser,
    "create_file": create_file,
    "update_file": update_file,
    "delete_file": delete_file,
}

tool_schema = [
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
]