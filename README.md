# codemeld

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
-   `toml`: For reading `pyproject.toml` configuration file. (Note: `tomllib` is used for Python 3.11+; `toml` is a fallback for older versions.)

### Development Dependencies

-   `pytest`: For running unit tests.
-   `ruff`: For linting and formatting.
-   `ty`: For static type checking.

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

### Building a Standalone Executable with PyInstaller

You can package codemeld into a standalone executable using PyInstaller. This allows you to run the application without a Python environment installed on the target machine.

1.  **Install PyInstaller**:

    ```bash
    .venv/bin/pip install pyinstaller
    ```

2.  **Build the Executable**:
    Run PyInstaller from the project root. The `--onefile` option creates a single executable file, `--name codemeld` sets the executable name, and `--distpath build/dist` specifies the output directory. The `--hidden-import` flags are crucial for `tiktoken` to function correctly in the bundled application.

    ```bash
    .venv/bin/pyinstaller src/code_combiner.py --onefile --name codemeld --distpath build/dist --hidden-import=tiktoken_ext --hidden-import=tiktoken_ext.openai_public
    ```

    The executable will be created in the `build/dist` directory.

3.  **Run the Executable**:

    ```bash
    ./build/dist/codemeld <directory> [options]
    ```

    For example:

    ```bash
    ./build/dist/CodeMeld . -o combined_project.txt
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
-   `--dry-run`: Simulate the combination process without writing any output file. Useful for previewing what would be included.
-   `--max-file-size-kb <size>`: Exclude files larger than the specified size in kilobytes.
-   `--token-encoding <encoding>`: Specify the token encoding model to use (default: `cl100k_base`).
-   `--custom-file-headers <json_string>`: Provide custom headers for specific file extensions as a JSON string (e.g., `'{"py": "# Python File: {path}", "js": "// Javascript File: {path}"}'`).
-   `--max-memory-mb <size>`: Set a maximum memory limit in megabytes for in-memory processing. If exceeded, the script will attempt to use a streaming approach.

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

2.  **Perform a dry run to see which files would be included, excluding files larger than 1MB**:

    ```bash
    .venv/bin/python main.py . --dry-run --max-file-size-kb 1024
    ```

3.  **Combine files with custom headers for Python and JavaScript files**:

    ```bash
    .venv/bin/python main.py . -e .py .js -o combined_with_headers.txt --custom-file-headers '{"py": "# Python File: {path}\n# ---------------------\n", "js": "// Javascript File: {path}\n// ---------------------\n"}'
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

<details>
<summary>Click to expand JSON example</summary>

```json
{
        "file1.py": "print('hello')",
        "file2.js": "console.log('world')",
        "subdir/file3.py": "x = 1"
    }
```

</details>

6.  **Sample XML Output**:

<details>
<summary>Click to expand XML example</summary>

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

</details>

### Using with Large Language Models (LLMs)

The primary goal of this script is to generate a single file that can be easily copied and pasted into an LLM chat interface.

-   **Text Format (`--format text`)**: This is the default and recommended format for most LLMs. It produces a clean, readable output that is easy to copy and paste.
-   **Markdown Format (`--format markdown`)**: This format is useful when you want to preserve the file structure and code formatting in a more structured way. Most LLMs render Markdown correctly. When converting from `json` or `xml` format, using `--convert-to markdown` will also generate a structured Markdown output suitable for LLMs.
-   **JSON and XML Formats (`--format json` or `--format xml`)**: These formats are less common for direct use with LLMs but can be useful for programmatic analysis or if the LLM has specific input requirements.

**Tip for Large Projects**: For very large projects, consider using the `--no-tokens` flag to disable token counting. This enables a memory-safe streaming approach, preventing potential out-of-memory errors.

### More Examples

7.  **Convert JSON Output to Markdown**:
    Generate an intermediate JSON representation and then convert it to a clean Markdown file.

    ```bash
    .venv/bin/python main.py . -e .py -o combined.md --format json --convert-to markdown
    ```

8.  **Force Streaming for a Large Project**:
    To avoid high memory usage, you can set a low memory limit to force the script to use a streaming approach.

    ```bash
    .venv/bin/python main.py . -o combined.txt --max-memory-mb 100
    ```

9.  **Always Include a Specific File**:
    Ensure a specific configuration file is included, even if it doesn't have a standard extension or is in a hidden directory.

    ```bash
    .venv/bin/python main.py . -o combined.txt --always-include ./.config/app.conf
    ```

### Extending with Custom Formatters

codemeld can be extended with custom formatters using a plugin-based architecture. This allows you to define your own output formats and integrate them seamlessly with the `main.py` script.

#### Creating a Custom Formatter Package

To create a custom formatter, you'll typically set up a small Python package.

1.  **Project Structure**:
    Organize your custom formatter in a dedicated directory, for example:

    ```
    my_custom_formatter_package/
    ├── pyproject.toml
    └── src/
        └── my_custom_formatter/
            ├── __init__.py
            └── formatter.py
    ```

2.  **Implement the `OutputFormatter` interface** (`src/my_custom_formatter/formatter.py`):
    Create a class that inherits from `OutputFormatter` and implements the required methods (`format_name`, `format_file`, `begin_output`, `end_output`, `supports_streaming`).

    ```python
    # src/my_custom_formatter/formatter.py
    from src.formatters import OutputFormatter
    from pathlib import Path

    class YAMLFormatter(OutputFormatter):
        format_name = "yaml"

        def format_file(self, relative_path: Path, content: str) -> str:
            # Simple YAML-like output
            # Indent content to fit under the 'content:' key
            indented_content = "\n".join(f"      {line}" for line in content.splitlines())
            return f'  - file: "{relative_path}"\n    content: |\n{indented_content}\n'

        def begin_output(self) -> str:
            return "files:\n"

        def end_output(self) -> str:
            return ""

        def supports_streaming(self) -> bool:
            return True
    ```

3.  **Configure `pyproject.toml` for Entry Point**:
    In your custom formatter package's `pyproject.toml`, add an entry point under the `[project.entry-points."codemeld.formatters"]` group. This tells CodeMeld where to find your custom formatter.

    ```toml
    # pyproject.toml in my_custom_formatter_package/
    [project]
    name = "my-custom-formatter"
    version = "0.1.0"
    dependencies = [
        "code-combiner", # Or your main project's name if it's a dependency
    ]

    [project.entry-points."code_combiner.formatters"]
    yaml = "my_custom_formatter.formatter:YAMLFormatter"
    ```

#### Installing and Using Your Custom Formatter

1.  **Install your custom formatter package**:
    Navigate to your `my_custom_formatter_package` directory and install it in editable mode into your CodeMeld's virtual environment:

    ```bash
    cd my_custom_formatter_package
    .venv/bin/pip install -e .
    ```
    (Make sure you have activated codemeld's virtual environment first.)

2.  **Use with `main.py`**:
    Once installed, codemeld will automatically discover and register your custom formatter. You can then use it with the `--format` option:

    ```bash
    .venv/bin/python main.py . --format yaml -o combined.yaml
    ```

This setup allows for a clean separation of concerns, making your custom formatters reusable and easy to manage.

## Architecture

**Filter Chain (Chain of Responsibility)**: The file filtering logic is implemented using the Chain of Responsibility pattern. Each filter is a separate class that handles a specific filtering rule (e.g., checking extensions, hidden files, or `.gitignore` rules). This design was chosen for its modularity and extensibility. While it might seem more complex than a single, monolithic filter class, it makes the code easier to understand, maintain, and extend. Adding a new filter only requires creating a new class that implements the `FileFilter` interface, without modifying the existing code. The performance overhead of this pattern is minimal and is outweighed by the benefits of a clean and maintainable design.

```
┌─────────────────────────────────────────────────────────┐
│                     codemeld                             │
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

### Handling Large Repositories

For very large projects, you might encounter performance or memory issues. Here are some tips:

-   **Use `--no-tokens`**: Disabling token counting (`--no-tokens`) can significantly reduce memory usage and speed up processing, especially for projects with many files.
-   **Set `--max-memory-mb`**: You can set a lower memory threshold (e.g., `--max-memory-mb 100`) to force the script to use streaming output earlier, which is more memory-efficient. Setting it to `0` disables the memory limit entirely.
-   **Exclude large files**: Use `--max-file-size-kb` to skip very large files that might consume excessive memory or processing time.
-   **Optimize `.gitignore`**: Ensure your `.gitignore` file is comprehensive to exclude irrelevant files and directories, reducing the number of files the script needs to process.


## Development

### Code Quality Checks

Use the provided `Makefile` for code quality checks:

-   `make format`: Formats the code using `ruff`.
-   `make lint`: Lints the code using `ruff`.
-   `make check`: Runs static type checking with `ty`.
-   `make check-strict`: Runs `ruff check`, `ty check`, and `pytest`.
-   `make all`: Runs format, lint, and check.

```bash
make all
```

### Dependency Vulnerability Scanning

This project uses `pip-audit` to scan for vulnerabilities in the dependencies.
To run the audit locally, install `pip-audit` and run it:

```bash
pip install pip-audit
pip-audit
```

### Linting with Ruff
Run `ruff check .` to lint the codebase, or `ruff check --fix .` to auto-fix issues. Configuration is defined in `pyproject.toml` under `[tool.ruff]`. To check formatting, run `ruff format --check .`.

## Development Quality Metrics

This project aims for high code quality, enforced by a suite of static analysis tools and comprehensive testing. Key metrics are:

-   **Maintainability Index**: Striving for >95.
-   **Cyclomatic Complexity**: Aiming for <2.5 average.
-   **Type Safety**: 100% strict type checking with `ty check`.
-   **Test Coverage**: Targeting >95% line coverage.

These metrics ensure the codebase is robust, easy to understand, and maintainable.

## Code Quality Evaluation

This project has undergone a thorough code quality evaluation, focusing on maintainability, cyclomatic complexity, type safety, and test coverage. The goal is to achieve a professional-grade Python project ready for publication and long-term maintenance.

## Static Analysis

For detailed information on the static analysis tools and guidelines used in this project (Ruff, MyPy, Radon), please refer to the [Static Analysis Guidelines](docs/static_analysis.md) document.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
