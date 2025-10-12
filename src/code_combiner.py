"""A script to combine code files from a directory into a single output file."""

import argparse
import json
import mimetypes
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

import pathspec
import toml
from tqdm import tqdm

FormatType = Literal["text", "markdown", "json", "xml"]
ConvertType = Literal["text", "markdown"]

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


def load_config_from_pyproject(root_path: Path) -> dict[str, Any]:
    """Load configuration from pyproject.toml if available."""
    config: dict[str, Any] = {}
    pyproject_path = root_path / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            pyproject_data: dict[str, Any] = toml.load(pyproject_path)
            if "tool" in pyproject_data and "code_combiner" in pyproject_data["tool"]:
                config = pyproject_data["tool"]["code_combiner"]
        except Exception as e:
            sys.stderr.write(f"Warning: Could not load pyproject.toml: {e}\n")
    return config


def is_code_file(
    filename: str,
    extensions: list[str],
    exclude_extensions: list[str],
) -> bool:
    """Check if a file has a code extension."""
    suffix: str = Path(filename).suffix.lower()
    if suffix in exclude_extensions:
        return False
    return suffix in extensions


def should_process_file(
    file_path: Path,
    root_path: Path,
    output_path: Path,
    spec: pathspec.PathSpec | None,
    extensions: list[str],
    exclude_extensions: list[str],
    use_gitignore: bool,
    include_hidden: bool,
) -> bool:
    """Determine if a file should be processed based on various filtering rules.

    Args:
        file_path: The path to the file being considered.
        root_path: The root directory being scanned.
        output_path: The path to the output file (to avoid processing itself).
        spec: The gitignore pathspec for matching ignored files, or None.
        extensions: A list of file extensions to include.
        exclude_extensions: A list of file extensions to exclude.
        use_gitignore: Whether to respect .gitignore rules.
        include_hidden: Whether to include hidden files and directories.

    Returns:
        True if the file should be processed, False otherwise.

    """
    if file_path.resolve() == output_path.resolve():
        return False

    if not file_path.is_file():
        return False

    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and not mime_type.startswith("text/"):
        if mime_type != "application/xml":  # Allow XML files to be processed
            return False

    if not is_code_file(file_path.name, extensions, exclude_extensions):
        return False

    relative_path: Path = file_path.relative_to(root_path)

    if use_gitignore and spec and spec.match_file(str(relative_path)):
        return False

    is_hidden: bool = any(part.startswith(".") for part in relative_path.parts)
    if not include_hidden and is_hidden:
        return False

    return True


def get_gitignore_spec(root_path: Path) -> pathspec.PathSpec | None:
    """Retrieve the pathspec from the .gitignore file."""
    current_path: Path = root_path.resolve()
    while current_path != current_path.parent:
        gitignore_path: Path = current_path / ".gitignore"
        if gitignore_path.is_file():
            with open(gitignore_path, encoding="utf-8") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        current_path = current_path.parent
    return None


def _indent_xml_element(elem: ET.Element, level: int = 0) -> None:
    """Recursively indents ElementTree elements for pretty printing.

    Args:
        elem: The current ElementTree element.
        level: The current indentation level.

    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            _indent_xml_element(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def generate_output(
    files_to_process: list[Path],
    root_path: Path,
    format: FormatType,
    header_width: int,
) -> tuple[str, str]:  # Returns formatted_content, raw_content
    """Generate the combined output content based on the specified format."""
    output_content: str = ""
    raw_combined_content: str = ""
    raw_content_parts: list[str] = []
    json_data: dict[str, str] = {}
    if format == "json":
        for file_path in tqdm(files_to_process, desc="Processing files (JSON)"):
            relative_path = file_path.relative_to(root_path)
            try:
                with open(file_path, encoding="utf-8") as infile:
                    content: str = infile.read()
                json_data[str(relative_path)] = content
                raw_content_parts.append(content)
                tqdm.write(f"Processed: {relative_path}")
            except UnicodeDecodeError:
                print(f"Skipping binary file: {relative_path}")
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}")
        output_content = json.dumps(json_data, indent=4)
        raw_combined_content = "".join(raw_content_parts)

    elif format == "xml":
        root_element: ET.Element = ET.Element("codebase")
        for file_path in tqdm(files_to_process, desc="Processing files (XML)"):
            relative_path = file_path.relative_to(root_path)
            try:
                with open(file_path, encoding="utf-8") as infile:
                    content = infile.read()
                file_element: ET.Element = ET.SubElement(root_element, "file")
                path_element: ET.Element = ET.SubElement(file_element, "path")
                path_element.text = str(relative_path)
                content_element: ET.Element = ET.SubElement(file_element, "content")
                content_element.text = content
                raw_content_parts.append(content)
                tqdm.write(f"Processed: {relative_path}")
            except UnicodeDecodeError:
                print(f"Skipping binary file: {relative_path}")
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}")
        _indent_xml_element(root_element)
        output_content = ET.tostring(root_element, encoding="utf-8").decode("utf-8")
        raw_combined_content = "".join(raw_content_parts)

    else:  # text or markdown
        formatted_content_parts: list[str] = []  # To build the formatted output
        for file_path in tqdm(
            files_to_process, desc="Processing files (Text/Markdown)"
        ):
            relative_path = file_path.relative_to(root_path)
            try:
                with open(file_path, encoding="utf-8") as infile:
                    content = infile.read()
                raw_content_parts.append(content)  # Append raw content

                if format == "markdown":
                    lang: str = relative_path.suffix.lstrip(".")
                    formatted_content_parts.append(
                        f"## FILE: {relative_path}\n\n```{lang}\n{content}\n```\n\n"
                    )
                else:  # text
                    formatted_content_parts.append(f"\n{'='*header_width}\n")
                    formatted_content_parts.append(f"FILE: {relative_path}\n")
                    formatted_content_parts.append(f"{ '='*header_width}\n\n")
                    formatted_content_parts.append(content)
                    formatted_content_parts.append("\n\n")

                tqdm.write(f"Processed: {relative_path}")

            except UnicodeDecodeError:
                print(f"Skipping binary file: {relative_path}")
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}")
        output_content = "".join(formatted_content_parts)
        raw_combined_content = "".join(raw_content_parts)  # Assigned here
    return output_content, raw_combined_content


def write_output(output_path: Path, output_content: str, force: bool):
    """Write the combined output content to the specified file.

    Args:
        output_path: The path to the output file.
        output_content: The content to write to the file.
        force: If True, overwrite the output file without prompting if it
            already exists.

    """
    if output_path.exists() and not force:
        response = input(
            f"Output file '{output_path}' already exists. Overwrite? (y/N): "
        )
        if response.lower() != "y":
            print("Operation cancelled by user.")
            return

    try:
        with open(output_path, "w", encoding="utf-8") as outfile:
            outfile.write(output_content)
        print(f"\nAll code files have been combined into: {output_path}")
    except Exception as e:
        print(f"Error creating or writing to output file {output_path}: {e}")


def convert_to_text(
    content: str,
    input_format: FormatType,
    header_width: int,
    output_format: ConvertType,
) -> str:
    """Convert XML or JSON content to a human-readable text/markdown format."""
    if input_format == "xml":
        try:
            root: ET.Element = ET.fromstring(content)
            text_output: list[str] = []
            for file_element in root.findall("file"):
                path_element: ET.Element | None = file_element.find("path")
                content_element: ET.Element | None = file_element.find("content")
                if path_element is not None and content_element is not None:
                    file_path: str = path_element.text if path_element.text else "N/A"
                    file_content: str = (
                        content_element.text if content_element.text else ""
                    )
                    if output_format == "markdown":
                        lang = Path(file_path).suffix.lstrip(".")
                        text_output.append(
                            f"## FILE: {file_path}\n\n"
                            f"```{lang}\n"
                            f"{file_content}\n"
                            f"```\n\n"
                        )
                    else:
                        text_output.append(f"{'=' * header_width}")
                        text_output.append(f"FILE: {file_path}")
                        text_output.append(f"{'=' * header_width}\n")
                        text_output.append(file_content)
                        text_output.append("\n\n")
            return "".join(text_output)
        except ET.ParseError:
            return f"Error: Could not parse XML content.\n{content}"
    elif input_format == "json":
        try:
            json_data: dict[str, str] = json.loads(content)
            text_output = []
            for file_path, file_content in json_data.items():
                if output_format == "markdown":
                    lang = Path(file_path).suffix.lstrip(".")
                    text_output.append(
                        f"## FILE: {file_path}\n\n"
                        f"```{lang}\n"
                        f"{file_content}\n"
                        f"```\n\n"
                    )
                else:
                    text_output.append(f"{'=' * header_width}")
                    text_output.append(f"FILE: {file_path}")
                    text_output.append(f"{'=' * header_width}\n")
                    text_output.append(file_content)
                    text_output.append("\n\n")
            return "".join(text_output)
        except json.JSONDecodeError:
            return f"Error: Could not parse JSON content.\n{content}"
    return content  # Return original content if not XML or JSON


def _collect_files(
    root_path: Path,
    output_path: Path,
    spec: pathspec.PathSpec | None,
    processed_extensions: list[str],
    processed_exclude_extensions: list[str],
    use_gitignore: bool,
    include_hidden: bool,
) -> list[Path]:
    """Collect files to be processed based on filtering rules."""
    all_files: list[Path] = list(root_path.rglob("*"))
    files_to_process: list[Path] = []

    for file_path in tqdm(all_files, desc="Scanning files"):
        if should_process_file(
            file_path,
            root_path,
            output_path,
            spec,
            processed_extensions,
            processed_exclude_extensions,
            use_gitignore,
            include_hidden,
        ):
            files_to_process.append(file_path)
            tqdm.write(f"Selected: {file_path.relative_to(root_path)}")
    return files_to_process


def scan_and_combine_code_files(
    root_dir: Path,
    output_file: str,
    extensions: list[str],
    exclude_extensions: list[str],
    use_gitignore: bool = True,
    include_hidden: bool = False,
    count_tokens: bool = True,
    header_width: int = 80,
    format: FormatType = "text",
    final_output_format: FormatType = "text",
    force: bool = False,  # Add force parameter
):
    """Scan a directory and combine code files into a single output file.

    Token counting, if enabled, is performed on the raw combined content
    (excluding headers and formatting) to accurately reflect LLM input size.
    """
    root_path: Path = Path(root_dir)
    output_path: Path = Path(output_file)

    if not root_path.is_dir():
        print(f"Error: Directory '{root_path}' does not exist.")
        return

    output_dir: Path = output_path.parent
    if not output_dir.is_dir():
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return
    if not os.access(output_dir, os.W_OK):
        print(f"Error: No write permissions for output directory '{output_dir}'.")
        return

    # Validate and normalize extensions and exclude_extensions
    processed_extensions: list[str] = []
    for ext in extensions:
        if not ext.startswith("."):
            sys.stderr.write(
                f"Error: Custom extension '{ext}' must start with a dot "
                f"(e.g., '.{ext}').\n"
            )
            return
        processed_extensions.append(ext.lower())

    processed_exclude_extensions: list[str] = []
    for ext in exclude_extensions:
        if not ext.startswith("."):
            sys.stderr.write(
                f"Error: Exclude extension '{ext}' must start with a dot "
                f"(e.g., '.{ext}').\n"
            )
            return
        processed_exclude_extensions.append(ext.lower())

    spec: pathspec.PathSpec | None = None
    if use_gitignore:
        spec = get_gitignore_spec(root_path)

    files_to_process = _collect_files(
        root_path,
        output_path,
        spec,
        processed_extensions,
        processed_exclude_extensions,
        use_gitignore,
        include_hidden,
    )

    formatted_output_content, raw_combined_content = generate_output(
        files_to_process, root_path, format, header_width
    )

    # Convert to text/markdown if original format was XML/JSON and final output is
    # text/markdown
    if format in ["json", "xml"] and final_output_format in ["text", "markdown"]:
        output_content = convert_to_text(
            formatted_output_content, format, header_width, final_output_format  # type: ignore[arg-type]
        )
    else:
        output_content = formatted_output_content

    # Count tokens before writing to file
    if count_tokens:
        tiktoken_module: ModuleType | None = None
        try:
            import tiktoken

            tiktoken_module = tiktoken
        except ImportError:
            print("Warning: tiktoken not found. Token counting will be skipped.")

        if tiktoken_module is not None:
            try:
                encoding = tiktoken_module.get_encoding("cl100k_base")
                tokens: list[int] = encoding.encode(
                    raw_combined_content
                )  # Use raw_combined_content
                print(f"Total tokens in raw combined content: {len(tokens)}")
            except ValueError as e:
                print(f"Error counting tokens: {e}")

    write_output(output_path, output_content, force)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the code combiner script."""
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
    return parser.parse_args()


def load_and_merge_config(args: argparse.Namespace) -> dict[str, Any]:
    """Load configuration from pyproject.toml and merge with command-line arguments."""
    directory_path: Path = Path(args.directory)

    if not directory_path.is_dir():
        print(f"Error: Directory '{args.directory}' does not exist.")
        sys.exit(1)  # Use sys.exit(1) for errors that prevent further execution

    config: dict[str, Any] = load_config_from_pyproject(directory_path)

    # Default extensions if not provided via command line or config
    # Default extensions are now loaded from the global DEFAULT_EXTENSIONS constant

    final_extensions: list[str] = config.get("extensions", DEFAULT_EXTENSIONS)
    if args.extensions is not None:
        final_extensions = args.extensions

    final_exclude_extensions: list[str] = config.get("exclude_extensions", [])
    if args.exclude is not None:
        final_exclude_extensions = args.exclude

    final_use_gitignore: bool = config.get("use_gitignore", True)
    final_include_hidden: bool = config.get("include_hidden", False)
    final_count_tokens: bool = config.get("count_tokens", True)
    final_header_width: int = config.get("header_width", 80)

    # Boolean flags: if present on command line, they override config
    if args.no_gitignore:
        final_use_gitignore = False
    elif "use_gitignore" in config:
        final_use_gitignore = config["use_gitignore"]

    if args.include_hidden:
        final_include_hidden = True
    elif "include_hidden" in config:
        final_include_hidden = config["include_hidden"]

    if args.no_tokens:
        final_count_tokens = False
    elif "count_tokens" in config:
        final_count_tokens = config["count_tokens"]

    if args.header_width != 80:
        final_header_width = args.header_width
    elif "header_width" in config:
        final_header_width = config["header_width"]

    final_format: FormatType = config.get("format", "text")
    if args.format != "text":
        final_format = args.format

    final_convert_to: ConvertType | FormatType = (
        args.convert_to if args.convert_to is not None else final_format  # type: ignore[assignment]
    )

    return {
        "directory_path": directory_path,
        "output": args.output,
        "extensions": final_extensions,
        "exclude_extensions": final_exclude_extensions,
        "use_gitignore": final_use_gitignore,
        "include_hidden": final_include_hidden,
        "count_tokens": final_count_tokens,
        "header_width": final_header_width,
        "format": final_format,
        "final_output_format": final_convert_to,
        "force": args.force,
    }


def run_code_combiner(config: dict[str, Any]) -> None:
    """Run the code combiner with the given configuration."""
    scan_and_combine_code_files(
        config["directory_path"],
        config["output"],
        config["extensions"],
        config["exclude_extensions"],
        config["use_gitignore"],
        config["include_hidden"],
        config["count_tokens"],
        config["header_width"],
        config["format"],
        config["final_output_format"],
        config["force"],  # Pass force parameter
    )


def main() -> None:
    """Parse arguments, load config, and run the code combiner."""
    args = parse_arguments()
    config = load_and_merge_config(args)
    run_code_combiner(config)


if __name__ == "__main__":
    main()
