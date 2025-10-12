"""Defines the filter chain for selecting files to be combined."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import pathspec

from .config import CombinerConfig

BINARY_EXTENSIONS: list[str] = [
    ".bin", ".exe", ".dll", ".so", ".dylib", ".o", ".a", ".lib",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".ico",
    ".mp3", ".wav", ".ogg", ".flac", ".aac", ".wma",
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".jar",
    ".sqlite", ".db", ".mdb",
    ".class", ".pyc", ".pyo",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
]

BINARY_DETECTION_CHUNK_SIZE = 1024

def is_likely_binary(file_path: Path) -> bool:
    """Check if a file is likely binary by extension or null bytes."""
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(BINARY_DETECTION_CHUNK_SIZE)
            return b"\0" in chunk
    except Exception:
        return True

class FileFilter(ABC):
    """Base class for file filters."""

    def __init__(self):
        self._next_filter: Optional[FileFilter] = None

    def set_next(self, filter: 'FileFilter') -> 'FileFilter':
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
    def __init__(self, extensions: list[str], exclude: list[str]):
        super().__init__()
        self.extensions = [e.lower() for e in extensions]
        self.exclude = [e.lower() for e in exclude]

    def _check(self, file_path: Path, context: dict) -> bool:
        suffix = file_path.suffix.lower()
        if suffix in self.exclude:
            return False
        return suffix in self.extensions

class HiddenFileFilter(FileFilter):
    def __init__(self, include_hidden: bool):
        super().__init__()
        self.include_hidden = include_hidden

    def _check(self, file_path: Path, context: dict) -> bool:
        if self.include_hidden:
            return True
        root_path = context.get('root_path')
        if not root_path:
            return True
        try:
            relative = file_path.relative_to(root_path)
            return not any(part.startswith('.') for part in relative.parts)
        except ValueError:
            return True


class GitignoreFilter(FileFilter):
    def __init__(self, spec: Optional[pathspec.PathSpec]):
        super().__init__()
        self.spec = spec

    def _check(self, file_path: Path, context: dict) -> bool:
        if not self.spec:
            return True
        root_path = context.get('root_path')
        if not root_path:
            return True
        try:
            relative = file_path.relative_to(root_path)
            return not self.spec.match_file(str(relative))
        except ValueError:
            return True

class OutputFileFilter(FileFilter):
    def __init__(self, output_path: Path):
        super().__init__()
        self.output_path = output_path.resolve()

    def _check(self, file_path: Path, context: dict) -> bool:
        return file_path.resolve() != self.output_path

class BinaryFileFilter(FileFilter):
    def _check(self, file_path: Path, context: dict) -> bool:
        return not is_likely_binary(file_path)

class SymlinkFilter(FileFilter):
    def _check(self, file_path: Path, context: dict) -> bool:
        return not file_path.is_symlink()

class FilterChainBuilder:
    @staticmethod
    def build(config: CombinerConfig, spec: Optional[pathspec.PathSpec]) -> FileFilter:
        chain = OutputFileFilter(Path(config.output))
        current = chain
        current = current.set_next(SymlinkFilter())
        current = current.set_next(BinaryFileFilter())
        current = current.set_next(ExtensionFilter(config.extensions, config.exclude_extensions))

        if not config.include_hidden:
            current = current.set_next(HiddenFileFilter(config.include_hidden))

        if config.use_gitignore and spec:
            current = current.set_next(GitignoreFilter(spec))

        return chain
