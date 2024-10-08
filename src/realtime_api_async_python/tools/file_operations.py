import json
import os

from pydantic import BaseModel
from ..openai.chat_prompt import chat_prompt
from ..openai.structured_output_prompt import structured_output_prompt
from ..openai.models import ModelName, model_name_to_id
from ..utils.timeit_decorator import timeit_decorator


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
