"""Defines strategies for formatting combined code output."""

import json
import xml.sax.saxutils
from abc import ABC, abstractmethod
from pathlib import Path
from typing import cast

from src.types import FormatType


class OutputFormatter(ABC):
    """Strategy interface for different output formats."""

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


class TextFormatter(OutputFormatter):
    """Formats output as plain text."""

    format_name = "text"

    def __init__(self, header_width: int = 80, **kwargs):
        """Initialize the TextFormatter."""
        self.header_width = header_width

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for text output."""
        return (
            f"\n{'=' * self.header_width}\n"
            f"FILE: {relative_path}\n"
            f"{'=' * self.header_width}\n\n"
            f"{content}\n\n"
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


class MarkdownFormatter(OutputFormatter):
    """Formats output as Markdown."""

    format_name = "markdown"

    def __init__(self, **kwargs):
        """Initialize the MarkdownFormatter."""
        pass

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for Markdown output."""
        lang = relative_path.suffix.lstrip(".")
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


class JSONFormatter(OutputFormatter):
    """Formats output as JSON."""

    format_name = "json"

    def __init__(self, **kwargs):
        """Initialize the JSONFormatter."""
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


class XMLFormatter(OutputFormatter):
    """Formats output as XML."""

    format_name = "xml"

    def __init__(self, **kwargs):
        """Initialize the XMLFormatter."""
        pass

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for XML output."""
        escaped = xml.sax.saxutils.escape(content)
        return (
            "  <file>\n"
            f"    <path>{relative_path}</path>\n"
            f"    <content>{escaped}</content>\n"
            "  </file>\n"
        )

    def begin_output(self) -> str:
        """Return any header/opening content for XML output."""
        return '<?xml version="1.0" encoding="UTF-8"?>\n<codebase>\n'

    def end_output(self) -> str:
        """Return any footer/closing content for XML output."""
        return "</codebase>"

    def supports_streaming(self) -> bool:
        """XML formatter supports streaming."""
        return True


class FormatterFactory:
    """Factory to create OutputFormatter instances."""

    _formatters: dict[str, type[OutputFormatter]] = {}

    @classmethod
    def register(cls, format_type: str, formatter_class: type[OutputFormatter]):
        """Register a new formatter."""
        cls._formatters[format_type] = formatter_class

    @classmethod
    def create(cls, format_type: FormatType, **kwargs) -> OutputFormatter:
        """Create an OutputFormatter instance based on the format type."""
        formatter_class = cls._formatters.get(format_type)
        if not formatter_class:
            raise ValueError(f"Unknown format: {format_type}")

        # Let formatters handle their own parameter validation
        try:
            return cast(OutputFormatter, formatter_class(**kwargs))
        except TypeError as e:
            raise TypeError(
                f"Formatter '{format_type}' initialization failed: {e}"
            ) from e


# Register built-in formatters
FormatterFactory.register("text", TextFormatter)
FormatterFactory.register("markdown", MarkdownFormatter)
FormatterFactory.register("json", JSONFormatter)
FormatterFactory.register("xml", XMLFormatter)
