# Copyright (c) 2025 skum

"""Defines strategies for formatting combined code output."""

from __future__ import annotations

import importlib.metadata
import json
import xml.sax.saxutils
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, final

from src._types import FormatType


class OutputFormatter(ABC):
    """Strategy interface for different output formats."""

    def __init__(
        self,
        custom_file_headers: dict[str, str] | None = None,
        **kwargs: Mapping[str, Any],
    ):
        """Initialize the OutputFormatter and validate kwargs."""
        if kwargs:
            raise TypeError(f"Unknown arguments for {self.format_name} formatter: {', '.join(kwargs.keys())}")
        self.custom_file_headers = custom_file_headers if custom_file_headers is not None else {}

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


@final
class TextFormatter(OutputFormatter):
    """Formats output as plain text."""

    format_name = "text"

    def __init__(self, header_width: int = 80, **kwargs: Any) -> None:
        """Initialize the TextFormatter."""
        super().__init__(**kwargs)
        self.header_width = header_width

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for text output."""
        # Check for custom header
        ext = relative_path.suffix.lstrip(".").lower()
        custom_header_format = self.custom_file_headers.get(ext)

        if custom_header_format:
            header = custom_header_format.format(path=relative_path)
            return f"{header}\n{content}\n\n"
        else:
            return f"\n{'=' * self.header_width}\nFILE: {relative_path}\n{'=' * self.header_width}\n\n{content}\n\n"

    def begin_output(self) -> str:
        """Return any header/opening content for text output."""
        return ""

    def end_output(self) -> str:
        """Return any footer/closing content for text output."""
        return ""

    def supports_streaming(self) -> bool:
        """Text formatter supports streaming."""
        return True


@final
class MarkdownFormatter(OutputFormatter):
    """Formats output as Markdown."""

    format_name = "markdown"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the MarkdownFormatter."""
        super().__init__(**kwargs)

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for Markdown output."""
        # Check for custom header
        ext = relative_path.suffix.lstrip(".").lower()
        custom_header_format = self.custom_file_headers.get(ext)

        lang = relative_path.suffix.lstrip(".")
        if custom_header_format:
            header = custom_header_format.format(path=relative_path, lang=lang)
            return f"{header}\n```{lang}\n{content}\n```\n\n"
        else:
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


@final
class JSONFormatter(OutputFormatter):
    """Formats output as JSON."""

    format_name = "json"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the JSONFormatter."""
        super().__init__(**kwargs)
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


@final
class XMLFormatter(OutputFormatter):
    """Formats output as XML."""

    format_name = "xml"

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the XMLFormatter."""
        super().__init__(**kwargs)

    def format_file(self, relative_path: Path, content: str) -> str:
        """Format a single file's content for XML output."""
        escaped = xml.sax.saxutils.escape(content)
        return f"  <file>\n    <path>{relative_path}</path>\n    <content>{escaped}</content>\n  </file>\n"

    def begin_output(self) -> str:
        """Return any header/opening content for XML output."""
        return '<?xml version="1.0" encoding="UTF-8"?>\n<codebase>\n'

    def end_output(self) -> str:
        """Return any footer/closing content for XML output."""
        return "</codebase>"

    def format_file_stream(self, relative_path: Path, file_path: Path, outfile: Any) -> None:
        """Stream XML content directly without building tree."""
        outfile.write(f"  <file>\n    <path>{relative_path}</path>\n    <content>")
        try:
            with open(file_path, encoding="utf-8") as f:
                for chunk in iter(lambda: f.read(8192), ""):
                    outfile.write(xml.sax.saxutils.escape(chunk))
        except Exception as e:
            from .utils import log_file_read_error

            log_file_read_error(file_path, e)
        outfile.write("</content>\n  </file>\n")

    def supports_streaming(self) -> bool:
        """XML formatter supports streaming."""
        return True


class FormatterFactory:
    """Factory to create OutputFormatter instances."""

    _formatters: dict[str, type[OutputFormatter]] = {}
    _plugins_loaded: bool = False

    @classmethod
    def _load_plugins(cls) -> None:
        """Discover and register formatters via entry points."""
        if cls._plugins_loaded:
            return
        for entry_point in importlib.metadata.entry_points(group="code_combiner.formatters"):
            try:
                formatter_class = entry_point.load()
                if issubclass(formatter_class, OutputFormatter):
                    cls.register(entry_point.name, formatter_class)
                else:
                    import logging

                    logging.warning(f"Entry point {entry_point.name} is not a subclass of OutputFormatter.")
            except Exception as e:
                import logging

                logging.error(f"Failed to load formatter plugin {entry_point.name}: {e}")
        cls._plugins_loaded = True

    @classmethod
    def register(cls, format_type: str, formatter_class: type[OutputFormatter]) -> None:
        """Register a new formatter."""
        cls._formatters[format_type] = formatter_class

    @classmethod
    def create(
        cls,
        format_type: FormatType,
        custom_file_headers: dict[str, str] | str | None = None,
        **kwargs: Any,
    ) -> OutputFormatter:
        """Create an OutputFormatter instance based on the format type."""
        cls._load_plugins()  # Ensure plugins are loaded before creation
        formatter_class = cls._formatters.get(format_type)
        if not formatter_class:
            raise ValueError(f"Unknown format: {format_type}")

        parsed_custom_headers: dict[str, str] | None = None
        if isinstance(custom_file_headers, str):
            try:
                parsed_custom_headers = json.loads(custom_file_headers)
            except json.JSONDecodeError as e:
                raise ValueError("Invalid JSON for custom file headers") from e
        elif isinstance(custom_file_headers, dict):
            parsed_custom_headers = custom_file_headers

        # Let formatters handle their own parameter validation
        try:
            return formatter_class(custom_file_headers=parsed_custom_headers, **kwargs)
        except TypeError as e:
            raise TypeError(f"Formatter '{format_type}' initialization failed: {e}") from e


# Register built-in formatters
FormatterFactory.register("text", TextFormatter)
FormatterFactory.register("markdown", MarkdownFormatter)
FormatterFactory.register("json", JSONFormatter)
FormatterFactory.register("xml", XMLFormatter)
