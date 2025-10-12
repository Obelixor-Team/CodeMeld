"""Defines strategies for formatting combined code output."""

from abc import ABC, abstractmethod
from pathlib import Path
import json
import xml.sax.saxutils
from typing import Literal

FormatType = Literal["text", "markdown", "json", "xml"]


class OutputFormatter(ABC):
    """Strategy interface for different output formats."""

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


class TextFormatter(OutputFormatter):
    format_name = "text"

    def __init__(self, header_width: int = 80, **kwargs):
        self.header_width = header_width

    def format_file(self, relative_path: Path, content: str) -> str:
        return (
            f"\n{'=' * self.header_width}\n"
            f"FILE: {relative_path}\n"
            f"{'=' * self.header_width}\n\n"
            f"{content}\n\n"
        )

    def begin_output(self) -> str:
        return ""

    def end_output(self) -> str:
        return ""

    def supports_streaming(self) -> bool:
        return True


class MarkdownFormatter(OutputFormatter):
    format_name = "markdown"

    def __init__(self, **kwargs):
        pass

    def format_file(self, relative_path: Path, content: str) -> str:
        lang = relative_path.suffix.lstrip(".")
        return f"## FILE: {relative_path}\n\n```{lang}\n{content}\n```\n\n"

    def begin_output(self) -> str:
        return ""

    def end_output(self) -> str:
        return ""

    def supports_streaming(self) -> bool:
        return True


class JSONFormatter(OutputFormatter):
    format_name = "json"

    def __init__(self, **kwargs):
        self.is_first = True

    def format_file(self, relative_path: Path, content: str) -> str:
        # For streaming
        prefix = "" if self.is_first else ",\n"
        self.is_first = False
        return f'{prefix}    "{relative_path}": {json.dumps(content)}'

    def begin_output(self) -> str:
        return "{\n"

    def end_output(self) -> str:
        return "\n}"

    def supports_streaming(self) -> bool:
        return True


class XMLFormatter(OutputFormatter):
    format_name = "xml"

    def __init__(self, **kwargs):
        pass

    def format_file(self, relative_path: Path, content: str) -> str:
        escaped = xml.sax.saxutils.escape(content)
        return (
            "  <file>\n"
            f"    <path>{relative_path}</path>\n"
            f"    <content>{escaped}</content>\n"
            "  </file>\n"
        )

    def begin_output(self) -> str:
        return '<?xml version="1.0" encoding="UTF-8"?>\n<codebase>\n'

    def end_output(self) -> str:
        return "</codebase>"

    def supports_streaming(self) -> bool:
        return True


# Factory to create formatters
class FormatterFactory:
    @staticmethod
    def create(format_type: FormatType, **kwargs) -> OutputFormatter:
        formatters = {
            "text": TextFormatter,
            "markdown": MarkdownFormatter,
            "json": JSONFormatter,
            "xml": XMLFormatter,
        }
        formatter_class = formatters.get(format_type)
        if not formatter_class:
            raise ValueError(f"Unknown format: {format_type}")
        return formatter_class(**kwargs)
