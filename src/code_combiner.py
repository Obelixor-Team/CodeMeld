from pathlib import Path
import argparse
import json
import os
import toml
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

import pathspec

if TYPE_CHECKING:
    import tiktoken

# The tiktoken library is optional. If it is not installed, tiktoken will be None.
try:
    import tiktoken
except ImportError:
    tiktoken = None  # type: ignore
    print("Warning: tiktoken not found. Token counting will be skipped.")


def load_config_from_pyproject(root_path: Path) -> dict:
    """Load configuration from pyproject.toml if available."""
    config = {}
    pyproject_path = root_path / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            pyproject_data = toml.load(pyproject_path)
            if "tool" in pyproject_data and "code_combiner" in pyproject_data["tool"]:
                config = pyproject_data["tool"]["code_combiner"]
        except Exception as e:
            print(f"Warning: Could not load pyproject.toml: {e}")
    return config


def is_code_file(
    filename: str, extensions: list[str], exclude_extensions: list[str]
) -> bool:
    """Check if file has a code extension"""
    suffix = Path(filename).suffix.lower()
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
    """Determine if a file should be processed based on filtering rules."""
    if file_path.resolve() == output_path.resolve():
        return False

    if not file_path.is_file():
        return False

    if not is_code_file(file_path.name, extensions, exclude_extensions):
        return False

    relative_path = file_path.relative_to(root_path)
    is_hidden = any(part.startswith(".") for part in relative_path.parts)

    # If --no-gitignore is present, we skip all gitignore and hidden file filtering
    if not use_gitignore:
        return True

    # If --no-gitignore is NOT present, apply filtering rules
    # Rule 1: Skip if not including hidden files and it is hidden
    if not include_hidden and is_hidden:
        return False

    # Rule 2: Skip if respecting gitignore and file is matched by gitignore
    # This rule is overridden for hidden files if include_hidden is True
    if spec and spec.match_file(str(relative_path)):
        if not (include_hidden and is_hidden):
            return False

    return True


def get_gitignore_spec(root_path: Path) -> pathspec.PathSpec | None:
    """Get the pathspec from the .gitignore file"""
    current_path = root_path.resolve()
    while current_path != current_path.parent:
        gitignore_path = current_path / ".gitignore"
        if gitignore_path.is_file():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        current_path = current_path.parent
    return None


def generate_output(
    files_to_process: list[Path],
    root_path: Path,
    format: str,
    header_width: int,
) -> str:
    output_content = ""
    if format == "json":
        json_data = {}
        for file_path in files_to_process:
            relative_path = file_path.relative_to(root_path)
            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    content = infile.read()
                json_data[str(relative_path)] = content
                print(f"Processed: {relative_path}")
            except UnicodeDecodeError:
                print(f"Skipping binary file: {relative_path}")
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}")
        output_content = json.dumps(json_data, indent=4)

    elif format == "xml":
        root_element = ET.Element("codebase")
        for file_path in files_to_process:
            relative_path = file_path.relative_to(root_path)
            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    content = infile.read()
                file_element = ET.SubElement(root_element, "file")
                path_element = ET.SubElement(file_element, "path")
                path_element.text = str(relative_path)
                content_element = ET.SubElement(file_element, "content")
                content_element.text = content
                print(f"Processed: {relative_path}")
            except UnicodeDecodeError:
                print(f"Skipping binary file: {relative_path}")
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}")
        output_content = ET.tostring(root_element, encoding="unicode")

    else:  # text or markdown
        combined_content = ""
        for file_path in files_to_process:
            relative_path = file_path.relative_to(root_path)
            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    content = infile.read()

                if format == "markdown":
                    lang = relative_path.suffix.lstrip(".")
                    combined_content += (
                        f"## FILE: {relative_path}\n\n```{lang}\n{content}\n```\n\n"
                    )
                else:  # text
                    combined_content += f"\n{'='*header_width}\n"
                    combined_content += f"FILE: {relative_path}\n"
                    combined_content += f"{'='*header_width}\n\n"
                    combined_content += content
                    combined_content += "\n\n"

                print(f"Processed: {relative_path}")

            except UnicodeDecodeError:
                print(f"Skipping binary file: {relative_path}")
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}")
        output_content = combined_content
    return output_content


def write_output(output_path: Path, output_content: str):
    try:
        with open(output_path, "w", encoding="utf-8") as outfile:
            outfile.write(output_content)
        print(f"\nAll code files have been combined into: {output_path}")
    except Exception as e:
        print(f"Error creating or writing to output file {output_path}: {e}")


def scan_and_combine_code_files(
    root_dir: Path,
    output_file: str,
    extensions: list[str],
    exclude_extensions: list[str],
    use_gitignore: bool = True,
    include_hidden: bool = False,
    count_tokens: bool = True,
    header_width: int = 80,
    format: str = "text",
):
    """Scan directory and combine code files into one output file"""

    root_path = Path(root_dir)
    output_path = Path(output_file)

    if not root_path.is_dir():
        print(f"Error: Directory '{root_path}' does not exist.")
        return

    output_dir = output_path.parent
    if not output_dir.is_dir():
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return
    if not os.access(output_dir, os.W_OK):
        print(f"Error: No write permissions for output directory '{output_dir}'.")
        return

    # Validate and normalize extensions and exclude_extensions
    normalized_extensions = []
    for ext in extensions:
        if not ext.startswith("."):
            print(
                f"Error: Custom extension '{ext}' must start with a dot (e.g., '.{ext}')."
            )
            return
        normalized_extensions.append(ext.lower())
    extensions = normalized_extensions

    normalized_exclude_extensions = []
    for ext in exclude_extensions:
        if not ext.startswith("."):
            print(
                f"Error: Exclude extension '{ext}' must start with a dot (e.g., '.{ext}')."
            )
            return
        normalized_exclude_extensions.append(ext.lower())
    exclude_extensions = normalized_exclude_extensions

    spec = None
    if use_gitignore:
        spec = get_gitignore_spec(root_path)

    all_files = root_path.rglob("*")
    files_to_process = []

    for file_path in all_files:
        if should_process_file(
            file_path,
            root_path,
            output_path,
            spec,
            extensions,
            exclude_extensions,
            use_gitignore,
            include_hidden,
        ):
            files_to_process.append(file_path)

    output_content = generate_output(files_to_process, root_path, format, header_width)

    # Count tokens before writing to file
    if count_tokens and tiktoken is not None:
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            tokens = encoding.encode(output_content)
            print(f"Total tokens in combined content: {len(tokens)}")
        except ValueError as e:
            print(f"Error counting tokens: {e}")
    elif count_tokens and not tiktoken:
        print("Token counting skipped: 'tiktoken' library not installed.")

    write_output(output_path, output_content)


def main():
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
        help="Custom file extensions to exclude (space separated, e.g., .txt .md). Exclusions take precedence over inclusions.",
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

    args = parser.parse_args()
    directory_path = Path(args.directory)

    if not directory_path.is_dir():
        print(f"Error: Directory '{args.directory}' does not exist.")
        return

    config = load_config_from_pyproject(directory_path)

    # Initialize parameters with config values, then override with command-line arguments
    default_extensions = [
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

    final_extensions = config.get("extensions", default_extensions)
    if args.extensions is not None:
        final_extensions = args.extensions

    final_exclude_extensions = config.get("exclude_extensions", [])
    if args.exclude is not None:
        final_exclude_extensions = args.exclude

    final_use_gitignore = config.get("use_gitignore", True)
    final_include_hidden = config.get("include_hidden", False)
    final_count_tokens = config.get("count_tokens", True)
    final_header_width = config.get("header_width", 80)

    # Boolean flags: if present on command line, they override config
    if args.no_gitignore:
        final_use_gitignore = False
    elif "use_gitignore" in config:  # Only use config if not overridden by command line
        final_use_gitignore = config["use_gitignore"]

    if args.include_hidden:
        final_include_hidden = True
    elif (
        "include_hidden" in config
    ):  # Only use config if not overridden by command line
        final_include_hidden = config["include_hidden"]

    if args.no_tokens:
        final_count_tokens = False
    elif "count_tokens" in config:  # Only use config if not overridden by command line
        final_count_tokens = config["count_tokens"]

    if args.header_width != 80:  # Only override if user explicitly set it
        final_header_width = args.header_width
    elif "header_width" in config:
        final_header_width = config["header_width"]

    final_format = config.get("format", "text")
    if args.format != "text":
        final_format = args.format

    scan_and_combine_code_files(
        directory_path,
        args.output,  # Output file is always from command line
        final_extensions,
        final_exclude_extensions,
        final_use_gitignore,
        final_include_hidden,
        final_count_tokens,
        final_header_width,
        final_format,
    )


if __name__ == "__main__":
    main()
