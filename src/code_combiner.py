"""A script to combine code files from a directory into a single output file."""

import argparse
import json
import logging
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

import pathspec
import toml

from .formatters import (
    FormatType,
    FormatterFactory,
    OutputFormatter,
    JSONFormatter,
    XMLFormatter,
)
from .filters import FilterChainBuilder, is_likely_binary, FileFilter
from .config import CombinerConfig, DEFAULT_EXTENSIONS, ConvertType, CodeCombinerError
from .config_builder import load_and_merge_config
from .output_generator import InMemoryOutputGenerator, StreamingOutputGenerator
from .observers import ProgressBarObserver, TokenCounterObserver

def write_output(output_path: Path, output_content: str, force: bool):
    """Write the combined output content to the specified file."""
    try:
        with open(
            output_path,
            "x",
            encoding="utf-8"
        ) as outfile:
            outfile.write(output_content)
        logging.info(f"\nAll code files have been combined into: {output_path}")
    except FileExistsError:
        if not force:
            response = input(
                f"Output file '{output_path}' already exists. Overwrite? (y/N): "
            )
            if response.lower() != "y":
                logging.info("Operation cancelled by user.")
                return
        try:
            with open(output_path, "w", encoding="utf-8") as outfile:
                outfile.write(output_content)
            logging.info(f"\nAll code files have been combined into: {output_path}")
        except Exception as e:
            logging.error(
                f"Error creating or writing to output file {output_path}: {e}"
            )
    except Exception as e:
        logging.error(f"Error creating or writing to output file {output_path}: {e}")




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
                        continue
                    file_path_display: str = file_path_text
                    file_content: str = content_element.text if content_element.text else ""
                    if output_format == "markdown":
                        lang = Path(file_path_display).suffix.lstrip(".")
                        text_output.append(
                            f"## FILE: {file_path_display}\n\n"
                            f"```{lang}\n"
                            f"{file_content}\n"
                            f"```\n\n"
                        )
                    else:
                        text_output.append(f"{ '=' * header_width}")
                        text_output.append(f"FILE: {file_path_display}")
                        text_output.append(f"{ '=' * header_width}\n")
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
                    text_output.append(f"{ '=' * header_width}")
                    text_output.append(f"FILE: {file_path_display}")
                    text_output.append(f"{ '=' * header_width}\n")
                    text_output.append(file_content)
                    text_output.append("\n\n")
            return "".join(text_output)
        except json.JSONDecodeError:
            return f"Error: Could not parse JSON content.\n{content}"
    return content

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



def run_code_combiner(config: CombinerConfig) -> None:
    """Run the code combiner with the given configuration."""
    config.validate_config()
    combiner = CodeCombiner(config)
    combiner.execute()

class CodeCombiner:
    """Orchestrates the code combining process."""

    def __init__(self, config: CombinerConfig):
        self.config = config
        self.formatter = FormatterFactory.create(
            config.format,
            header_width=config.header_width
        )
        self.filter_chain = self._build_filter_chain()

    def _build_filter_chain(self) -> FileFilter:
        spec = self._get_gitignore_spec() if self.config.use_gitignore else None
        return FilterChainBuilder.build(self.config, spec)

    def _get_gitignore_spec(self) -> pathspec.PathSpec | None:
        current_path: Path = self.config.directory_path.resolve()
        while current_path != current_path.parent:
            gitignore_path: Path = current_path / ".gitignore"
            if gitignore_path.is_file():
                with open(gitignore_path, encoding="utf-8") as f:
                    return pathspec.PathSpec.from_lines("gitwildmatch", f)
            current_path = current_path.parent
        return None

    def _scan_files(self) -> list[Path]:
        """Scan directory for matching files."""
        files = []
        context = {'root_path': self.config.directory_path}
        
        for file_path in self.config.directory_path.rglob("*"):
            if file_path.is_file() and self.filter_chain.should_process(file_path, context):
                files.append(file_path)
        
        return files

    def execute(self) -> None:
        """Execute the combining process."""
        files = self._scan_files()

        if self.config.count_tokens or self.config.final_output_format:
            generator = InMemoryOutputGenerator(files, self.config.directory_path, self.formatter)
            if self.config.count_tokens:
                token_counter = TokenCounterObserver()
                generator.subscribe(token_counter)
        else:
            generator = StreamingOutputGenerator(
                files, self.config.directory_path, self.formatter, Path(self.config.output)
            )

        progress_bar = ProgressBarObserver(len(files), "Processing files")
        generator.subscribe(progress_bar)

        result = generator.generate()

        if isinstance(generator, InMemoryOutputGenerator):
            output, raw_content = result
            if self.config.final_output_format:
                output = convert_to_text(
                    output, self.config.format, self.config.header_width, self.config.final_output_format
                )
            write_output(Path(self.config.output), output, self.config.force)

def main() -> None:
    """Parse arguments, load config, and run the code combiner."""
    try:
        args = parse_arguments()
        config = load_and_merge_config(args)
        run_code_combiner(config)
    except CodeCombinerError as e:
        logging.error(f"{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
