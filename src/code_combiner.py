"""A script to combine code files from a directory into a single output file."""

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
import xml.sax.saxutils
from dataclasses import dataclass
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


def read_file_content(file_path: Path) -> str | None:
    """Read file content with proper error handling."""
    if is_likely_binary(file_path):
        print(f"Skipping binary file: {file_path}")
        return None
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"Skipping binary file: {file_path}")
        return None
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error reading {file_path}: {e}")
        return None


def is_likely_binary(file_path: Path) -> bool:
    """Check if a file is likely binary by looking for null bytes."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)  # Read first 1024 bytes
            return b"\0" in chunk  # Null bytes often indicate binary
    except Exception:
        return True  # Assume binary if cannot read or error occurs


class CodeCombinerError(Exception):
    """Custom exception for CodeCombiner errors."""


@dataclass
class CombinerConfig:
    """Configuration for the CodeCombiner tool."""

    directory_path: Path
    output: str
    extensions: list[str]
    exclude_extensions: list[str]
    use_gitignore: bool
    include_hidden: bool
    count_tokens: bool
    header_width: int
    format: FormatType
    final_output_format: ConvertType | None
    force: bool


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


def _merge_config_value(
    config: dict[str, Any],
    args: argparse.Namespace,
    config_key: str,
    arg_name: str,
    argparse_default: Any,  # The default value argparse would assign if not provided
    config_default: Any,  # The default value if neither CLI nor config provides it
) -> Any:
    """Merge CLI argument, config value, and default value, prioritizing CLI.

    Args:
        config: The configuration dictionary loaded from pyproject.toml.
        args: The argparse.Namespace object containing CLI arguments.
        config_key: The key for the setting in the pyproject.toml config.
        arg_name: The attribute name for the setting in the argparse.Namespace.
        argparse_default: The default value argparse would assign if the argument
                          is not provided on the command line.
        config_default: The default value to use if neither CLI nor pyproject.toml
                        provides a value.

    Returns:
        The merged value, prioritizing CLI > config > default.

    """
    cli_value = getattr(args, arg_name)

    # The current implementation correctly distinguishes between an argument
    # not provided (which results in argparse_default) and an argument
    # explicitly provided with a value that happens to be the same as the default.
    # This is particularly important for nargs arguments where cli_value can be None
    # if not provided, which is different from an empty list provided by the user.
    if cli_value is not argparse_default:
        return cli_value

    # If CLI value is the argparse default, check config
    return config.get(config_key, config_default)


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


def _generate_output_in_memory(
    files_to_process: list[Path],
    root_path: Path,
    format: FormatType,
    header_width: int,
) -> tuple[str, str]:  # Returns formatted_content, raw_content
    """Generate the combined output content in memory based on the specified format."""
    output_content: str = ""
    raw_combined_content: str = ""
    raw_content_parts: list[str] = []
    json_data: dict[str, str] = {}
    if format == "json":
        for file_path in tqdm(files_to_process, desc="Processing files (JSON)"):
            relative_path = file_path.relative_to(root_path)
            content = read_file_content(file_path)
            if content is None:
                continue
            json_data[str(relative_path)] = content
            raw_content_parts.append(content)
            tqdm.write(f"Processed: {relative_path}")
        output_content = json.dumps(json_data, indent=4)
        raw_combined_content = "".join(raw_content_parts)

    elif format == "xml":
        root_element: ET.Element = ET.Element("codebase")
        for file_path in tqdm(files_to_process, desc="Processing files (XML)"):
            relative_path = file_path.relative_to(root_path)
            content = read_file_content(file_path)
            if content is None:
                continue
            file_element: ET.Element = ET.SubElement(root_element, "file")
            path_element: ET.Element = ET.SubElement(file_element, "path")
            path_element.text = str(relative_path)
            content_element: ET.Element = ET.SubElement(file_element, "content")
            content_element.text = content
            raw_content_parts.append(content)
            tqdm.write(f"Processed: {relative_path}")
        _indent_xml_element(root_element)
        output_content = ET.tostring(root_element, encoding="utf-8").decode("utf-8")
        raw_combined_content = "".join(raw_content_parts)

    else:  # text or markdown
        formatted_content_parts: list[str] = []  # To build the formatted output
        for file_path in tqdm(
            files_to_process, desc="Processing files (Text/Markdown)"
        ):
            relative_path = file_path.relative_to(root_path)
            content = read_file_content(file_path)
            if content is None:
                continue
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
        output_content = "".join(formatted_content_parts)
        raw_combined_content = "".join(raw_content_parts)  # Assigned here
    return output_content, raw_combined_content


def _generate_output_streaming(
    files_to_process: list[Path],
    root_path: Path,
    format: FormatType,
    header_width: int,
    output_path: Path,
) -> None:
    """Stream the combined output content directly to a file."""
    with open(output_path, "w", encoding="utf-8") as outfile:
        if format == "json":
            outfile.write("{\n")
            first_file = True
            file_count = 0
            for file_path in tqdm(
                files_to_process, desc="Processing files (JSON Streaming)"
            ):
                relative_path = file_path.relative_to(root_path)
                content = read_file_content(file_path)
                if content is None:
                    continue
                if not first_file:
                    outfile.write(",\n")
                outfile.write(f'    "{relative_path}": {json.dumps(content)}')
                first_file = False
                file_count += 1
                tqdm.write(f"Processed: {relative_path}")
            if file_count == 0:
                outfile.seek(0)  # Rewind and write empty object
                outfile.write("{}")
            else:
                outfile.write("\n}")

        elif format == "xml":
            file_count = 0
            xml_content_parts = []
            for file_path in tqdm(
                files_to_process, desc="Processing files (XML Streaming)"
            ):
                relative_path = file_path.relative_to(root_path)
                content = read_file_content(file_path)
                if content is None:
                    continue
                escaped_content = xml.sax.saxutils.escape(content)  # Escape content
                xml_content_parts.append("  <file>\n")
                xml_content_parts.append(f"    <path>{relative_path}</path>\n")
                xml_content_parts.append(f"    <content>{escaped_content}</content>\n")
                xml_content_parts.append("  </file>\n")
                file_count += 1
                tqdm.write(f"Processed: {relative_path}")

            if file_count == 0:
                outfile.write("<codebase />")
            else:
                outfile.write('<?xml version="1.0" encoding="UTF-8"?>\n<codebase>\n')
                outfile.write("".join(xml_content_parts))
                outfile.write("</codebase>")

        else:  # text or markdown
            for file_path in tqdm(
                files_to_process, desc="Processing files (Text/Markdown Streaming)"
            ):
                relative_path = file_path.relative_to(root_path)
                content = read_file_content(file_path)
                if content is None:
                    continue

                if format == "markdown":
                    lang: str = relative_path.suffix.lstrip(".")
                    outfile.write(
                        f"## FILE: {relative_path}\n\n```{lang}\n{content}\n```\n\n"
                    )
                else:  # text
                    outfile.write(f"\n{'='*header_width}\n")
                    outfile.write(f"FILE: {relative_path}\n")
                    outfile.write(f"{ '='*header_width}\n\n")
                    outfile.write(content)
                    outfile.write("\n\n")

                tqdm.write(f"Processed: {relative_path}")


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
        sys.stderr.write(
            f"Error creating or writing to output file {output_path}: {e}\n"
        )


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
                    file_path_text = path_element.text
                    if file_path_text is None:
                        continue  # Skip if path is None

                    file_path_display: str = file_path_text
                    file_content: str = (
                        content_element.text if content_element.text else ""
                    )
                    if output_format == "markdown":
                        lang = Path(file_path_display).suffix.lstrip(".")
                        text_output.append(
                            f"## FILE: {file_path_display}\n\n"
                            f"```{lang}\n"
                            f"{file_content}\n"
                            f"```\n\n"
                        )
                    else:
                        text_output.append(f"{'=' * header_width}")
                        text_output.append(f"FILE: {file_path_display}")
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
            for original_file_path, file_content in json_data.items():
                file_path_display = original_file_path
                if output_format == "markdown":
                    lang = Path(file_path_display).suffix.lstrip(".")
                    text_output.append(
                        f"## FILE: {file_path_display}\n\n"
                        f"```{lang}\n"
                        f"{file_content}\n"
                        f"```\n\n"
                    )
                else:
                    text_output.append(f"{'=' * header_width}")
                    text_output.append(f"FILE: {file_path_display}")
                    text_output.append(f"{'=' * header_width}\n")
                    text_output.append(file_content)
                    text_output.append("\n\n")
            return "".join(text_output)
        except json.JSONDecodeError:
            return f"Error: Could not parse JSON content.\n{content}"
    return content  # Return original content if not XML or JSON


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


def load_and_merge_config(args: argparse.Namespace) -> CombinerConfig:
    """Load configuration from pyproject.toml and merge with command-line arguments."""
    directory_path: Path = Path(args.directory)

    if not directory_path.is_dir():
        raise CodeCombinerError(f"Error: Directory '{args.directory}' does not exist.")

    config: dict[str, Any] = load_config_from_pyproject(directory_path)

    # Default extensions if not provided via command line or config
    # Default extensions are now loaded from the global DEFAULT_EXTENSIONS constant

    final_extensions: list[str] = _merge_config_value(
        config, args, "extensions", "extensions", None, DEFAULT_EXTENSIONS
    )
    final_exclude_extensions: list[str] = _merge_config_value(
        config, args, "exclude_extensions", "exclude", None, []
    )

    final_use_gitignore: bool = config.get("use_gitignore", True)
    if args.no_gitignore:
        final_use_gitignore = False

    final_include_hidden: bool = config.get("include_hidden", False)
    if args.include_hidden:
        final_include_hidden = True

    final_count_tokens: bool = config.get("count_tokens", True)
    if args.no_tokens:
        final_count_tokens = False

    final_header_width: int = _merge_config_value(
        config, args, "header_width", "header_width", 80, 80
    )

    final_format: FormatType = _merge_config_value(
        config, args, "format", "format", "text", "text"
    )

    final_output_format: ConvertType | None = args.convert_to

    return CombinerConfig(
        directory_path=directory_path,
        output=args.output,
        extensions=final_extensions,
        exclude_extensions=final_exclude_extensions,
        use_gitignore=final_use_gitignore,
        include_hidden=final_include_hidden,
        count_tokens=final_count_tokens,
        header_width=final_header_width,
        format=final_format,
        final_output_format=final_output_format,
        force=args.force,
    )


def run_code_combiner(config: CombinerConfig) -> None:
    """Run the code combiner with the given configuration."""

    combiner = CodeCombiner(config)

    combiner.execute()


class CodeCombiner:
    """Manages the process of scanning, filtering.

    combining, and outputting code files.

    """

    def __init__(self, config: CombinerConfig):
        """Initialize the CodeCombiner with the given configuration."""
        self.config = config
        self.root_path: Path = config.directory_path
        self.output_path: Path = Path(config.output)
        self.extensions: list[str] = config.extensions
        self.exclude_extensions: list[str] = config.exclude_extensions
        self.use_gitignore: bool = config.use_gitignore
        self.include_hidden: bool = config.include_hidden
        self.count_tokens: bool = config.count_tokens
        self.header_width: int = config.header_width
        self.format: FormatType = config.format
        self.final_output_format: ConvertType | None = config.final_output_format
        self.force: bool = config.force

        self.processed_extensions: list[str] = []
        self.processed_exclude_extensions: list[str] = []
        self.spec: pathspec.PathSpec | None = None

    def _validate_inputs(self) -> bool:
        if not self.root_path.is_dir():
            raise CodeCombinerError(
                f"Error: Directory '{self.root_path}' does not exist."
            )

        output_dir: Path = self.output_path.parent
        if not output_dir.is_dir():
            raise CodeCombinerError(
                f"Error: Output directory '{output_dir}' does not exist."
            )
        if not os.access(output_dir, os.W_OK):
            raise CodeCombinerError(
                f"Error: No write permissions for output directory '{output_dir}'."
            )
        return True

    def _process_extensions(self) -> bool:
        for ext in self.extensions:
            if not ext.startswith("."):
                raise CodeCombinerError(
                    f"Error: Custom extension '{ext}' must start with a dot "
                    f"(e.g., '.{ext}')."
                )
            self.processed_extensions.append(ext.lower())

        for ext in self.exclude_extensions:
            if not ext.startswith("."):
                raise CodeCombinerError(
                    f"Error: Exclude extension '{ext}' must start with a dot "
                    f"(e.g., '.{ext}')."
                )
            self.processed_exclude_extensions.append(ext.lower())
        return True

    def _get_gitignore_spec(self) -> pathspec.PathSpec | None:
        """Retrieve the pathspec from the .gitignore file using the global function."""
        return get_gitignore_spec(self.root_path)

    def _should_process_file(self, file_path: Path) -> bool:
        if file_path.resolve() == self.output_path.resolve():
            return False

        if not file_path.is_file() or file_path.is_symlink():
            return False

        if not is_code_file(
            file_path.name, self.processed_extensions, self.processed_exclude_extensions
        ):
            return False

        relative_path: Path = file_path.relative_to(self.root_path)

        if (
            self.use_gitignore
            and self.spec
            and self.spec.match_file(str(relative_path))
        ):
            return False

        is_hidden: bool = any(part.startswith(".") for part in relative_path.parts)
        if not self.include_hidden and is_hidden:
            return False

        return True

    def _collect_files(self) -> list[Path]:
        all_files: list[Path] = list(self.root_path.rglob("*"))
        files_to_process: list[Path] = []

        for file_path in tqdm(all_files, desc="Scanning files"):
            if self._should_process_file(file_path):
                files_to_process.append(file_path)
                tqdm.write(f"Selected: {file_path.relative_to(self.root_path)}")
        return files_to_process

    def _generate_output(self, files_to_process: list[Path]) -> tuple[str, str]:
        return _generate_output_in_memory(
            files_to_process, self.root_path, self.format, self.header_width
        )

    def _count_tokens(self, raw_combined_content: str) -> None:
        if self.count_tokens:
            tiktoken_module: ModuleType | None = None
            try:
                import tiktoken

                tiktoken_module = tiktoken
            except ImportError:
                print("Warning: tiktoken not found. Token counting will be skipped.")

            if tiktoken_module is not None:
                try:
                    encoding = tiktoken_module.get_encoding("cl100k_base")
                    tokens: list[int] = encoding.encode(raw_combined_content)
                    print(f"Total tokens in raw combined content: {len(tokens)}")
                except ValueError as e:
                    print(f"Error counting tokens: {e}")

    def _write_output(self, output_content: str) -> None:
        write_output(self.output_path, output_content, self.force)

    def execute(self) -> None:
        """Execute the code combination process based on the.

        initialized configuration.

        """
        self._validate_inputs()

        self._process_extensions()

        if self.use_gitignore:
            self.spec = self._get_gitignore_spec()

        files_to_process = self._collect_files()

        # Determine if in-memory processing is required
        # This is needed for token counting or if JSON/XML output needs to be converted
        needs_in_memory_processing = self.count_tokens or (
            self.format in ["json", "xml"]
            and self.final_output_format in ["text", "markdown"]
        )

        if needs_in_memory_processing:
            formatted_output_content, raw_combined_content = _generate_output_in_memory(
                files_to_process, self.root_path, self.format, self.header_width
            )

            output_to_write: str
            if self.format in ["json", "xml"] and self.final_output_format in [
                "text",
                "markdown",
            ]:
                output_to_write = convert_to_text(
                    formatted_output_content,
                    self.format,
                    self.header_width,
                    self.final_output_format,
                )
            else:
                output_to_write = formatted_output_content

            if self.count_tokens:
                self._count_tokens(raw_combined_content)

            self._write_output(output_to_write)
        else:
            # Use streaming for simple text/markdown output
            # without token counting or conversion
            _generate_output_streaming(
                files_to_process,
                self.root_path,
                self.format,
                self.header_width,
                self.output_path,
            )
            # The streaming function writes directly to the file.
            # Print the success message here.
            print(f"\nAll code files have been combined into: {self.output_path}")


def main() -> None:
    """Parse arguments, load config, and run the code combiner."""
    try:
        args = parse_arguments()
        config = load_and_merge_config(args)
        run_code_combiner(config)
    except CodeCombinerError as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
