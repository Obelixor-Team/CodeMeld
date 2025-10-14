# Copyright (c) 2025 skum

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
    """
    Determine if a file is likely binary.

    Determines if a file is likely binary based on its extension and/or content analysis.
    This is a heuristic check, optimized for performance, especially with large files.
    It's not foolproof and might misclassify some files.
    """
    # 1. Fast check by file extension:
    # If the file has a common binary extension, it's immediately classified as binary.
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    # 2. Content analysis for other files:
    # For files without a known binary extension, perform a quick content scan.
    try:
        file_size = file_path.stat().st_size
        # Determine sample size: For very large files (>1MB), only read the first 8KB.
        # Otherwise, read up to 8KB or the entire file if smaller.
        sample_size = min(8192, file_size) if file_size > 1024 * 1024 else file_size

        with open(file_path, "rb") as f:
            chunk = f.read(sample_size)
            if not chunk:
                # Empty file or unable to read, assume not binary (or handle as per policy)
                return False

            # Heuristic 1: Check for null bytes
            # The presence of null bytes (b'\0') is a strong indicator of a binary file.
            if b"\0" in chunk:
                return True

            # Heuristic 2: Check proportion of non-text bytes
            # Count bytes that are not common ASCII text characters (printable + whitespace).
            # If a significant proportion (e.g., >30%) are non-text, it's likely binary.
            text_chars = bytes(range(32, 127)) + b"\n\r\t\f\b"
            non_text = sum(1 for byte in chunk if byte not in text_chars)
            # This threshold (0.30) is a common heuristic; it can be tuned.
            return (non_text / len(chunk)) > 0.30
    except Exception as e:
        # Log any errors during file access or analysis and default to treating as binary
        # to prevent potential issues with processing unreadable or problematic files.
        logging.warning(f"Error checking binary status for {file_path}: {e}")
        return True
