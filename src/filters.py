"""Defines the filter chain for selecting files to be combined."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pathspec

from .config import CombinerConfig
from .utils import is_likely_binary


class FileFilter(ABC):
    """Base class for file filters."""

    def __init__(self):
        """Initialize the file filter."""
        self._next_filter: FileFilter | None = None

    def set_next(self, filter: FileFilter) -> FileFilter:
        """Set the next filter in the chain."""
        self._next_filter = filter
        return filter

    def should_process(self, file_path: Path, context: dict) -> bool:
        """Return True if file should be processed."""
        if not self._check(file_path, context):
            return False
        if self._next_filter:
            return self._next_filter.should_process(file_path, context)
        return True

    @abstractmethod
    def _check(self, file_path: Path, context: dict) -> bool:
        """Individual filter logic."""
        pass


class ExtensionFilter(FileFilter):
    """Filter files based on their extensions."""

    def __init__(self, extensions: list[str], exclude: list[str]):
        """Initialize the extension filter."""
        super().__init__()
        self.extensions = [e.lower() for e in extensions]
        self.exclude = [e.lower() for e in exclude]

    def _check(self, file_path: Path, context: dict) -> bool:
        suffix = file_path.suffix.lower()
        if suffix in self.exclude:
            return False
        return suffix in self.extensions


class HiddenFileFilter(FileFilter):
    """Filter hidden files and directories."""

    def __init__(self, include_hidden: bool):
        """Initialize the hidden file filter."""
        super().__init__()
        self.include_hidden = include_hidden

    def _check(self, file_path: Path, context: dict) -> bool:
        if self.include_hidden:
            return True
        root_path = context.get("root_path")
        if not root_path:
            return True
        try:
            relative = file_path.relative_to(root_path)
            return not any(part.startswith(".") for part in relative.parts)
        except ValueError:
            return True


class GitignoreFilter(FileFilter):
    """Filter files based on .gitignore rules."""

    def __init__(self, spec: pathspec.PathSpec | None):
        """Initialize the gitignore filter."""
        super().__init__()
        self.spec = spec

    def _check(self, file_path: Path, context: dict) -> bool:
        if not self.spec:
            return True
        root_path = context.get("root_path")
        if not root_path:
            return True
        try:
            relative = file_path.relative_to(root_path)
            return not self.spec.match_file(str(relative))
        except ValueError:
            return True


class OutputFilePathFilter(FileFilter):
    """Filters out the output file itself."""

    def __init__(self, output_path: Path):
        """Initialize the OutputFilePathFilter."""
        super().__init__()
        self.output_path = output_path.resolve()

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Determine if the file should be processed."""
        return file_path.resolve() != self.output_path


class BinaryFileFilter(FileFilter):
    """Filter binary files."""

    def _check(self, file_path: Path, context: dict) -> bool:
        return not is_likely_binary(file_path)


class SymlinkFilter(FileFilter):
    """Filter symbolic links."""

    def _check(self, file_path: Path, context: dict) -> bool:
        return not file_path.is_symlink()


class SecurityFilter(FileFilter):
    """Filter to prevent path traversal by ensuring files are within the root path."""

    def _check(self, file_path: Path, context: dict) -> bool:
        root_path = context.get("root_path")
        if not root_path:
            # If root_path is not provided, we cannot perform the check, so allow.
            return True
        try:
            # Resolve both paths to handle symlinks and '..' correctly
            file_path.resolve().relative_to(root_path.resolve())
            return True
        except ValueError:
            # file_path is not a subpath of root_path
            return False


class FileSizeFilter(FileFilter):
    """Filter files based on their size."""

    def __init__(self, max_file_size_kb: int):
        """Initialize the FileSizeFilter."""
        super().__init__()
        self.max_file_size_bytes = max_file_size_kb * 1024

    def _check(self, file_path: Path, context: dict) -> bool:
        try:
            return file_path.stat().st_size <= self.max_file_size_bytes
        except FileNotFoundError:
            # If file is not found, it cannot be processed, so filter it out.
            return False
        except Exception as e:
            # Log other potential errors (e.g., permission issues) and filter out.
            import logging

            logging.warning(f"Error checking file size for {file_path}: {e}")
            return False


class FilterChainBuilder:
    """Builder for constructing file filter chains."""

    @staticmethod
    def build(config: CombinerConfig, spec: pathspec.PathSpec | None) -> FileFilter:
        """
        Build a filter chain based on configuration.

        Args:
            config: The combiner configuration
            spec: Optional gitignore PathSpec for filtering

        Returns:
            The head of the filter chain

        """
        output_path = Path(config.output)
        if not output_path.is_absolute():
            output_path = (config.directory_path / output_path).resolve()

        filters: list[FileFilter] = [
            SecurityFilter(),
            SymlinkFilter(),
            BinaryFileFilter(),
        ]

        if config.max_file_size_kb is not None and config.max_file_size_kb > 0:
            filters.append(FileSizeFilter(config.max_file_size_kb))

        filters.append(ExtensionFilter(config.extensions, config.exclude_extensions))

        if not config.include_hidden:
            filters.append(HiddenFileFilter(config.include_hidden))

        if config.use_gitignore and spec:
            filters.append(GitignoreFilter(spec))

        chain = OutputFilePathFilter(output_path)
        current: FileFilter = chain
        for f in filters:
            current = current.set_next(f)

        return chain
