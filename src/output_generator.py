# Copyright (c) 2025 skum

"""Provides abstract and concrete classes for generating combined code output."""

from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .context import GeneratorContext
from .formatters import JSONFormatter, OutputFormatter, XMLFormatter
from .observers import (
    FileContentProcessedData,
    FileProcessedData,
    OutputGeneratedData,
    ProcessingEvent,
    ProcessingStartedData,
    Publisher,
)
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

    def __init__(self, context: GeneratorContext):
        """Initialize the InMemoryOutputGenerator."""
        super().__init__(
            context.files_to_process,
            context.root_path,
            context.formatter,
            context.publisher,
        )
        self.output_content = ""
        self.raw_combined_content = ""
        self.raw_content_parts: list[str] = []
        self.formatted_content_parts: list[str] = []
        self.json_data: dict[str, str] = {}
        self.xml_root_element: ET.Element | None = None
        self.memory_monitor = context.memory_monitor
        self.publisher = context.publisher
        self.output_path = context.output_path
        self.ui = context.ui
        self.token_counter_observer = context.token_counter_observer
        self.line_counter_observer = context.line_counter_observer

    def _read_file_and_notify(self, file_path: Path) -> tuple[Path, str | None]:
        """Read a file's content and notify observers."""
        content_chunks = list(read_file_content(file_path))
        if not content_chunks and not is_likely_binary(file_path):
            return file_path, None

        full_content = "".join(content_chunks)
        for chunk in content_chunks:
            self.publisher.notify(
                ProcessingEvent.FILE_CONTENT_PROCESSED,
                FileContentProcessedData(content_chunk=chunk),
            )
        return file_path, full_content

    def generate(self) -> tuple[str, str]:
        """Generate output in memory."""
        self.publisher.notify(
            ProcessingEvent.PROCESSING_STARTED,
            ProcessingStartedData(total_files=len(self.files_to_process)),
        )

        self._begin_output()

        file_contents = {}
        with ThreadPoolExecutor() as executor:
            future_to_path = {
                executor.submit(self._read_file_and_notify, path): path
                for path in self.files_to_process
            }
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    _, content = future.result()
                    file_contents[path] = content
                except Exception as e:
                    log_file_read_error(path, e)
                    file_contents[path] = None

        check_interval = max(1, min(10, len(self.files_to_process) // 20))

        for i, file_path in enumerate(self.files_to_process):
            content = file_contents.get(file_path)
            self._process_single_file(i, file_path, content, check_interval)

        result = self._end_output()
        self.publisher.notify(
            ProcessingEvent.OUTPUT_GENERATED,
            OutputGeneratedData(
                output_path=str(self.output_path),
                total_tokens=(
                    self.token_counter_observer.total_tokens
                    if self.token_counter_observer
                    else None
                ),
                total_lines=(
                    self.line_counter_observer.total_lines
                    if self.line_counter_observer
                    else None
                ),
            ),
        )
        self.publisher.notify(ProcessingEvent.PROCESSING_COMPLETE, None)
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

    def _get_relative_path(self, file_path: Path) -> Path:
        try:
            return file_path.relative_to(self.root_path)
        except ValueError:
            return file_path

    def _update_ui(self, relative_path: Path, skipped: bool) -> None:
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
            skipped=skipped,
            tokens=tokens,
            lines=lines,
        )

    def _process_single_file(
        self, i: int, file_path: Path, content: str | None, check_interval: int
    ) -> None:
        """Process a single file within the main loop."""
        # Sample memory usage instead of checking every file
        if i % check_interval == 0:
            if self.memory_monitor:
                self.memory_monitor.check_memory_usage()

        relative_path = self._get_relative_path(file_path)

        self.publisher.notify(
            ProcessingEvent.FILE_PROCESSED, FileProcessedData(path=str(relative_path))
        )

        self._update_ui(relative_path, content is None)

        if content is None:
            return
        self._process_file(relative_path, content)


class StreamingOutputGenerator(OutputGenerator):
    """Streams the combined output content directly to a file."""

    def __init__(self, context: GeneratorContext):
        """Initialize the StreamingOutputGenerator."""
        super().__init__(
            context.files_to_process,
            context.root_path,
            context.formatter,
            context.publisher,
        )
        self.output_path = context.output_path
        self.dry_run = context.dry_run
        self.dry_run_output_path = (
            Path(context.dry_run_output) if context.dry_run_output else None
        )
        self.ui = context.ui
        self.token_counter_observer = context.token_counter_observer
        self.line_counter_observer = context.line_counter_observer

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

        self.publisher.notify(
            ProcessingEvent.FILE_PROCESSED, FileProcessedData(path=str(relative_path))
        )
        content_generator = read_file_content(file_path)
        full_content = ""
        for chunk in content_generator:
            full_content += chunk
            self.publisher.notify(
                ProcessingEvent.FILE_CONTENT_PROCESSED,
                FileContentProcessedData(content_chunk=chunk),
            )  # Notify with chunk

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

        self.publisher.notify(ProcessingEvent.PROCESSING_COMPLETE, None)
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
            self.publisher.notify(ProcessingEvent.PROCESSING_COMPLETE, None)
            return

        temp_path = self.output_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as outfile:
                self._write_stream_to_file(outfile, is_dry_run=False)
            temp_path.replace(self.output_path)  # Atomic rename
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
