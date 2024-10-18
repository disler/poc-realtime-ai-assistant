# Tools

## Utility Functions
- `get_current_time`: Returns the current time.
- `get_random_number`: Returns a random number between 1 and 100.
- `open_browser`: Opens a browser tab with the best-fitting URL based on the user's prompt.
- `runnable_code_check`: Checks if the code in the specified file is runnable and provides necessary changes if not.
- `run_python`: Executes a Python script from the `scratch_pad_dir` based on the user's prompt and returns the output.

## File Operations
- `create_file`: Generates content for a new file based on the user's prompt and file name.
- `update_file`: Updates a file based on the user's prompt.
- `delete_file`: Deletes a file based on the user's prompt.
- `discuss_file`: Discusses a file's content based on the user's prompt, considering the current memory content.
- `read_file_into_memory`: Reads a file from the scratch_pad_dir and saves its content into memory based on the user's prompt.
- `read_dir_into_memory`: Reads all files from the scratch_pad_dir and saves their content into memory.
- `clipboard_to_file`: Gets content from clipboard, generates a file name based on the content, and saves the content (trimmed to 1000 chars max) to a file in the scratch_pad_dir.

## Memory Management
- `clipboard_to_memory`: Copies the content from the clipboard to memory.
- `add_to_memory`: Adds a key-value pair to memory.
- `remove_variable_from_memory`: Removes a variable from memory based on the user's prompt.
- `reset_active_memory`: Resets the active memory to an empty dictionary.

## Information Sourcing
- `scrap_to_file_from_clipboard`: Gets a URL from the clipboard, scrapes its content, and saves it to a file in the scratch_pad_dir.

## Data Visualization
- `generate_diagram`: Generates mermaid diagrams based on the user's prompt.
- `create_python_chart`: Generates a Python script to create a chart based on the user's prompt and a specified CSV file. The function reads the CSV file, provides a preview of the data, and generates code for creating the requested chart type using libraries like matplotlib or seaborn.

## AI Assistant Chat History Management
- `ingest_memory`: Returns the current memory content using memory_manager and returns it to be read into the realtime api chat history.
- `ingest_file`: Selects a file based on the user's prompt, reads its content, and returns the file data to be read into the realtime api chat history.

## SQL and Database Operations
- `load_tables_into_memory`: Loads table definitions from Database and saves them to active memory.
- `generate_sql_save_to_file`: Generates an SQL query based on user's prompt and saves it to a file.
- `generate_sql_and_execute`: Generates an SQL query based on the user's prompt, executes it, and saves the results to a file in the specified format (CSV, JSONL, or JSON array).
- `run_sql_file`: Executes an SQL file based on the user's prompt, and saves the results to the specified format (CSV, JSONL, or JSON array).