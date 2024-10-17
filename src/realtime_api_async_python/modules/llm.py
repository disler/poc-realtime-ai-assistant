import openai
import os
from pydantic import BaseModel


def structured_output_prompt(
    prompt: str, response_format: BaseModel, llm_model: str = "gpt-4o-2024-08-06"
) -> BaseModel:
    """
    Parse the response from the OpenAI API using structured output.

    Args:
        prompt (str): The prompt to send to the OpenAI API.
        response_format (BaseModel): The Pydantic model representing the expected response format.

    Returns:
        BaseModel: The parsed response from the OpenAI API.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.beta.chat.completions.parse(
        model=llm_model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        response_format=response_format,
    )

    message = completion.choices[0].message

    if not message.parsed:
        raise ValueError(message.refusal)

    return message.parsed


def chat_prompt(prompt: str, model: str) -> str:
    """
    Run a chat model based on the specified model name.

    Args:
        prompt (str): The prompt to send to the OpenAI API.
        model (str): The model ID to use for the API call.

    Returns:
        str: The assistant's response.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )

    message = completion.choices[0].message

    return message.content


def parse_markdown_backticks(str) -> str:
    if "```" not in str:
        return str.strip()
    # Remove opening backticks and language identifier
    str = str.split("```", 1)[-1].split("\n", 1)[-1]
    # Remove closing backticks
    str = str.rsplit("```", 1)[0]
    # Remove any leading or trailing whitespace
    return str.strip()
