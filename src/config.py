"""Defines the configuration for the code combiner."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .formatters import FormatType


class CodeCombinerError(Exception):
    """Custom exception for CodeCombiner errors."""


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

ConvertType = Literal["text", "markdown"]


@dataclass
class CombinerConfig:
    """Configuration for the CodeCombiner tool."""

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

    def validate_config(self) -> None:
        """Validate the configuration settings."""
        if not self.directory_path.is_dir():
            raise CodeCombinerError(
                f"Error: Directory '{self.directory_path}' does not exist."
            )

        if not self.extensions:
            raise CodeCombinerError("Error: Extension list cannot be empty.")

        for ext in self.extensions:
            if not ext.startswith("."):
                raise CodeCombinerError(f"Extension must start with '.': {ext}")

        if self.final_output_format and self.format not in ["json", "xml"]:
            raise CodeCombinerError("--convert-to only works with json/xml formats")

        if self.final_output_format and self.format == self.final_output_format:
            raise CodeCombinerError(
                f"Error: Cannot convert format '{self.format}' to itself."
            )

        output_suffix = Path(self.output).suffix.lstrip(".").lower()
        expected_suffix: FormatType | ConvertType
        if self.final_output_format:
            expected_suffix = self.final_output_format
        else:
            expected_suffix = self.format

        if expected_suffix == "text" and output_suffix not in ["txt", "md"]:
            print(
                f"Warning: Output file extension '.{output_suffix}' does not typically "
                f"match 'text' format. Consider using .txt or .md."
            )
        elif expected_suffix == "markdown" and output_suffix not in ["md", "txt"]:
            print(
                f"Warning: Output file extension '.{output_suffix}' does not typically "
                f"match 'markdown' format. Consider using .md or .txt."
            )
        elif expected_suffix == "json" and output_suffix != "json":
            raise CodeCombinerError(
                f"Error: Output file extension '.{output_suffix}' does not match "
                f"'json' format. Consider using .json."
            )
        elif expected_suffix == "xml" and output_suffix != "xml":
            raise CodeCombinerError(
                f"Error: Output file extension '.{output_suffix}' does not match "
                f"'xml' format. Consider using .xml."
            )
