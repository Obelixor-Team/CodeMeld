# Copyright (c) 2025 skum

"""Defines the filter chain for selecting files to be combined."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pathspec

from .config import CombinerConfig
from .utils import is_likely_binary


class FileFilter(ABC):
    """Base class for file filters."""

    filters: list[FileFilter] = []

    def should_process(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Return True if file should be processed."""
        result = self._check(file_path, context)
        logging.debug(
            f"{self.__class__.__name__}._check({file_path.name}) returned {result}"
        )
        return result

    @abstractmethod
    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Individual filter logic."""
        pass


class CompositeFilter(FileFilter):
    """A filter that is composed of other filters. All filters must pass."""

    def __init__(self, filters: list[FileFilter]):
        """Initialize the composite filter."""
        self.filters = filters

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Check the file against all filters in the composite."""
        for f in self.filters:
            if not f.should_process(file_path, context):
                return False
        return True


class ExtensionFilter(FileFilter):
    """Filter files based on their extensions."""

    def __init__(self, extensions: list[str], exclude: list[str]):
        """Initialize the extension filter."""
        self.extensions = [e.lower() for e in extensions]
        self.exclude = [e.lower() for e in exclude]

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        suffix = file_path.suffix.lower()
        if suffix in self.exclude:
            return False
        return suffix in self.extensions


class HiddenFileFilter(FileFilter):
    """Filter hidden files and directories."""

    def __init__(self, include_hidden: bool):
        """Initialize the hidden file filter."""
        self.include_hidden = include_hidden

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
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
        self.spec = spec

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
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
        self.output_path = output_path.resolve()

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        """Determine if the file should be processed."""
        return file_path.resolve() != self.output_path


class BinaryFileFilter(FileFilter):
    """Filter binary files."""

    def __init__(self, config: CombinerConfig):
        """Initialize the binary file filter."""
        self.config = config

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        return not is_likely_binary(file_path, self.config)


class SymlinkFilter(FileFilter):
    """Filter symbolic links, with an option to follow them."""

    def __init__(self, follow_symlinks: bool):
        """Initialize the SymlinkFilter."""
        self.follow_symlinks = follow_symlinks

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        if self.follow_symlinks:
            return True  # If following symlinks, don't filter them out

        import logging

        logging.debug(
            f"SymlinkFilter: Checking {file_path}, is_symlink: {file_path.is_symlink()}"
        )

        return not file_path.is_symlink()


class SecurityFilter(FileFilter):
    """Filter to prevent path traversal by ensuring files are within the root path."""

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        import logging

        root_path = context.get("root_path")

        if not root_path:
            logging.debug(
                f"SecurityFilter: No root_path in context for {file_path}. Allowing."
            )

            return True

        try:
            resolved_file_path = file_path.resolve()

            resolved_root_path = root_path.resolve()

            resolved_file_path.relative_to(resolved_root_path)

            logging.debug(
                f"SecurityFilter: {resolved_file_path} in "
                f"{resolved_root_path}. Allowing."
            )

            return True

        except ValueError:
            logging.debug(
                f"SecurityFilter: {resolved_file_path} NOT in "
                f"{resolved_root_path}. Blocking."
            )

            return False


class AlwaysIncludeFilter(FileFilter):
    """Filter for files that should always be included."""

    def __init__(self, always_include_paths: list[Path]):
        """Initialize the AlwaysIncludeFilter."""
        self.always_include_paths = {p.resolve() for p in always_include_paths}

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        return file_path.resolve() in self.always_include_paths


class FileSizeFilter(FileFilter):
    """Filter files based on their size."""

    def __init__(self, max_file_size_kb: int):
        """Initialize the FileSizeFilter."""
        self.max_file_size_bytes = max_file_size_kb * 1024

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        try:
            return file_path.stat().st_size <= self.max_file_size_bytes
        except FileNotFoundError:
            # If file is not found, it cannot be processed, so filter it out.
            return False
        except Exception as e:
            # Log other potential errors (e.g., permission issues) and filter out.
            import logging

            logging.debug(f"Error checking file size for {file_path}: {e}")
            return False


class OrFilter(FileFilter):
    """A filter that passes if any of its sub-filters pass."""

    def __init__(self, filters: list[FileFilter]):
        """Initialize the OrFilter."""
        self.filters = filters

    def _check(self, file_path: Path, context: dict[str, Any]) -> bool:
        if not self.filters:
            logging.debug(f"OrFilter: No filters provided for {file_path}")
            return False

        for f in self.filters:
            if f.should_process(file_path, context):
                logging.debug(f"OrFilter: {f.__class__.__name__} accepted {file_path}")
                return True
        return False


class FilterChainBuilder:
    """Builder for constructing file filter chains."""

    @staticmethod
    def _resolve_output_path(config: CombinerConfig) -> Path:
        output_path = Path(config.output)
        if not output_path.is_absolute():
            output_path = (config.directory_path / output_path).resolve()
        return output_path

    @staticmethod
    def build_safety_chain(config: CombinerConfig) -> CompositeFilter:
        """Build a filter chain for safety checks only."""
        output_path = FilterChainBuilder._resolve_output_path(config)
        filters: list[FileFilter] = [
            SecurityFilter(),
            SymlinkFilter(config.follow_symlinks),
            BinaryFileFilter(config),
            OutputFilePathFilter(output_path),
        ]
        if config.max_file_size_kb is not None and config.max_file_size_kb > 0:
            filters.append(FileSizeFilter(config.max_file_size_kb))
        return CompositeFilter(filters)

    @staticmethod
    def build_full_chain(
        config: CombinerConfig,
        spec: pathspec.PathSpec | None,
        safety_chain: CompositeFilter,
        always_include_paths: list[Path],
    ) -> CompositeFilter:
        """
        Build the full filter chain with the logic.

        The logic is:
        (pass_always_include OR pass_content_filters) AND pass_safety_filters
        """
        content_filters: list[FileFilter] = [
            ExtensionFilter(config.extensions, config.exclude_extensions)
        ]
        if not config.include_hidden:
            content_filters.append(HiddenFileFilter(config.include_hidden))
        if config.use_gitignore and spec:
            content_filters.append(GitignoreFilter(spec))

        main_selection_filters: list[FileFilter] = [CompositeFilter(content_filters)]
        if always_include_paths:
            main_selection_filters.insert(0, AlwaysIncludeFilter(always_include_paths))

        # The core logic: a file is included if it's either in the always_include list
        # OR it passes all the content filters.
        main_filter = OrFilter(main_selection_filters)

        # The final chain: the file must pass the main filter AND the safety filter.
        return CompositeFilter([main_filter, safety_chain])
