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


def read_file_content(file_path: Path) -> str | None:
    """Read file content with proper error handling."""
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        print(f"Skipping binary file: {file_path}")
        return None
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error reading {file_path}: {e}")
        return None


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

    # If CLI value is provided (i.e., not the argparse_default)
    # For nargs arguments, cli_value will be None if not provided,
    # which is not argparse_default
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
            # For JSON, we still need to collect all data to form a valid JSON object
            # This means JSON cannot be truly streamed in the same way as text/markdown
            # For now, we'll write an empty object or handle it as a special case.
            # A more advanced solution would involve writing a JSON array of objects
            # or using a custom JSON stream writer.
            outfile.write("{\n")
            first_file = True
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
                tqdm.write(f"Processed: {relative_path}")
            outfile.write("\n}")

        elif format == "xml":
            # Similar to JSON, XML needs a root element, making true
            # streaming difficult.
            # A SAX-like approach would be needed for large XML streaming.
            # For simplicity, we'll write a basic structure.
            outfile.write("<codebase>\n")
            for file_path in tqdm(
                files_to_process, desc="Processing files (XML Streaming)"
            ):
                relative_path = file_path.relative_to(root_path)
                content = read_file_content(file_path)
                if content is None:
                    continue
                outfile.write("  <file>\n")
                outfile.write(f"    <path>{relative_path}</path>\n")
                outfile.write(f"    <content><![CDATA[{content}]]></content>\n")
                outfile.write("  </file>\n")
                tqdm.write(f"Processed: {relative_path}")
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

    final_convert_to: ConvertType | None = args.convert_to

    config_dict = {
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
    return config_dict


def run_code_combiner(config: dict[str, Any]) -> None:
    """Run the code combiner with the given configuration."""

    combiner = CodeCombiner(config)

    combiner.execute()


class CodeCombiner:
    """Manages the process of scanning, filtering.

    combining, and outputting code files.

    """

    def __init__(self, config: dict[str, Any]):
        """Initialize the CodeCombiner with the given configuration."""
        self.config = config
        self.root_path: Path = config["directory_path"]
        self.output_path: Path = Path(config["output"])
        self.extensions: list[str] = config["extensions"]
        self.exclude_extensions: list[str] = config["exclude_extensions"]
        self.use_gitignore: bool = config["use_gitignore"]
        self.include_hidden: bool = config["include_hidden"]
        self.count_tokens: bool = config["count_tokens"]
        self.header_width: int = config["header_width"]
        self.format: FormatType = config["format"]
        self.final_output_format: ConvertType | None = config["final_output_format"]
        self.force: bool = config["force"]

        self.processed_extensions: list[str] = []
        self.processed_exclude_extensions: list[str] = []
        self.spec: pathspec.PathSpec | None = None

    def _validate_inputs(self) -> bool:
        if not self.root_path.is_dir():
            print(f"Error: Directory '{self.root_path}' does not exist.")
            return False

        output_dir: Path = self.output_path.parent
        if not output_dir.is_dir():
            print(f"Error: Output directory '{output_dir}' does not exist.")
            return False
        if not os.access(output_dir, os.W_OK):
            print(f"Error: No write permissions for output directory '{output_dir}'.")
            return False
        return True

    def _process_extensions(self) -> bool:
        for ext in self.extensions:
            if not ext.startswith("."):
                sys.stderr.write(
                    f"Error: Custom extension '{ext}' must start with a dot "
                    f"(e.g., '.{ext}').\n"
                )
                return False
            self.processed_extensions.append(ext.lower())

        for ext in self.exclude_extensions:
            if not ext.startswith("."):
                sys.stderr.write(
                    f"Error: Exclude extension '{ext}' must start with a dot "
                    f"(e.g., '.{ext}').\n"
                )
                return False
            self.processed_exclude_extensions.append(ext.lower())
        return True

    def _get_gitignore_spec(self) -> pathspec.PathSpec | None:
        current_path: Path = self.root_path.resolve()
        while current_path != current_path.parent:
            gitignore_path: Path = current_path / ".gitignore"
            if gitignore_path.is_file():
                with open(gitignore_path, encoding="utf-8") as f:
                    return pathspec.PathSpec.from_lines("gitwildmatch", f)
            current_path = current_path.parent
        return None

    def _should_process_file(self, file_path: Path) -> bool:
        if file_path.resolve() == self.output_path.resolve():
            return False

        if not file_path.is_file():
            return False

        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and not mime_type.startswith("text/"):
            if mime_type != "application/xml":  # Allow XML files to be processed
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
        if not self._validate_inputs():
            return

        if not self._process_extensions():
            return

        if self.use_gitignore:
            self.spec = self._get_gitignore_spec()

        files_to_process = self._collect_files()

        if self.count_tokens:
            formatted_output_content, raw_combined_content = _generate_output_in_memory(
                files_to_process, self.root_path, self.format, self.header_width
            )

            if self.format in ["json", "xml"] and self.final_output_format in [
                "text",
                "markdown",
            ]:
                output_content = convert_to_text(
                    formatted_output_content,
                    self.format,
                    self.header_width,
                    self.final_output_format,
                )
            else:
                output_content = formatted_output_content

            self._count_tokens(raw_combined_content)
            self._write_output(output_content)
        else:
            _generate_output_streaming(
                files_to_process,
                self.root_path,
                self.format,
                self.header_width,
                self.output_path,
            )
            print(f"\nAll code files have been combined into: {self.output_path}")


def main() -> None:
    """Parse arguments, load config, and run the code combiner."""
    args = parse_arguments()
    config = load_and_merge_config(args)
    run_code_combiner(config)


if __name__ == "__main__":
    main()
