"""Utility functions for the code combiner."""

from __future__ import annotations

import logging
from pathlib import Path

BINARY_EXTENSIONS = {
    ".bin",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".o",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
}


def log_file_read_error(file_path: Path, error: Exception) -> None:
    """Log a warning for file read errors."""

    if isinstance(error, UnicodeDecodeError):

        logging.warning(f"Skipping file due to UnicodeDecodeError: {file_path}")

    elif isinstance(error, FileNotFoundError):

        logging.warning(f"Skipping file not found: {file_path}")

    elif isinstance(error, PermissionError):

        logging.warning(f"Skipping file due to permission error: {file_path}")

    elif isinstance(error, IsADirectoryError):

        logging.warning(f"Skipping directory treated as file: {file_path}")

    else:

        logging.error(
            f"An unexpected error occurred while reading {file_path}: {error}"
        )


def is_likely_binary(file_path: Path) -> bool:
    """Check if a file is likely binary - optimized for large files."""
    # Check extension first (fast)
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    # For large files, do quicker content analysis
    try:
        file_size = file_path.stat().st_size
        # For very large files, only check first few KB
        sample_size = min(8192, file_size) if file_size > 1024 * 1024 else 8192

        with open(file_path, "rb") as f:
            chunk = f.read(sample_size)
            if not chunk:
                return False

            # Check for null bytes
            if b"\0" in chunk:
                return True

            # Check proportion of non-text bytes
            text_chars = bytes(range(32, 127)) + b"\n\r\t\f\b"
            non_text = sum(1 for byte in chunk if byte not in text_chars)
            return (non_text / len(chunk)) > 0.30
    except Exception:
        return True
