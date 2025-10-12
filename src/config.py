"""Defines the configuration for the code combiner."""

from dataclasses import dataclass, field
from pathlib import Path

from src.types import ConvertType, FormatType


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
    always_include: list[str] = field(default_factory=list)
