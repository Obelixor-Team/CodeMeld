# Copyright (c) 2025 skum

"""Provides abstract and concrete classes for generating combined code output."""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from collections.abc import Generator
from pathlib import Path
from typing import Any

from .formatters import JSONFormatter, OutputFormatter, XMLFormatter
from .memory_monitor import MemoryMonitor
from .observers import LineCounterObserver, Publisher, TokenCounterObserver
from .ui import LiveUI
from .utils import is_likely_binary, log_file_read_error


def read_file_content(
    file_path: Path, chunk_size: int = 65536
) -> Generator[str, None, None]:
    """Read file content in chunks with proper error handling."""
    if is_likely_binary(file_path):
        return
    try:
        with open(file_path, encoding="utf-8") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    except UnicodeDecodeError as e:
        log_file_read_error(file_path, e)
    except FileNotFoundError as e:
        log_file_read_error(file_path, e)
    except PermissionError as e:
        log_file_read_error(file_path, e)
    except IsADirectoryError as e:
        log_file_read_error(file_path, e)
    except Exception as e:
        log_file_read_error(file_path, e)


class OutputGenerator(ABC):
    """Abstract base class for output generation."""

    def __init__(
        self,
        files_to_process: list[Path],
        root_path: Path,
        formatter: OutputFormatter,
        publisher: Publisher,
    ) -> None:
        """Initialize the OutputGenerator."""
        self.files_to_process = files_to_process
        self.root_path = root_path
        self.formatter = formatter
        self.publisher = publisher

    @abstractmethod
    def generate(self) -> Any:
        """Generate the output."""
        pass

    @abstractmethod
    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        pass


class InMemoryOutputGenerator(OutputGenerator):
    """Generates the combined output content in memory."""

    def __init__(
        self,
        files_to_process: list[Path],
        root_path: Path,
        formatter: OutputFormatter,
        memory_monitor: MemoryMonitor,
        publisher: Publisher,
        output_path: Path,
        ui: LiveUI,
        token_counter_observer: TokenCounterObserver | None,
        line_counter_observer: LineCounterObserver | None,
    ):
        """Initialize the InMemoryOutputGenerator."""
        super().__init__(files_to_process, root_path, formatter, publisher)
        self.output_content = ""
        self.raw_combined_content = ""
        self.raw_content_parts: list[str] = []
        self.formatted_content_parts: list[str] = []
        self.json_data: dict[str, str] = {}
        self.xml_root_element: ET.Element | None = None
        self.memory_monitor = memory_monitor
        self.publisher = publisher
        self.output_path = output_path
        self.ui = ui
        self.token_counter_observer = token_counter_observer
        self.line_counter_observer = line_counter_observer

    def generate(self) -> tuple[str, str]:
        """Generate output in memory."""
        self.publisher.notify(
            "processing_started",
            {
                "total_files": len(self.files_to_process),
                "description": self._get_progress_bar_description(),
            },
        )

        self._begin_output()

        check_interval = max(
            1, len(self.files_to_process) // 10
        )  # Check 10 times total

        for i, file_path in enumerate(self.files_to_process):
            self._process_single_file(i, file_path, check_interval)

        result = self._end_output()
        self.publisher.notify(
            "output_generated", result[0]
        )  # Notify with formatted content
        self.publisher.notify("processing_complete", result)
        return result

    def _begin_output(self) -> None:
        """Prepare for in-memory output generation."""
        if isinstance(self.formatter, XMLFormatter):
            self.xml_root_element = ET.Element("codebase")

    def _process_file(self, relative_path: Path, content: str) -> None:
        """Process each file's content for in-memory storage."""
        self.raw_content_parts.append(content)
        if isinstance(self.formatter, JSONFormatter):
            self.json_data[str(relative_path)] = content
        elif (
            isinstance(self.formatter, XMLFormatter)
            and self.xml_root_element is not None
        ):
            file_element = ET.SubElement(self.xml_root_element, "file")
            path_element = ET.SubElement(file_element, "path")
            path_element.text = str(relative_path)
            content_element = ET.SubElement(file_element, "content")
            content_element.text = content
        else:
            self.formatted_content_parts.append(
                self.formatter.format_file(relative_path, content)
            )

    def _end_output(self) -> tuple[str, str]:
        """Finalize in-memory output and return it."""
        if isinstance(self.formatter, JSONFormatter):
            self.output_content = json.dumps(self.json_data, indent=4)
        elif (
            isinstance(self.formatter, XMLFormatter)
            and self.xml_root_element is not None
        ):
            ET.indent(self.xml_root_element)  # Python 3.9+
            self.output_content = ET.tostring(
                self.xml_root_element, encoding="utf-8", xml_declaration=True
            ).decode("utf-8")
        else:
            self.output_content = "".join(self.formatted_content_parts)

        self.raw_combined_content = "".join(self.raw_content_parts)
        return self.output_content, self.raw_combined_content

    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        return f"Processing files ({self.formatter.format_name})"

    def _process_single_file(
        self, i: int, file_path: Path, check_interval: int
    ) -> None:
        """Process a single file within the main loop."""
        # Sample memory usage instead of checking every file
        if i % check_interval == 0:
            self.memory_monitor.check_memory_usage()

        try:
            relative_path = file_path.relative_to(self.root_path)
        except ValueError:
            relative_path = file_path  # Use full path if not relative to root

        content_generator = read_file_content(file_path)
        self.publisher.notify("file_processed", relative_path)
        full_content = ""
        for chunk in content_generator:
            full_content += chunk
            self.publisher.notify("file_content_processed", chunk)  # Notify with chunk

        if not full_content and not is_likely_binary(file_path):
            # If content is empty and not binary, it means an error occurred during reading
            # or the file was genuinely empty. Treat as skipped for UI purposes.
            content = None
        else:
            content = full_content

        # Update UI
        tokens = (
            self.token_counter_observer.total_tokens
            if self.token_counter_observer
            else None
        )
        lines = (
            self.line_counter_observer.total_lines
            if self.line_counter_observer
            else None
        )
        self.ui.update(
            str(relative_path),
            skipped=(content is None),
            tokens=tokens,
            lines=lines,
        )

        if content is None:
            return  # Changed from continue to return as it's a separate function
        self._process_file(relative_path, content)


class StreamingOutputGenerator(OutputGenerator):
    """Streams the combined output content directly to a file."""

    def __init__(
        self,
        files_to_process: list[Path],
        root_path: Path,
        formatter: OutputFormatter,
        output_path: Path,
        publisher: Publisher,
        ui: LiveUI,
        token_counter_observer: TokenCounterObserver | None,
        line_counter_observer: LineCounterObserver | None,
        dry_run: bool = False,
        dry_run_output: str | None = None,
    ) -> None:
        """Initialize the StreamingOutputGenerator."""
        super().__init__(files_to_process, root_path, formatter, publisher)
        self.output_path = output_path
        self.dry_run = dry_run
        self.dry_run_output_path = Path(dry_run_output) if dry_run_output else None
        self.ui = ui
        self.token_counter_observer = token_counter_observer
        self.line_counter_observer = line_counter_observer

    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        return "Processing files (Streaming)"

    def _process_file_streaming(
        self, file_path: Path, outfile: Any | None = None
    ) -> None:
        try:
            relative_path = file_path.relative_to(self.root_path)
        except ValueError:
            relative_path = file_path  # Use full path if not relative to root

        self.publisher.notify("file_processed", relative_path)
        content_generator = read_file_content(file_path)
        full_content = ""
        for chunk in content_generator:
            full_content += chunk
            self.publisher.notify("file_content_processed", chunk)  # Notify with chunk

        if not full_content and not is_likely_binary(file_path):
            content = None
        else:
            content = full_content

        # Update UI
        tokens = (
            self.token_counter_observer.total_tokens
            if self.token_counter_observer
            else None
        )
        lines = (
            self.line_counter_observer.total_lines
            if self.line_counter_observer
            else None
        )
        self.ui.update(
            str(relative_path),
            skipped=(content is None),
            tokens=tokens,
            lines=lines,
        )

        if content is not None and outfile is not None:
            if isinstance(self.formatter, XMLFormatter):
                self.formatter.format_file_stream(relative_path, file_path, outfile)
            else:
                outfile.write(self.formatter.format_file(relative_path, full_content))
        elif content is not None and outfile is None and self.dry_run:
            import sys

            sys.stdout.write(self.formatter.format_file(relative_path, content))

    def generate(self) -> None:
        """Generate output by streaming to file or printing to stdout if dry_run."""
        if self.dry_run:
            self._handle_dry_run_streaming()
        else:
            self._handle_actual_streaming()

        self.publisher.notify("processing_complete", None)
        return None

    def _stream_files_to_output(self, outfile: Any, is_dry_run: bool) -> None:
        for file_path in self.files_to_process:
            self._process_file_streaming(file_path, outfile if not is_dry_run else None)

    def _write_stream_to_file(self, outfile: Any, is_dry_run: bool) -> None:
        outfile.write(self.formatter.begin_output())
        self._stream_files_to_output(outfile, is_dry_run)
        outfile.write(self.formatter.end_output())

    def _handle_dry_run_streaming(self) -> None:
        import sys

        logging.info("--- Dry Run Output (Streaming) ---")
        self._write_stream_to_file(sys.stdout, is_dry_run=True)
        logging.info("--- End Dry Run Output (Streaming) ---")
        if self.dry_run_output_path:
            try:
                self.dry_run_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.dry_run_output_path, "w", encoding="utf-8") as outfile:
                    self._write_stream_to_file(outfile, is_dry_run=True)
                logging.info(
                    f"Dry run output also written to: {self.dry_run_output_path}"
                )
            except Exception as e:
                logging.error(
                    f"Error writing dry run output to {self.dry_run_output_path}: {e}"
                )

    def _handle_actual_streaming(self) -> None:
        # Determine if we are using a streaming formatter that writes directly to file
        is_direct_streaming_formatter = hasattr(self.formatter, "format_file_stream")

        if not self.files_to_process and not is_direct_streaming_formatter:
            logging.info("No content to write. File not created.")
            self.publisher.notify("processing_complete", None)
            return

        with open(self.output_path, "w", encoding="utf-8") as outfile:
            self._write_stream_to_file(outfile, is_dry_run=False)
