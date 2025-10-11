# Code Combiner

A Python script to scan a specified directory, identify code files based on their extensions, and combine their contents into a single output file. It respects `.gitignore` patterns by default, supports custom file extensions, and can include hidden files. The script also counts tokens in the generated output file.

## Features

-   **Combine Code Files**: Merges multiple code files into a single, readable text file.
-   **Gitignore Support**: Automatically excludes files and directories specified in `.gitignore` by default.
-   **Hidden File Control**: Ignores hidden files and folders by default, with an option to include them.
-   **Custom Extensions**: Allows users to specify which file extensions to include.
-   **Token Counting**: Provides a token count of the combined output, useful for AI model contexts.
-   **Error Handling**: Basic error handling for file operations and token counting.

## Installation

1.  **Clone the repository** (if you haven't already):

    ```bash
    git clone https://github.com/your-username/DevScripts.git
    cd DevScripts
    ```

2.  **Create and activate a virtual environment**:

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

## Usage

```bash
.venv/bin/python src/code_combiner.py <directory> [options]
```

### Arguments

-   `<directory>`: The path to the directory to scan for code files.

### Options

-   `-o, --output <filename>`: Specify the output file name (default: `combined_code.txt`).
-   `-e, --extensions <ext1> <ext2> ...`: Custom file extensions to include (space-separated, e.g., `.py .js .ts`). Extensions must start with a dot.
-   `--exclude <ext1> <ext2> ...`: Custom file extensions to exclude (space-separated, e.g., `.txt .md`). Exclusions take precedence over inclusions.
-   `--no-gitignore`: Do not respect the `.gitignore` file. All files not explicitly excluded by other means will be considered.
-   `--include-hidden`: Include hidden files and folders (those starting with a dot). By default, hidden files are ignored.
-   `--no-tokens`: Do not count tokens in the combined output file.
-   `--header-width <width>`: Specify the width of the separator lines in the combined file header (default: 80).

### Examples

1.  **Combine all Python and JavaScript files in the current directory, ignoring hidden files and `.gitignore` entries (default behavior)**:

    ```bash
    .venv/bin/python src/code_combiner.py . -o combined_project.txt -e .py .js
    ```

2.  **Combine all files in a specific directory, including hidden files, and ignoring `.gitignore`**: 

    ```bash
    .venv/bin/python src/code_combiner.py /path/to/your/project --include-hidden --no-gitignore -o all_project_files.txt
    ```

3.  **Combine files in a directory, respecting `.gitignore`, but only including `.md` files**:

    ```bash
    .venv/bin/python src/code_combiner.py . -e .md -o documentation.txt
    ```

## Development

### Code Quality Checks

Use the provided `Makefile` for code quality checks:

-   `make format`: Formats the code using `black`.
-   `make lint`: Lints the code using `ruff`.
-   `make check`: Runs static type checking with `mypy`.
-   `make all`: Runs format, lint, and check.

```bash
make all
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.