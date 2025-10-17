# Copyright (c) 2025 skum

import logging
from pathlib import Path

import pytest

from src.utils import is_likely_binary, log_file_read_error


@pytest.fixture
def temp_files(tmp_path: Path):
    text_file = tmp_path / "text.txt"
    text_file.write_text("This is a plain text file.\nIt has multiple lines.")

    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe")

    large_text_file = tmp_path / "large_text.log"
    large_text_file.write_text("a" * (2 * 1024 * 1024))  # 2MB text file

    large_binary_file = tmp_path / "large_binary.zip"
    large_binary_file.write_bytes(b"\x00\x01\x02\x03" * (500 * 1024))  # 2MB binary file

    utf16_file = tmp_path / "utf16.txt"
    utf16_file.write_text("This is a UTF-16 encoded file.", encoding="utf-16")

    mixed_content_file = tmp_path / "mixed.txt"
    mixed_content_file.write_bytes(b"Some text" + b"\x00" + b"more text")

    unusual_ext_file = tmp_path / "data.unknown"
    unusual_ext_file.write_text("Some text in a file with an unusual extension.")

    return {
        "text": text_file,
        "binary": binary_file,
        "large_text": large_text_file,
        "large_binary": large_binary_file,
        "utf16": utf16_file,
        "mixed": mixed_content_file,
        "unusual": unusual_ext_file,
    }


def test_is_likely_binary_text_file(temp_files):
    assert not is_likely_binary(temp_files["text"])


def test_is_likely_binary_binary_file(temp_files):
    assert is_likely_binary(temp_files["binary"])


def test_is_likely_binary_large_text_file(temp_files):
    assert not is_likely_binary(temp_files["large_text"])


def test_is_likely_binary_large_binary_file(temp_files):
    assert is_likely_binary(temp_files["large_binary"])


def test_is_likely_binary_empty_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.touch()
    assert not is_likely_binary(empty_file)


def test_is_likely_binary_with_binary_extension(tmp_path):
    image_file = tmp_path / "image.png"
    image_file.touch()
    assert is_likely_binary(image_file)


def test_is_likely_binary_with_text_extension(tmp_path):
    script_file = tmp_path / "script.py"
    script_file.write_text("print('hello')")
    assert not is_likely_binary(script_file)


def test_is_likely_binary_utf16_file(temp_files):
    assert is_likely_binary(temp_files["utf16"])


def test_is_likely_binary_mixed_content(temp_files):
    assert is_likely_binary(temp_files["mixed"])


def test_is_likely_binary_unusual_extension(temp_files):
    assert not is_likely_binary(temp_files["unusual"])


def test_log_file_read_error_unicode_decode_error(caplog):
    with caplog.at_level(logging.WARNING):
        log_file_read_error(
            Path("test.txt"), UnicodeDecodeError("utf-8", b"", 0, 1, "reason")
        )
    assert "Skipping file due to UnicodeDecodeError: test.txt" in caplog.text


def test_log_file_read_error_file_not_found_error(caplog):
    with caplog.at_level(logging.WARNING):
        log_file_read_error(Path("test.txt"), FileNotFoundError())
    assert "Skipping file not found: test.txt" in caplog.text


def test_log_file_read_error_permission_error(caplog):
    with caplog.at_level(logging.WARNING):
        log_file_read_error(Path("test.txt"), PermissionError())
    assert "Skipping file due to permission error: test.txt" in caplog.text


def test_log_file_read_error_is_a_directory_error(caplog):
    with caplog.at_level(logging.WARNING):
        log_file_read_error(Path("test.txt"), IsADirectoryError())
    assert "Skipping directory treated as file: test.txt" in caplog.text


def test_log_file_read_error_generic_exception(caplog):
    with caplog.at_level(logging.ERROR):
        log_file_read_error(Path("test.txt"), Exception())
    assert "An unexpected error occurred while reading test.txt" in caplog.text
