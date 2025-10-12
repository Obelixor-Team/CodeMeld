"""Provides abstract and concrete classes for generating combined code output."""

import json
import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import psutil

from .formatters import JSONFormatter, OutputFormatter, XMLFormatter
from .observers import Publisher
from .utils import is_likely_binary


def read_file_content(file_path: Path) -> str | None:
    """Read file content with proper error handling."""
    if is_likely_binary(file_path):
        return None
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        return None
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return None


class OutputGenerator(ABC, Publisher):
    """Abstract base class for output generation."""

    def __init__(
        self, files_to_process: list[Path], root_path: Path, formatter: OutputFormatter
    ):
        """Initialize the OutputGenerator."""
        super().__init__()
        self.files_to_process = files_to_process
        self.root_path = root_path
        self.formatter = formatter

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
        self, files_to_process: list[Path], root_path: Path, formatter: OutputFormatter
    ):
        """Initialize the InMemoryOutputGenerator."""
        super().__init__(files_to_process, root_path, formatter)
        self.output_content = ""
        self.raw_combined_content = ""
        self.raw_content_parts: list[str] = []
        self.formatted_content_parts: list[str] = []
        self.json_data: dict[str, str] = {}
        self.xml_root_element: ET.Element | None = None

    def generate(self) -> tuple[str, str]:
        """Generate output in memory."""
        self.notify(
            "processing_started",
            {
                "total_files": len(self.files_to_process),
                "description": self._get_progress_bar_description(),
            },
        )

        self._begin_output()

        process = psutil.Process()
        memory_threshold_mb = 500  # 500 MB

        for file_path in self.files_to_process:
            # Check memory usage before processing each file
            current_memory_rss_mb = process.memory_info().rss / (1024 * 1024)
            if current_memory_rss_mb > memory_threshold_mb:
                logging.warning(
                    f"High memory usage detected (RSS: {current_memory_rss_mb:.1f}MB)"
                )

            relative_path = file_path.relative_to(self.root_path)
            content = read_file_content(file_path)
            if content is None:
                continue
            self._process_file(relative_path, content)
            self.notify("file_processed", relative_path)

        result = self._end_output()
        self.notify("processing_complete", result)
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
            self._indent_xml_element(self.xml_root_element)
            self.output_content = ET.tostring(
                self.xml_root_element, encoding="utf-8"
            ).decode("utf-8")
        else:
            self.output_content = "".join(self.formatted_content_parts)

        self.raw_combined_content = "".join(self.raw_content_parts)
        return self.output_content, self.raw_combined_content

    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        return f"Processing files ({self.formatter.format_name})"

    def _indent_xml_element(self, elem: ET.Element, level: int = 0) -> None:
        """Recursively indents ElementTree elements for pretty printing."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml_element(child, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


class StreamingOutputGenerator(OutputGenerator):
    """Streams the combined output content directly to a file."""

    def __init__(
        self,
        files_to_process: list[Path],
        root_path: Path,
        formatter: OutputFormatter,
        output_path: Path,
    ):
        """Initialize the StreamingOutputGenerator."""
        super().__init__(files_to_process, root_path, formatter)
        self.output_path = output_path

    def generate(self) -> None:
        """Generate output by streaming to file."""
        self.notify(
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
                self.notify("file_processed", relative_path)

            outfile.write(self.formatter.end_output())

        self.notify("processing_complete", None)
        return None

    def _get_progress_bar_description(self) -> str:
        """Return the description for the progress bar."""
        return "Processing files (Streaming)"
