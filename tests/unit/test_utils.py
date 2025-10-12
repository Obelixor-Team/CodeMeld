import pytest
from pathlib import Path
from src.utils import is_likely_binary

@pytest.fixture
def temp_files(tmp_path: Path):
    text_file = tmp_path / "text.txt"
    text_file.write_text("This is a plain text file.\nIt has multiple lines.")

    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe')

    large_text_file = tmp_path / "large_text.log"
    large_text_file.write_text("a" * (2 * 1024 * 1024)) # 2MB text file

    large_binary_file = tmp_path / "large_binary.zip"
    large_binary_file.write_bytes(b'\x00\x01\x02\x03' * (500 * 1024)) # 2MB binary file

    return {
        "text": text_file,
        "binary": binary_file,
        "large_text": large_text_file,
        "large_binary": large_binary_file,
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
    script_file.touch()
    assert not is_likely_binary(script_file)
