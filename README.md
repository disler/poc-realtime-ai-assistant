# POC Python Realtime API o1 assistant
> This is a proof of concept for using the OpenAI's [Realtime API](https://openai.com/index/introducing-the-realtime-api/) to chain tools, call o1-preview & o1-mini, [structure output](https://openai.com/index/introducing-structured-outputs-in-the-api/) responses, and glimpse into the future of **AI assistant powered engineering**.
>
> See video where we [use and discuss this POC](https://youtu.be/vN0t-kcPOXo)
>
> See video where we [add memory and tools to the assistant](https://youtu.be/090oR--s__8)
>
> This codebase is a v0.2, poc. It's buggy, but contains the core ideas for realtime personal ai assistants & AI Agents.

<img src="./images/engineers-ai-assistant.png" alt="engineers-ai-assistant" style="max-width: 800px;">

<img src="./images/ada-is-back.png" alt="realtime-assistant" style="max-width: 800px;">

## Setup
- [Install uv](https://docs.astral.sh/uv/), the hyper modern Python package manager.
- Setup environment `cp .env.sample .env` add your `OPENAI_API_KEY` and a `FIRECRAWL_API_KEY` for scraping.
- Update `personalization.json` to fit your setup
- Install dependencies `uv sync`
- Run the realtime assistant `uv run main` or `uv run main --prompts "Hello, how are you?|What time is it?|Open Hacker News"`

## Assistant Tools
The assistant is equipped with the following tools:

### Utility Functions
- `get_current_time`: Returns the current time.
- `get_random_number`: Returns a random number between 1 and 100.
- `open_browser`: Opens a browser tab with the best-fitting URL based on the user's prompt.
- `generate_diagram`: Generates mermaid diagrams based on the user's prompt.
- `runnable_code_check`: Checks if the code in the specified file is runnable and provides necessary changes if not.
- `run_python`: Executes a Python script from the `scratch_pad_dir` based on the user's prompt and returns the output.

### Browser and File Operations
- `create_file`: Generates content for a new file based on the user's prompt and file name.
- `update_file`: Updates a file based on the user's prompt.
- `delete_file`: Deletes a file based on the user's prompt.
- `discuss_file`: Discusses a file's content based on the user's prompt, considering the current memory content.
- `read_file_into_memory`: Reads a file from the scratch_pad_dir and saves its content into memory based on the user's prompt.
- `read_dir_into_memory`: Reads all files from the scratch_pad_dir and saves their content into memory.

### Memory Management
- `clipboard_to_memory`: Copies the content from the clipboard to memory.
- `add_to_memory`: Adds a key-value pair to memory.
- `remove_variable_from_memory`: Removes a variable from memory based on the user's prompt.
- `reset_active_memory`: Resets the active memory to an empty dictionary.

### Information Sourcing
- `scrap_to_file_from_clipboard`: Gets a URL from the clipboard, scrapes its content, and saves it to a file in the scratch_pad_dir. Requires a [firecrawl](https://www.firecrawl.dev/) `FIRECRAWL_API_KEY` environment variable.
- `ingest_file`: Selects a file based on the user's prompt, reads its content, and returns the file data.
- `ingest_memory`: Returns the current memory content using memory_manager.
- `clipboard_to_file`: Gets content from clipboard, generates a file name based on the content, and saves the content (trimmed to 1000 chars max) to a file in the scratch_pad_dir.
- `load_tables_into_memory`: Loads table definitions from Database and saves them to active memory.
- `generate_sql_save_to_file`: Generates an SQL query based on user's prompt and saves it to a file.

## Try This

### Voice Commands
Here are some voice commands you can try with the assistant:

- "Hey Ada, how are you?"
- "What's the current time?"
- "Generate a random number."
- "Open ChatGPT, Claude, and Hacker News."
- "Create a new CSV file called user analytics with 10 mock rows."
- "Update the user analytics file, add 20 additional mock rows, use a reasoning model."
- "Get the current time, then add the current time to memory with the key 'current_time'."
- "Hey Ada, generate a diagram outlining the architecture of a minimal tiktok clone."
- "Hey Ada, check if `example.py` is runnable."
- "Hey Ada, run `example.py`."

### CLI Text Prompts
You can also pass text prompts to the assistant via the CLI.
Use '|' to separate prompts to chain commands.

- `uv run main --prompts "Hello, how are you?"`
- `uv run main --prompts "Open Hacker News"`
- `uv run main --prompts "Hey Ada!|What time is it?|Open Hacker News|Open Simon Willison blog|Open Aider"`
- `uv run main --prompts "copy my current clipboard to memory"`
- `uv run main --prompts "copy my current clipboard to memory with the key 'url'"`
- `uv run main --prompts "call remove_variable_from_memory to delete the clipboard_content variable from active memory"`
- `uv run main --prompts "Create a new CSV file called user analytics with 10 mock rows."`
- `uv run main --prompts "read file user analytics into memory"`
- `uv run main --prompts "reset active memory"`
- `uv run main --prompts "add to memory the key 'project_status' with the value 'in progress'"`
- `uv run main --prompts "read all files in the scratch pad directory into memory"`
- `uv run main --prompts "scrape the URL from my clipboard and save it to a file"`
- `uv run main --prompts "ada update the openai_structured_outputs file. clean it up and focus on the coding examples and the key usecases of structured outputs. use a fast model"`
- `uv run main --prompts "Generate a diagram outlining the architecture of a minimal tiktok clone"`
- `uv run main --prompts "Check if example.py is runnable code"`
- `uv run main --prompts "Run example.py"`

## Code Breakdown

### Code Organization
The codebase is organized within the `src/realtime_api_async_python` directory. The application is modularized, with core functionality divided into separate Python modules located in the `modules/` directory. Tests are located in the `tests/` directory, providing a starting point for testing the application's components.

### Important Files and Directories
- **`main.py`**: This is the entry point of the application. It sets up the WebSocket connection, handles audio input/output, and manages the interaction between the user and the AI assistant.
- **`modules/` Directory**: Contains various modules handling different functionalities of the assistant:
  - `audio.py`: Handles audio playback.
  - `async_microphone.py`: Manages asynchronous audio input.
  - `llm.py`: Interfaces with language models.
  - `tools.py`: Contains definitions of tools that the assistant can use.
  - `utils.py`: Provides utility functions used across the application.
  - `memory_management.py`: Manages the assistant's memory.
- **`tests/` Directory**: Contains minimal tests for the application's modules.
- **`active_memory.json`**: Stores the assistant's active memory state, allowing it to persist information between interactions.

### Memory Management
The assistant uses the `MemoryManager` class in `memory_management.py` to handle memory operations. This class provides methods to create, read, update, delete, and list memory entries. Memory is stored persistently in `active_memory.json`, enabling the assistant to access and manipulate memory across sessions.

### Tools Framework
Tools are functions defined in `modules/tools.py` that extend the assistant's capabilities. These tools are mapped in `function_map` and are available for the assistant to perform actions based on user requests. The assistant uses these tools to execute specific tasks, enhancing its functionality and allowing for dynamic interactions.

## Improvements
> Up for a challenge? Here are some ideas on how to improve the experience:

- Add interruption handling. Current version prevents it for simplicity.
- Add transcript logging.
- Make personalization.json a pydantic type.
- Let tools run in parallel.
- Fix audio randomly cutting out near the end.

## Resources
- https://www.firecrawl.dev/
- https://youtu.be/vN0t-kcPOXo
- https://youtu.be/090oR--s__8
- https://openai.com/index/introducing-the-realtime-api/
- https://openai.com/index/introducing-structured-outputs-in-the-api/
- https://platform.openai.com/docs/guides/realtime/events
- https://platform.openai.com/docs/api-reference/realtime-client-events/response-create
- https://platform.openai.com/playground/realtime
- https://github.com/Azure-Samples/aoai-realtime-audio-sdk/blob/main/README.md
- https://docs.astral.sh/uv/
- https://docs.astral.sh/uv/guides/scripts/#running-a-script-with-dependencies
