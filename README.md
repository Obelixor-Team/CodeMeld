# Code Combiner

A Python script to scan a specified directory, identify code files based on their extensions, and combine their contents into a single output file. It respects `.gitignore` patterns by default, supports custom file extensions, and can include hidden files. The script also counts tokens in the generated output file.

## Features

-   **Combine Code Files**: Merges multiple code files into a single, readable text file.
-   **Multiple Output Formats**: Supports `text`, `markdown`, `json`, and `xml` output formats.
-   **Gitignore Support**: Automatically excludes files and directories specified in `.gitignore` by default.
-   **Hidden File Control**: Ignores hidden files and folders by default, with an option to include them.
-   **Custom Extensions**: Allows users to specify which file extensions to include and exclude.
-   **Token Counting**: Provides a token count of the combined output, useful for AI model contexts.
-   **Configuration File**: Supports configuration via `pyproject.toml`.
-   **Error Handling**: Basic error handling for file operations and token counting.

## Dependencies

### Runtime Dependencies

-   `tiktoken`: For counting tokens in the output file.
-   `pathspec`: For handling `.gitignore` patterns.
-   `tqdm`: For showing progress.
-   `toml`: For reading `pyproject.toml` configuration file.

### Development Dependencies

-   `pytest`: For running unit tests.
-   `black`: For code formatting.
-   `ruff`: For linting.
-   `mypy`: For static type checking.
-   `radon`: For calculating code complexity metrics.

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
    make install
    ```

## Usage

```bash
.venv/bin/python main.py <directory> [options]
```

### Arguments

-   `<directory>`: The path to the directory to scan for code files.

### Options

-   `-o, --output <filename>`: Specify the output file name (default: `combined_code.txt`).
-   `-e, --extensions <ext1> <ext2> ...`: Custom file extensions to include (space-separated, e.g., `.py .js .ts`). Extensions must start with a dot.
-   `--exclude <ext1> <ext2> ...`: Custom file extensions to exclude (space-separated, e.g., `.txt .md`). Exclusions take precedence over inclusions.
-   `--format <format>`: Output format (`text`, `markdown`, `json`, `xml`). Default is `text`.
-   `--convert-to <format>`: Convert XML/JSON output to `text` or `markdown` format. This option is only applicable when `--format` is `json` or `xml`.
-   `--no-gitignore`: Do not respect the `.gitignore` file. All files not explicitly excluded by other means will be considered.
-   `--include-hidden`: Include hidden files and folders (those starting with a dot). By default, hidden files are ignored.
-   `--no-tokens`: Do not count tokens in the combined output file.
-   `--header-width <width>`: Specify the width of the separator lines in the combined file header (default: 80).

### Configuration File

Alternatively, you can configure the script using a `pyproject.toml` file in your project's root directory. Settings under the `[tool.code_combiner]` section will be loaded. Command-line arguments will always override settings from the configuration file.

Example `pyproject.toml`:

```toml
[tool.code_combiner]
extensions = [".py", ".js"]
exclude_extensions = [".txt"]
use_gitignore = true
include_hidden = false
count_tokens = true
header_width = 70
format = "markdown"
```

### Examples

1.  **Combine all Python and JavaScript files in the current directory, ignoring hidden files and `.gitignore` entries (default behavior)**:

    ```bash
    .venv/bin/python main.py . -o combined_project.txt -e .py .js
    ```

2.  **Combine all files in a specific directory, including hidden files, and ignoring `.gitignore`**: 

    ```bash
    .venv/bin/python main.py /path/to/your/project --include-hidden --no-gitignore -o all_project_files.txt
    ```

3.  **Combine files in a directory and output as Markdown**:

    ```bash
    .venv/bin/python main.py . -e .py .md -o documentation.md --format markdown
    ```

4.  **Combine files using settings from `pyproject.toml` and output as JSON**:

    ```bash
    .venv/bin/python main.py . -o combined.json --format json
    ```

5.  **Sample JSON Output**:

    ```json
    {
        "file1.py": "print('hello')",
        "file2.js": "console.log('world')",
        "subdir/file3.py": "x = 1"
    }
    ```

6.  **Sample XML Output**:

    ```xml
    <codebase>
        <file>
            <path>file1.py</path>
            <content>print('hello')</content>
        </file>
        <file>
            <path>file2.js</path>
            <content>console.log('world')</content>
        </file>
        <file>
            <path>subdir/file3.py</path>
            <content>x = 1</content>
        </file>
    </codebase>
    ```

### Using with Large Language Models (LLMs)

The primary goal of this script is to generate a single file that can be easily copied and pasted into an LLM chat interface.

-   **Text Format (`--format text`)**: This is the default and recommended format for most LLMs. It produces a clean, readable output that is easy to copy and paste.
-   **Markdown Format (`--format markdown`)**: This format is useful when you want to preserve the file structure and code formatting in a more structured way. Most LLMs render Markdown correctly. When converting from `json` or `xml` format, using `--convert-to markdown` will also generate a structured Markdown output suitable for LLMs.
-   **JSON and XML Formats (`--format json` or `--format xml`)**: These formats are less common for direct use with LLMs but can be useful for programmatic analysis or if the LLM has specific input requirements.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     CodeCombiner                         │
│  (Orchestrates the entire process)                       │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Filters  │  │Formatters│  │Generators│
  │ (Chain)  │  │(Strategy)│  │(Template)│
  └──────────┘  └──────────┘  └──────────┘
        │             │             │
        └─────────────┴─────────────┘
                      │
                      ▼
              ┌───────────────┐
              │   Observers   │
              │  (Publisher)  │
              └───────────────┘
```

**Design Patterns Used:**
- **Strategy Pattern**: OutputFormatter (text/markdown/json/xml)
- **Chain of Responsibility**: FileFilter chain
- **Template Method**: OutputGenerator
- **Observer Pattern**: Progress/metrics reporting
- **Builder Pattern**: Configuration assembly
- **Factory Pattern**: Formatter creation

## Troubleshooting

### `ModuleNotFoundError: No module named 'src'` when running tests

If you encounter this error when running `pytest`, it means Python cannot find the `src` module. The `pytest.ini` file is configured to automatically set the `PYTHONPATH`, so this error should not occur if you are running `pytest` from the project root.

### `Warning: tiktoken not found. Token counting will be skipped.`

This warning indicates that the `tiktoken` library, which is used for token counting, is not installed. `tiktoken` is an optional dependency. If you wish to enable token counting, you can install it using pip:

```bash
pip install tiktoken
```

If you do not need token counting, you can safely ignore this warning.


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

### Linting with Ruff
Run `ruff check .` to lint the codebase, or `ruff check --fix .` to auto-fix issues. Configuration is defined in `pyproject.toml` under `[tool.ruff]`. To check formatting, run `ruff format --check .`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
