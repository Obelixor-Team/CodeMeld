"""Utility functions for the code combiner."""

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
