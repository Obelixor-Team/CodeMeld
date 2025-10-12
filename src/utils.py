"""Utility functions for the code combiner."""

from pathlib import Path


def is_likely_binary(file_path: Path) -> bool:
    """Check if a file is likely a binary file based on its content."""
    # Read the first 1024 bytes to check for null bytes
    with open(file_path, "rb") as f:
        initial_bytes = f.read(1024)
    return b"\0" in initial_bytes
