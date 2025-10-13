"""Defines the configuration for the code combiner."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src._types import ConvertType, FormatType


class CodeCombinerError(Exception):
    """Custom exception for CodeCombiner errors."""


class MemoryThresholdExceededError(CodeCombinerError):
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
    token_encoding_model: str = "cl100k_base"
    max_memory_mb: int | None = 500
    custom_file_headers: dict[str, str] = field(default_factory=dict)
    dry_run: bool = False
    max_file_size_kb: int | None = None
    verbose: bool = False
    list_files: bool = False
