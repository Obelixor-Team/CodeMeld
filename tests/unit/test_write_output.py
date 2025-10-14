# Copyright (c) 2025 skum

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import logging

from src.code_combiner import write_output

@pytest.fixture
def mock_output_path(tmp_path):
    output_file = tmp_path / "output.txt"
    return output_file

def test_write_output_file_exists_no_overwrite(mock_output_path, caplog):
    mock_output_path.write_text("existing content")
    with patch('sys.stdin.isatty', return_value=True):
        with patch('builtins.input', return_value='n'):
            with caplog.at_level(logging.INFO):
                write_output(mock_output_path, "new content", force=False)
                assert "Operation cancelled by user. File not overwritten." in caplog.text
                assert mock_output_path.read_text() == "existing content"

def test_write_output_file_exists_overwrite(mock_output_path, caplog):
    mock_output_path.write_text("existing content")
    with patch('sys.stdin.isatty', return_value=True):
        with patch('builtins.input', return_value='y'):
            with caplog.at_level(logging.INFO):
                write_output(mock_output_path, "new content", force=False)
                assert "All code files have been combined into:" in caplog.text
                assert mock_output_path.read_text() == "new content"

def test_write_output_file_exists_force_overwrite(mock_output_path, caplog):
    mock_output_path.write_text("existing content")
    with caplog.at_level(logging.INFO):
        write_output(mock_output_path, "new content", force=True)
        assert "All code files have been combined into:" in caplog.text
        assert mock_output_path.read_text() == "new content"

def test_write_output_file_does_not_exist(mock_output_path, caplog):
    with caplog.at_level(logging.INFO):
        write_output(mock_output_path, "new content", force=False)
        assert "All code files have been combined into:" in caplog.text
        assert mock_output_path.read_text() == "new content"

def test_write_output_dry_run(mock_output_path, caplog, capsys):
    with caplog.at_level(logging.INFO):
        write_output(mock_output_path, "dry run content", force=False, dry_run=True)
        assert "--- Dry Run Output ---" in caplog.text
        assert "--- End Dry Run Output ---" in caplog.text
        captured = capsys.readouterr()
        assert "dry run content" in captured.out
        assert not mock_output_path.exists()

def test_write_output_non_interactive_no_overwrite(mock_output_path, caplog):
    mock_output_path.write_text("existing content")
    with patch('sys.stdin.isatty', return_value=False):
        with caplog.at_level(logging.INFO):
            write_output(mock_output_path, "new content", force=False)
            assert "Skipping overwrite in non-interactive mode." in caplog.text
            assert mock_output_path.read_text() == "existing content"

def test_write_output_permission_error(mock_output_path, caplog):
    # Simulate a PermissionError when trying to write to the file
    mock_output_path.parent.mkdir(parents=True, exist_ok=True)
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        with caplog.at_level(logging.ERROR):
            with pytest.raises(PermissionError):
                write_output(mock_output_path, "content", force=True)
            assert "Error writing to output file" in caplog.text

def test_write_output_parent_dir_creation(tmp_path, caplog):
    non_existent_dir = tmp_path / "non_existent_parent"
    output_file = non_existent_dir / "output.txt"
    assert not non_existent_dir.exists()
    with caplog.at_level(logging.INFO):
        write_output(output_file, "content", force=False)
        assert non_existent_dir.exists()
        assert output_file.read_text() == "content"
        assert "All code files have been combined into:" in caplog.text
