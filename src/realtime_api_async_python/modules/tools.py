import asyncio
import os
import json
import random
import logging
import subprocess
import pyperclip
from pydantic import BaseModel
from typing import Any, Dict, Tuple, List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from .llm import structured_output_prompt, chat_prompt
from .memory_management import memory_manager
from .logging import log_info
from .utils import (
    timeit_decorator,
    ModelName,
    model_name_to_id,
    SESSION_INSTRUCTIONS,
    personalization,
    scrap_url_clean,
    run_uv_script,
)
from .mermaid import generate_diagram


@timeit_decorator
async def ingest_file(prompt: str) -> dict:
    """
    Selects a file based on the user's prompt, reads its content, and returns the file data.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    # Step 1: Select the file based on the prompt
    select_file_prompt = f"""
<purpose>
    Select a file from the available files based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to ingest.</instruction>
    <instruction>If no file matches, return an empty string for 'file'.</instruction>
</instructions>

<available-files>
    {", ".join(os.listdir(scratch_pad_dir))}
</available-files>

<user-prompt>
    {prompt}
</user-prompt>
    """

    file_selection_response = structured_output_prompt(
        select_file_prompt,
        FileReadResponse,
        llm_model=model_name_to_id[ModelName.fast_model],
    )

    if not file_selection_response.file:
        return {"status": "error", "message": "No matching file found for the given prompt."}

    file_path = os.path.join(scratch_pad_dir, file_selection_response.file)

    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"File '{file_selection_response.file}' does not exist in '{scratch_pad_dir}'."
        }

    # Read the file content
    try:
        with open(file_path, "r") as f:
            file_content = f.read()
    except Exception as e:
        return {"status": "error", "message": f"Failed to read the file: {str(e)}"}

    return {
        "status": "success",
        "file_name": file_selection_response.file,
        "file_content": file_content
    }


@timeit_decorator
async def add_to_memory(key: str, value: Any) -> dict:
    """
    Add a key-value pair to memory using the MemoryManager's upsert method.
    """
    success = memory_manager.upsert(key, value)
    if success:
        return {
            "status": "success",
            "message": f"Added '{key}' to memory with value '{value}'",
        }
    else:
        return {
            "status": "error",
            "message": f"Failed to add '{key}' to memory",
        }


@timeit_decorator
async def reset_active_memory(force_delete: bool = False) -> dict:
    """
    Reset the active memory to an empty dictionary.
    If force_delete is False, ask for confirmation before resetting.
    """
    if not force_delete:
        return {
            "status": "confirmation_required",
            "message": "Are you sure you want to reset the active memory? This action cannot be undone. Reply with 'force delete' to confirm.",
        }

    memory_manager.reset()
    return {
        "status": "success",
        "message": "Active memory has been reset to an empty dictionary.",
    }


class MemoryKeyResponse(BaseModel):
    key: str


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


class FileReadResponse(BaseModel):
    file: str
    model: ModelName = ModelName.base_model


class IsRunnable(BaseModel):
    code_is_runnable: bool


class MakeCodeRunnableResponse(BaseModel):
    changes_described: List[str]
    full_updated_code: str


class RunPythonResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None


@timeit_decorator
async def get_current_time():
    return {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@timeit_decorator
async def get_random_number():
    return {"random_number": random.randint(1, 100)}


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
    browser_command = personalization.get("browser_command", "open -a 'Google Chrome'")

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

    log_info(f"📖 open_browser() Prompt: {prompt_structure}", style="bold magenta")

    # Call the LLM to select the best-fit URL
    response = structured_output_prompt(prompt_structure, WebUrl)

    log_info(f"📖 open_browser() Response: {response}", style="bold cyan")

    # Open the URL if it's not empty
    if response.url:
        logging.info(f"📖 open_browser() Opening URL: {response.url}")
        try:
            subprocess.Popen(f"{browser_command} {response.url}", shell=True)
            return {"status": "Browser opened", "url": response.url}
        except Exception as e:
            logging.error(f"Failed to open browser: {str(e)}")
            return {"status": "Error", "message": f"Failed to open browser: {str(e)}"}
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

    # Get all memory content
    memory_content = memory_manager.get_xml_for_prompt(["*"])

    # Build the structured prompt
    prompt_structure = f"""
<purpose>
    Generate content for a new file based on the user's prompt, the file name, and the current memory content.
</purpose>

<instructions>
    <instruction>Based on the user's prompt, the file name, and the current memory content, generate content for a new file.</instruction>
    <instruction>The file name is the name of the file that the user wants to create.</instruction>
    <instruction>The user's prompt is the prompt that the user wants to use to generate the content for the new file.</instruction>
    <instruction>Consider the current memory content when generating the file content, if relevant.</instruction>
    <instruction>If code generation was requested, be sure to output runnable code, don't include any markdown formatting.</instruction>
</instructions>

<user-prompt>
    {prompt}
</user-prompt>

<file-name>
    {file_name}
</file-name>

{memory_content}
    """

    # Call the LLM to generate the file content
    response = structured_output_prompt(prompt_structure, CreateFileResponse)

    # Write the generated content to the file
    with open(file_path, "w") as f:
        f.write(response.file_content)

    return {"status": "file created", "file_name": response.file_name}


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

    # Build the structured prompt to select the file
    select_file_prompt = f"""
<purpose>
    Select a file from the available files based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to update.</instruction>
    <instruction>If no file matches, return an empty string for 'file'.</instruction>
</instructions>

<available-files>
    {available_files_str}
</available-files>

<user-prompt>
    {prompt}
</user-prompt>
"""

    # Call the LLM to select the file
    file_selection_response = structured_output_prompt(
        select_file_prompt,
        FileSelectionResponse,
        llm_model=model_name_to_id[ModelName.fast_model],
    )

    # Check if a file was selected
    if not file_selection_response.file:
        return {"status": "No matching file found"}

    selected_file = file_selection_response.file
    file_path = os.path.join(scratch_pad_dir, selected_file)

    # Load the content of the selected file
    with open(file_path, "r") as f:
        file_content = f.read()

    # Get all memory content
    memory_content = memory_manager.get_xml_for_prompt(["*"])

    # Build the structured prompt to generate the updates
    update_file_prompt = f"""
<purpose>
    Update the content of the file based on the user's prompt, the current file content, and the current memory content.
</purpose>

<instructions>
    <instruction>Based on the user's prompt, the current file content, and the current memory content, generate the updated content for the file.</instruction>
    <instruction>The file-name is the name of the file to update.</instruction>
    <instruction>The user's prompt describes the updates to make.</instruction>
    <instruction>Consider the current memory content when generating the file updates, if relevant.</instruction>
    <instruction>Respond exclusively with the updates to the file and nothing else; they will be used to overwrite the file entirely using f.write().</instruction>
    <instruction>Do not include any preamble or commentary or markdown formatting, just the raw updates.</instruction>
    <instruction>Be precise and accurate.</instruction>
    <instruction>If code generation was requested, be sure to output runnable code, don't include any markdown formatting.</instruction>
</instructions>

<file-name>
    {selected_file}
</file-name>

<file-content>
    {file_content}
</file-content>

{memory_content}

<user-prompt>
    {prompt}
</user-prompt>
"""

    # Call the LLM to generate the updates using the specified model
    file_update_response = chat_prompt(update_file_prompt, model_name_to_id[model])

    # Apply the updates by writing the new content to the file
    with open(file_path, "w") as f:
        f.write(file_update_response)

    return {
        "status": "File updated",
        "file_name": selected_file,
        "model_used": model,
    }


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
async def discuss_file(prompt: str, model: ModelName = ModelName.base_model) -> dict:
    """
    Discuss a file's content based on the user's prompt, considering the current memory content.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
    focus_file = personalization.get("focus_file")

    if focus_file:
        file_path = os.path.join(scratch_pad_dir, focus_file)
        if not os.path.exists(file_path):
            return {"status": "Focus file not found", "file_name": focus_file}
    else:
        # List available files in SCRATCH_PAD_DIR
        available_files = os.listdir(scratch_pad_dir)
        available_files_str = ", ".join(available_files)

        # Build the structured prompt to select the file
        select_file_prompt = f"""
<purpose>
    Select a file from the available files based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to discuss.</instruction>
    <instruction>If no file matches, return an empty string for 'file'.</instruction>
</instructions>

<available-files>
    {available_files_str}
</available-files>

<user-prompt>
    {prompt}
</user-prompt>
        """

        # Call the LLM to select the file
        file_selection_response = structured_output_prompt(
            select_file_prompt,
            FileReadResponse,
            llm_model=model_name_to_id[ModelName.fast_model],
        )

        if not file_selection_response.file:
            return {"status": "No matching file found"}

        file_path = os.path.join(scratch_pad_dir, file_selection_response.file)

    # Read the content of the file
    with open(file_path, "r") as f:
        file_content = f.read()

    # Get all memory content
    memory_content = memory_manager.get_xml_for_prompt(["*"])

    # Build the structured prompt to discuss the file content
    discuss_file_prompt = f"""
<purpose>
    Discuss the content of the file based on the user's prompt and the current memory content.
</purpose>

<instructions>
    <instruction>Based on the user's prompt, the file content, and the current memory content, provide a relevant discussion or analysis.</instruction>
    <instruction>Be concise and focus on the aspects mentioned in the user's prompt.</instruction>
    <instruction>Consider the current memory content when discussing the file, if relevant.</instruction>
    <instruction>Keep responses short and concise. Keep response under 3 sentences for concise conversations.</instruction>
</instructions>

<file-content>
{file_content}
</file-content>

{memory_content}

<user-prompt>
{prompt}
</user-prompt>
    """

    # Call the LLM to discuss the file content
    discussion = chat_prompt(discuss_file_prompt, model_name_to_id[model])

    return {
        "status": "File discussed",
        "file_name": os.path.basename(file_path),
        "discussion": discussion,
    }


@timeit_decorator
async def clipboard_to_memory(key: Optional[str] = None) -> dict:
    """
    Copy the content from the clipboard to memory.
    If a key is provided, it will be used to store the content in memory.
    If no key is provided, a default key 'clipboard_content' will be used.
    """
    try:
        clipboard_content = pyperclip.paste()
        memory_key = key if key else "clipboard_content"
        memory_manager.upsert(memory_key, clipboard_content)
        return {
            "status": "success",
            "key": memory_key,
            "message": f"Clipboard content stored in memory under key '{memory_key}'",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to copy clipboard content to memory: {str(e)}",
        }


@timeit_decorator
async def remove_variable_from_memory(prompt: str) -> dict:
    """
    Remove a key from memory if it exists, based on the user's prompt.
    """
    available_keys = memory_manager.list_keys()
    available_keys_str = ", ".join(available_keys)

    select_key_prompt = f"""
<purpose>
    Select a key from the available keys in memory based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the list of available keys, infer which key the user wants to remove from memory.</instruction>
    <instruction>If no key matches, return an empty string for 'key'.</instruction>
</instructions>

<available-keys>
    {available_keys_str}
</available-keys>

<user-prompt>
    {prompt}
</user-prompt>
    """

    key_selection_response = structured_output_prompt(
        select_key_prompt, MemoryKeyResponse
    )

    logging.info(f"Key selection response: {key_selection_response}")

    if not key_selection_response.key:
        return {"status": "not_found", "message": "No matching key found in memory"}

    if memory_manager.delete(key_selection_response.key):
        return {
            "status": "success",
            "message": f"Key '{key_selection_response.key}' removed from memory",
        }
    else:
        return {
            "status": "error",
            "message": f"Failed to remove key '{key_selection_response.key}' from memory",
        }


@timeit_decorator
async def read_file_into_memory(prompt: str) -> dict:
    """
    Read a file from the scratch_pad_dir and save its content into memory based on the user's prompt.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
    available_files = os.listdir(scratch_pad_dir)
    available_files_str = ", ".join(available_files)

    # Build the structured prompt to select the file
    select_file_prompt = f"""
<purpose>
    Select a file from the available files based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to read into memory.</instruction>
    <instruction>If no file matches, return an empty string for 'file'.</instruction>
</instructions>

<available-files>
    {available_files_str}
</available-files>

<user-prompt>
    {prompt}
</user-prompt>
    """

    # Call the LLM to select the file
    file_selection_response = structured_output_prompt(
        select_file_prompt,
        FileReadResponse,
        llm_model=model_name_to_id[ModelName.fast_model],
    )

    if not file_selection_response.file:
        return {"status": "error", "message": "No matching file found"}

    file_path = os.path.join(scratch_pad_dir, file_selection_response.file)

    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"File '{file_selection_response.file}' not found in scratch_pad_dir",
        }

    try:
        with open(file_path, "r") as file:
            content = file.read()

        memory_manager.upsert(file_selection_response.file, content)
        return {
            "status": "success",
            "message": f"File '{file_selection_response.file}' content saved to memory",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to read file '{file_selection_response.file}' into memory: {str(e)}",
        }


async def read_dir_into_memory() -> dict:
    """
    Read all files from the scratch_pad_dir and save their content into memory.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    try:
        files = os.listdir(scratch_pad_dir)
        for file_name in files:
            file_path = os.path.join(scratch_pad_dir, file_name)
            if os.path.isfile(file_path):
                with open(file_path, "r") as file:
                    content = file.read()
                memory_manager.upsert(file_name, content)

        return {
            "status": "success",
            "message": f"All files from '{scratch_pad_dir}' have been read into memory",
            "files_read": len(files),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to read directory into memory: {str(e)}",
        }


@timeit_decorator
async def scrap_to_file_from_clipboard() -> dict:
    """
    Get content from clipboard, validate it's a URL, generate a file name,
    scrape the URL, and save the content to a file in the scratch_pad_dir.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")

    try:
        # Get content from clipboard
        url = pyperclip.paste().strip()

        # Validate URL (simple check, can be improved)
        if not url.startswith(("http://", "https://")):
            return {
                "status": "error",
                "message": "Clipboard content is not a valid URL",
            }

        # Generate file name
        file_name_prompt = f"""
<purpose>
    Generate a suitable file name for the content of this URL: {url}
</purpose>

<instructions>
    <instruction>Create a short, descriptive file name based on the URL.</instruction>
    <instruction>Use lowercase letters, numbers, and underscores only.</instruction>
    <instruction>Include the .md extension at the end.</instruction>
</instructions>
        """

        class FileNameResponse(BaseModel):
            file_name: str

        file_name_response = structured_output_prompt(
            file_name_prompt, FileNameResponse
        )
        file_name = file_name_response.file_name

        # Scrape URL
        content = scrap_url_clean(url)

        # Save to file
        file_path = os.path.join(scratch_pad_dir, file_name)
        with open(file_path, "w") as file:
            file.write(content)

        return {
            "status": "success",
            "message": f"Content scraped and saved to {file_path}",
            "file_name": file_name,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to scrape URL and save to file: {str(e)}",
        }


@timeit_decorator
async def runnable_code_check(prompt: str) -> dict:
    """
    Checks if the code in the specified file is runnable. If not, provides the necessary changes to make it runnable.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
    memory_content = memory_manager.get_xml_for_prompt(["*"])

    # Step 1: Select the file based on the prompt
    select_file_prompt = f"""
<purpose>
    Select a file from the available files based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the list of available files, infer which file the user wants to check for runnable code.</instruction>
    <instruction>If no file matches, return an empty string for 'file'.</instruction>
</instructions>

<available-files>
    {", ".join(os.listdir(scratch_pad_dir))}
</available-files>

<user-prompt>
    {prompt}
</user-prompt>
    """

    file_selection_response = structured_output_prompt(
        select_file_prompt,
        FileReadResponse,
        llm_model=model_name_to_id[ModelName.fast_model],
    )

    if not file_selection_response.file:
        return {"status": "No matching file found for the given prompt."}

    file_path = os.path.join(scratch_pad_dir, file_selection_response.file)

    if not os.path.exists(file_path):
        return {
            "status": f"File '{file_selection_response.file}' does not exist in '{scratch_pad_dir}'."
        }

    # Read the file content
    try:
        with open(file_path, "r") as f:
            code_content = f.read()
    except Exception as e:
        return {"status": "Error", "message": f"Failed to read the file: {str(e)}"}

    # Step 2: Determine if the code is runnable
    check_runnable_prompt = f"""
<purpose>
    Determine if the following code is runnable.
</purpose>

<instructions>
    <instruction>Analyze the code and determine if it can be executed without errors.</instruction>
    <instruction>Respond with a boolean value indicating the result.</instruction>
    <instruction>Consider the current memory content when analyzing the code.</instruction>
</instructions>

<code-content>
{code_content}
</code-content>

{memory_content}
"""

    is_runnable_response = structured_output_prompt(check_runnable_prompt, IsRunnable)

    if is_runnable_response.code_is_runnable:
        return {"status": "success", "message": "The code is runnable."}

    # Step 3: If not runnable, get the necessary changes
    make_runnable_prompt = f"""
<purpose>
    Provide the necessary changes to make the following code runnable.
</purpose>

<instructions>
    <instruction>Analyze the code and list the changes required to make it executable without errors.</instruction>
    <instruction>Provide a list of change descriptions and the full updated code.</instruction>
    <instruction>Do not include any additional commentary.</instruction>
    <instruction>Consider the current memory content when applying changes.</instruction>
</instructions>

<code-content>
{code_content}
</code-content>

{memory_content}
"""

    make_runnable_response = structured_output_prompt(
        make_runnable_prompt, MakeCodeRunnableResponse
    )

    # Write the updated code to the file
    try:
        with open(file_path, "w") as f:
            f.write(make_runnable_response.full_updated_code)
    except Exception as e:
        return {"status": "Error", "message": f"Failed to update the file: {str(e)}"}

    return {
        "status": "code_updated",
        "message": "The code was not runnable. Necessary changes have been applied.",
        "changes": make_runnable_response.changes_described,
        "file_name": file_selection_response.file,
    }


@timeit_decorator
async def run_python(prompt: str) -> dict:
    """
    Executes a Python script from the scratch_pad_dir based on the user's prompt.
    Returns the output and a success or failure status.
    """
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
    memory_content = memory_manager.get_xml_for_prompt(["*"])

    # Step 1: Select the file based on the prompt
    select_file_prompt = f"""
<purpose>
    Select a Python file to execute based on the user's prompt.
</purpose>

<instructions>
    <instruction>Based on the user's prompt and the list of available Python files, infer which file the user wants to execute.</instruction>
    <instruction>If no file matches, return an empty string for 'file'.</instruction>
</instructions>

<available-files>
    {", ".join([f for f in os.listdir(scratch_pad_dir) if f.endswith('.py')])}
</available-files>

<memory-content>
    {memory_content}
</memory-content>

<user-prompt>
    {prompt}
</user-prompt>
    """

    file_selection_response = structured_output_prompt(
        select_file_prompt,
        FileReadResponse,
        llm_model=model_name_to_id[ModelName.fast_model],
    )

    if not file_selection_response.file:
        return {
            "status": "error",
            "message": "No matching Python file found for the given prompt.",
        }

    file_path = os.path.join(scratch_pad_dir, file_selection_response.file)

    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": f"File '{file_selection_response.file}' does not exist in '{scratch_pad_dir}'.",
        }

    # Read the Python code from the selected file
    try:
        with open(file_path, "r") as f:
            python_code = f.read()
    except Exception as e:
        return {"status": "error", "message": f"Failed to read the file: {str(e)}"}

    # Execute the Python code using run_uv_script
    output = run_uv_script(python_code)

    # Save the output to a file with '_output' suffix
    output_file_name = os.path.splitext(file_selection_response.file)[0] + "_output.txt"
    output_file_path = os.path.join(scratch_pad_dir, output_file_name)
    with open(output_file_path, "w") as f:
        f.write(output)

    # Determine success based on presence of errors
    if "Traceback" in output or "Error" in output:
        success = False
        error_message = output
    else:
        success = True
        error_message = None

    return {
        "status": "success" if success else "failure",
        "error": error_message,
        "file_name": file_selection_response.file,
        "output_file": output_file_name,
    }


# Map function names to their corresponding functions
function_map = {
    "get_current_time": get_current_time,
    "get_random_number": get_random_number,
    "open_browser": open_browser,
    "create_file": create_file,
    "update_file": update_file,
    "delete_file": delete_file,
    "discuss_file": discuss_file,
    "clipboard_to_memory": clipboard_to_memory,
    "remove_variable_from_memory": remove_variable_from_memory,
    "read_file_into_memory": read_file_into_memory,
    "read_dir_into_memory": read_dir_into_memory,
    "reset_active_memory": reset_active_memory,
    "add_to_memory": add_to_memory,
    "scrap_to_file_from_clipboard": scrap_to_file_from_clipboard,
    "generate_diagram": generate_diagram,
    "runnable_code_check": runnable_code_check,
    "run_python": run_python,
    "ingest_file": ingest_file,
}

# Tools array for session initialization
tools = [
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
        "name": "reset_active_memory",
        "description": "Resets the active memory to an empty dictionary.",
        "parameters": {
            "type": "object",
            "properties": {
                "force_delete": {
                    "type": "boolean",
                    "description": "Whether to force reset the memory without confirmation. Defaults to false if not specified.",
                },
            },
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
                    "description": "The model to use for updating the file content. Defaults to 'base_model' if not explicitly specified.",
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
    {
        "type": "function",
        "name": "discuss_file",
        "description": "Discusses a file's content based on the user's prompt, considering the current memory content.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's prompt, question, or statement describing what to discuss about the file content.",
                },
                "model": {
                    "type": "string",
                    "enum": [
                        "state_of_the_art_model",
                        "reasoning_model",
                        "base_model",
                        "fast_model",
                    ],
                    "description": "The model to use for discussing the file content. Defaults to 'base_model' if not explicitlyspecified.",
                },
            },
            "required": ["prompt"],  # 'model' is optional
        },
    },
    {
        "type": "function",
        "name": "clipboard_to_memory",
        "description": "Copies the content from the clipboard to memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key to use for storing the clipboard content in memory. If not provided, a default key 'clipboard_content' will be used.",
                },
            },
            "required": [],  # 'key' is optional
        },
    },
    {
        "type": "function",
        "name": "remove_variable_from_memory",
        "description": "Remove/drop/delete a variable from memory based on the user's prompt.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's prompt describing what variable to remove from memory.",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "type": "function",
        "name": "read_file_into_memory",
        "description": "Reads a file from the scratch_pad_dir and saves its content into memory based on the user's prompt.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's prompt describing the file to read into memory.",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "type": "function",
        "name": "add_to_memory",
        "description": "Adds a key-value pair to memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key to use for storing the value in memory.",
                },
                "value": {
                    "type": "string",
                    "description": "The value to store in memory.",
                },
            },
            "required": ["key", "value"],
        },
    },
    {
        "type": "function",
        "name": "read_dir_into_memory",
        "description": "Reads all files from the scratch_pad_dir and saves their content into memory.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "scrap_to_file_from_clipboard",
        "description": "Gets a URL from the clipboard, scrapes its content, and saves it to a file in the scratch_pad_dir.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "generate_diagram",
        "description": "Generates mermaid diagrams based on the user's prompt.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's prompt describing the diagram to generate.",
                },
                "version_count": {
                    "type": "integer",
                    "description": "The total number of diagram versions to generate. Defaults to 1 if not specified.",
                },
            },
            "required": ["prompt"],  # 'version_count' is optional
        },
    },
    {
        "type": "function",
        "name": "runnable_code_check",
        "description": "Checks if the code in the specified file is runnable and provides necessary changes if not.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's prompt describing which file to check for runnable code.",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "type": "function",
        "name": "run_python",
        "description": "Executes a Python script from the scratch_pad_dir based on the user's prompt and returns the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's prompt describing which Python file to execute.",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "type": "function",
        "name": "ingest_file",
        "description": "Selects a file based on the user's prompt, reads its content, and returns the file data.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The user's prompt describing which file to ingest.",
                },
            },
            "required": ["prompt"],
        },
    },
]
