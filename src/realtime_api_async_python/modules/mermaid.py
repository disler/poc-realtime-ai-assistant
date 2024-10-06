# mermaid.py

import os
import base64
import requests
from PIL import Image, UnidentifiedImageError
import io
from typing import Optional, List
from pydantic import BaseModel
from dotenv import load_dotenv
import openai

from realtime_api_async_python.modules.memory_management import memory_manager

from realtime_api_async_python.modules.llm import structured_output_prompt

# Load environment variables from .env file
load_dotenv()


class MermaidResponse(BaseModel):
    base_name: str
    mermaid_diagrams: List[str]


# Helper functions
def build_file_path(name: str):
    scratch_pad_dir = os.getenv("SCRATCH_PAD_DIR", "./scratchpad")
    os.makedirs(scratch_pad_dir, exist_ok=True)
    return os.path.join(scratch_pad_dir, name)


def build_image(graph: str, filename: str) -> Optional[Image.Image]:
    graphbytes = graph.encode("utf8")
    base64_bytes = base64.b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")

    url = f"https://mermaid.ink/img/{base64_string}"

    response = requests.get(url)
    try:
        img = Image.open(io.BytesIO(response.content))
        return img
    except UnidentifiedImageError:
        print(f"Error: Unable to generate image for '{filename}'")
        return None


def mm(graph: str, filename: str) -> Optional[Image.Image]:
    img = build_image(graph, filename)
    if img:
        output_path = build_file_path(filename)
        img.save(output_path)
        return img
    else:
        return None


# Main function to generate diagrams
async def generate_diagram(prompt: str, version_count: int = 1) -> dict:
    """
    Generates diagrams based on the prompt, producing multiple versions.

    Args:
        prompt (str): The prompt describing the diagram to generate.
        version_count (int): The number of versions to generate.

    Returns:
        dict: A dictionary containing information about the generated diagrams.
    """
    memory_content = memory_manager.get_xml_for_prompt(["*"])

    mermaid_prompt = f"""
<purpose>
    Generate {version_count} mermaid diagram(s) based on the user's prompt and the current memory content.
</purpose>

<instructions>
    <instruction>For each version, create a unique mermaid diagram code that represents the user's prompt.</instruction>
    <instruction>Generate a suitable 'base_name' for the filenames based on the user's prompt. Use lowercase letters, numbers, and underscores only.</instruction>
    <instruction>Only provide the 'base_name' and the list of mermaid diagram codes in a dictionary format, without any additional text or formatting.</instruction>
    <instruction>Consider the current memory content when generating the diagrams, if relevant.</instruction>
</instructions>

<user_prompt>
    {prompt}
</user_prompt>

{memory_content}
"""

    response = structured_output_prompt(mermaid_prompt, MermaidResponse)
    base_name = response.base_name

    diagrams_info = []
    successful_count = 0
    failed_count = 0

    for i, mermaid_code in enumerate(response.mermaid_diagrams):
        image_filename = f"diagram_{base_name}_{i+1}.png"
        text_filename = f"diagram_text_{base_name}_{i+1}.md"

        img = mm(mermaid_code, image_filename)

        if img:
            # Save the mermaid code to a text file
            text_file_path = build_file_path(text_filename)
            with open(text_file_path, "w") as f:
                f.write(mermaid_code)

            successful_count += 1
            diagrams_info.append(
                {
                    "version": i + 1,
                    "image_file": build_file_path(image_filename),
                    "text_file": text_file_path,
                    "mermaid_code": mermaid_code,
                }
            )
        else:
            failed_count += 1
            continue

    if successful_count > 0:
        message = f"Generated {successful_count} diagram(s)"
        if failed_count > 0:
            message += f"; {failed_count} diagram(s) failed to generate"
        status = "success"
    else:
        message = "No diagrams were generated successfully."
        status = "failure"

    return {
        "status": status,
        "message": message,
    }
