## FILE: README.md

```md
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
-   `toml`: For reading `pyproject.toml` configuration file. (Note: `tomllib` is used for Python 3.11+).
  - **Minimum Supported Python Version**: 3.11 (due to use of tomllib and other modern Python features)

### Development Dependencies

-   `pytest`: For running unit tests.
-   `ruff`: For linting and formatting.
-   `mypy`: For static mypype checking. (Note: `mypy` is an experimental mypype checker from Astral and may behave differently from more established tools like `mypy`.)

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
     .venv/bin/pyinstaller main.py --onefile --name codemeld --distpath build/dist --hidden-import=tiktoken_ext --hidden-import=tiktoken_ext.openai_public
     ```

     The executable will be created in the `build/dist` directory.

3.  **Run the Executable**:

     ```bash
     ./build/dist/codemeld <directory> [options]
     ```

     For example:

     ```bash
     ./build/dist/codemeld . -o combined_project.txt
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
-   `--convert-to <format>`: Convert XML/JSON output to `text` or `markdown` format. This option is only applicable when `--format` is `json` or `xml` (enforced by validation).
-   `--no-gitignore`: Do not respect the `.gitignore` file. All files not explicitly excluded by other means will be considered.
-   `--include-hidden`: Include hidden files and folders (those starting with a dot). By default, hidden files are ignored.
-   `--no-tokens`: Do not count tokens in the combined output file.
-   `--header-width <width>`: Specify the width of the separator lines in the combined file header (default: 80).
-   `--dry-run`: Simulate the combination process without writing any output file. Useful for previewing what would be included.
-   `--max-file-size-kb <size>`: Exclude files larger than the specified size in kilobytes.
-   `--token-encoding <encoding>`: Specify the token encoding model to use (default: `cl100k_base`). Note that different models use different encodings; refer to the tiktoken documentation for details.
-   `--custom-file-headers <json_string>`: Provide custom headers for specific file extensions as a JSON string (e.g., `'{"py": "# Python File: {path}", "js": "// Javascript File: {path}"}'`).
-   `--max-memory-mb <size>`: Set a maximum memory limit in megabytes for in-memory processing. If exceeded, the script will fall back to a streaming approach (when token counting is disabled and the formatter supports streaming). Setting to 0 disables the memory limit entirely.

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

4.  **Combine all files in a specific directory, including hidden files, and ignoring `.gitignore`**: 

     ```bash
     .venv/bin/python main.py /path/to/your/project --include-hidden --no-gitignore -o all_project_files.txt
     ```

5.  **Combine files in a directory and output as Markdown**:

     ```bash
     .venv/bin/python main.py . -e .py .md -o documentation.md --format markdown
     ```

6.  **Combine files using settings from `pyproject.toml` and output as JSON**:

     ```bash
     .venv/bin/python main.py . -o combined.json --format json
     ```

7.  **Sample JSON Output**:

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

8.  **Sample XML Output**:

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

9.  **Convert JSON Output to Markdown**:
     Generate an intermediate JSON representation and then convert it to a clean Markdown file.

     ```bash
     .venv/bin/python main.py . -e .py -o combined.md --format json --convert-to markdown
     ```

10.  **Force Streaming for a Large Project**:
     To avoid high memory usage, you can set a low memory limit to force the script to use a streaming approach.

     ```bash
     .venv/bin/python main.py . -o combined.txt --max-memory-mb 100
     ```

11.  **Always Include a Specific File**:
     Ensure a specific configuration file is included, even if it doesn't have a standard extension or is in a hidden directory.

     ```bash
     .venv/bin/python main.py . -o combined.txt --always-include ./.config/app.conf
     ```



### Extending with Custom Formatters

codemeld can be extended with custom formatters using a plugin-based architecture. This allows you to define your own output formats and integrate them seamlessly with the `main.py` script.

#### Creating a Custom Formatter Package

To create a custom formatter, you'll mypypically set up a small Python package.

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

**Filter Chain (Chain of Responsibilimypy)**: The file filtering logic is implemented using the Chain of Responsibilimypy pattern. Each filter is a separate class that handles a specific filtering rule (e.g., checking extensions, hidden files, or `.gitignore` rules). This design was chosen for its modularimypy and extensibilimypy. While it might seem more complex than a single, monolithic filter class, it makes the code easier to understand, maintain, and extend. Adding a new filter only requires creating a new class that implements the `FileFilter` interface, without modifying the existing code. The performance overhead of this pattern is minimal and is outweighed by the benefits of a clean and maintainable design.

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
- **Chain of Responsibilimypy**: FileFilter chain
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

### Code Qualimypy Checks

Use the provided `Makefile` for code qualimypy checks:

-   `make format`: Formats the code using `ruff`.
-   `make lint`: Lints the code using `ruff`.
-   `make check`: Runs static mypype checking with `mypy`.
-   `make check-strict`: Runs `ruff check`, `mypy check`, and `pytest`.
-   `make all`: Runs format, lint, and check.

```bash
make all
```

### Dependency Vulnerabilimypy Scanning

This project uses `pip-audit` to scan for vulnerabilities in the dependencies.
To run the audit locally, install `pip-audit` and run it:

```bash
pip install pip-audit
pip-audit
```

### Linting with Ruff
Run `ruff check .` to lint the codebase, or `ruff check --fix .` to auto-fix issues. Configuration is defined in `pyproject.toml` under `[tool.ruff]`. To check formatting, run `ruff format --check .`.

## Development Qualimypy Metrics

This project aims for high code qualimypy, enforced by a suite of static analysis tools and comprehensive testing. Key metrics are:

-   **Maintainabilimypy Index**: Striving for >95.
-   **Cyclomatic Compleximypy**: Aiming for <2.5 average.
-   **Type Safemypy**: 100% strict mypype checking with `mypy check`.
-   **Test Coverage**: Targeting >95% line coverage.

These metrics ensure the codebase is robust, easy to understand, and maintainable.

## Code Qualimypy Evaluation

This project has undergone a thorough code qualimypy evaluation, focusing on maintainabilimypy, cyclomatic compleximypy, mypype safemypy, and test coverage. The goal is to achieve a professional-grade Python project ready for publication and long-term maintenance.

## Static Analysis

For detailed information on the static analysis tools and guidelines used in this project (Ruff, MyPy, Radon), please refer to the [Static Analysis Guidelines](docs/static_analysis.md) document.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```

## FILE: custom_formatter_example/README.md

```md
# My CodeMeld Formatter

This is an example of a custom formatter for the `code-combiner` script, packaged as a separate installable package.

## Installation

To install this custom formatter, run the following command from the root of this example directory:

```bash
pip install .
```

## Usage

Once installed, you can use the `yaml` format with the `code-combiner` script:

```bash
.venv/bin/python main.py . --format yaml -o combined.yaml
```

```

## FILE: custom_formatter_example/src/my_formatter/formatter.py

```py
from pathlib import Path
from typing import Any


# This is a simplified version of the OutputFormatter for the example.
# In a real-world scenario, this would be imported from the code_combiner package.
class OutputFormatter:
    def __init__(self, **kwargs: Any) -> None:
        # This method is intentionally empty for this example, as no specific
        # initialization is required for the base OutputFormatter in this context.
        pass

    def format_file(self, relative_path: Path, content: str) -> str:
        raise NotImplementedError

    def begin_output(self) -> str:
        raise NotImplementedError

    def end_output(self) -> str:
        raise NotImplementedError

    def supports_streaming(self) -> bool:
        raise NotImplementedError


class YAMLFormatter(OutputFormatter):
    format_name = "yaml"

    def format_file(self, relative_path: Path, content: str) -> str:
        # Simple YAML-like output
        return f'  - file: "{relative_path}"\n    content: |\n' + "\n".join(
            f"      {line}" for line in content.splitlines()
        )

    def begin_output(self) -> str:
        return "files:\n"

    def end_output(self) -> str:
        return ""

    def supports_streaming(self) -> bool:
        return True

```

## FILE: docs/README.md

```md
# Documentation

This directory contains project documentation.

## Architecture Decision Records (ADRs)

ADRs are located in the `adr` directory. They document important architectural decisions made throughout the project's lifecycle.

*   [ADR-001: Use Makefile for Build Automation](./adr/001-use-makefile-for-build-automation.md)

## Performance

The `CodeMeld` script is designed to be efficient, but its performance can be affected by several factors:

*   **Number of files:** The more files to process, the longer it will take.
*   **File size:** Large files consume more memory and take longer to read.
*   **Token counting:** Enabling token counting adds overhead, as it requires an extra processing step.
*   **Memory usage:** The script can operate in two modes: in-memory and streaming. The in-memory mode is faster but consumes more memory. The streaming mode is slower but can handle a larger number of files and larger file sizes without running out of memory.

## Security

Security is an important consideration for `CodeMeld`.

*   **File system access:** The script reads files from the local file system. It includes a security filter to prevent it from accessing files outside the specified project directory. This is a crucial safeguard against accidentally including sensitive files from other parts of the system.
*   **Symbolic links:** By default, the script does not follow symbolic links. This is a security measure to prevent it from following a link to a sensitive file or directory outside the project.
*   **Dependencies:** The project has a minimal set of dependencies, which are regularly scanned for vulnerabilities using `dependabot`.

```

## FILE: docs/adr/001-use-makefile-for-build-automation.md

```md
# 1. Use Makefile for Build Automation

*   **Status:** Accepted
*   **Date:** 2025-10-16

## Context and Problem Statement

The project needs a consistent and easy way to manage common development tasks such as installing dependencies, running tests, linting, and formatting the codebase. Relying on developers to remember and run individual commands can lead to inconsistencies and errors.

## Decision Drivers

*   Simplicity and ease of use.
*   Ubiquity in the Python ecosystem.
*   Ability to chain commands.
*   Desire to have a single entry point for all build and development tasks.

## Considered Options

*   **Makefile:** A classic build automation tool. It's simple, well-understood, and powerful enough for this project's needs.
*   **tox:** A powerful tool for testing in multiple Python environments. It's more complex than a Makefile and might be overkill for this project.
*   **invoke:** A Python-based task execution tool. It's a good alternative to Make, but Make is more common and requires no extra dependencies.
*   **Custom shell scripts:** Can be brittle and less organized than a Makefile.

## Decision Outcome

Chosen option: **Makefile**, because it is simple, effective, and a well-established convention in many projects. It provides a straightforward way to define and run all the necessary development tasks.

```

## FILE: main.py

```py
"""Main entry point for the CodeMeld application."""

import logging
import multiprocessing
import sys

from src.code_combiner import parse_arguments, run_code_combiner
from src.config import CodeMeldError
from src.config_builder import load_and_merge_config

if __name__ == "__main__":
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        args = parse_arguments()
        config = load_and_merge_config(args)
        run_code_combiner(config)
    except CodeMeldError as e:
        logging.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("\nOperation cancelled by user.")
        sys.exit(130)

```

## FILE: requirements-dev.txt

```txt
ruff==0.15.12
mypy
pytest==9.0.3
pytest-cov==7.1.0
types-requests==2.33.0.20260408
types-tqdm==4.67.3.20260408
pytest-mock==3.15.1
types-psutil==7.2.2.20260408
pytest-benchmark==5.2.3
pip-audit==2.10.0
pyinstaller

```

## FILE: requirements.txt

```txt
pathspec==1.1.1
tiktoken==0.12.0
tqdm==4.67.3
psutil==7.2.2

```

## FILE: src/__init__.py

```py
# Copyright (c) 2025 skum

"""Initialization file for the src package."""

__version__ = "0.1.0"

```

## FILE: src/_types.py

```py
# Copyright (c) 2025 skum

"""Defines common type aliases used across the codebase."""

from __future__ import annotations

from typing import Literal

FormatType = Literal["text", "markdown", "json", "xml"]
ConvertType = Literal["text", "markdown"]

```

## FILE: src/code_combiner.py

```py
# Copyright (c) 2025 skum

"""A script to combine code files from a directory into a single output file."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Iterator
from pathlib import Path

import pathspec

from src.config import CodeMeldError, CombinerConfig, MemoryThresholdExceededError
from src.config_builder import load_and_merge_config
from src.context import GeneratorContext
from src.filters import CompositeFilter, FileFilter, FilterChainBuilder
from src.formatters import FormatterFactory
from src.memory_monitor import TracemallocMemoryMonitor
from src.observers import (
    LineCounterObserver,
    Publisher,
    TelemetryObserver,
    TokenCounterObserver,
)
from src.output_generator import InMemoryOutputGenerator, StreamingOutputGenerator
from src.ui import LiveUI


def write_output(
    output_path: Path,
    output_content: str,
    force: bool,
    dry_run: bool = False,
    dry_run_output_path: Path | None = None,
) -> None:
    """Write the combined output content to the specified file."""
    if dry_run:
        logging.info("\n--- Dry Run Output ---")
        print(output_content)
        logging.info("--- End Dry Run Output ---")
        if dry_run_output_path:
            try:
                dry_run_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dry_run_output_path, "w", encoding="utf-8") as outfile:
                    outfile.write(output_content)
                logging.info(f"Dry run output also written to: {dry_run_output_path}")
            except Exception as e:
                logging.error(
                    f"Error writing dry run output to {dry_run_output_path}: {e}"
                )
        return

    if output_path.exists() and not force:
        import sys

        if sys.stdin.isatty():
            response = input(
                f"Output file '{output_path}' already exists. Overwrite? (y/N): "
            )
            if response.lower() != "y":
                logging.info("Operation cancelled by user. File not overwritten.")
                return
        else:
            logging.info(
                f"Output file '{output_path}' already exists. "
                "Skipping overwrite in non-interactive mode."
            )
            return

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as outfile:
            outfile.write(output_content)
        logging.info(f"\nAll code files have been combined into: {output_path}")
    except Exception as e:
        logging.error(f"Error writing to output file {output_path}: {e}")
        raise


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the CodeMeld script."""
    parser = argparse.ArgumentParser(
        description="Combine code files from a directory into a single file."
    )
    parser.add_argument("directory", help="The directory to scan for code files.")
    parser.add_argument(
        "-o",
        "--output",
        default="combined_code.txt",
        help="The output file name (default: combined_code.txt).",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        help="Custom file extensions to include (space-separated, e.g., .py .js .ts).",
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Do not respect the .gitignore file.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and folders (those starting with a dot).",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help=(
            "Custom file extensions to exclude (space separated, e.g., .txt .md). "
            "Exclusions take precedence over inclusions."
        ),
    )
    parser.add_argument(
        "--no-tokens",
        action="store_true",
        help="Do not count tokens in the combined output file.",
    )
    parser.add_argument(
        "--header-width",
        type=int,
        default=80,
        help="Width of the separator lines in the combined file header (default: 80).",
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "markdown", "json", "xml"],
        help="Output format (text, markdown, json, xml). Default is text.",
    )
    parser.add_argument(
        "--convert-to",
        choices=["text", "markdown"],
        help="Convert XML/JSON output to text or markdown format.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output file if it already exists without prompting.",
    )
    parser.add_argument(
        "--always-include",
        nargs="+",
        help=(
            "Always include specified files, bypassing other filters "
            "(space-separated paths)."
        ),
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links when scanning directories.",
    )
    parser.add_argument(
        "--token-encoding",
        default="cl100k_base",
        help=(
            "The token encoding model to use for token counting (default: cl100k_base)."
        ),
    )
    parser.add_argument(
        "--max-memory-mb",
        type=int,
        default=500,
        help=(
            "Maximum memory in MB to use before falling back to streaming "
            "(default: 500). Set to 0 for no limit."
        ),
    )
    parser.add_argument(
        "--custom-file-headers",
        default="{}",
        help=(
            """JSON string of custom file headers per extension (e.g., "
            "'{\"py\": \"# FILE: {path}\", \"js\": \"// FILE: {path}\"}'"""
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without writing any output files.",
    )
    parser.add_argument(
        "--max-file-size-kb",
        type=int,
        help=(
            "Maximum file size in KB to include (e.g., 1024 for 1MB). "
            "Files larger than this will be skipped."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output, showing each file as it's processed.",
    )
    parser.add_argument(
        "--list-files",
        action="store_true",
        help="List all files that were added to the output file.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary of the processing results.",
    )
    parser.add_argument(
        "--dry-run-output",
        type=str,
        help=(
            "Optional: write the list of files processed during a dry run to this file."
        ),
    )
    parser.add_argument(
        "--progress-style",
        type=str,
        help=(
            "Customize the progress bar style (e.g., 'ascii', 'block'). "
            "Set to 'none' to disable."
        ),
    )
    return parser.parse_args()


def run_code_combiner(config: CombinerConfig) -> None:
    """Run CodeMeld with the given configuration."""
    combiner = CodeMeld(config)
    combiner.execute()


class CodeMeld:
    """Orchestrates the code combining process."""

    def __init__(self, config: CombinerConfig):
        """Initialize CodeMeld."""
        self.config = config
        self.root_path = self.config.directory_path.resolve()
        self.safety_filter_chain = FilterChainBuilder.build_safety_chain(self.config)
        self.always_included_files = self._process_always_include_files()

        # Determine the effective format based on --convert-to
        effective_format = (
            config.final_output_format if config.final_output_format else config.format
        )

        formatter_kwargs = {}
        if effective_format == "text":
            formatter_kwargs["header_width"] = config.header_width

        self.formatter = FormatterFactory.create(
            effective_format,
            custom_file_headers=self.config.custom_file_headers,
            **formatter_kwargs,
        )
        self.full_filter_chain = self._build_full_filter_chain(self.safety_filter_chain)

    def _build_full_filter_chain(
        self, safety_chain_head: CompositeFilter
    ) -> FileFilter:
        spec = self._get_gitignore_spec() if self.config.use_gitignore else None
        return FilterChainBuilder.build_full_chain(
            self.config, spec, safety_chain_head, self.always_included_files
        )

    def _get_gitignore_spec(self) -> pathspec.PathSpec | None:
        """
        Search for and parse a .gitignore file.

        Searches for a .gitignore file in the current directory or any parent directory
        up to the root. If found, it parses the file and returns a PathSpec object
        for matching. This allows respecting gitignore rules for file filtering.
        """
        current_path: Path = self.config.directory_path.resolve()
        # Traverse up the directory tree to find a .gitignore file
        while current_path != current_path.parent:
            gitignore_path: Path = current_path / ".gitignore"
            if gitignore_path.is_file():
                # If a .gitignore is found, read its contents and create a PathSpec
                with open(gitignore_path, encoding="utf-8") as f:
                    return pathspec.PathSpec.from_lines("gitwildmatch", f)
            # Move to the parent directory
            current_path = current_path.parent
        # If no .gitignore file is found after traversing to the root, return None
        return None

    def _iter_files(self) -> Iterator[Path]:
        """Iterate over files in the directory using pathlib.Path.rglob()."""
        # rglob will traverse all directories, including hidden ones.
        # The HiddenFileFilter will then handle filtering of hidden files/directories
        # based on self.config.include_hidden in the filter chain.
        for path in self.root_path.rglob("*"):
            if path.is_file():
                yield path

    def _collect_all_files(self) -> list[Path]:
        """Collect all files from the root directory, handling potential errors."""
        all_files: list[Path] = []
        try:
            all_files = list(self._iter_files())
        except PermissionError as e:
            raise CodeMeldError(f"Insufficient permissions to read files: {e}") from e
        except OSError as e:
            raise CodeMeldError(f"File system error: {e}") from e
        return all_files

    def _apply_filters_to_files(self, files: list[Path]) -> list[Path]:
        """Apply the full filter chain to a list of files."""
        filtered_files = [
            file
            for file in files
            if self.full_filter_chain.should_process(
                file, {"root_path": self.root_path}
            )
        ]
        return filtered_files

    def _get_filtered_files(self, files: list[Path] | None = None) -> list[Path]:
        """
        Get a list of files to be processed after applying all filters.

        Args:
            files: An optional list of files to filter. If not provided,
                   all files in the directory will be collected.

        Returns:
            A sorted list of file paths.

        """
        if files is None:
            files = self._collect_all_files()
        filtered_files = self._apply_filters_to_files(files)
        return sorted(filtered_files)

    def _resolve_path(self, path: Path) -> Path:
        """Resolve a path to its absolute form."""
        if path.is_absolute():
            return path.resolve()
        return (self.config.directory_path / path).resolve()

    def _process_always_include_files(self) -> list[Path]:
        """Process --always-include files with safety checks."""
        always_included_files: list[Path] = []
        for path_str in self.config.always_include:
            path = Path(path_str)
            resolved_path = self._resolve_path(path)
            if not resolved_path.is_file():
                logging.warning(
                    f"Warning: --always-include path '{path_str}' "
                    "is not a file or does not exist. Skipping."
                )
                continue

            if not self.safety_filter_chain.should_process(
                resolved_path, {"root_path": self.root_path}
            ):
                logging.warning(
                    f"Warning: --always-include path '{path_str}' "
                    "was filtered out by safety checks. Skipping."
                )
                continue
            always_included_files.append(resolved_path)
        return always_included_files

    def _prepare_files(self) -> list[Path]:
        all_files = self._collect_all_files()
        combined_files = sorted(set(all_files + self.always_included_files))
        return self._get_filtered_files(combined_files)

    def _setup_ui(self, total_files: int) -> LiveUI:
        ui = LiveUI(total_files=total_files)
        ui.apply_config(self.config)
        ui.print_header()
        ui.print_config()
        ui.start()
        return ui

    def _run_generation(self, all_files_to_process: list[Path], ui: LiveUI) -> None:
        memory_monitor = TracemallocMemoryMonitor(
            self.config.max_memory_mb,
            self.config.count_tokens,
            self.config.safety_margin,
        )

        with Publisher(total_files=len(all_files_to_process)) as publisher:
            token_counter_observer = None
            line_counter_observer = None
            if self.config.count_tokens:
                token_counter_observer = TokenCounterObserver(
                    self.config.token_encoding_model
                )
                publisher.subscribe(token_counter_observer)
                line_counter_observer = LineCounterObserver()
                publisher.subscribe(line_counter_observer)
                publisher.subscribe(TelemetryObserver())

            output_written_by_streaming = False
            context = GeneratorContext(
                files_to_process=all_files_to_process,
                root_path=self.config.directory_path,
                formatter=self.formatter,
                publisher=publisher,
                output_path=Path(self.config.output),
                ui=ui,
                token_counter_observer=token_counter_observer,
                line_counter_observer=line_counter_observer,
                memory_monitor=memory_monitor,
                dry_run=self.config.dry_run,
                dry_run_output=self.config.dry_run_output,
            )
            try:
                generator = InMemoryOutputGenerator(context)
                output_content, _ = generator.generate()
            except MemoryThresholdExceededError:
                if not self.config.count_tokens and self.formatter.supports_streaming():
                    logging.warning(
                        "Falling back to streaming due to memory constraints."
                    )
                    streaming_generator = StreamingOutputGenerator(context)
                    streaming_generator.generate()
                    output_written_by_streaming = True
                    output_content = ""
                else:
                    raise

            if not output_written_by_streaming and output_content:
                write_output(
                    Path(self.config.output),
                    output_content,
                    self.config.force,
                    self.config.dry_run,
                    (
                        Path(self.config.dry_run_output)
                        if self.config.dry_run_output
                        else None
                    ),
                )

    def execute(self) -> None:
        """Execute the combining process."""
        all_files_to_process = self._prepare_files()
        if not all_files_to_process:
            logging.info("No files found to process. Exiting.")
            return

        ui = self._setup_ui(len(all_files_to_process))
        self._run_generation(all_files_to_process, ui)
        ui.finish()


def main() -> None:
    """Run CodeMeld from the command line."""
    args = parse_arguments()
    config = load_and_merge_config(args)
    run_code_combiner(config)


if __name__ == "__main__":
    main()

```

## FILE: src/config.py

```py
# Copyright (c) 2025 skum

"""Defines the configuration for the CodeMeld tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src._types import ConvertType, FormatType


class CodeMeldError(Exception):
    """Custom exception for CodeMeld errors."""


class MemoryThresholdExceededError(CodeMeldError):
    """Custom exception for when memory threshold is exceeded."""


DEFAULT_EXTENSIONS: list[str] = [
    ".py",
    ".js",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".go",
    ".rs",
    ".ts",
    ".html",
    ".css",
    ".xml",
    ".json",
    ".yml",
    ".yaml",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
    ".md",
    ".txt",
]


@dataclass
class CombinerConfig:
    """Configuration for the CodeMeld tool."""

    directory_path: Path
    output: str = "combined_code.txt"
    extensions: list[str] = field(default_factory=lambda: DEFAULT_EXTENSIONS)
    exclude_extensions: list[str] = field(default_factory=list)
    use_gitignore: bool = True
    include_hidden: bool = False
    count_tokens: bool = True
    header_width: int = 80
    format: FormatType = "text"
    final_output_format: ConvertType | None = None
    force: bool = False
    always_include: list[str] = field(default_factory=list)
    follow_symlinks: bool = False
    token_encoding_model: str = "cl100k_base"
    max_memory_mb: int | None = 500
    custom_file_headers: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False
    max_file_size_kb: int | None = None
    verbose: bool = False
    list_files: bool = False
    summary: bool = True
    dry_run_output: str | None = None
    progress_style: str | None = None
    sample_size_bytes: int = 8192
    large_file_threshold_bytes: int = 1024 * 1024  # 1MB
    non_text_threshold: float = 0.30
    safety_margin: float = 0.1

```

## FILE: src/config_builder.py

```py
# Copyright (c) 2025 skum

from __future__ import annotations

"""Provides a builder for creating CombinerConfig objects."""

import argparse
import logging
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from .config import DEFAULT_EXTENSIONS, CombinerConfig
from .config_validator import ConfigValidator


def load_toml(path: Path) -> dict[str, Any]:
    """Load TOML data from a file using tomllib (Python 3.11+)."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config_from_pyproject(root_path: Path) -> dict[str, Any]:
    """Load configuration from pyproject.toml if available."""
    config: dict[str, Any] = {}
    pyproject_path = root_path / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            pyproject_data: dict[str, Any] = load_toml(pyproject_path)
            if "tool" in pyproject_data and "code_combiner" in pyproject_data["tool"]:
                config = pyproject_data["tool"]["code_combiner"]
        except Exception as e:
            logging.warning(f"Error parsing pyproject.toml: {e}")
    return config


class CombinerConfigBuilder:
    """Builder for CombinerConfig with proper precedence."""

    def __init__(self) -> None:
        """Initialize the builder with default values."""
        self._config = {
            "extensions": DEFAULT_EXTENSIONS,
            "exclude_extensions": [],
            "use_gitignore": True,
            "include_hidden": False,
            "count_tokens": True,
            "header_width": 80,
            "format": "text",
            "final_output_format": None,
            "force": False,
            "always_include": [],
            "safety_margin": 0.1,
        }

    def with_defaults(self) -> CombinerConfigBuilder:
        """Use default values."""
        return self

    def with_pyproject_config(self, config: dict[str, Any]) -> CombinerConfigBuilder:
        """Apply pyproject.toml settings."""
        for key, value in config.items():
            if key in self._config:
                self._config[key] = value
        return self

    def _apply_arg_if_present(
        self,
        args: argparse.Namespace,
        arg_name: str,
        config_key: str | None = None,
        transform_func: Callable[[Any], Any] | None = None,
    ) -> None:
        if config_key is None:
            config_key = arg_name
        if hasattr(args, arg_name) and getattr(args, arg_name) is not None:
            value = getattr(args, arg_name)
            if transform_func:
                self._config[config_key] = transform_func(value)
            else:
                self._config[config_key] = value

    def with_cli_args(self, args: argparse.Namespace) -> CombinerConfigBuilder:
        """Apply CLI arguments (highest precedence)."""
        self._apply_arg_if_present(args, "extensions")
        self._apply_arg_if_present(args, "exclude", "exclude_extensions")
        if hasattr(args, "no_gitignore") and args.no_gitignore:
            self._config["use_gitignore"] = False
        self._apply_arg_if_present(args, "include_hidden")
        if hasattr(args, "no_tokens") and args.no_tokens:
            self._config["count_tokens"] = False
        if hasattr(args, "header_width") and args.header_width != 80:
            # Check against default
            self._config["header_width"] = args.header_width
        self._apply_arg_if_present(args, "format")
        self._apply_arg_if_present(args, "convert_to", "final_output_format")
        self._apply_arg_if_present(args, "force")
        self._apply_arg_if_present(args, "always_include")
        self._apply_arg_if_present(args, "follow_symlinks")
        self._apply_arg_if_present(args, "token_encoding_model")
        self._apply_arg_if_present(args, "max_memory_mb")
        self._apply_arg_if_present(args, "custom_file_headers")
        self._apply_arg_if_present(args, "dry_run")
        self._apply_arg_if_present(args, "max_file_size_kb")
        self._apply_arg_if_present(args, "verbose")
        self._apply_arg_if_present(args, "list_files")
        self._apply_arg_if_present(args, "summary")
        self._apply_arg_if_present(args, "dry_run_output")
        self._apply_arg_if_present(args, "progress_style")
        self._apply_arg_if_present(args, "safety_margin")

        return self

    def validate(self, directory: str, output: str) -> CombinerConfigBuilder:
        """Validate configuration."""
        validator = ConfigValidator(self._config, directory, output)
        validator.validate()
        return self

    def build(self, directory_path: Path, output: str) -> CombinerConfig:
        """Build the final configuration."""
        return CombinerConfig(
            directory_path=directory_path, output=output, **cast(Any, self._config)
        )


def load_and_merge_config(args: argparse.Namespace) -> CombinerConfig:
    """Load configuration from pyproject.toml and merge with command-line arguments."""
    directory_path = Path(args.directory).resolve()

    pyproject_config = load_config_from_pyproject(directory_path)

    return (
        CombinerConfigBuilder()
        .with_defaults()
        .with_pyproject_config(pyproject_config)
        .with_cli_args(args)
        .validate(args.directory, args.output)
        .build(directory_path, args.output)
    )

```

## FILE: src/config_validator.py

```py
# Copyright (c) 2025 skum

"""Provides a validator for the combiner configuration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import tiktoken

from .config import CodeMeldError


class ConfigValidator:
    """Validates the combiner configuration."""

    def __init__(self, config: dict[str, Any], directory: str, output: str):
        """Initialize the ConfigValidator."""
        self._config = config
        self._directory = directory
        self._output = output

    def validate(self) -> None:
        """Run all validation checks."""
        self._validate_directory()
        self._validate_extensions()
        self._validate_header_width()
        self._validate_output_path()
        self._validate_conversion()
        self._validate_max_memory_mb()
        self._validate_max_file_size_kb()
        self._validate_token_encoding_model()
        self._validate_custom_file_headers()

    def _validate_directory(self) -> None:
        directory_path = Path(self._directory)
        if not directory_path.is_dir():
            raise CodeMeldError(f"Error: Directory '{self._directory}' does not exist.")

    def _validate_extensions(self) -> None:
        if not self._config["extensions"]:
            raise CodeMeldError("Error: Extension list cannot be empty.")

        for i, ext in enumerate(self._config["extensions"]):
            if not ext.startswith("."):
                suggested_ext = f".{ext.lower()}"
                raise CodeMeldError(
                    f"Error: Extension '{ext}' must start with '.'. "
                    f"Did you mean '{suggested_ext}'?"
                )
            self._config["extensions"][i] = ext.lower()

    def _validate_header_width(self) -> None:
        if self._config["header_width"] <= 0:
            raise CodeMeldError("Header width must be positive")

    def _validate_output_path(self) -> None:
        output_path = Path(self._output)
        if not output_path.parent.exists():
            logging.info(
                f"Output directory '{output_path.parent}' "
                "does not exist and will be created."
            )

    def _validate_conversion(self) -> None:
        if self._config["final_output_format"]:
            if self._config["format"] not in ["json", "xml"]:
                raise CodeMeldError(
                    "--convert-to can only be used when --format is 'json' or 'xml'"
                )
            if self._config["format"] == self._config["final_output_format"]:
                raise CodeMeldError(
                    f"Error: Cannot convert format '{self._config['format']}' "
                    "to itself."
                )

    def _validate_max_memory_mb(self) -> None:
        max_mem = self._config.get("max_memory_mb")
        if max_mem is not None and (not isinstance(max_mem, int) or max_mem < -1):
            raise CodeMeldError("Max memory must be an integer greater than -1.")

    def _validate_max_file_size_kb(self) -> None:

        max_size = self._config.get("max_file_size_kb")
        if max_size is not None and (not isinstance(max_size, int) or max_size <= 0):
            raise CodeMeldError("Max file size must be a positive integer.")

    def _validate_token_encoding_model(self) -> None:
        if self._config.get("count_tokens"):
            token_encoding_model = self._config.get("token_encoding_model")
            if token_encoding_model:
                try:
                    tiktoken.encoding_for_model(token_encoding_model)
                except KeyError as e:
                    raise CodeMeldError(
                        f"Invalid token encoding model: {token_encoding_model}"
                    ) from e

    def _validate_custom_file_headers(self) -> None:
        custom_headers_str = self._config.get("custom_file_headers")
        if custom_headers_str:
            try:
                # Attempt to parse the JSON string
                parsed_headers = json.loads(custom_headers_str)
                if not isinstance(parsed_headers, dict):
                    raise ValueError("Custom file headers must be a JSON object.")
                # Optionally, add more specific validation for the content of
                # parsed_headers
                # For example, check if keys are strings and values are strings.
                for key, value in parsed_headers.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        raise ValueError(
                            "All keys and values in custom file headers "
                            "must be strings."
                        )
                # If validation passes, store the parsed dictionary back in _config
                self._config["custom_file_headers"] = parsed_headers
            except json.JSONDecodeError as e:
                raise CodeMeldError(
                    f"Invalid JSON in custom_file_headers: {e}\n"
                    """Example: '{"py": "# Python: {path}"}"""
                ) from e
            except ValueError as e:
                raise CodeMeldError(
                    f"Invalid custom_file_headers format: {e}\n"
                    """Example: '{"py": "# Python: {path}"}"""
                ) from e

```

## FILE: src/context.py

```py
# Copyright (c) 2025 skum

"""Defines the context object for output generators."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .formatters import OutputFormatter
    from .memory_monitor import MemoryMonitor
    from .observers import LineCounterObserver, Publisher, TokenCounterObserver
    from .ui import LiveUI


@dataclass
class GeneratorContext:
    """A dataclass to hold the context for output generators."""

    files_to_process: list[Path]
    root_path: Path
    formatter: OutputFormatter
    publisher: Publisher
    output_path: Path
    ui: LiveUI
    token_counter_observer: TokenCounterObserver | None
    line_counter_observer: LineCounterObserver | None
    memory_monitor: MemoryMonitor | None = None  # For InMemory
    dry_run: bool = False  # For Streaming
    dry_run_output: str | None = None  # For Streaming

```

## FILE: src/filters.py

```py
# Copyright (c) 2025 skum

"""Defines the filter chain for selecting files to be combined."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pathspec

from .config import CombinerConfig
from .utils import is_likely_binary


class FileFilter(ABC):
    """Base class for file filters."""

    filters: list[FileFilter] = []

    def should_process(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Return True if file should be processed."""
        result = self._check(file_path, context)
        logging.debug(
            f"{self.__class__.__name__}._check({file_path.name}) returned {result}"
        )
        return result

    @abstractmethod
    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Individual filter logic."""
        pass


class CompositeFilter(FileFilter):
    """A filter that is composed of other filters. All filters must pass."""

    def __init__(self, filters: list[FileFilter]):
        """Initialize the composite filter."""
        self.filters = filters

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Check the file against all filters in the composite."""
        for f in self.filters:
            if not f.should_process(file_path, context):
                return False
        return True


class ExtensionFilter(FileFilter):
    """Filter files based on their extensions."""

    def __init__(self, extensions: list[str], exclude: list[str]):
        """Initialize the extension filter."""
        self.extensions = [e.lower() for e in extensions]
        self.exclude = [e.lower() for e in exclude]

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        suffix = file_path.suffix.lower()
        if suffix in self.exclude:
            return False
        return suffix in self.extensions


class HiddenFileFilter(FileFilter):
    """Filter hidden files and directories."""

    def __init__(self, include_hidden: bool):
        """Initialize the hidden file filter."""
        self.include_hidden = include_hidden

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        if self.include_hidden:
            return True
        root_path = context.get("root_path")
        if not root_path:
            return True
        try:
            relative = file_path.relative_to(root_path)
            return not any(part.startswith(".") for part in relative.parts)
        except ValueError:
            return True


class GitignoreFilter(FileFilter):
    """Filter files based on .gitignore rules."""

    def __init__(self, spec: pathspec.PathSpec | None):
        """Initialize the gitignore filter."""
        self.spec = spec

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        if not self.spec:
            return True
        root_path = context.get("root_path")
        if not root_path:
            return True
        try:
            relative = file_path.relative_to(root_path)
            return not self.spec.match_file(str(relative))
        except ValueError:
            return True


class OutputFilePathFilter(FileFilter):
    """Filters out the output file itself."""

    def __init__(self, output_path: Path):
        """Initialize the OutputFilePathFilter."""
        self.output_path = output_path.resolve()

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Determine if the file should be processed."""
        return file_path.resolve() != self.output_path


class BinaryFileFilter(FileFilter):
    """Filter binary files."""

    def __init__(self, config: CombinerConfig):
        """Initialize the binary file filter."""
        self.config = config

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        return not is_likely_binary(file_path, self.config)


class SymlinkFilter(FileFilter):
    """Filter symbolic links, with an option to follow them."""

    def __init__(self, follow_symlinks: bool):
        """Initialize the SymlinkFilter."""
        self.follow_symlinks = follow_symlinks

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        if self.follow_symlinks:
            return True  # If following symlinks, don't filter them out

        import logging

        logging.debug(
            f"SymlinkFilter: Checking {file_path}, is_symlink: {file_path.is_symlink()}"
        )

        return not file_path.is_symlink()


class SecurityFilter(FileFilter):
    """Filter to prevent path traversal by ensuring files are within the root path."""

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        import logging

        root_path = context.get("root_path")

        if not root_path:
            logging.debug(
                f"SecurityFilter: No root_path in context for {file_path}. Allowing."
            )

            return True

        try:
            resolved_file_path = file_path.resolve()

            resolved_root_path = root_path.resolve()

            resolved_file_path.relative_to(resolved_root_path)

            logging.debug(
                f"SecurityFilter: {resolved_file_path} in "
                f"{resolved_root_path}. Allowing."
            )

            return True

        except ValueError:
            logging.debug(
                f"SecurityFilter: {resolved_file_path} NOT in "
                f"{resolved_root_path}. Blocking."
            )

            return False


class AlwaysIncludeFilter(FileFilter):
    """Filter for files that should always be included."""

    def __init__(self, always_include_paths: list[Path]):
        """Initialize the AlwaysIncludeFilter."""
        self.always_include_paths = {p.resolve() for p in always_include_paths}

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        return file_path.resolve() in self.always_include_paths


class FileSizeFilter(FileFilter):
    """Filter files based on their size."""

    def __init__(self, max_file_size_kb: int):
        """Initialize the FileSizeFilter."""
        self.max_file_size_bytes = max_file_size_kb * 1024

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        try:
            return file_path.stat().st_size <= self.max_file_size_bytes
        except FileNotFoundError:
            # If file is not found, it cannot be processed, so filter it out.
            return False
        except Exception as e:
            # Log other potential errors (e.g., permission issues) and filter out.
            import logging

            logging.debug(f"Error checking file size for {file_path}: {e}")
            return False


class OrFilter(FileFilter):
    """A filter that passes if any of its sub-filters pass."""

    def __init__(self, filters: list[FileFilter]):
        """Initialize the OrFilter."""
        self.filters = filters

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        if not self.filters:
            logging.debug(f"OrFilter: No filters provided for {file_path}")
            return False

        for f in self.filters:
            if f.should_process(file_path, context):
                logging.debug(f"OrFilter: {f.__class__.__name__} accepted {file_path}")
                return True
        return False


class FilterChainBuilder:
    """Builder for constructing file filter chains."""

    @staticmethod
    def _resolve_output_path(config: CombinerConfig) -> Path:
        output_path = Path(config.output)
        if not output_path.is_absolute():
            output_path = (config.directory_path / output_path).resolve()
        return output_path

    @staticmethod
    def build_safety_chain(config: CombinerConfig) -> CompositeFilter:
        """Build a filter chain for safety checks only."""
        output_path = FilterChainBuilder._resolve_output_path(config)
        filters: list[FileFilter] = [
            SecurityFilter(),
            SymlinkFilter(config.follow_symlinks),
            BinaryFileFilter(config),
            OutputFilePathFilter(output_path),
        ]
        if config.max_file_size_kb is not None and config.max_file_size_kb > 0:
            filters.append(FileSizeFilter(config.max_file_size_kb))
        return CompositeFilter(filters)

    @staticmethod
    def build_full_chain(
        config: CombinerConfig,
        spec: pathspec.PathSpec | None,
        safety_chain: CompositeFilter,
        always_include_paths: list[Path],
    ) -> CompositeFilter:
        """
        Build the full filter chain with the logic.

        The logic is:
        (pass_always_include OR pass_content_filters) AND pass_safety_filters
        """
        content_filters: list[FileFilter] = [
            ExtensionFilter(config.extensions, config.exclude_extensions)
        ]
        if not config.include_hidden:
            content_filters.append(HiddenFileFilter(config.include_hidden))
        if config.use_gitignore and spec:
            content_filters.append(GitignoreFilter(spec))

        main_selection_filters: list[FileFilter] = [CompositeFilter(content_filters)]
        if always_include_paths:
            main_selection_filters.insert(0, AlwaysIncludeFilter(always_include_paths))

        # The core logic: a file is included if it's either in the always_include list
        # OR it passes all the content filters.
        main_filter = OrFilter(main_selection_filters)

        # The final chain: the file must pass the main filter AND the safety filter.
        return CompositeFilter([main_filter, safety_chain])

```

## FILE: src/formatters.py

```py
# Copyright (c) 2025 skum

"""Defines strategies for formatting combined code output."""

from __future__ import annotations

import importlib.metadata
import json
import xml.sax.saxutils
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, final

from src._types import FormatType


class OutputFormatter(ABC):
    """Strategy interface for different output formats."""

    def __init__(
        self,
        custom_file_headers: dict[str, str] | None = None,
        **kwargs: Mapping[str, Any],
    ):
        """Initialize the OutputFormatter and validate kwargs."""
        if kwargs:
            raise TypeError(
                f"Unknown arguments for {self.format_name} formatter: "
                f"{', '.join(kwargs.keys())}"
            )
        self.custom_file_headers = (
            custom_file_headers if custom_file_headers is not None else {}
        )

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the name of the format."""
        pass

    @abstractmethod
    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content."""
        pass

    @abstractmethod
    def begin_output(self) -> str:
        """Return any header/opening content."""
        pass

    @abstractmethod
    def end_output(self) -> str:
        """Return any footer/closing content."""
        pass

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Whether this formatter can stream output."""
        pass


@final
class TextFormatter(OutputFormatter):
    """Formats output as plain text."""

    format_name = "text"

    def __init__(self, header_width: int = 80, **kwargs: Any) -> None:
        """Initialize the TextFormatter."""
        super().__init__(**kwargs)
        self.header_width = header_width

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for text output."""
        # Check for custom header
        ext = relative_path.suffix.lstrip(".").lower()
        custom_header_format = self.custom_file_headers.get(ext)

        if custom_header_format:
            header = custom_header_format.format(path=relative_path)
            return f"{header}\n{content}\n\n"
        else:
            return (
                f"\n{'=' * self.header_width}\nFILE: {relative_path}\n"
                f"{'=' * self.header_width}\n\n{content}\n\n"
            )

    def begin_output(self) -> str:
        """Return any header/opening content for text output."""
        return ""

    def end_output(self) -> str:
        """Return any footer/closing content for text output."""
        return ""

    def supports_streaming(self) -> bool:
        """Text formatter supports streaming."""
        return True


@final
class MarkdownFormatter(OutputFormatter):
    """Formats output as Markdown."""

    format_name = "markdown"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the MarkdownFormatter."""
        super().__init__(**kwargs)

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for Markdown output."""
        # Check for custom header
        ext = relative_path.suffix.lstrip(".").lower()
        custom_header_format = self.custom_file_headers.get(ext)

        lang = relative_path.suffix.lstrip(".")
        if custom_header_format:
            header = custom_header_format.format(path=relative_path, lang=lang)
            return f"{header}\n```{lang}\n{content}\n```\n\n"
        else:
            return f"## FILE: {relative_path}\n\n```{lang}\n{content}\n```\n\n"

    def begin_output(self) -> str:
        """Return any header/opening content for Markdown output."""
        return ""

    def end_output(self) -> str:
        """Return any footer/closing content for Markdown output."""
        return ""

    def supports_streaming(self) -> bool:
        """Markdown formatter supports streaming."""
        return True


@final
class JSONFormatter(OutputFormatter):
    """Formats output as JSON."""

    format_name = "json"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the JSONFormatter."""
        super().__init__(**kwargs)
        self.is_first = True

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for JSON output."""
        # For streaming
        prefix = "" if self.is_first else ",\n"
        self.is_first = False
        return f'{prefix}    "{relative_path}": {json.dumps(content)}'

    def begin_output(self) -> str:
        """Return any header/opening content for JSON output."""
        self.is_first = True  # Reset state
        return "{\n"

    def end_output(self) -> str:
        """Return any footer/closing content for JSON output."""
        return "\n}"

    def supports_streaming(self) -> bool:
        """JSON formatter supports streaming."""
        return True


@final
class XMLFormatter(OutputFormatter):
    """Formats output as XML."""

    format_name = "xml"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the XMLFormatter."""
        super().__init__(**kwargs)

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for XML output."""
        escaped = xml.sax.saxutils.escape(content)
        return (
            f"  <file>\n    <path>{relative_path}</path>\n"
            f"    <content>{escaped}</content>\n  </file>\n"
        )

    def begin_output(self) -> str:
        """Return any header/opening content for XML output."""
        return '<?xml version="1.0" encoding="UTF-8"?>\n<codebase>\n'

    def end_output(self) -> str:
        """Return any footer/closing content for XML output."""
        return "</codebase>"

    def format_file_stream(
        self, relative_path: Path, file_path: Path, outfile: Any
    ) -> None:
        """Stream XML content directly without building tree."""
        outfile.write(f"  <file>\n    <path>{relative_path}</path>\n    <content>")
        try:
            with open(file_path, encoding="utf-8") as f:
                for chunk in iter(lambda: f.read(8192), ""):
                    outfile.write(xml.sax.saxutils.escape(chunk))
        except Exception as e:
            from .utils import log_file_read_error

            log_file_read_error(file_path, e)
        outfile.write("</content>\n  </file>\n")

    def supports_streaming(self) -> bool:
        """XML formatter supports streaming."""
        return True


class FormatterFactory:
    """Factory to create OutputFormatter instances."""

    _formatters: dict[str, type[OutputFormatter]] = {}
    _plugins_loaded: bool = False

    @classmethod
    def _load_plugins(cls) -> None:
        """Discover and register formatters via entry points."""
        if cls._plugins_loaded:
            return
        for entry_point in importlib.metadata.entry_points(
            group="code_combiner.formatters"
        ):
            try:
                formatter_class = entry_point.load()
                if issubclass(formatter_class, OutputFormatter):
                    cls.register(entry_point.name, formatter_class)
                else:
                    import logging

                    logging.warning(
                        f"Entry point {entry_point.name} is not a subclass "
                        "of OutputFormatter."
                    )
            except Exception as e:
                import logging

                logging.error(
                    f"Failed to load formatter plugin {entry_point.name}: {e}"
                )
        cls._plugins_loaded = True

    @classmethod
    def register(cls, format_type: str, formatter_class: type[OutputFormatter]) -> None:
        """Register a new formatter."""
        cls._formatters[format_type] = formatter_class

    @classmethod
    def create(
        cls,
        format_type: FormatType,
        custom_file_headers: dict[str, str] | str | None = None,
        **kwargs: Any,
    ) -> OutputFormatter:
        """Create an OutputFormatter instance based on the format type."""
        cls._load_plugins()  # Ensure plugins are loaded before creation
        formatter_class = cls._formatters.get(format_type)
        if not formatter_class:
            raise ValueError(f"Unknown format: {format_type}")

        parsed_custom_headers: dict[str, str] | None = None
        if isinstance(custom_file_headers, str):
            try:
                parsed_custom_headers = json.loads(custom_file_headers)
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON for custom file headers") from e
        elif isinstance(custom_file_headers, dict):
            parsed_custom_headers = custom_file_headers

        # Let formatters handle their own parameter validation
        try:
            return formatter_class(custom_file_headers=parsed_custom_headers, **kwargs)
        except TypeError as e:
            raise TypeError(
                f"Formatter '{format_type}' initialization failed: {e}"
            ) from e


# Register built-in formatters
FormatterFactory.register("text", TextFormatter)
FormatterFactory.register("markdown", MarkdownFormatter)
FormatterFactory.register("json", JSONFormatter)
FormatterFactory.register("xml", XMLFormatter)

```

## FILE: src/memory_monitor.py

```py
# Copyright (c) 2025 skum

"""Monitors system memory usage and raises an error if a threshold is exceeded."""

from __future__ import annotations

import logging
import tracemalloc
from abc import ABC, abstractmethod

import psutil

from .config import MemoryThresholdExceededError


class MemoryMonitor(ABC):
    """Abstract base class for memory monitoring."""

    def __init__(self, max_memory_mb: int | None = None, count_tokens: bool = True):
        """Initialize the MemoryMonitor."""
        self.max_memory_mb = max_memory_mb
        self.count_tokens = count_tokens

    @abstractmethod
    def check_memory_usage(self) -> None:
        """Check memory usage against threshold; raise error if exceeded."""
        pass


class SystemMemoryMonitor(MemoryMonitor):
    """Concrete implementation of MemoryMonitor using psutil."""

    def check_memory_usage(self) -> None:
        """Check memory usage against threshold; raise error if exceeded."""
        if self.max_memory_mb is None or self.max_memory_mb <= 0:
            return

        process = psutil.Process()
        current_memory_rss_mb = process.memory_info().rss / (1024 * 1024)

        if current_memory_rss_mb > self.max_memory_mb:
            logging.warning(
                f"High memory usage detected (RSS: {current_memory_rss_mb:.1f}MB). "
                f"Threshold: {self.max_memory_mb}MB. Falling back to streaming."
            )
            raise MemoryThresholdExceededError(
                f"Memory usage exceeded {self.max_memory_mb}MB. "
                f"Falling back to streaming output."
            )


class TracemallocMemoryMonitor(MemoryMonitor):
    """Memory monitor using tracemalloc for more precise Python-specific tracking."""

    def __init__(
        self,
        max_memory_mb: int | None = None,
        count_tokens: bool = True,
        safety_margin: float = 0.1,
    ):
        """Initialize the TracemallocMemoryMonitor."""
        super().__init__(max_memory_mb, count_tokens)
        self.safety_margin = safety_margin
        if self.max_memory_mb is not None and self.max_memory_mb > 0:
            if not tracemalloc.is_tracing():
                tracemalloc.start()

    def check_memory_usage(self) -> None:
        """Check memory usage against threshold; raise error if exceeded."""
        if self.max_memory_mb is None or self.max_memory_mb <= 0:
            return

        current_size, peak_size = tracemalloc.get_traced_memory()
        current_memory_mb = current_size / (1024 * 1024)

        threshold = self.max_memory_mb * (1 - self.safety_margin)

        if current_memory_mb > threshold:
            peak_memory_mb = peak_size / (1024 * 1024)
            logging.warning(
                "High Python memory usage detected (Current: %.1fMB, Peak: %.1fMB). "
                "Threshold: %.1fMB (Safety Margin: %.0f%%). Falling back to streaming.",
                current_memory_mb,
                peak_memory_mb,
                threshold,
                self.safety_margin * 100,
            )
            raise MemoryThresholdExceededError(
                f"Python memory usage exceeded {threshold:.1f}MB. "
                f"Falling back to streaming output."
            )

    def __del__(self) -> None:
        """Stop tracemalloc if it's running."""
        if tracemalloc.is_tracing():
            tracemalloc.stop()

```

## FILE: src/observers.py

```py
# Copyright (c) 2025 skum

"""Defines the observer pattern for progress reporting and token counting."""

from __future__ import annotations

import logging
import sys
import threading
import time
from builtins import BaseException
from enum import Enum, auto
from types import ModuleType, TracebackType
from typing import Any, Literal, Protocol, Self, TypedDict, TypeVar, overload



class ProcessingEvent(Enum):
    """Enum for different processing events."""

    PROCESSING_STARTED = auto()
    FILE_PROCESSED = auto()
    FILE_CONTENT_PROCESSED = auto()
    PROCESSING_COMPLETE = auto()
    OUTPUT_GENERATED = auto()


class ProcessingStartedData(TypedDict):
    """Data for the processing started event."""

    total_files: int


class FileProcessedData(TypedDict):
    """Data for a file processed event."""

    path: str


class FileContentProcessedData(TypedDict):
    """Data for file content processed event."""

    content_chunk: str


class OutputGeneratedData(TypedDict):
    """Data for the output generated event."""

    output_path: str
    total_tokens: int | None
    total_lines: int | None


_T = TypeVar("_T", contravariant=True)


class Observer(Protocol[_T]):
    """Protocol for observers, generic over the event data type."""

    def update(self, event: ProcessingEvent, data: _T) -> None:
        """Receive update from subject."""
        ...


class Publisher:
    """Publisher class for the observer pattern."""

    def __init__(self, total_files: int = 0):
        """Initialize the Publisher."""
        self.observers: list[Observer[Any]] = []
        self.total_files = total_files

    def __enter__(self) -> Self:
        """Enter runtime context; notify observers processing started."""
        self.notify(
            ProcessingEvent.PROCESSING_STARTED,
            ProcessingStartedData(total_files=self.total_files),
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Exit the runtime context and notify observers that processing is complete."""
        self.notify(ProcessingEvent.PROCESSING_COMPLETE, None)
        return False

    def subscribe(self, observer: Observer[Any]) -> None:
        """Subscribe an observer to the publisher."""
        self.observers.append(observer)

    def unsubscribe(self, observer: Observer[Any]) -> None:
        """Unsubscribe an observer from the publisher."""
        try:
            self.observers.remove(observer)
        except ValueError:
            pass

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.PROCESSING_STARTED],
        data: ProcessingStartedData,
    ) -> None: ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.FILE_PROCESSED],
        data: FileProcessedData,
    ) -> None: ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.FILE_CONTENT_PROCESSED],
        data: FileContentProcessedData,
    ) -> None: ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.PROCESSING_COMPLETE],
        data: None,
    ) -> None: ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.OUTPUT_GENERATED],
        data: OutputGeneratedData,
    ) -> None: ...

    def notify(self, event: ProcessingEvent, data: Any) -> None:
        """
        Notify all subscribed observers of an event.

        Args:
            event: The event type (e.g., 'file_processed', 'processing_complete')
            data: Event-specific data to pass to observers

        Note:
            Failed observers are logged but don't stop other observers.

        """
        for observer in self.observers[:]:  # Copy list to allow modifications
            try:
                observer.update(event, data)
            except Exception as e:
                logging.error(f"Observer {observer.__class__.__name__} failed: {e}")


class LineCounterObserver(Observer[FileContentProcessedData]):
    """Observer for counting lines."""

    def __init__(self) -> None:
        """Initialize the LineCounterObserver."""
        self._total_lines: int = 0
        self._lock = threading.Lock()

    @property
    def total_lines(self) -> int:
        """Return the total number of lines counted."""
        return self._total_lines

    def update(self, event: ProcessingEvent, data: FileContentProcessedData) -> None:
        """Count lines based on the event."""
        if event == ProcessingEvent.FILE_CONTENT_PROCESSED:
            with self._lock:
                chunk = data["content_chunk"]
                self._total_lines += chunk.count("\n") + 1 if chunk else 0


class TelemetryObserver(Observer[ProcessingStartedData | None]):
    """Observer for logging telemetry data like total files processed and time taken."""

    def __init__(self) -> None:
        """Initialize the TelemetryObserver."""
        self.start_time: float | None = None
        self.total_files_processed: int = 0

    def update(
        self, event: ProcessingEvent, data: ProcessingStartedData | None
    ) -> None:
        """Receive update from subject and log telemetry."""
        if event == ProcessingEvent.PROCESSING_STARTED:
            self.start_time = time.time()
            if data:
                self.total_files_processed = data.get("total_files", 0)
        elif (
            event == ProcessingEvent.PROCESSING_COMPLETE and self.start_time is not None
        ):
            duration = time.time() - self.start_time
            logging.info(f"Processing complete. Duration: {duration:.2f}s")


class TokenCounterObserver(Observer[FileContentProcessedData]):
    """Observer for counting tokens."""

    def __init__(self, token_encoding_model: str = "cl100k_base") -> None:
        """Initialize the TokenCounterObserver."""
        self.total_tokens = 0
        self.token_encoding_model = token_encoding_model
        self._lock = threading.Lock()
        self._tiktoken_module: ModuleType | None = None

    @property
    def tiktoken_module(self) -> ModuleType | None:
        """Lazily import and return the tiktoken module."""
        if self._tiktoken_module is None:
            try:
                import tiktoken

                self._tiktoken_module = tiktoken
            except ImportError:
                logging.warning("tiktoken not found. Token counting will be skipped.")
        return self._tiktoken_module

    def update(self, event: ProcessingEvent, data: FileContentProcessedData) -> None:
        """Count tokens based on the event."""
        if self.tiktoken_module is None:
            return

        if event == ProcessingEvent.FILE_CONTENT_PROCESSED:
            content = data["content_chunk"]
            try:
                encoding = self.tiktoken_module.get_encoding(self.token_encoding_model)
                tokens: list[int] = encoding.encode(content)
                with self._lock:
                    self.total_tokens += len(tokens)
            except ValueError as e:
                logging.error(f"Error counting tokens for file content: {e}")

```

## FILE: src/output_generator.py

```py
# Copyright (c) 2025 skum

"""Provides abstract and concrete classes for generating combined code output."""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from pathlib import Path
from typing import Any

from .context import GeneratorContext
from .formatters import JSONFormatter, OutputFormatter, XMLFormatter
from .observers import (
    FileContentProcessedData,
    FileProcessedData,
    OutputGeneratedData,
    ProcessingEvent,
    ProcessingStartedData,
    Publisher,
)
from .utils import is_likely_binary, log_file_read_error


def read_file_content(file_path: Path, chunk_size: int = 65536) -> Generator[str]:
    """Read file content in chunks with proper error handling."""
    if is_likely_binary(file_path):
        return
    try:
        with open(file_path, encoding="utf-8") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    except (
        UnicodeDecodeError,
        FileNotFoundError,
        PermissionError,
        IsADirectoryError,
    ) as e:
        log_file_read_error(file_path, e)


class OutputGenerator(ABC):
    """Abstract base class for output generation."""

    def __init__(
        self,
        files_to_process: list[Path],
        root_path: Path,
        formatter: OutputFormatter,
        publisher: Publisher,
    ) -> None:
        """Initialize the OutputGenerator."""
        self.files_to_process = files_to_process
        self.root_path = root_path
        self.formatter = formatter
        self.publisher = publisher

    @abstractmethod
    def generate(self) -> Any:
        """Generate the output."""
        pass

    @abstractmethod
    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        pass


class InMemoryOutputGenerator(OutputGenerator):
    """Generates the combined output content in memory."""

    def __init__(self, context: GeneratorContext):
        """Initialize the InMemoryOutputGenerator."""
        super().__init__(
            context.files_to_process,
            context.root_path,
            context.formatter,
            context.publisher,
        )
        self.output_content = ""
        self.raw_combined_content = ""
        self.raw_content_parts: list[str] = []
        self.formatted_content_parts: list[str] = []
        self.json_data: dict[str, str] = {}
        self.memory_monitor = context.memory_monitor
        self.publisher = context.publisher
        self.output_path = context.output_path
        self.ui = context.ui
        self.token_counter_observer = context.token_counter_observer
        self.line_counter_observer = context.line_counter_observer
        self.xml_root_element: ET.Element | None = None

    def _read_file_and_notify(self, file_path: Path) -> tuple[Path, str | None]:
        """Read a file's content and notify observers."""
        content_chunks = list(read_file_content(file_path))
        if not content_chunks and not is_likely_binary(file_path):
            return file_path, None

        full_content = "".join(content_chunks)
        for chunk in content_chunks:
            self.publisher.notify(
                ProcessingEvent.FILE_CONTENT_PROCESSED,
                FileContentProcessedData(content_chunk=chunk),
            )
        return file_path, full_content

    def generate(self) -> tuple[str, str]:
        """Generate output in memory."""
        self.publisher.notify(
            ProcessingEvent.PROCESSING_STARTED,
            ProcessingStartedData(total_files=len(self.files_to_process)),
        )

        self._begin_output()

        file_contents = {}
        import os

        max_workers = min(32, (os.cpu_count() or 1) + 4)
        future_to_path = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            try:
                for path in self.files_to_process:
                    future = executor.submit(self._read_file_and_notify, path)
                    future_to_path[future] = path

                failed_files = []
                for future in as_completed(future_to_path, timeout=300):
                    path = future_to_path[future]
                    try:
                        _, content = future.result(timeout=10)
                        file_contents[path] = content
                    except TimeoutError:
                        logging.warning(f"Timeout reading {path}")
                        file_contents[path] = None
                        failed_files.append(path)
                    except Exception as e:
                        log_file_read_error(path, e)
                        file_contents[path] = None
                        failed_files.append(path)

                if failed_files:
                    logging.warning(
                        f"Failed to read {len(failed_files)} files. "
                        f"See log for details."
                    )

            except Exception as e:
                logging.error(f"An error occurred during file processing: {e}")
                executor.shutdown(wait=False, cancel_futures=True)
                raise

        check_interval = max(1, min(10, len(self.files_to_process) // 20))

        for i, file_path in enumerate(self.files_to_process):
            content = file_contents.get(file_path)
            self._process_single_file(i, file_path, content, check_interval)

        result = self._end_output()
        self.publisher.notify(
            ProcessingEvent.OUTPUT_GENERATED,
            OutputGeneratedData(
                output_path=str(self.output_path),
                total_tokens=(
                    self.token_counter_observer.total_tokens
                    if self.token_counter_observer
                    else None
                ),
                total_lines=(
                    self.line_counter_observer.total_lines
                    if self.line_counter_observer
                    else None
                ),
            ),
        )
        return result

    def _begin_output(self) -> None:
        """Prepare for in-memory output generation."""
        if not isinstance(self.formatter, JSONFormatter):
            self.formatted_content_parts.append(self.formatter.begin_output())

    def _process_file(self, relative_path: Path, content: str) -> None:
        """Process each file's content for in-memory storage."""
        self.raw_content_parts.append(content)
        if isinstance(self.formatter, JSONFormatter):
            self.json_data[str(relative_path)] = content
        else:
            self.formatted_content_parts.append(
                self.formatter.format_file(relative_path, content)
            )

    def _end_output(self) -> tuple[str, str]:
        """Finalize in-memory output and return it."""
        if isinstance(self.formatter, JSONFormatter):
            self.output_content = json.dumps(self.json_data, indent=4)
        else:
            self.formatted_content_parts.append(self.formatter.end_output())
            self.output_content = "".join(self.formatted_content_parts)

        self.raw_combined_content = "".join(self.raw_content_parts)
        return self.output_content, self.raw_combined_content

    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        return f"Processing files ({self.formatter.format_name})"

    def _get_relative_path(self, file_path: Path) -> Path:
        try:
            return file_path.relative_to(self.root_path)
        except ValueError:
            return file_path

    def _update_ui(self, relative_path: Path, skipped: bool) -> None:
        tokens = (
            self.token_counter_observer.total_tokens
            if self.token_counter_observer
            else None
        )
        lines = (
            self.line_counter_observer.total_lines
            if self.line_counter_observer
            else None
        )
        self.ui.update(
            str(relative_path),
            skipped=skipped,
            tokens=tokens,
            lines=lines,
        )

    def _process_single_file(
        self, i: int, file_path: Path, content: str | None, check_interval: int
    ) -> None:
        """Process a single file within the main loop."""
        # Sample memory usage instead of checking every file
        if i % check_interval == 0:
            if self.memory_monitor:
                self.memory_monitor.check_memory_usage()

        relative_path = self._get_relative_path(file_path)

        self.publisher.notify(
            ProcessingEvent.FILE_PROCESSED, FileProcessedData(path=str(relative_path))
        )

        self._update_ui(relative_path, content is None)

        if content is None:
            return
        self._process_file(relative_path, content)


class StreamingOutputGenerator(OutputGenerator):
    """Streams the combined output content directly to a file."""

    def __init__(self, context: GeneratorContext):
        """Initialize the StreamingOutputGenerator."""
        super().__init__(
            context.files_to_process,
            context.root_path,
            context.formatter,
            context.publisher,
        )
        self.output_path = context.output_path
        self.dry_run = context.dry_run
        self.dry_run_output_path = (
            Path(context.dry_run_output) if context.dry_run_output else None
        )
        self.ui = context.ui
        self.token_counter_observer = context.token_counter_observer
        self.line_counter_observer = context.line_counter_observer

    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        return "Processing files (Streaming)"

    def _process_file_streaming(
        self, file_path: Path, outfile: Any | None = None
    ) -> None:
        try:
            relative_path = file_path.relative_to(self.root_path)
        except ValueError:
            relative_path = file_path  # Use full path if not relative to root

        self.publisher.notify(
            ProcessingEvent.FILE_PROCESSED, FileProcessedData(path=str(relative_path))
        )
        content_generator = read_file_content(file_path)
        full_content = ""
        for chunk in content_generator:
            full_content += chunk
            self.publisher.notify(
                ProcessingEvent.FILE_CONTENT_PROCESSED,
                FileContentProcessedData(content_chunk=chunk),
            )  # Notify with chunk

        if not full_content and not is_likely_binary(file_path):
            content = None
        else:
            content = full_content

        # Update UI
        tokens = (
            self.token_counter_observer.total_tokens
            if self.token_counter_observer
            else None
        )
        lines = (
            self.line_counter_observer.total_lines
            if self.line_counter_observer
            else None
        )
        self.ui.update(
            str(relative_path),
            skipped=(content is None),
            tokens=tokens,
            lines=lines,
        )

        if content is not None and outfile is not None:
            if isinstance(self.formatter, XMLFormatter):
                self.formatter.format_file_stream(relative_path, file_path, outfile)
            else:
                outfile.write(self.formatter.format_file(relative_path, full_content))
        elif content is not None and outfile is None and self.dry_run:
            import sys

            sys.stdout.write(self.formatter.format_file(relative_path, content))

    def generate(self) -> None:
        """Generate output by streaming to file or printing to stdout if dry_run."""
        if self.dry_run:
            self._handle_dry_run_streaming()
        else:
            self._handle_actual_streaming()

        return None

    def _stream_files_to_output(self, outfile: Any, is_dry_run: bool) -> None:
        for file_path in self.files_to_process:
            self._process_file_streaming(file_path, outfile if not is_dry_run else None)

    def _write_stream_to_file(self, outfile: Any, is_dry_run: bool) -> None:
        outfile.write(self.formatter.begin_output())
        self._stream_files_to_output(outfile, is_dry_run)
        outfile.write(self.formatter.end_output())

    def _handle_dry_run_streaming(self) -> None:
        import sys

        logging.info("--- Dry Run Output (Streaming) ---")
        for file_path in self.files_to_process:
            self._process_file_streaming(file_path, sys.stdout)
        logging.info("--- End Dry Run Output (Streaming) ---")
        if self.dry_run_output_path:
            try:
                self.dry_run_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.dry_run_output_path, "w", encoding="utf-8") as outfile:
                    for file_path in self.files_to_process:
                        self._process_file_streaming(file_path, outfile)
                logging.info(
                    f"Dry run output also written to: {self.dry_run_output_path}"
                )
            except Exception as e:
                logging.error(
                    f"Error writing dry run output to {self.dry_run_output_path}: {e}"
                )

    def _handle_actual_streaming(self) -> None:
        # Determine if we are using a streaming formatter that writes directly to file
        is_direct_streaming_formatter = hasattr(self.formatter, "format_file_stream")

        if not self.files_to_process and not is_direct_streaming_formatter:
            logging.info("No content to write. File not created.")
            return

        temp_path = self.output_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as outfile:
                self._write_stream_to_file(outfile, is_dry_run=False)
            temp_path.replace(self.output_path)  # Atomic rename
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

```

## FILE: src/ui.py

```py
# Copyright (c) 2025 skum

"""User interface for CodeMeld, providing live progress and a final summary."""

from __future__ import annotations

import logging
import shutil
import sys
import time
from typing import Any

from tqdm import tqdm

_psutil_module: Any | None
try:
    import psutil

    _psutil_module = psutil
except ImportError:
    _psutil_module = None


class LiveUI:
    """A combined live + static text UI for CodeCombiner."""

    def __init__(
        self,
        total_files: int = 0,
        title: str = "CODEMELD",
        version: str = "v0.1.0",
    ):
        """Initialize the LiveUI with default values."""
        self.total_files = total_files
        self.title = title
        self.version = version
        self.start_time: float | None = None
        self._progress_bar: tqdm[Any] | None = None
        self.processed = 0
        self.skipped = 0
        self.tokens = 0
        self.total_lines = 0
        self.memory_mb = 0.0
        self.output_file: str = ""
        self.use_gitignore = True
        self.include_hidden = False
        self.count_tokens = True
        self.format = "text"
        self.directory = "."
        self.verbose = False
        self._included_files_set: set[str] = set()
        self.included_files: list[str] = []
        self.list_files: bool = False
        self.summary: bool = False
        self.progress_style: str | None = None

    # ───────────────────────────────
    # Header & Config Display
    # ───────────────────────────────
    def print_header(self) -> None:
        """Print the header of the UI, including title and version."""
        width = shutil.get_terminal_size((80, 20)).columns
        bar = "═" * (width - 2)
        print(f"╔{bar}╗")
        print(f"║{self.title.center(width - 2)}║")
        print(f"║{self.version.center(width - 2)}║")
        print(f"╚{bar}╝\n")

    def print_config(self) -> None:
        """Print the current configuration settings."""
        width = shutil.get_terminal_size((80, 20)).columns
        separator = "─" * width
        label_width = 18

        labels = {
            "Input Directory": self.directory,
            "Output File": self.output_file,
            "Format": self.format,
            "Include Hidden": "yes" if self.include_hidden else "no",
            "Use .gitignore": "yes" if self.use_gitignore else "no",
            "Count Tokens": "yes" if self.count_tokens else "no",
        }

        for label, value in labels.items():
            print(f"{label:<{label_width}} : {value}")
        print(f"\n{separator}")
        print("Scanning files...")

    # ───────────────────────────────
    # Live Progress Handling
    # ───────────────────────────────
    def start(self) -> None:
        """Start live progress display."""
        self.start_time = time.time()
        if self.progress_style == "none":
            self._progress_bar = None
            if self.verbose:
                print(f"Processing {self.total_files} files...")
            return

        if sys.stdout.isatty():
            tqdm_kwargs: dict[str, Any] = {
                "total": self.total_files,
                "desc": "Processing files",
                "ncols": shutil.get_terminal_size((80, 20)).columns,
                "leave": False,
            }
            if self.progress_style:
                # Allow custom bar_format if a style is provided, otherwise use default
                tqdm_kwargs["bar_format"] = (
                    "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]"
                )
                if self.progress_style == "ascii":
                    tqdm_kwargs["ascii"] = True
                elif self.progress_style == "block":
                    tqdm_kwargs["bar_format"] = (
                        "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]"
                    )
                # Add more styles as needed

            self._progress_bar = tqdm(**tqdm_kwargs)
        elif self.verbose:
            print(f"Processing {self.total_files} files...")

    def update(
        self,
        file_path: str | None = None,
        skipped: bool = False,
        tokens: int | None = None,
        lines: int | None = None,
    ) -> None:
        """Update progress line-by-line."""
        self.processed += 0 if skipped else 1
        self.skipped += 1 if skipped else 0
        if tokens is not None:
            self.tokens = tokens
        if lines is not None:
            self.total_lines = lines
        if _psutil_module:
            proc = _psutil_module.Process()
            self.memory_mb = proc.memory_info().rss / (1024 * 1024)
        if self._progress_bar:
            self._progress_bar.update(1)
            self._progress_bar.set_postfix(
                {
                    "file": file_path,
                    "mem": f"{self.memory_mb:.0f} MB",
                    "tokens": f"{self.tokens:,}",
                }
            )
        elif self.verbose:
            print(f"Processed: {file_path}")

        if not skipped:
            if file_path and file_path not in self._included_files_set:
                self._included_files_set.add(file_path)
                self.included_files.append(file_path)
            logging.debug(
                f"LiveUI.update: Added {file_path}. Count: {len(self.included_files)}"
            )

    # ───────────────────────────────
    # Final Summary
    # ───────────────────────────────
    def finish(self) -> None:
        """Close the live view and show static summary."""
        if self._progress_bar:
            self._progress_bar.close()
        duration = time.time() - (self.start_time or time.time())

        width = shutil.get_terminal_size((80, 20)).columns
        separator = "─" * width
        label_width = 25  # Increased label width for summary

        logging.debug(
            f"LiveUI.finish: list_files={self.list_files}, "
            f"count={len(self.included_files)}"
        )

        if self.list_files and self.included_files:
            print("Included files:")
            for path in sorted(self._included_files_set):
                print(f"  - {path}")

        if self.summary:
            summary_items = {
                "Total files processed": self.processed,
                "Skipped (binary)": self.skipped,
                "Total lines": f"{self.total_lines:,}",
                "Output file": self.output_file,
            }
            if self.count_tokens:
                summary_items["Token count"] = f"{self.tokens:,}"
            if _psutil_module:
                summary_items["Peak memory usage"] = f"{self.memory_mb:.0f} MB"
            summary_items["Duration"] = f"{duration:.1f}s"

            print(f"\n{separator}")
            print("Summary:")
            for label, value in summary_items.items():
                print(f"  {label:<{label_width}} : {value}")

            print(f"{separator}")
            print("All done!\n")

    # ───────────────────────────────
    # Utility: Apply from Config
    # ───────────────────────────────
    def apply_config(self, config: Any) -> None:
        """Apply CodeCombiner config to the UI display."""
        self.directory = str(config.directory_path)
        self.output_file = config.output
        self.format = config.format
        self.include_hidden = config.include_hidden
        self.use_gitignore = config.use_gitignore
        self.count_tokens = config.count_tokens
        self.verbose = config.verbose
        self.list_files = config.list_files
        self.summary = config.summary
        self.progress_style = config.progress_style

```

## FILE: src/utils.py

```py
# Copyright (c) 2025 skum

"""Utility functions for the CodeMeld tool."""

import logging
from pathlib import Path

from src.config import CombinerConfig

BINARY_EXTENSIONS = {
    ".bin",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".o",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
}


def log_file_read_error(file_path: Path, error: Exception) -> None:
    """Log a warning for file read errors."""

    if isinstance(error, UnicodeDecodeError):
        logging.warning(
            f"Skipping file due to UnicodeDecodeError: {file_path} "
            f"(codec: {error.encoding}, position: {error.start}-{error.end})"
        )

    elif isinstance(error, FileNotFoundError):
        logging.warning(f"Skipping file not found: {file_path}")

    elif isinstance(error, PermissionError):
        logging.warning(f"Skipping file due to permission error: {file_path}")

    elif isinstance(error, IsADirectoryError):
        logging.warning(f"Skipping directory treated as file: {file_path}")

    else:
        logging.error(
            f"An unexpected error occurred while reading {file_path}: {error}"
        )


def is_likely_binary(file_path: Path, config: CombinerConfig | None = None) -> bool:
    """
    Determine if a file is likely binary.

    Determines if a file is likely binary based on its extension and/or
    content analysis.
    This is a heuristic check, optimized for performance, especially with large files.
    It's not foolproof and might misclassify some files.
    """
    # 1. Fast check by file extension:
    # If the file has a common binary extension, it's immediately classified as binary.
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    # Use configurable values or defaults
    sample_size_bytes = config.sample_size_bytes if config else 8192
    large_file_threshold_bytes = (
        config.large_file_threshold_bytes if config else 1024 * 1024
    )
    non_text_threshold = config.non_text_threshold if config else 0.30

    # 2. Content analysis for other files:
    # For files without a known binary extension, perform a quick content scan.
    try:
        file_size = file_path.stat().st_size
        # Determine sample size: For very large files (>1MB), only read the first 8KB.
        # Otherwise, read up to 8KB or the entire file if smaller.
        sample_size = (
            min(sample_size_bytes, file_size)
            if file_size > large_file_threshold_bytes
            else file_size
        )

        with open(file_path, "rb") as f:
            chunk = f.read(sample_size)
            if not chunk:
                # Empty file or unable to read, assume not binary (or
                # handle as per policy)
                return False

            # Heuristic 1: Check for null bytes
            # The presence of null bytes (b'\0') is a strong indicator of a binary file.
            if b"\0" in chunk:
                return True

            # Heuristic 2: Check proportion of non-text bytes
            # Count bytes that are not common ASCII text characters
            # (printable + whitespace).
            # If a significant proportion (e.g., >30%) are non-text, it's likely binary.
            text_chars = bytes(range(32, 127)) + b"\n\r\t\f\b"
            non_text = sum(1 for byte in chunk if byte not in text_chars)
            # This threshold (0.30) is a common heuristic; it can be tuned.
            return (non_text / len(chunk)) > non_text_threshold
    except Exception as e:
        # Log any errors during file access or analysis and default to
        # treating as binary
        # to prevent potential issues with processing unreadable or problematic files.
        logging.warning(f"Error checking binary status for {file_path}: {e}")
        return True

```

## FILE: tests/integration/test_always_include_safety.py

```py
from src.code_combiner import CodeMeld
from src.config import CombinerConfig


def test_always_include_with_large_binary_file_blocked(tmp_path):
    """Integration test: --always-include should NOT bypass safety filters"""
    # Create a large binary file
    large_binary = tmp_path / "huge.bin"
    large_binary.write_bytes(b"\x00" * (200 * 1024))

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(tmp_path / "output.txt"),
        always_include=[str(large_binary)],
        max_file_size_kb=100,  # Block files > 100KB
    )

    combiner = CodeMeld(config)
    combiner.execute()

    # The file should be filtered out, so the output file should not be created
    # or should be empty if it was created by some other mechanism.
    output_file_path = tmp_path / "output.txt"
    assert not output_file_path.exists() or output_file_path.read_text() == "", (
        "Output file should not exist or be empty if all files are filtered out."
    )

```

## FILE: tests/integration/test_cli_end_to_end.py

```py
# Copyright (c) 2025 skum

import subprocess
import sys


def test_cli_basic_run(tmp_path):
    """Test a basic CLI run with default options."""
    (tmp_path / "file1.py").write_text("print('hello')")
    (tmp_path / "file2.txt").write_text("just text")

    output_file = tmp_path / "combined_code.txt"

    # Construct the command to run the script
    command = [
        sys.executable,
        "-m",
        "src.code_combiner",
        str(tmp_path),
        "-o",
        str(output_file),
        "-e",
        ".py",
        ".txt",
        "--force",
    ]

    # Execute the command in a pseudo-terminal
    result = subprocess.run(command, capture_output=True, text=True, check=True)

    # Assertions
    assert result.returncode == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "FILE: file1.py" in content
    assert "print('hello')" in content
    assert "FILE: file2.txt" in content
    assert "just text" in content

```

## FILE: tests/integration/test_end_to_end.py

```py
# Copyright (c) 2025 skum

import logging

from src.code_combiner import CodeMeld
from src.config import CombinerConfig


def test_complete_refactored_flow(tmp_path):
    """Test the entire refactored architecture end-to-end."""
    # Create test files
    (tmp_path / "file1.py").write_text("print('test')")
    (tmp_path / "file2.js").write_text("console.log('test')")
    (tmp_path / ".gitignore").write_text("*.log")
    (tmp_path / "debug.log").write_text("should be ignored")

    output = tmp_path / "output.txt"

    # Run with various options
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output),
        extensions=[".py", ".js"],
        use_gitignore=True,
        count_tokens=False,
    )

    combiner = CodeMeld(config)
    combiner.execute()

    # Verify
    assert output.exists()
    content = output.read_text()
    assert "print('test')" in content
    assert "console.log('test')" in content
    assert "should be ignored" not in content


def test_convert_json_to_markdown(tmp_path):
    """Test converting JSON output to Markdown format."""
    (tmp_path / "test.py").write_text("def func():\n    pass")
    output_file = tmp_path / "output.md"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        extensions=[".py"],
        format="json",
        final_output_format="markdown",
    )

    combiner = CodeMeld(config)
    combiner.execute()

    assert output_file.exists()
    content = output_file.read_text()
    assert "## FILE: test.py" in content
    assert "```py" in content  # Changed from "```python"
    assert "def func():" in content
    assert "pass" in content
    assert "{" not in content  # Should not contain JSON syntax
    assert "}" not in content  # Should not contain JSON syntax


def test_convert_xml_to_text(tmp_path):
    """Test converting XML output to plain text format."""
    (tmp_path / "main.js").write_text("console.log('hello');")
    output_file = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        extensions=[".js"],
        format="xml",
        final_output_format="text",
    )

    combiner = CodeMeld(config)
    combiner.execute()

    assert output_file.exists()
    content = output_file.read_text()
    assert "FILE: main.js" in content
    assert "console.log('hello');" in content
    assert "<" not in content  # Should not contain XML syntax
    assert ">" not in content  # Should not contain XML syntax


def test_dry_run_mode(tmp_path, capsys, caplog):
    """Test that --dry-run mode prints to stdout and does not create an output file."""

    (tmp_path / "file1.py").write_text("print('dry run test')")

    output_file = tmp_path / "dry_run_output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        extensions=[".py"],
        dry_run=True,
    )

    combiner = CodeMeld(config)

    with caplog.at_level(logging.INFO):
        combiner.execute()

    # Verify that the output file was NOT created

    assert not output_file.exists()

    # Verify that the content was printed to stdout

    captured_stdout = capsys.readouterr().out

    # Verify logging messages using caplog

    assert "--- Dry Run Output ---" in caplog.text

    assert "--- End Dry Run Output ---" in caplog.text

    assert "print('dry run test')" in captured_stdout


def test_gitignore_precedence(tmp_path):
    """Test that .gitignore rules take precedence over included extensions."""
    # Create a Python file
    (tmp_path / "ignored_file.py").write_text("print('This should be ignored')")
    # Create a .gitignore that ignores all .py files
    (tmp_path / ".gitignore").write_text("*.py")

    output = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output),
        extensions=[".py"],
        use_gitignore=True,
        count_tokens=False,
    )

    combiner = CodeMeld(config)
    combiner.execute()

    # Verify that the output file exists but does NOT contain the ignored Python file
    assert not output.exists()


def test_custom_file_headers_formatting(tmp_path):
    """Test that --custom-file-headers formatting is applied correctly."""
    (tmp_path / "script.py").write_text("print('Hello from Python')")
    (tmp_path / "app.js").write_text("console.log('Hello from JS')")

    output = tmp_path / "output.txt"

    custom_headers = {"py": "# Python File: {path}", "js": "// JavaScript File: {path}"}

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output),
        extensions=[".py", ".js"],
        custom_file_headers=custom_headers,
        count_tokens=False,
    )

    combiner = CodeMeld(config)
    combiner.execute()

    assert output.exists()
    content = output.read_text()

    assert "# Python File: script.py" in content
    assert "print('Hello from Python')" in content
    assert "// JavaScript File: app.js" in content
    assert "console.log('Hello from JS')" in content


def test_memory_threshold_fallback(tmp_path, caplog):
    """Test that memory threshold exceeding triggers fallback to streaming output."""
    large_file = tmp_path / "large_file.txt"
    large_file.write_text("a" * (1024 * 1024 * 2))  # 2MB file

    output_file = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        extensions=[".txt"],
        max_memory_mb=1,  # Intentionally very low
        count_tokens=False,  # Fallback only occurs if token counting is not needed
    )

    combiner = CodeMeld(config)

    with caplog.at_level(logging.WARNING):
        combiner.execute()

    # Output file should exist (streaming fallback succeeded)
    assert output_file.exists()
    content = output_file.read_text()
    assert "a" * (1024 * 1024 * 2) in content

    # Log should contain fallback message (looser match for robustness)
    assert any(
        "Falling back to streaming due to memory constraints" in record.message
        for record in caplog.records
    )


def test_dry_run_mode_with_streaming_fallback(tmp_path, capsys, caplog):
    """Test that --dry-run mode with forced streaming fallback prints to
    stdout and does not create an output file."""
    large_file = tmp_path / "large_file.txt"
    large_file.write_text("a" * (1024 * 1024 * 2))  # 2MB file

    output_file = tmp_path / "dry_run_streaming_output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        extensions=[".txt"],
        dry_run=True,
        max_memory_mb=1,  # Force streaming fallback
        count_tokens=False,  # Required for streaming fallback
    )

    combiner = CodeMeld(config)

    with caplog.at_level(logging.INFO):
        combiner.execute()

    # Verify that the output file was NOT created
    assert not output_file.exists()

    # Verify that the content was printed to stdout
    captured_stdout = capsys.readouterr().out

    # Verify logging messages using caplog
    assert "--- Dry Run Output (Streaming) ---" in caplog.text
    assert "--- End Dry Run Output (Streaming) ---" in caplog.text
    assert "Falling back to streaming due to memory constraints" in caplog.text

    assert "a" * (1024 * 1024 * 2) in captured_stdout

```

## FILE: tests/integration/test_large_files.py

```py
# Copyright (c) 2025 skum

from pathlib import Path

import pytest

from src.code_combiner import CodeMeld
from src.config import CombinerConfig


@pytest.fixture
def large_file(tmp_path: Path) -> Path:
    large_file_path = tmp_path / "large_file.txt"
    # Create a smaller file for testing (10KB instead of 1MB)
    with open(large_file_path, "w") as f:
        f.write("a" * 10 * 1024)  # 10KB
    return large_file_path


@pytest.fixture
def large_xml_file(tmp_path: Path) -> Path:
    large_file_path = tmp_path / "large_file.xml"
    with open(large_file_path, "w") as f:
        f.write("<data>" + "a" * (10 * 1024) + "</data>")
    return large_file_path


def test_large_file_processing(tmp_path: Path, large_file: Path):
    output_path = tmp_path / "output.txt"
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_path),
        extensions=[".txt"],
        count_tokens=False,  # Disable token counting for large files
    )
    combiner = CodeMeld(config)
    combiner.execute()

    assert output_path.exists()
    # Check that file was processed without hanging
    assert output_path.stat().st_size > 0


def test_large_xml_file_streaming(tmp_path: Path, large_xml_file: Path):
    output_path = tmp_path / "output.xml"
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_path),
        extensions=[".xml"],
        format="xml",
        count_tokens=False,
        max_memory_mb=1,  # Force streaming
    )
    combiner = CodeMeld(config)
    combiner.execute()

    assert output_path.exists()
    content = output_path.read_text()
    assert "&lt;data&gt;" + "a" * (10 * 1024) + "&lt;/data&gt;" in content

```

## FILE: tests/performance/test_benchmarks.py

```py
# Copyright (c) 2025 skum


from src.code_combiner import CodeMeld
from src.config import CombinerConfig


def test_processing_speed_benchmark(benchmark, tmp_path):
    """Benchmark processing speed for 1K files."""
    num_files = 1000
    for i in range(num_files):
        (tmp_path / f"file_{i}.py").write_text(f"# File {i}\nprint({i})")

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(tmp_path / "output.txt"),
        extensions=[".py"],
        count_tokens=False,  # Disable token counting for benchmark
    )

    # Benchmark the execute method
    benchmark(CodeMeld(config).execute)

    # Assert that the output file exists
    output_path = tmp_path / "output.txt"
    assert output_path.exists()

```

## FILE: tests/test_benchmark.py

```py
import pytest

from src.code_combiner import CodeMeld
from src.config import CombinerConfig, MemoryThresholdExceededError


@pytest.mark.benchmark(group="codemeld")
def test_inmemory_generation_benchmark(benchmark, tmp_path):
    """Benchmark performance of in-memory generation."""
    small_dir = tmp_path / "src"
    small_dir.mkdir()
    (small_dir / "a.py").write_text("print('a')")
    (small_dir / "b.py").write_text("print('b')")

    base_config = CombinerConfig(directory_path=small_dir)

    def run_in_memory(**kwargs):
        CodeMeld(base_config).execute()

    benchmark.pedantic(run_in_memory)


@pytest.mark.benchmark(group="codemeld")
def test_streaming_generation_benchmark(benchmark, tmp_path):
    """Benchmark performance of streaming generation."""
    small_dir = tmp_path / "src"
    small_dir.mkdir()
    (small_dir / "a.py").write_text("print('a')")
    (small_dir / "b.py").write_text("print('b')")

    stream_cfg = CombinerConfig(directory_path=small_dir, max_memory_mb=1)

    def run_streaming(**kwargs):
        try:
            CodeMeld(stream_cfg).execute()
        except MemoryThresholdExceededError:
            pass  # Expected behavior for streaming fallback

    benchmark.pedantic(run_streaming)

```

## FILE: tests/unit/conftest.py

```py
# tests/unit/conftest.py
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.config import CombinerConfig


@pytest.fixture
def create_common_file_structure(tmp_path):
    file1 = tmp_path / "file1.py"
    file1.touch()
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.js"
    file2.touch()
    hidden_file = tmp_path / ".hidden_file.txt"
    hidden_file.touch()
    hidden_dir = tmp_path / ".hidden_dir"
    hidden_dir.mkdir()
    hidden_dir_file = hidden_dir / "secret.txt"
    hidden_dir_file.touch()
    return file1, file2, hidden_file, hidden_dir_file, tmp_path


@pytest.fixture
def mock_code_combiner_config():
    config = MagicMock(spec=CombinerConfig)
    # Create a mock Path object for directory_path
    mock_dir_path: Any = MagicMock()
    mock_dir_path.rglob = MagicMock(return_value=iter([]))  # Default empty rglob
    mock_dir_path.__truediv__.side_effect = lambda x: Path(
        str(mock_dir_path) + "/" + str(x)
    )  # Allow division for path joining
    mock_dir_path.is_absolute.return_value = True
    mock_dir_path.resolve.return_value = mock_dir_path  # Assume it resolves to itself
    mock_dir_path.__str__.return_value = "/mock/dir"  # For string representation

    config.directory_path = mock_dir_path
    config.extensions = [".py"]
    config.exclude_extensions = []
    config.use_gitignore = False
    config.include_hidden = False
    config.count_tokens = False
    config.header_width = 80
    config.format = "text"
    config.final_output_format = None
    config.force = False
    config.always_include = []
    config.output = "output.txt"
    config.token_encoding_model = "cl100k_base"
    config.max_memory_mb = 500
    config.custom_file_headers = {}
    config.max_file_size_kb = None  # Added
    return config


@pytest.fixture
def mock_filter_config():
    return CombinerConfig(
        directory_path=Path("/mock/root"),
        output="output.txt",
        extensions=[".py", ".js"],
        exclude_extensions=[".tmp"],
        use_gitignore=True,
        include_hidden=False,
        follow_symlinks=False,
        max_file_size_kb=100,
    )


@pytest.fixture
def mock_context():
    return {"root_path": Path("/mock/root")}


@pytest.fixture
def mock_file_path():
    return Path("/mock/root/test.py")


@pytest.fixture
def mock_spec():
    spec = MagicMock()
    spec.match_file.side_effect = lambda p: p == "ignored.py"
    return spec

```

## FILE: tests/unit/test_code_combiner.py

```py
# Copyright (c) 2025 skum

# This file is intentionally left empty after refactoring.
# The tests have been moved to more specific files:
# - test_code_combiner_scanning.py
# - test_code_combiner_execution.py
# - test_code_combiner_gitignore.py
# - test_code_combiner_always_include.py

```

## FILE: tests/unit/test_code_combiner_always_include.py

```py
# Copyright (c) 2025 skum

import logging

from src.code_combiner import CodeMeld


def test_get_filtered_files_always_include_non_existent(
    mock_code_combiner_config, caplog, tmp_path
):
    non_existent_file = tmp_path / "non_existent_file.py"
    mock_code_combiner_config.always_include = [non_existent_file]
    combiner = CodeMeld(mock_code_combiner_config)
    with caplog.at_level(logging.WARNING):
        combiner.execute()
    assert (
        f"Warning: --always-include path '{non_existent_file}' "
        "is not a file or does not exist. Skipping." in caplog.text
    )


def test_get_filtered_files_always_include_directory(
    mock_code_combiner_config, caplog, tmp_path
):
    mock_dir = tmp_path / "always_include_dir"
    mock_dir.mkdir()
    mock_code_combiner_config.always_include = [mock_dir]
    combiner = CodeMeld(mock_code_combiner_config)
    with caplog.at_level(logging.WARNING):
        combiner.execute()
    assert (
        f"Warning: --always-include path '{mock_dir}' "
        "is not a file or does not exist. Skipping." in caplog.text
    )

```

## FILE: tests/unit/test_code_combiner_execution.py

```py
# Copyright (c) 2025 skum

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.code_combiner import CodeMeld
from src.config import MemoryThresholdExceededError


def test_execute_output_written_by_streaming_path(mock_code_combiner_config, tmp_path):
    mock_code_combiner_config.count_tokens = False
    mock_code_combiner_config.output = str(tmp_path / "output.txt")
    combiner = CodeMeld(mock_code_combiner_config)

    with patch(
        "src.output_generator.InMemoryOutputGenerator"
    ) as MockInMemoryOutputGenerator:
        mock_in_memory_generator_instance = MockInMemoryOutputGenerator.return_value
        mock_in_memory_generator_instance.generate.side_effect = (
            MemoryThresholdExceededError("Memory exceeded")
        )

        with patch(
            "src.output_generator.StreamingOutputGenerator"
        ) as MockStreamingOutputGenerator:
            mock_streaming_generator_instance = (
                MockStreamingOutputGenerator.return_value
            )
            mock_streaming_generator_instance.generate.return_value = None
            # Simulate streaming writing directly

            with patch("src.code_combiner.write_output") as mock_write_output:
                combiner.execute()
                mock_write_output.assert_not_called()


def test_execute_processing_complete_notification_with_files(
    mock_code_combiner_config, caplog, tmp_path
):
    mock_code_combiner_config.output = str(tmp_path / "output.txt")
    file1 = tmp_path / "file1.py"
    file1.touch()
    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = [file1]

    with patch("src.output_generator.is_likely_binary", return_value=False):
        with patch.object(
            CodeMeld, "_get_filtered_files", return_value=[file1]
        ) as _mock_get_filtered_files:
            with patch(
                "builtins.open",
                MagicMock(
                    return_value=MagicMock(
                        __enter__=lambda self: MagicMock(
                            read=MagicMock(side_effect=["file content", ""])
                        ),
                        __exit__=MagicMock(),
                    )
                ),
            ):
                with patch(
                    "src.code_combiner.InMemoryOutputGenerator"
                ) as MockInMemoryOutputGeneratorClass:
                    mock_in_memory_generator_instance = (
                        MockInMemoryOutputGeneratorClass.return_value
                    )
                    mock_in_memory_generator_instance.generate.return_value = (
                        "output_content",
                        "raw_content",
                    )
                    with patch("src.code_combiner.Publisher") as MockPublisherClass:
                        mock_publisher_instance = MockPublisherClass.return_value

                        # Configure the __exit__ method of the mock instance
                        def mock_exit(exc_type, exc_val, exc_tb):
                            mock_publisher_instance.notify("processing_complete", None)
                            return False

                        mock_publisher_instance.__exit__.side_effect = mock_exit

                        mock_formatter = MagicMock()
                        mock_formatter.supports_streaming.return_value = True
                        combiner = CodeMeld(mock_code_combiner_config)
                        with patch(
                            "src.formatters.FormatterFactory.create",
                            return_value=mock_formatter,
                        ):
                            with patch("psutil.Process") as MockProcess:
                                mock_process_instance = MockProcess.return_value
                                mock_process_instance.memory_info.return_value.rss = (
                                    100 * 1024 * 1024
                                )  # Mock 100MB RSS
                                combiner.execute()
                            MockInMemoryOutputGeneratorClass.assert_called_once()
                            mock_in_memory_generator_instance.generate.assert_called_once()
                            mock_publisher_instance.notify.assert_called_with(
                                "processing_complete", None
                            )


def test_execute_write_output_called_when_not_streaming(
    mock_code_combiner_config, tmp_path
):
    mock_code_combiner_config.always_include = []
    mock_code_combiner_config.output = str(tmp_path / "output.txt")
    mock_code_combiner_config.force = True
    mock_code_combiner_config.dry_run = False
    mock_code_combiner_config.dry_run_output = None

    file1 = tmp_path / "file1.py"
    file1.touch()

    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = [file1]

    combiner = CodeMeld(mock_code_combiner_config)

    with patch.object(
        CodeMeld, "_get_filtered_files", return_value=[file1]
    ) as _mock_get_filtered_files:
        with patch(
            "src.code_combiner.InMemoryOutputGenerator"
        ) as MockInMemoryOutputGeneratorClass:
            mock_in_memory_generator_instance = (
                MockInMemoryOutputGeneratorClass.return_value
            )
            mock_in_memory_generator_instance.generate.return_value = (
                "some content",
                "raw content",
            )
            with patch("src.code_combiner.write_output") as mock_write_output:
                combiner.execute()
                mock_write_output.assert_called_once_with(
                    Path(mock_code_combiner_config.output),
                    "some content",
                    mock_code_combiner_config.force,
                    mock_code_combiner_config.dry_run,
                    None,  # dry_run_output_path
                )


def test_execute_no_files_to_process(mock_code_combiner_config, caplog, tmp_path):
    mock_code_combiner_config.always_include = []
    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = []
    # Simulate _get_filtered_files returning an empty list
    with patch.object(CodeMeld, "_get_filtered_files", return_value=[]):
        combiner = CodeMeld(mock_code_combiner_config)
        with caplog.at_level(logging.INFO):
            combiner.execute()
        assert "No files found to process. Exiting." in caplog.text

```

## FILE: tests/unit/test_code_combiner_extra.py

```py
# Copyright (c) 2025 skum

from unittest.mock import MagicMock, patch

from src.code_combiner import main, write_output
from src.config import CombinerConfig


def test_write_output_overwrite_interactive_yes(tmp_path):
    output_path = tmp_path / "output.txt"
    output_path.write_text("old content")

    with (
        patch("builtins.input", return_value="y"),
        patch("sys.stdin.isatty", return_value=True),
    ):
        write_output(output_path, "new content", force=False)

    assert output_path.read_text() == "new content"


def test_write_output_overwrite_interactive_no(tmp_path):
    output_path = tmp_path / "output.txt"
    output_path.write_text("old content")

    with patch("builtins.input", return_value="n"):
        write_output(output_path, "new content", force=False)

    assert output_path.read_text() == "old content"


def test_write_output_no_overwrite_non_interactive(tmp_path):
    output_path = tmp_path / "output.txt"
    output_path.write_text("old content")

    with patch("sys.stdin.isatty", return_value=False):
        write_output(output_path, "new content", force=False)

    assert output_path.read_text() == "old content"


def test_write_output_dry_run_with_output_path(tmp_path):
    output_path = tmp_path / "output.txt"
    dry_run_output_path = tmp_path / "dry_run_output.txt"

    write_output(
        output_path,
        "new content",
        force=False,
        dry_run=True,
        dry_run_output_path=dry_run_output_path,
    )

    assert not output_path.exists()
    assert dry_run_output_path.read_text() == "new content"


@patch("src.code_combiner.run_code_combiner")
@patch("src.code_combiner.load_and_merge_config")
@patch("src.code_combiner.parse_arguments")
def test_main(mock_parse_arguments, mock_load_and_merge_config, mock_run_code_combiner):
    mock_args = MagicMock()
    mock_parse_arguments.return_value = mock_args
    mock_config = MagicMock(spec=CombinerConfig)
    mock_load_and_merge_config.return_value = mock_config

    main()

    mock_parse_arguments.assert_called_once()
    mock_load_and_merge_config.assert_called_once_with(mock_args)
    mock_run_code_combiner.assert_called_once_with(mock_config)


@patch("argparse.ArgumentParser.parse_args")
def test_parse_arguments(mock_parse_args):
    from src.code_combiner import parse_arguments

    mock_args = MagicMock()
    mock_parse_args.return_value = mock_args

    args = parse_arguments()

    assert args == mock_args

```

## FILE: tests/unit/test_code_combiner_gitignore.py

```py
# Copyright (c) 2025 skum

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.code_combiner import CodeMeld


def test_get_gitignore_spec_found_in_current_dir(mock_code_combiner_config):
    mock_code_combiner_config.directory_path.resolve.return_value = Path("/mock/dir")
    with patch.object(
        Path,
        "is_file",
        side_effect=lambda: (
            True
            if (str(Path("/mock/dir/.gitignore")) == str(Path("/mock/dir/.gitignore")))
            else False
        ),
    ):
        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=lambda self: ["*.pyc"], __exit__=MagicMock()
                )
            ),
        ):
            combiner = CodeMeld(mock_code_combiner_config)
            spec = combiner._get_gitignore_spec()
            assert spec is not None
            assert spec.match_file("test.pyc")


def test_get_gitignore_spec_found_in_parent_dir(mock_code_combiner_config):
    # Simulate a directory structure like /mock/parent/dir and .gitignore in
    # /mock/parent
    mock_code_combiner_config.directory_path.resolve.return_value = Path(
        "/mock/parent/dir"
    )

    # Mock Path.is_file for .gitignore in parent directory
    def is_file_side_effect():
        if str(Path("/mock/parent/.gitignore")) == str(Path("/mock/parent/.gitignore")):
            return True
        return False

    with patch.object(Path, "is_file", side_effect=is_file_side_effect):
        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=lambda self: ["*.log"], __exit__=MagicMock()
                )
            ),
        ):
            combiner = CodeMeld(mock_code_combiner_config)
            spec = combiner._get_gitignore_spec()
            assert spec is not None
            assert spec.match_file("test.log")
            assert not spec.match_file("test.py")


def test_get_gitignore_spec_not_found(mock_code_combiner_config):
    mock_code_combiner_config.directory_path.resolve.return_value = Path("/mock/dir")
    with patch.object(Path, "is_file", return_value=False):
        combiner = CodeMeld(mock_code_combiner_config)
        spec = combiner._get_gitignore_spec()
        assert spec is None

```

## FILE: tests/unit/test_code_combiner_scanning.py

```py
# Copyright (c) 2025 skum

from unittest.mock import MagicMock, patch

import pytest

from src.code_combiner import CodeMeld
from src.config import CodeMeldError
from src.filters import FilterChainBuilder


def test_scan_files_permission_error(mock_code_combiner_config, tmp_path):
    # Simulate PermissionError during Path.rglob() iteration
    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    with patch.object(
        CodeMeld, "_iter_files", side_effect=PermissionError("Permission denied")
    ):
        combiner = CodeMeld(mock_code_combiner_config)
        with pytest.raises(
            CodeMeldError, match="Insufficient permissions to read files"
        ):
            combiner._get_filtered_files()


def test_scan_files_os_error(mock_code_combiner_config, tmp_path):
    # Simulate OSError during Path.rglob() iteration
    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    with patch.object(
        CodeMeld, "_iter_files", side_effect=OSError("OS error occurred")
    ):
        combiner = CodeMeld(mock_code_combiner_config)
        with pytest.raises(CodeMeldError, match="File system error: OS error occurred"):
            combiner._get_filtered_files()


def test_scan_files_no_error(mock_code_combiner_config, tmp_path):
    # Test normal operation without errors
    file1 = tmp_path / "file1.py"
    file1.touch()
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.py"
    file2.touch()

    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    with patch.object(CodeMeld, "_iter_files", return_value=[file1, file2]):
        with patch.object(CodeMeld, "_resolve_path", side_effect=lambda p: p):
            with patch.object(
                FilterChainBuilder, "build_safety_chain"
            ) as mock_build_safety_chain:
                mock_safety_filter_chain = MagicMock()
                mock_safety_filter_chain.should_process.return_value = True
                mock_build_safety_chain.return_value = mock_safety_filter_chain
                with patch.object(
                    CodeMeld, "_build_full_filter_chain"
                ) as mock_build_full_filter_chain:
                    mock_full_filter_chain = MagicMock()
                    mock_full_filter_chain.should_process.return_value = True
                    mock_build_full_filter_chain.return_value = mock_full_filter_chain

                    combiner = CodeMeld(mock_code_combiner_config)
                    files = combiner._get_filtered_files()
                    assert len(files) == 2
                    assert file1 in files
                    assert file2 in files


def test_iter_files_rglob_no_hidden(
    mock_code_combiner_config, create_common_file_structure
):
    file1, file2, hidden_file, hidden_dir_file, tmp_path = create_common_file_structure
    mock_code_combiner_config.include_hidden = False

    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = [
        file1,
        file2,
        hidden_file,
        hidden_dir_file,
    ]

    combiner = CodeMeld(mock_code_combiner_config)
    files = list(combiner._iter_files())
    assert len(files) == 4
    assert file1 in files
    assert file2 in files
    assert hidden_file in files
    assert hidden_dir_file in files


def test_iter_files_rglob_include_hidden(
    mock_code_combiner_config, create_common_file_structure
):
    file1, file2, hidden_file, hidden_dir_file, tmp_path = create_common_file_structure
    mock_code_combiner_config.include_hidden = True

    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = [
        file1,
        file2,
        hidden_file,
        hidden_dir_file,
    ]

    combiner = CodeMeld(mock_code_combiner_config)
    files = list(combiner._iter_files())
    assert len(files) == 4
    assert file1 in files
    assert file2 in files
    assert hidden_dir_file in files


def test_iter_files_rglob_no_hidden_files(
    mock_code_combiner_config, create_common_file_structure
):
    file1, file2, hidden_file, hidden_dir_file, tmp_path = create_common_file_structure

    mock_code_combiner_config.directory_path = tmp_path
    mock_code_combiner_config.include_hidden = False

    combiner = CodeMeld(mock_code_combiner_config)
    files = list(combiner._iter_files())

    # _iter_files itself should only yield all files, filtering happens later
    assert len(files) == 4
    assert file1 in files
    assert file2 in files
    assert hidden_file in files
    assert hidden_dir_file in files


def test_iter_files_rglob_with_hidden_files(
    mock_code_combiner_config, create_common_file_structure
):
    file1, file2, hidden_file, hidden_dir_file, tmp_path = create_common_file_structure

    mock_code_combiner_config.directory_path = tmp_path
    mock_code_combiner_config.include_hidden = True

    combiner = CodeMeld(mock_code_combiner_config)
    files = list(combiner._iter_files())

    assert len(files) == 4
    assert file1 in files
    assert file2 in files
    assert hidden_file in files
    assert hidden_dir_file in files

```

## FILE: tests/unit/test_config_builder.py

```py
# Copyright (c) 2025 skum

from argparse import Namespace

import pytest

from src.config import CodeMeldError
from src.config_builder import CombinerConfigBuilder, load_and_merge_config


def test_header_width_validation_positive():
    # Test that a positive header_width passes validation
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    config = load_and_merge_config(args)
    assert config.header_width == 80


def test_header_width_validation_zero_raises_error():
    # Test that a header_width of 0 raises an error
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=0,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(CodeMeldError, match="Header width must be positive"):
        load_and_merge_config(args)


def test_header_width_validation_negative_raises_error():
    # Test that a negative header_width raises an error
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=-1,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(CodeMeldError, match="Header width must be positive"):
        load_and_merge_config(args)


def test_output_directory_is_not_created_during_config(tmp_path):
    # Test that the output directory is not created during the configuration phase.
    non_existent_dir = tmp_path / "non_existent_parent" / "output.txt"
    args = Namespace(
        directory=str(tmp_path),
        output=str(non_existent_dir),
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    load_and_merge_config(args)
    assert not non_existent_dir.parent.exists()


def test_extension_without_dot_raises_error_with_suggestion():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=["py"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError,
        match=r"Error: Extension 'py' must start with '.'. Did you mean '.py'\?",
    ):
        load_and_merge_config(args)


def test_extension_with_dot_and_case_conversion():  # This test name is now misleading
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=["PY"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError,
        match=r"Error: Extension 'PY' must start with '.'. Did you mean '.py'\?",
    ):
        load_and_merge_config(args)


def test_multiple_extensions_with_one_invalid():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".js", "py", ".ts"],  # One invalid
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError,
        match=r"Error: Extension 'py' must start with '.'. Did you mean '.py'\?",
    ):
        load_and_merge_config(args)


def test_convert_to_with_invalid_format_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".py"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",  # Invalid format for --convert-to
        convert_to="markdown",
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError,
        match="--convert-to can only be used when --format is 'json' or 'xml'",
    ):
        load_and_merge_config(args)


def test_convert_to_same_format_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".py"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="json",
        convert_to="json",  # Converting to the same format
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError, match="Error: Cannot convert format 'json' to itself."
    ):
        load_and_merge_config(args)


def test_malformed_custom_file_headers_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers='{"py": "# Python"',  # Invalid JSON
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(CodeMeldError, match="Invalid JSON in custom_file_headers"):
        load_and_merge_config(args)


def test_non_existent_directory_raises_error():
    builder = CombinerConfigBuilder()
    with pytest.raises(
        CodeMeldError, match="Error: Directory 'non_existent_dir' does not exist."
    ):
        builder.validate("non_existent_dir", "output.txt")


def test_max_file_size_kb_validation_zero_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=0,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError, match="Max file size must be a positive integer."
    ):
        load_and_merge_config(args)


def test_max_file_size_kb_validation_negative_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=-10,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError, match="Max file size must be a positive integer."
    ):
        load_and_merge_config(args)


def test_invalid_token_encoding_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=1024,
        token_encoding_model="invalid_encoding",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError, match="Invalid token encoding model: invalid_encoding"
    ):
        load_and_merge_config(args)

```

## FILE: tests/unit/test_config_builder_extra.py

```py
# Copyright (c) 2025 skum

from unittest.mock import patch

from src.config_builder import CombinerConfigBuilder, load_config_from_pyproject


def test_load_config_from_pyproject_malformed(tmp_path):
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text("[tool.code_combiner]\ninvalid_toml")

    with patch("logging.warning") as mock_warning:
        config = load_config_from_pyproject(tmp_path)
        assert config == {}
        mock_warning.assert_called_once()


def test_with_pyproject_config_unknown_key():
    builder = CombinerConfigBuilder()
    config = {"unknown_key": "value"}
    builder.with_pyproject_config(config)
    assert "unknown_key" not in builder._config

```

## FILE: tests/unit/test_file_filters.py

```py
# Copyright (c) 2025 skum

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.code_combiner import CodeMeld
from src.config import CombinerConfig
from src.filters import (
    AlwaysIncludeFilter,
    BinaryFileFilter,
    CompositeFilter,
    ExtensionFilter,
    FileFilter,
    FileSizeFilter,
    FilterChainBuilder,
    GitignoreFilter,
    HiddenFileFilter,
    OrFilter,
    OutputFilePathFilter,
    SecurityFilter,
    SymlinkFilter,
)


@pytest.fixture
def mock_config():
    return CombinerConfig(
        directory_path=Path("/mock/root"),
        output="output.txt",
        extensions=[".py", ".js"],
        exclude_extensions=[".tmp"],
        use_gitignore=True,
        include_hidden=False,
        follow_symlinks=False,
        max_file_size_kb=100,
    )


@pytest.fixture
def mock_context():
    return {"root_path": Path("/mock/root")}


@pytest.fixture
def mock_file_path():
    return Path("/mock/root/test.py")


class TestExtensionFilter:
    def test_include_extension(self, mock_file_path):
        extension_filter = ExtensionFilter([".py"], [])
        assert extension_filter.should_process(mock_file_path, {})

    def test_exclude_extension(self, mock_file_path):
        extension_filter = ExtensionFilter([".js"], [".py"])
        assert not extension_filter.should_process(mock_file_path, {})

    def test_no_match(self, mock_file_path):
        extension_filter = ExtensionFilter([".js"], [])
        assert not extension_filter.should_process(mock_file_path, {})

    def test_case_insensitivity(self):
        extension_filter = ExtensionFilter([".PY"], [])
        assert extension_filter.should_process(Path("file.py"), {})

    def test_empty_extensions_list(self):
        extension_filter = ExtensionFilter([], [])
        assert not extension_filter.should_process(Path("file.py"), {})


class TestHiddenFileFilter:
    def test_include_hidden_true(self, mock_file_path):
        hidden_file_filter = HiddenFileFilter(include_hidden=True)
        assert hidden_file_filter.should_process(
            Path("/mock/root/.hidden_file"), {"root_path": Path("/mock/root")}
        )

    def test_include_hidden_false_visible_file(self, mock_file_path):
        hidden_file_filter = HiddenFileFilter(include_hidden=False)
        assert hidden_file_filter.should_process(
            Path("/mock/root/visible_file.py"), {"root_path": Path("/mock/root")}
        )

    def test_include_hidden_false_hidden_file(self, mock_file_path):
        hidden_file_filter = HiddenFileFilter(include_hidden=False)
        assert not hidden_file_filter.should_process(
            Path("/mock/root/.hidden_file"), {"root_path": Path("/mock/root")}
        )

    def test_include_hidden_false_hidden_dir(self, mock_file_path):
        hidden_file_filter = HiddenFileFilter(include_hidden=False)
        assert not hidden_file_filter.should_process(
            Path("/mock/root/.hidden_dir/file.py"), {"root_path": Path("/mock/root")}
        )

    def test_no_root_path_context(self):
        hidden_file_filter = HiddenFileFilter(include_hidden=False)
        assert hidden_file_filter.should_process(Path("/mock/root/.hidden_file"), {})


@pytest.fixture
def mock_spec():
    spec = MagicMock()
    spec.match_file.side_effect = lambda p: p == "ignored.py"
    return spec


class TestGitignoreFilter:
    def test_file_ignored(self, mock_spec):
        gitignore_filter = GitignoreFilter(mock_spec)
        assert not gitignore_filter.should_process(
            Path("/mock/root/ignored.py"), {"root_path": Path("/mock/root")}
        )

    def test_file_not_ignored(self, mock_spec):
        gitignore_filter = GitignoreFilter(mock_spec)
        assert gitignore_filter.should_process(
            Path("/mock/root/not_ignored.py"), {"root_path": Path("/mock/root")}
        )

    def test_no_spec(self):
        gitignore_filter = GitignoreFilter(None)
        assert gitignore_filter.should_process(Path("/mock/root/test.py"), {})

    def test_no_root_path_context(self, mock_spec):
        gitignore_filter = GitignoreFilter(mock_spec)
        assert gitignore_filter.should_process(Path("/mock/root/ignored.py"), {})


class TestOutputFilePathFilter:
    def test_output_file_is_filtered(self, tmp_path):
        output_file = tmp_path / "output.txt"
        output_filter = OutputFilePathFilter(output_file)
        assert not output_filter.should_process(output_file, {})

    def test_other_file_is_not_filtered(self, tmp_path):
        output_file = tmp_path / "output.txt"
        other_file = tmp_path / "other.py"
        output_filter = OutputFilePathFilter(output_file)
        assert output_filter.should_process(other_file, {})


class TestBinaryFileFilter:
    @pytest.fixture
    def binary_filter_config(self):
        # Create a minimal mock config for BinaryFileFilter
        mock_config = MagicMock(spec=CombinerConfig)
        mock_config.sample_size_bytes = 8192
        mock_config.large_file_threshold_bytes = 1024 * 1024
        mock_config.non_text_threshold = 0.30
        return mock_config

    @patch("src.filters.is_likely_binary", return_value=True)
    def test_binary_file_is_filtered(self, mock_is_likely_binary, binary_filter_config):
        binary_filter = BinaryFileFilter(binary_filter_config)
        assert not binary_filter.should_process(Path("binary.bin"), {})

    @patch("src.filters.is_likely_binary", return_value=False)
    def test_text_file_is_not_filtered(
        self, mock_is_likely_binary, binary_filter_config
    ):
        binary_filter = BinaryFileFilter(binary_filter_config)
        assert binary_filter.should_process(Path("text.txt"), {})


class TestSymlinkFilter:
    @pytest.fixture
    def mock_symlink_file(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("target content")
        symlink = tmp_path / "link.txt"
        os.symlink(target, symlink)
        return symlink

    def test_symlink_filtered_when_not_following(self, mock_symlink_file):
        symlink_filter = SymlinkFilter(follow_symlinks=False)
        assert not symlink_filter.should_process(mock_symlink_file, {})

    def test_symlink_not_filtered_when_following(self, mock_symlink_file):
        symlink_filter = SymlinkFilter(follow_symlinks=True)
        assert symlink_filter.should_process(mock_symlink_file, {})

    def test_non_symlink_not_filtered(self, tmp_path):
        non_symlink = tmp_path / "regular.txt"
        non_symlink.write_text("regular content")
        symlink_filter = SymlinkFilter(follow_symlinks=False)
        assert symlink_filter.should_process(non_symlink, {})


class TestSecurityFilter:
    def test_file_within_root(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        file_path = root / "file.txt"
        file_path.write_text("content")
        security_filter = SecurityFilter()
        assert security_filter.should_process(file_path, {"root_path": root})

    def test_file_outside_root(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        file_path = tmp_path / "outside.txt"
        file_path.write_text("content")
        security_filter = SecurityFilter()
        assert not security_filter.should_process(file_path, {"root_path": root})

    def test_no_root_path_context(self, tmp_path):
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        security_filter = SecurityFilter()
        assert security_filter.should_process(file_path, {})


class TestFileSizeFilter:
    def test_file_within_size_limit(self, tmp_path):
        file_path = tmp_path / "small.txt"
        file_path.write_text("a" * 50 * 1024)  # 50KB
        file_size_filter = FileSizeFilter(max_file_size_kb=100)
        assert file_size_filter.should_process(file_path, {})

    def test_file_exceeds_size_limit(self, tmp_path):
        file_path = tmp_path / "large.txt"
        file_path.write_text("a" * 150 * 1024)  # 150KB
        file_size_filter = FileSizeFilter(max_file_size_kb=100)
        assert not file_size_filter.should_process(file_path, {})

    def test_file_not_found(self):
        file_size_filter = FileSizeFilter(max_file_size_kb=100)
        assert not file_size_filter.should_process(Path("non_existent.txt"), {})


class TestCompositeFilter:
    def test_all_filters_pass(self):
        mock_filter1 = MagicMock(spec=FileFilter)
        mock_filter1.should_process.return_value = True
        mock_filter2 = MagicMock(spec=FileFilter)
        mock_filter2.should_process.return_value = True

        composite = CompositeFilter([mock_filter1, mock_filter2])
        assert composite.should_process(Path("file.txt"), {})
        mock_filter1.should_process.assert_called_once()
        mock_filter2.should_process.assert_called_once()

    def test_one_filter_fails(self):
        mock_filter1 = MagicMock(spec=FileFilter)
        mock_filter1.should_process.return_value = True
        mock_filter2 = MagicMock(spec=FileFilter)
        mock_filter2.should_process.return_value = False

        composite = CompositeFilter([mock_filter1, mock_filter2])
        assert not composite.should_process(Path("file.txt"), {})
        mock_filter1.should_process.assert_called_once()
        mock_filter2.should_process.assert_called_once()

    def test_empty_composite(self):
        composite = CompositeFilter([])
        assert composite.should_process(Path("file.txt"), {})

    def test_always_include_bypasses_other_filters(self, tmp_path):
        # Create a large file that should be filtered by size
        large_file = tmp_path / "large_file.bin"
        large_file.write_text("a" * 200 * 1024)  # 200KB

        # Create a filter chain that includes a size filter and an always-include filter
        always_include_filter = AlwaysIncludeFilter(always_include_paths=[large_file])
        file_size_filter = FileSizeFilter(max_file_size_kb=100)  # Max 100KB

        # The composite filter contains both. The bug is that AlwaysIncludeFilter
        # causes the FileSizeFilter to be ignored.
        composite_filter: CompositeFilter = CompositeFilter(
            [always_include_filter, file_size_filter]
        )

        # This test ensures that AlwaysIncludeFilter does not bypass other essential
        # filters, such as FileSizeFilter. A correct implementation must return False if
        # the file exceeds the size limit, regardless of whether it is explicitly
        # included.
        assert not composite_filter.should_process(
            large_file, {"root_path": tmp_path}
        ), "AlwaysIncludeFilter should not bypass the FileSizeFilter"


class TestFilterChainBuilder:
    def test_build_safety_chain(self, mock_config, tmp_path):
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.max_file_size_kb = 50
        safety_chain: CompositeFilter = FilterChainBuilder.build_safety_chain(
            mock_config
        )
        assert isinstance(safety_chain, CompositeFilter)
        # Further assertions to check the types of filters within the composite
        assert any(isinstance(f, SecurityFilter) for f in safety_chain.filters)
        assert any(isinstance(f, SymlinkFilter) for f in safety_chain.filters)
        assert any(isinstance(f, BinaryFileFilter) for f in safety_chain.filters)
        assert any(isinstance(f, OutputFilePathFilter) for f in safety_chain.filters)
        assert any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_safety_chain_no_file_size(self, mock_config, tmp_path):
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.max_file_size_kb = None
        safety_chain: CompositeFilter = FilterChainBuilder.build_safety_chain(
            mock_config
        )
        assert not any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_safety_chain_with_file_size(self, mock_config, tmp_path):
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.max_file_size_kb = 50
        safety_chain: CompositeFilter = FilterChainBuilder.build_safety_chain(
            mock_config
        )
        assert isinstance(safety_chain, CompositeFilter)
        assert any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_full_chain(self, mock_config, mock_spec, tmp_path):
        mock_config.output = str(tmp_path / "output.txt")
        safety_chain: CompositeFilter = FilterChainBuilder.build_safety_chain(
            mock_config
        )
        full_chain = FilterChainBuilder.build_full_chain(
            mock_config, mock_spec, safety_chain, []
        )
        assert isinstance(full_chain, CompositeFilter)
        # Check the order and types of filters
        filters = full_chain.filters
        assert len(filters) == 2
        assert isinstance(filters[0], OrFilter)
        assert isinstance(filters[1], CompositeFilter)  # This is the safety_chain

        or_filters = filters[0].filters
        assert len(or_filters) == 1  # Only content filters, no always_include_paths
        content_filters = or_filters[0].filters  # CompositeFilter for content filters

        assert any(isinstance(f, ExtensionFilter) for f in content_filters)
        assert any(isinstance(f, HiddenFileFilter) for f in content_filters)
        assert any(isinstance(f, GitignoreFilter) for f in content_filters)

        # Verify safety_chain is indeed the safety_chain
        assert filters[1] is safety_chain

    def test_code_combiner_integration(self, mock_config, tmp_path):
        # This is an integration-style test for the filter chain within CodeCombiner
        mock_config.directory_path = tmp_path
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.extensions = [".py"]
        mock_config.exclude_extensions = []
        mock_config.use_gitignore = False
        mock_config.include_hidden = False
        mock_config.follow_symlinks = False
        mock_config.max_file_size_kb = None

        # Create some dummy files
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")
        (tmp_path / ".hidden.py").write_text("hidden content")

        combiner = CodeMeld(mock_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 1
        assert filtered_files[0].name == "file1.py"

    def test_code_combiner_integration_with_gitignore(self, mock_config, tmp_path):
        mock_config.directory_path = tmp_path
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.extensions = [".py"]
        mock_config.use_gitignore = True
        (tmp_path / ".gitignore").write_text("*.py")  # Ignore all python files

        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")

        combiner = CodeMeld(mock_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 0

    def test_code_combiner_integration_with_always_include(self, mock_config, tmp_path):
        mock_config.directory_path = tmp_path
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.extensions = [".py"]
        mock_config.always_include = [
            str(tmp_path / "file2.js")
        ]  # Include a non-python file

        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")

        combiner = CodeMeld(mock_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 2
        assert Path(tmp_path / "file1.py") in filtered_files
        assert Path(tmp_path / "file2.js") in filtered_files

```

## FILE: tests/unit/test_formatters.py

```py
# Copyright (c) 2025 skum

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.formatters import (
    FormatterFactory,
    JSONFormatter,
    MarkdownFormatter,
    OutputFormatter,
    TextFormatter,
    XMLFormatter,
)


def test_create_text_formatter():
    formatter = FormatterFactory.create("text")
    assert isinstance(formatter, TextFormatter)


def test_create_text_formatter_with_header_width():
    formatter = FormatterFactory.create("text", header_width=100)
    assert isinstance(formatter, TextFormatter)
    assert formatter.header_width == 100


def test_create_json_formatter():
    formatter = FormatterFactory.create("json")
    assert isinstance(formatter, JSONFormatter)


def test_create_xml_formatter():
    formatter = FormatterFactory.create("xml")
    assert isinstance(formatter, XMLFormatter)


def test_create_unknown_formatter_raises_error():
    with pytest.raises(ValueError):
        FormatterFactory.create("unknown_format")


class CustomFormatter(OutputFormatter):
    format_name = "custom"

    def format_file(self, relative_path: Path, content: str) -> str:
        return f"Custom formatted file: {relative_path}"

    def begin_output(self) -> str:
        return ""

    def end_output(self) -> str:
        return ""

    def supports_streaming(self) -> bool:
        return True


def test_register_and_create_custom_formatter():
    FormatterFactory.register("custom", CustomFormatter)
    formatter = FormatterFactory.create("custom")
    assert isinstance(formatter, CustomFormatter)


def test_create_text_formatter_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError,
        match=(
            "Formatter 'text' initialization failed: "
            "Unknown arguments for text formatter: unknown_arg"
        ),
    ):
        FormatterFactory.create("text", header_width=80, unknown_arg="value")


def test_create_markdown_formatter_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError,
        match=(
            "Formatter 'markdown' initialization failed: "
            "Unknown arguments for markdown formatter: unknown_arg"
        ),
    ):
        FormatterFactory.create("markdown", unknown_arg="value")


def test_create_json_formatter_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError,
        match=(
            "Formatter 'json' initialization failed: "
            "Unknown arguments for json formatter: unknown_arg"
        ),
    ):
        FormatterFactory.create("json", unknown_arg="value")


def test_create_xml_formatter_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError,
        match=(
            "Formatter 'xml' initialization failed: "
            "Unknown arguments for xml formatter: unknown_arg"
        ),
    ):
        FormatterFactory.create("xml", unknown_arg="value")


def test_text_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError, match="Unknown arguments for text formatter: unknown_arg"
    ):
        TextFormatter(header_width=80, custom_file_headers={}, unknown_arg="value")


def test_markdown_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError, match="Unknown arguments for markdown formatter: unknown_arg"
    ):
        MarkdownFormatter(custom_file_headers={}, unknown_arg="value")


def test_json_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError, match="Unknown arguments for json formatter: unknown_arg"
    ):
        JSONFormatter(custom_file_headers={}, unknown_arg="value")


def test_xml_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError, match="Unknown arguments for xml formatter: unknown_arg"
    ):
        XMLFormatter(custom_file_headers={}, unknown_arg="value")


def test_text_formatter_with_custom_header():
    custom_headers = {"py": "# Python File: {path}"}
    formatter = FormatterFactory.create("text", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    expected_output = "# Python File: my_script.py\nprint('Hello')\n\n"
    assert formatter.format_file(relative_path, content) == expected_output


def test_markdown_formatter_with_custom_header():
    custom_headers = {"js": "// JavaScript File: {path}"}
    # Custom header no longer includes ```lang
    formatter = FormatterFactory.create("markdown", custom_file_headers=custom_headers)
    relative_path = Path("my_script.js")
    content = "console.log('Hello');"
    expected_output = (
        "// JavaScript File: my_script.js\n"
        "```js\n"
        "console.log('Hello');\n"
        "```\n\n"
    )  # Formatter adds ```js
    assert formatter.format_file(relative_path, content) == expected_output


def test_text_formatter_with_no_matching_custom_header():
    custom_headers = {"java": "// Java File: {path}"}
    formatter = FormatterFactory.create("text", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    # Should fall back to default text header
    expected_output = (
        f"\n{'=' * 80}\nFILE: my_script.py\n{'=' * 80}\n\nprint('Hello')\n\n"
    )
    assert formatter.format_file(relative_path, content) == expected_output


def test_markdown_formatter_with_no_matching_custom_header():
    custom_headers = {"java": "// Java File: {path}"}
    formatter = FormatterFactory.create("markdown", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    # Should fall back to default markdown header
    expected_output = "## FILE: my_script.py\n\n```py\nprint('Hello')\n```\n\n"
    assert formatter.format_file(relative_path, content) == expected_output


def test_markdown_formatter_custom_header_with_invalid_placeholder():
    custom_headers = {"js": "// JavaScript File: {foo}"}
    formatter = FormatterFactory.create("markdown", custom_file_headers=custom_headers)
    relative_path = Path("my_script.js")
    content = "console.log('Hello');"
    with pytest.raises(KeyError):
        formatter.format_file(relative_path, content)


def test_text_formatter_begin_end_output():
    formatter = TextFormatter()
    assert formatter.begin_output() == ""
    assert formatter.end_output() == ""


def test_markdown_formatter_begin_end_output():
    formatter = MarkdownFormatter()
    assert formatter.begin_output() == ""
    assert formatter.end_output() == ""


def test_json_formatter_streaming():
    formatter = JSONFormatter()
    assert formatter.begin_output() == "{\n"
    assert (
        formatter.format_file(Path("file1.txt"), "content1")
        == '    "file1.txt": "content1"'
    )
    assert (
        formatter.format_file(Path("file2.txt"), "content2")
        == ',\n    "file2.txt": "content2"'
    )
    assert formatter.end_output() == "\n}"


def test_xml_formatter_begin_end_output():
    formatter = XMLFormatter()
    assert formatter.begin_output() == (
        '<?xml version="1.0" encoding="UTF-8"?>\n<codebase>\n'
    )
    assert formatter.end_output() == "</codebase>"


def test_xml_formatter_content_escaping():
    formatter = XMLFormatter()
    content = "<tag>&'</tag>"
    formatted_content = formatter.format_file(Path("file.xml"), content)
    assert "&lt;tag&gt;&amp;'&lt;/tag&gt;" in formatted_content


@patch("importlib.metadata.entry_points")
def test_formatter_factory_plugin_loading(mock_entry_points):
    class PluginFormatter(OutputFormatter):
        format_name = "plugin"

        def format_file(self, relative_path: Path, content: str) -> str:
            return ""

        def begin_output(self) -> str:
            return ""

        def end_output(self) -> str:
            return ""

        def supports_streaming(self) -> bool:
            return True

    mock_entry_point = MagicMock()
    mock_entry_point.name = "plugin"
    mock_entry_point.load.return_value = PluginFormatter
    mock_entry_points.return_value = [mock_entry_point]

    FormatterFactory._plugins_loaded = False
    FormatterFactory._formatters = {
        "text": TextFormatter,
        "markdown": MarkdownFormatter,
        "json": JSONFormatter,
        "xml": XMLFormatter,
    }
    formatter = FormatterFactory.create("plugin")
    assert isinstance(formatter, PluginFormatter)


@patch("importlib.metadata.entry_points")
def test_formatter_factory_plugin_loading_error(mock_entry_points, caplog):
    mock_entry_point = MagicMock()
    mock_entry_point.name = "bad_plugin"
    mock_entry_point.load.side_effect = Exception("loading error")
    mock_entry_points.return_value = [mock_entry_point]

    FormatterFactory._plugins_loaded = False
    FormatterFactory._formatters = {
        "text": TextFormatter,
        "markdown": MarkdownFormatter,
        "json": JSONFormatter,
        "xml": XMLFormatter,
    }
    with pytest.raises(ValueError):
        FormatterFactory.create("bad_plugin")
    assert "Failed to load formatter plugin bad_plugin: loading error" in caplog.text


def test_formatter_factory_malformed_json_custom_headers():
    with pytest.raises(ValueError, match="Invalid JSON for custom file headers"):
        FormatterFactory.create("text", custom_file_headers="{invalid json}")


def test_text_formatter_custom_header_with_invalid_placeholder():
    custom_headers = {"py": "# Python File: {lang}"}
    formatter = FormatterFactory.create("text", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    with pytest.raises(KeyError, match="'lang'"):
        formatter.format_file(relative_path, content)

```

## FILE: tests/unit/test_memory_monitor.py

```py
import pytest

from src.config import MemoryThresholdExceededError
from src.memory_monitor import (
    MemoryMonitor,
    SystemMemoryMonitor,
    TracemallocMemoryMonitor,
)


def test_system_memory_monitor_no_limit():
    """
    Test that SystemMemoryMonitor.check_memory_usage does nothing when
    max_memory_mb is None, 0, or negative.
    """
    monitor_none = SystemMemoryMonitor(max_memory_mb=None)
    monitor_none.check_memory_usage()  # Should not raise an error

    monitor_zero = SystemMemoryMonitor(max_memory_mb=0)
    monitor_zero.check_memory_usage()  # Should not raise an error

    monitor_negative = SystemMemoryMonitor(max_memory_mb=-100)
    monitor_negative.check_memory_usage()  # Should not raise an error


def test_tracemalloc_memory_monitor_no_limit():
    """
    Test that TracemallocMemoryMonitor.check_memory_usage does nothing when
    max_memory_mb is None, 0, or negative.
    """
    monitor_none = TracemallocMemoryMonitor(max_memory_mb=None)
    monitor_none.check_memory_usage()  # Should not raise an error

    monitor_zero = TracemallocMemoryMonitor(max_memory_mb=0)
    monitor_zero.check_memory_usage()  # Should not raise an error

    monitor_negative = TracemallocMemoryMonitor(max_memory_mb=-100)
    monitor_negative.check_memory_usage()  # Should not raise an error


def test_system_memory_monitor_threshold_exceeded(mocker):
    """
    Test that SystemMemoryMonitor raises MemoryThresholdExceededError when
    memory usage exceeds the limit.
    """
    mock_process = mocker.Mock()
    mock_process.memory_info.return_value.rss = 200 * 1024 * 1024  # 200 MB
    mocker.patch("psutil.Process", return_value=mock_process)

    monitor = SystemMemoryMonitor(max_memory_mb=100)  # Set limit to 100 MB

    with pytest.raises(MemoryThresholdExceededError) as excinfo:
        monitor.check_memory_usage()

    assert "Memory usage exceeded 100MB" in str(excinfo.value)


def test_tracemalloc_memory_monitor_threshold_exceeded(mocker):
    """
    Test that TracemallocMemoryMonitor raises MemoryThresholdExceededError when
    memory usage exceeds the limit.
    """
    mocker.patch(
        "tracemalloc.get_traced_memory",
        return_value=(200 * 1024 * 1024, 250 * 1024 * 1024),
    )
    mocker.patch("tracemalloc.is_tracing", return_value=True)

    monitor = TracemallocMemoryMonitor(max_memory_mb=100)  # Set limit to 100 MB

    with pytest.raises(MemoryThresholdExceededError) as excinfo:
        monitor.check_memory_usage()

    assert "Python memory usage exceeded" in str(excinfo.value)


def test_memory_monitor_abstract_pass_statement():
    """Test that the pass statement in the abstract
    MemoryMonitor.check_memory_usage is covered."""

    class ConcreteMemoryMonitor(MemoryMonitor):
        def check_memory_usage(self) -> None:
            # This method is intentionally empty as it's a concrete implementation
            # of an abstract method, and the test specifically covers the 'pass'
            # statement in the abstract base class.
            pass

    monitor = ConcreteMemoryMonitor()
    monitor.check_memory_usage()


def test_system_memory_monitor_no_limit_explicit():
    """
    Explicitly test the no-limit case for SystemMemoryMonitor to force coverage.
    """
    monitor = SystemMemoryMonitor(max_memory_mb=None)
    monitor.check_memory_usage()
    monitor = SystemMemoryMonitor(max_memory_mb=0)
    monitor.check_memory_usage()
    monitor = SystemMemoryMonitor(max_memory_mb=-1)
    monitor.check_memory_usage()

```

## FILE: tests/unit/test_observers.py

```py
# Copyright (c) 2025 skum

import importlib
import logging
from typing import Any
from unittest.mock import MagicMock, patch

import src.observers
from src.observers import (
    FileContentProcessedData,
    FileProcessedData,
    LineCounterObserver,
    Observer,
    ProcessingEvent,
    ProcessingStartedData,
    Publisher,
    TokenCounterObserver,
)


class MockObserver(Observer[Any]):
    def __init__(self) -> None:
        self.update_called = False
        self.event: ProcessingEvent | None = None
        self.data: Any = None

    def update(self, event: ProcessingEvent, data: Any):
        self.update_called = True
        self.event = event
        self.data = data


def test_publisher_subscribe_and_notify():
    publisher = Publisher()
    observer: MockObserver = MockObserver()
    publisher.subscribe(observer)
    publisher.notify(
        ProcessingEvent.PROCESSING_STARTED, ProcessingStartedData(total_files=10)
    )
    assert observer.update_called
    assert observer.event == ProcessingEvent.PROCESSING_STARTED
    assert observer.data == ProcessingStartedData(total_files=10)


def test_publisher_unsubscribe():
    publisher = Publisher()
    observer: MockObserver = MockObserver()
    publisher.notify(
        ProcessingEvent.FILE_PROCESSED, FileProcessedData(path="test_file")
    )
    assert not observer.update_called


def test_publisher_notify_multiple_observers():
    publisher = Publisher()
    observer1: MockObserver = MockObserver()
    observer2: MockObserver = MockObserver()
    publisher.subscribe(observer1)
    publisher.subscribe(observer2)
    publisher.notify(
        ProcessingEvent.FILE_PROCESSED, FileProcessedData(path="test_file")
    )
    assert observer1.update_called
    assert observer2.update_called


def test_line_counter_observer():
    observer: LineCounterObserver = LineCounterObserver()
    observer.update(
        ProcessingEvent.FILE_CONTENT_PROCESSED,
        FileContentProcessedData(content_chunk="line 1\nline 2\nline 3"),
    )
    assert observer.total_lines == 3

    observer.update(
        ProcessingEvent.FILE_CONTENT_PROCESSED,
        FileContentProcessedData(content_chunk="line 4\nline 5"),
    )
    assert observer.total_lines == 5

def test_token_counter_observer():
    # Mock tiktoken in sys.modules

    with patch.dict("sys.modules", {"tiktoken": MagicMock()}) as mock_sys_modules:
        mock_tiktoken = mock_sys_modules["tiktoken"]

        mock_encoding = MagicMock()

        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # Simulate 5 tokens

        mock_tiktoken.get_encoding.return_value = mock_encoding

        # Create an observer instance after mocking

        observer = TokenCounterObserver()

        observer.update(
            ProcessingEvent.FILE_CONTENT_PROCESSED,
            FileContentProcessedData(content_chunk="some text"),
        )

        # Assert that get_encoding was called with the expected encoding type

        mock_tiktoken.get_encoding.assert_called_once_with("cl100k_base")

        # Assert that encode was called with the correct text

        mock_encoding.encode.assert_called_once_with("some text")

        assert observer.total_tokens == 5


def test_token_counter_observer_no_tiktoken(caplog):
    # Temporarily remove tiktoken from sys.modules to simulate it not being installed

    with patch.dict("sys.modules", {"tiktoken": None}):
        # Reload src.observers to ensure the lazy import logic is re-evaluated

        importlib.reload(src.observers)

        with caplog.at_level(logging.WARNING):
            observer = TokenCounterObserver()

            assert observer.tiktoken_module is None

            assert caplog.records[0].message == (
                "tiktoken not found. Token counting will be skipped."
            )

        # Ensure update does nothing if tiktoken_module is None

        initial_tokens = observer.total_tokens

        observer.update(
            ProcessingEvent.FILE_CONTENT_PROCESSED,
            FileContentProcessedData(content_chunk="some text"),
        )

        assert observer.total_tokens == initial_tokens


def test_publisher_unsubscribe_not_subscribed():
    publisher = Publisher()

    observer = MockObserver()

    # Should not raise an error

    publisher.unsubscribe(observer)


def test_observer_failure_does_not_stop_others(caplog):
    publisher = Publisher()

    failing_observer = MagicMock(spec=Observer)

    failing_observer.update.side_effect = Exception("Test Exception")

    working_observer: MockObserver = MockObserver()

    publisher.subscribe(failing_observer)

    publisher.subscribe(working_observer)

    with caplog.at_level(logging.ERROR):
        publisher.notify(
            ProcessingEvent.PROCESSING_STARTED, ProcessingStartedData(total_files=5)
        )

        assert "failed: Test Exception" in caplog.text


def test_token_counter_observer_with_custom_encoding():
    custom_encoding_model = "gpt2"

    # Mock tiktoken in sys.modules
    with patch.dict("sys.modules", {"tiktoken": MagicMock()}) as mock_sys_modules:
        # Reload src.observers to ensure the lazy import logic is re-evaluated
        importlib.reload(src.observers)
        from src.observers import (
            FileContentProcessedData,
            ProcessingEvent,
            TokenCounterObserver,
        )

        mock_tiktoken = mock_sys_modules["tiktoken"]
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3]  # Simulate 3 tokens
        mock_tiktoken.get_encoding.return_value = mock_encoding

        # Create an observer instance after mocking
        observer: TokenCounterObserver = TokenCounterObserver(
            token_encoding_model=custom_encoding_model
        )

        observer.update(
            ProcessingEvent.FILE_CONTENT_PROCESSED,
            FileContentProcessedData(content_chunk="some custom text"),
        )

        # Assert that get_encoding was called with the custom encoding type
        mock_tiktoken.get_encoding.assert_called_once_with(custom_encoding_model)

        # Assert that encode was called with the correct text
        mock_encoding.encode.assert_called_once_with("some custom text")

        assert observer.total_tokens == 3

```

## FILE: tests/unit/test_observers_coverage.py

```py
import logging
import sys
from unittest.mock import patch

import pytest

from src.observers import (
    FileProcessedData,
    LineCounterObserver,
    ProcessingEvent,
    TelemetryObserver,
    TokenCounterObserver,
)


@pytest.fixture
def mock_file_processed_data():
    return FileProcessedData(path="test/file.py")


def test_line_counter_observer_empty_content_chunk():
    """Test LineCounterObserver with an empty content chunk."""
    observer = LineCounterObserver()
    observer.update(ProcessingEvent.FILE_CONTENT_PROCESSED, {"content_chunk": ""})
    assert observer.total_lines == 0


def test_telemetry_observer_init():
    """Test TelemetryObserver initialization."""
    observer = TelemetryObserver()
    assert observer.start_time is None
    assert observer.total_files_processed == 0


def test_token_counter_observer_tiktoken_import_error(caplog):
    """Test TokenCounterObserver handles ImportError when tiktoken is not found."""
    with patch.dict(sys.modules, {"tiktoken": None}):
        # Simulate tiktoken not being importable
        with caplog.at_level(logging.WARNING):
            observer = TokenCounterObserver()
            assert observer.tiktoken_module is None
            assert "tiktoken not found. Token counting will be skipped." in caplog.text
            # Ensure update does nothing if tiktoken_module is None
            observer.update(
                ProcessingEvent.FILE_CONTENT_PROCESSED,
                {"content_chunk": "some content"},
            )

```

## FILE: tests/unit/test_output_generator.py

```py
# Copyright (c) 2025 skum

import collections
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import MemoryThresholdExceededError
from src.context import GeneratorContext
from src.formatters import TextFormatter
from src.memory_monitor import SystemMemoryMonitor
from src.observers import ProcessingEvent
from src.output_generator import (
    InMemoryOutputGenerator,
    StreamingOutputGenerator,
    read_file_content,
)


@pytest.fixture
def mock_files_to_process():
    return [Path("/mock/file1.py"), Path("/mock/file2.py")]


@pytest.fixture
def mock_root_path(tmp_path):
    root = tmp_path / "mock_root"
    root.mkdir()
    return root


@pytest.fixture
def mock_formatter():
    return TextFormatter()


def test_in_memory_generator_memory_warning(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path
):
    """Ensure MemoryThresholdExceededError is raised when memory exceeds threshold."""
    with patch("psutil.Process") as mock_process_class:
        mock_process_instance = mock_process_class.return_value
        mock_process_instance.memory_info.return_value.rss = (
            1000 * 1024 * 1024
        )  # 1000MB, very high

        memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)

        with patch(
            "src.output_generator.read_file_content", return_value="some content"
        ):
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=mock_formatter,
                memory_monitor=memory_monitor,
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)
            with pytest.raises(MemoryThresholdExceededError):
                generator.generate()


def test_thread_pool_executor_worker_cap(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path
):
    """Ensure ThreadPoolExecutor max_workers is capped correctly."""
    with patch("os.cpu_count", return_value=100):
        with patch("src.output_generator.ThreadPoolExecutor") as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = (
                mock_executor_instance
            )

            # Mock the submit method to return a real Future that is already done
            from concurrent.futures import Future

            def mock_submit(func, *args, **kwargs) -> Future[tuple[Path, str | None]]:
                future: Future[tuple[Path, str | None]] = Future()
                future.set_result((args[0], "dummy content"))
                return future

            mock_executor_instance.submit.side_effect = mock_submit

            memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=mock_formatter,
                memory_monitor=memory_monitor,
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)
            generator.generate()

            mock_executor_class.assert_called_once()
            # The cap is min(32, (os.cpu_count() or 1) + 4)
            # With os.cpu_count() = 100, it should be min(32, 104) which is 32
            assert mock_executor_class.call_args[1]["max_workers"] == 32

    with patch("os.cpu_count", return_value=2):
        with patch("src.output_generator.ThreadPoolExecutor") as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = (
                mock_executor_instance
            )

            # Mock the submit method to return a real Future that is already done
            from concurrent.futures import Future

            def mock_submit(func, *args, **kwargs) -> Future[tuple[Path, str | None]]:
                future: Future[tuple[Path, str | None]] = Future()
                future.set_result((args[0], "dummy content"))
                return future

            mock_executor_instance.submit.side_effect = mock_submit

            memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=mock_formatter,
                memory_monitor=memory_monitor,
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)
            generator.generate()

            mock_executor_class.assert_called_once()
            # With os.cpu_count() = 2, it should be min(32, 2 + 4) which is 6
            assert mock_executor_class.call_args[1]["max_workers"] == 6


def test_in_memory_generator_failed_files_logging(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path
):
    """Ensure failed files are logged when _read_file_and_notify raises an exception."""
    with patch("os.cpu_count", return_value=2):
        with patch("src.output_generator.ThreadPoolExecutor") as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = (
                mock_executor_instance
            )

            from concurrent.futures import Future

            def mock_submit_with_exception(
                func, *args, **kwargs
            ) -> Future[tuple[Path, str | None]]:
                future: Future[tuple[Path, str | None]] = Future()
                future.set_exception(Exception("Test exception"))
                return future

            mock_executor_instance.submit.side_effect = mock_submit_with_exception

            memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=mock_formatter,
                memory_monitor=memory_monitor,
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)

            with patch("logging.warning") as mock_warning:
                generator.generate()
                mock_warning.assert_called_once_with(
                    f"Failed to read {len(mock_files_to_process)} files. "
                    f"See log for details."
                )


def test_read_file_content_binary_file(tmp_path, mocker):
    """Test that read_file_content returns an empty generator for binary files."""
    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03")

    mocker.patch("src.output_generator.is_likely_binary", return_value=True)

    content_generator = read_file_content(binary_file)
    assert list(content_generator) == []


def test_read_file_content_unicode_decode_error(tmp_path, mocker):
    """Test that read_file_content handles UnicodeDecodeError."""
    bad_encoding_file = tmp_path / "bad_encoding.txt"
    # Write some bytes that are not valid UTF-8
    bad_encoding_file.write_bytes(b"\x80\x81\x82")

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    # Iterate over the generator to trigger the read and potential error
    collections.deque(read_file_content(bad_encoding_file), maxlen=0)

    mock_log_file_read_error.assert_called_once()
    assert "codec can't decode byte" in str(mock_log_file_read_error.call_args[0][1])


def test_read_file_content_file_not_found_error(tmp_path, mocker):
    """Test that read_file_content handles FileNotFoundError."""
    non_existent_file = tmp_path / "non_existent.txt"

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    collections.deque(read_file_content(non_existent_file), maxlen=0)

    mock_log_file_read_error.assert_called_once()
    assert "No such file or directory" in str(mock_log_file_read_error.call_args[0][1])


def test_read_file_content_permission_error(tmp_path, mocker):
    """Test that read_file_content handles PermissionError."""
    permission_denied_file = tmp_path / "permission_denied.txt"
    permission_denied_file.touch()
    permission_denied_file.chmod(0o000)  # Remove all permissions

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    collections.deque(read_file_content(permission_denied_file), maxlen=0)

    mock_log_file_read_error.assert_called_once()
    assert "Permission denied" in str(mock_log_file_read_error.call_args[0][1])

    # Restore permissions for cleanup
    permission_denied_file.chmod(0o644)


def test_read_file_content_is_a_directory_error(tmp_path, mocker):
    """Test that read_file_content handles IsADirectoryError."""
    directory_path = tmp_path / "a_directory"
    directory_path.mkdir()

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    collections.deque(read_file_content(directory_path), maxlen=0)

    mock_log_file_read_error.assert_called_once()
    assert "Is a directory" in str(mock_log_file_read_error.call_args[0][1])


def test_in_memory_generator_file_not_relative_to_root(
    mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _get_relative_path handles files not relative to root_path."""
    # Create a file outside the mock_root_path
    external_file = tmp_path / "external_dir" / "external_file.txt"
    external_file.parent.mkdir()
    external_file.write_text("external content")

    context = GeneratorContext(
        files_to_process=[external_file],
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = InMemoryOutputGenerator(context)

    mocker.patch(
        "src.output_generator.read_file_content", return_value=["external content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    output, _ = generator.generate()

    # The external file's full path should be used as its relative path
    assert str(external_file) in output
    assert "external content" in output

    def test_in_memory_generator_xml_output(
        mock_files_to_process, mock_root_path, tmp_path, mocker
    ):
        """Test that XMLFormatter's methods are called correctly in
        InMemoryOutputGenerator."""
        from src.formatters import XMLFormatter

        mock_xml_formatter = XMLFormatter()
        mocker.patch.object(mock_xml_formatter, "begin_output", return_value="<root>")
        mocker.patch.object(mock_xml_formatter, "end_output", return_value="</root>")
        mocker.patch.object(mock_xml_formatter, "format_file", return_value="<file/>")

        context = GeneratorContext(
            files_to_process=mock_files_to_process,
            root_path=mock_root_path,
            formatter=mock_xml_formatter,
            publisher=MagicMock(),
            output_path=tmp_path / "output.xml",
            ui=MagicMock(),
            token_counter_observer=MagicMock(),
            line_counter_observer=MagicMock(),
        )
        generator = InMemoryOutputGenerator(context)

        # Mock read_file_content to return some content
        mocker.patch(
            "src.output_generator.read_file_content", return_value=["some content"]
        )
        mocker.patch("src.output_generator.is_likely_binary", return_value=False)

        generator.generate()

        # Check that the formatter's methods were called as expected
        mock_xml_formatter.begin_output.assert_called_once()
        assert mock_xml_formatter.format_file.call_count == len(mock_files_to_process)
        mock_xml_formatter.end_output.assert_called_once()


def test_streaming_output_generator_no_files_no_direct_streaming_formatter(
    mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _handle_actual_streaming logs info and notifies complete
    when no files and no direct streaming formatter."""
    context = GeneratorContext(
        files_to_process=[],  # Empty list of files
        root_path=mock_root_path,
        formatter=mock_formatter,  # TextFormatter is not a direct streaming formatter
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    mock_logging_info = mocker.patch("logging.info")
    mock_publisher_notify = mocker.patch.object(generator.publisher, "notify")

    generator.generate()

    mock_logging_info.assert_called_once_with("No content to write. File not created.")
    mock_publisher_notify.assert_called_with(ProcessingEvent.PROCESSING_COMPLETE, None)


def test_streaming_output_generator_handle_actual_streaming_exception(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _handle_actual_streaming handles exceptions during file writing."""
    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    mocker.patch(
        "src.output_generator.read_file_content", return_value=["some content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    # Mock the open function to raise an exception when writing to the temporary file
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mock_open.return_value.__enter__.return_value.write.side_effect = OSError(
        "Disk full"
    )

    with pytest.raises(IOError, match="Disk full"):
        generator._handle_actual_streaming()

    # Ensure the temporary file is unlinked
    mock_open.assert_called_with(tmp_path / "output.tmp", "w", encoding="utf-8")
    assert (tmp_path / "output.tmp").exists() is False  # Unlinked by except block


def test_streaming_output_generator_dry_run_output_path_handling(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _handle_dry_run_streaming writes to dry_run_output_path if set."""
    dry_run_output_file = tmp_path / "dry_run_output.txt"
    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        dry_run=True,
        dry_run_output=str(dry_run_output_file),
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    mocker.patch(
        "src.output_generator.read_file_content", return_value=["some content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)
    mocker.patch(
        "logging.info"
    )  # Mock logging.info to prevent console output during test

    generator._handle_dry_run_streaming()

    assert dry_run_output_file.exists()
    assert "some content" in dry_run_output_file.read_text()


def test_streaming_output_generator_dry_run_output_path_exception(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _handle_dry_run_streaming handles exceptions when
    writing to dry_run_output_path."""
    dry_run_output_file = tmp_path / "dry_run_output.txt"
    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        dry_run=True,
        dry_run_output=str(dry_run_output_file),
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    mocker.patch(
        "src.output_generator.read_file_content", return_value=["some content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)
    mocker.patch(
        "logging.info"
    )  # Mock logging.info to prevent console output during test
    mock_logging_error = mocker.patch("logging.error")

    # Mock the open function to raise an exception when writing
    # to the dry_run_output_path
    _ = mocker.patch("builtins.open", side_effect=OSError("Permission denied"))

    generator._handle_dry_run_streaming()

    mock_logging_error.assert_called_once()
    assert "Error writing dry run output to" in mock_logging_error.call_args[0][0]
    assert "Permission denied" in str(mock_logging_error.call_args[0][0])


def test_streaming_output_generator_dry_run_output_path(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path
):
    """Test that dry_run_output_path is correctly set in StreamingOutputGenerator."""
    dry_run_output_path_str = str(tmp_path / "dry_run_output.txt")
    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        dry_run_output=dry_run_output_path_str,
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    assert generator.dry_run_output_path == Path(dry_run_output_path_str)


def test_streaming_output_generator_empty_non_binary_file(
    mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that StreamingOutputGenerator._process_file_streaming
    handles an empty, non-binary file."""
    empty_file = mock_root_path / "empty.txt"
    empty_file.touch()

    mock_ui = MagicMock()
    mock_publisher = MagicMock()
    mock_token_counter = MagicMock()
    mock_line_counter = MagicMock()

    context = GeneratorContext(
        files_to_process=[empty_file],
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=mock_publisher,
        output_path=tmp_path / "output.txt",
        ui=mock_ui,
        token_counter_observer=mock_token_counter,
        line_counter_observer=mock_line_counter,
    )
    generator = StreamingOutputGenerator(context)

    mocker.patch("src.output_generator.read_file_content", return_value=[])
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    generator._process_file_streaming(empty_file)

    mock_ui.update.assert_called_once_with(
        str(empty_file.relative_to(mock_root_path)),
        skipped=True,
        tokens=mock_token_counter.total_tokens,
        lines=mock_line_counter.total_lines,
    )

```

## FILE: tests/unit/test_output_generator_ext.py

```py
# Copyright (c) 2025 skum

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.context import GeneratorContext
from src.formatters import TextFormatter, XMLFormatter
from src.output_generator import (
    InMemoryOutputGenerator,
    StreamingOutputGenerator,
    read_file_content,
)


@pytest.fixture
def mock_files_to_process():
    return [Path("/mock/file1.py"), Path("/mock/file2.py")]


@pytest.fixture
def mock_root_path():
    return Path("/mock")


@pytest.fixture
def mock_formatter():
    return TextFormatter()


class TestReadFileContent:
    def test_read_file_not_found(self, caplog):
        with caplog.at_level(logging.WARNING):
            content = list(read_file_content(Path("/non/existent/file.txt")))
            assert not content
            assert "No such file or directory" in caplog.text

    def test_read_permission_error(self, tmp_path, caplog):
        with caplog.at_level(logging.WARNING):
            file_path = tmp_path / "no_permission.txt"
            file_path.write_text("test")
            with patch(
                "builtins.open", side_effect=PermissionError("Permission denied")
            ):
                content = list(read_file_content(file_path))
                assert not content
            assert "Permission denied" in caplog.text

    def test_read_is_a_directory_error(self, tmp_path, caplog):
        with caplog.at_level(logging.WARNING):
            content = list(read_file_content(tmp_path))
            assert not content
            assert "Is a directory" in caplog.text

    def test_read_unicode_decode_error(self, tmp_path, caplog):
        with caplog.at_level(logging.WARNING):
            file_path = tmp_path / "unicode_error.txt"
            file_path.write_bytes(b"\x80")  # Invalid UTF-8 byte
            with patch("src.output_generator.is_likely_binary", return_value=False):
                with patch(
                    "builtins.open",
                    side_effect=UnicodeDecodeError(
                        "utf-8", b"", 0, 1, "invalid start byte"
                    ),
                ):
                    content = list(read_file_content(file_path))
                    assert not content
            assert "UnicodeDecodeError" in caplog.text

    def test_read_general_exception(self, tmp_path, caplog):
        with caplog.at_level(logging.WARNING):
            file_path = tmp_path / "general_error.txt"
            file_path.write_text("test")
            with patch("builtins.open", side_effect=Exception("General error")):
                content = list(read_file_content(file_path))
                assert not content
            assert "General error" in caplog.text


class TestInMemoryOutputGenerator:
    def test_xml_formatter(self, mock_files_to_process, mock_root_path, tmp_path):
        with patch(
            "src.output_generator.read_file_content", return_value=["some content"]
        ):
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=XMLFormatter(),
                publisher=MagicMock(),
                output_path=tmp_path / "output.xml",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)
            output, _ = generator.generate()
            assert "<codebase>" in output
            assert "</codebase>" in output
            assert "<file>" in output
            assert "<path>file1.py</path>" in output
            assert "<content>some content</content>" in output


class TestStreamingOutputGenerator:
    def test_xml_formatter_streaming(
        self, mock_files_to_process, mock_root_path, tmp_path
    ):
        output_path = tmp_path / "output.xml"

        def process_file_streaming_mock(file_path, outfile):
            outfile.write(
                "<file><path>file1.py</path><content>some content</content></file>"
            )

        with patch.object(
            StreamingOutputGenerator,
            "_process_file_streaming",
            side_effect=process_file_streaming_mock,
        ):
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=XMLFormatter(),
                publisher=MagicMock(),
                output_path=output_path,
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = StreamingOutputGenerator(context)
            generator.generate()
            output = output_path.read_text()
            assert "<codebase>" in output
            assert "</codebase>" in output
            assert "<file>" in output
            assert "<path>file1.py</path>" in output
            assert "<content>some content</content>" in output

    def test_dry_run_with_output_file(
        self, mock_files_to_process, mock_root_path, tmp_path
    ):
        dry_run_output_path = tmp_path / "dry_run_output.txt"

        def process_file_streaming_mock(file_path, outfile):
            if outfile:
                outfile.write("some content")

        with patch.object(
            StreamingOutputGenerator,
            "_process_file_streaming",
            side_effect=process_file_streaming_mock,
        ):
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=TextFormatter(),
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
                dry_run=True,
                dry_run_output=str(dry_run_output_path),
            )
            generator = StreamingOutputGenerator(context)
            generator.generate()

        assert dry_run_output_path.exists()
        assert "some content" in dry_run_output_path.read_text()

    def test_no_files_to_process(self, mock_root_path, tmp_path, caplog):
        output_path = tmp_path / "output.txt"
        with caplog.at_level(logging.INFO):
            context = GeneratorContext(
                files_to_process=[],
                root_path=mock_root_path,
                formatter=TextFormatter(),
                publisher=MagicMock(),
                output_path=output_path,
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = StreamingOutputGenerator(context)
            generator.generate()
            assert not output_path.exists()

    def test_write_error(self, mock_files_to_process, mock_root_path, tmp_path, caplog):
        output_path = tmp_path / "output.txt"
        with caplog.at_level(logging.ERROR):
            with patch(
                "builtins.open", side_effect=PermissionError("Permission denied")
            ):
                context = GeneratorContext(
                    files_to_process=mock_files_to_process,
                    root_path=mock_root_path,
                    formatter=TextFormatter(),
                    publisher=MagicMock(),
                    output_path=output_path,
                    ui=MagicMock(),
                    token_counter_observer=MagicMock(),
                    line_counter_observer=MagicMock(),
                )
                generator = StreamingOutputGenerator(context)
                with pytest.raises(PermissionError):
                    generator.generate()

```

## FILE: tests/unit/test_ui.py

```py
# Copyright (c) 2025 skum

from unittest.mock import MagicMock, patch

from src.ui import LiveUI


class TestLiveUI:
    def test_start_no_progress_bar(self, capsys):
        ui = LiveUI(total_files=10)
        ui.progress_style = "none"
        ui.verbose = True
        ui.start()
        captured = capsys.readouterr()
        assert "Processing 10 files..." in captured.out

    def test_start_ascii_progress_bar(self):
        with (
            patch("src.ui.tqdm") as mock_tqdm,
            patch("shutil.get_terminal_size", return_value=MagicMock(columns=80)),
        ):
            ui = LiveUI(total_files=10)
            ui.progress_style = "ascii"
            with patch("sys.stdout.isatty", return_value=True):
                ui.start()
            mock_tqdm.assert_called_with(
                total=10,
                desc="Processing files",
                ncols=80,
                leave=False,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
                ascii=True,
            )

    def test_start_block_progress_bar(self):
        with (
            patch("src.ui.tqdm") as mock_tqdm,
            patch("shutil.get_terminal_size", return_value=MagicMock(columns=80)),
        ):
            ui = LiveUI(total_files=10)
            ui.progress_style = "block"
            with patch("sys.stdout.isatty", return_value=True):
                ui.start()
            mock_tqdm.assert_called_with(
                total=10,
                desc="Processing files",
                ncols=80,
                leave=False,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
            )

    def test_start_verbose_non_tty(self, capsys):
        with patch("sys.stdout.isatty", return_value=False):
            ui = LiveUI(total_files=10)
            ui.verbose = True
            ui.start()
            captured = capsys.readouterr()
            assert "Processing 10 files..." in captured.out


class TestLiveUIUpdate:
    def test_update_skipped(self):
        ui = LiveUI()
        ui.update("file.txt", skipped=True)
        assert ui.processed == 0
        assert ui.skipped == 1

    def test_update_no_tokens_lines(self):
        ui = LiveUI()
        ui.update("file.txt", tokens=None, lines=None)
        assert ui.tokens == 0
        assert ui.total_lines == 0


class TestLiveUIFinish:
    def test_finish_list_files(self, capsys):
        ui = LiveUI()
        ui.list_files = True
        ui._included_files_set = {"file1.txt", "file2.txt"}
        ui.included_files = ["file1.txt", "file2.txt"]
        ui.finish()
        captured = capsys.readouterr()
        assert "Included files:" in captured.out
        assert "- file1.txt" in captured.out
        assert "- file2.txt" in captured.out

    def test_finish_summary_no_tokens(self, capsys):
        ui = LiveUI()
        ui.summary = True
        ui.count_tokens = False
        ui.finish()
        captured = capsys.readouterr()
        assert "Token count" not in captured.out

    def test_finish_no_psutil(self, capsys):
        with patch("src.ui._psutil_module", None):
            ui = LiveUI()
            ui.summary = True
            ui.finish()
            captured = capsys.readouterr()
            assert "Peak memory usage" not in captured.out

```

## FILE: tests/unit/test_utils.py

```py
# Copyright (c) 2025 skum

import logging
from pathlib import Path

import pytest

from src.utils import is_likely_binary, log_file_read_error


@pytest.fixture
def temp_files(tmp_path: Path):
    text_file = tmp_path / "text.txt"
    text_file.write_text("This is a plain text file.\nIt has multiple lines.")

    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")

    large_text_file = tmp_path / "large_text.log"
    large_text_file.write_text("a" * (2 * 1024 * 1024))  # 2MB text file

    large_binary_file = tmp_path / "large_binary.zip"
    large_binary_file.write_bytes(b"\x00\x01\x02\x03" * (500 * 1024))  # 2MB binary file

    utf16_file = tmp_path / "utf16.txt"
    utf16_file.write_text("This is a UTF-16 encoded file.", encoding="utf-16")

    mixed_content_file = tmp_path / "mixed.txt"
    mixed_content_file.write_bytes(b"Some text" + b"\x00" + b"more text")

    unusual_ext_file = tmp_path / "data.unknown"
    unusual_ext_file.write_text("Some text in a file with an unusual extension.")

    return {
        "text": text_file,
        "binary": binary_file,
        "large_text": large_text_file,
        "large_binary": large_binary_file,
        "utf16": utf16_file,
        "mixed": mixed_content_file,
        "unusual": unusual_ext_file,
    }


def test_is_likely_binary_text_file(temp_files):
    assert not is_likely_binary(temp_files["text"])


def test_is_likely_binary_binary_file(temp_files):
    assert is_likely_binary(temp_files["binary"])


def test_is_likely_binary_large_text_file(temp_files):
    assert not is_likely_binary(temp_files["large_text"])


def test_is_likely_binary_large_binary_file(temp_files):
    assert is_likely_binary(temp_files["large_binary"])


def test_is_likely_binary_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    assert not is_likely_binary(empty_file)


def test_is_likely_binary_with_binary_extension(tmp_path):
    image_file = tmp_path / "image.png"
    image_file.touch()
    assert is_likely_binary(image_file)


def test_is_likely_binary_with_text_extension(tmp_path):
    script_file = tmp_path / "script.py"
    script_file.write_text("print('hello')")
    assert not is_likely_binary(script_file)


def test_is_likely_binary_utf16_file(temp_files):
    assert is_likely_binary(temp_files["utf16"])


def test_is_likely_binary_mixed_content(temp_files):
    assert is_likely_binary(temp_files["mixed"])


def test_is_likely_binary_unusual_extension(temp_files):
    assert not is_likely_binary(temp_files["unusual"])


def test_log_file_read_error_unicode_decode_error(caplog):
    with caplog.at_level(logging.WARNING):
        log_file_read_error(
            Path("test.txt"), UnicodeDecodeError("utf-8", b"", 0, 1, "reason")
        )
    assert "Skipping file due to UnicodeDecodeError: test.txt" in caplog.text


def test_log_file_read_error_file_not_found_error(caplog):
    with caplog.at_level(logging.WARNING):
        log_file_read_error(Path("test.txt"), FileNotFoundError())
    assert "Skipping file not found: test.txt" in caplog.text


def test_log_file_read_error_permission_error(caplog):
    with caplog.at_level(logging.WARNING):
        log_file_read_error(Path("test.txt"), PermissionError())
    assert "Skipping file due to permission error: test.txt" in caplog.text


def test_log_file_read_error_is_a_directory_error(caplog):
    with caplog.at_level(logging.WARNING):
        log_file_read_error(Path("test.txt"), IsADirectoryError())
    assert "Skipping directory treated as file: test.txt" in caplog.text


def test_log_file_read_error_generic_exception(caplog):
    with caplog.at_level(logging.ERROR):
        log_file_read_error(Path("test.txt"), Exception())
    assert "An unexpected error occurred while reading test.txt" in caplog.text

```

## FILE: tests/unit/test_write_output.py

```py
# Copyright (c) 2025 skum

import logging
from unittest.mock import patch

import pytest

from src.code_combiner import write_output


@pytest.fixture
def mock_output_path(tmp_path):
    output_file = tmp_path / "output.txt"
    return output_file


def test_write_output_file_exists_no_overwrite(mock_output_path, caplog):
    mock_output_path.write_text("existing content")
    with patch("sys.stdin.isatty", return_value=True):
        with patch("builtins.input", return_value="n"):
            with caplog.at_level(logging.INFO):
                write_output(mock_output_path, "new content", force=False)
                assert (
                    "Operation cancelled by user. File not overwritten." in caplog.text
                )
                assert mock_output_path.read_text() == "existing content"


def test_write_output_file_exists_overwrite(mock_output_path, caplog):
    mock_output_path.write_text("existing content")
    with patch("sys.stdin.isatty", return_value=True):
        with patch("builtins.input", return_value="y"):
            with caplog.at_level(logging.INFO):
                write_output(mock_output_path, "new content", force=False)
                assert "All code files have been combined into:" in caplog.text
                assert mock_output_path.read_text() == "new content"


def test_write_output_file_exists_force_overwrite(mock_output_path, caplog):
    mock_output_path.write_text("existing content")
    with caplog.at_level(logging.INFO):
        write_output(mock_output_path, "new content", force=True)
        assert "All code files have been combined into:" in caplog.text
        assert mock_output_path.read_text() == "new content"


def test_write_output_file_does_not_exist(mock_output_path, caplog):
    with caplog.at_level(logging.INFO):
        write_output(mock_output_path, "new content", force=False)
        assert "All code files have been combined into:" in caplog.text
        assert mock_output_path.read_text() == "new content"


def test_write_output_dry_run(mock_output_path, caplog, capsys):
    with caplog.at_level(logging.INFO):
        write_output(mock_output_path, "dry run content", force=False, dry_run=True)
        assert "--- Dry Run Output ---" in caplog.text
        assert "--- End Dry Run Output ---" in caplog.text
        captured = capsys.readouterr()
        assert "dry run content" in captured.out
        assert not mock_output_path.exists()


def test_write_output_non_interactive_no_overwrite(mock_output_path, caplog):
    mock_output_path.write_text("existing content")
    with patch("sys.stdin.isatty", return_value=False):
        with caplog.at_level(logging.INFO):
            write_output(mock_output_path, "new content", force=False)
            assert "Skipping overwrite in non-interactive mode." in caplog.text
            assert mock_output_path.read_text() == "existing content"


def test_write_output_permission_error(mock_output_path, caplog):
    # Simulate a PermissionError when trying to write to the file
    mock_output_path.parent.mkdir(parents=True, exist_ok=True)
    with patch("builtins.open", side_effect=PermissionError("Permission denied")):
        with caplog.at_level(logging.ERROR):
            with pytest.raises(PermissionError):
                write_output(mock_output_path, "content", force=True)
            assert "Error writing to output file" in caplog.text


def test_write_output_parent_dir_creation(tmp_path, caplog):
    non_existent_dir = tmp_path / "non_existent_parent"
    output_file = non_existent_dir / "output.txt"
    assert not non_existent_dir.exists()
    with caplog.at_level(logging.INFO):
        write_output(output_file, "content", force=False)
        assert non_existent_dir.exists()
        assert output_file.read_text() == "content"
        assert "All code files have been combined into:" in caplog.text

```

