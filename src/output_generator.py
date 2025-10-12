"""Provides abstract and concrete classes for generating combined code output."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .formatters import JSONFormatter, OutputFormatter, XMLFormatter
from .memory_monitor import MemoryMonitor
from .observers import Publisher
from .utils import is_likely_binary, log_file_read_error


def read_file_content(file_path: Path) -> str | None:
    """Read file content with proper error handling."""
    if is_likely_binary(file_path):
        return None
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError as e:
        log_file_read_error(file_path, e)
        return None
    except FileNotFoundError as e:
        log_file_read_error(file_path, e)
        return None
    except PermissionError as e:
        log_file_read_error(file_path, e)
        return None
    except IsADirectoryError as e:
        log_file_read_error(file_path, e)
        return None
    except Exception as e:
        log_file_read_error(file_path, e)
        return None


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
            # Sample memory usage instead of checking every file
            if i % check_interval == 0:
                self.memory_monitor.check_memory_usage()

            relative_path = file_path.relative_to(self.root_path)
            content = read_file_content(file_path)
            if content is None:
                continue
            self._process_file(relative_path, content)
            self.publisher.notify("file_processed", relative_path)

        result = self._end_output()
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


class StreamingOutputGenerator(OutputGenerator):
    """Streams the combined output content directly to a file."""

    def __init__(
        self,
        files_to_process: list[Path],
        root_path: Path,
        formatter: OutputFormatter,
        output_path: Path,
        publisher: Publisher,
    ) -> None:
        """Initialize the StreamingOutputGenerator."""
        super().__init__(files_to_process, root_path, formatter, publisher)
        self.output_path = output_path

    def generate(self) -> None:
        """Generate output by streaming to file."""
        self.publisher.notify(
            "processing_started",
            {
                "total_files": len(self.files_to_process),
                "description": self._get_progress_bar_description(),
            },
        )

        with open(self.output_path, "w", encoding="utf-8") as outfile:
            outfile.write(self.formatter.begin_output())

            for file_path in self.files_to_process:
                relative_path = file_path.relative_to(self.root_path)
                content = read_file_content(file_path)
                if content is None:
                    continue

                # Write the formatted file content
                outfile.write(self.formatter.format_file(relative_path, content))
                self.publisher.notify("file_processed", relative_path)

            outfile.write(self.formatter.end_output())

        self.publisher.notify("processing_complete", None)
        return None

    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        return "Processing files (Streaming)"
