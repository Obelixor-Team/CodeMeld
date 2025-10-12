import pytest
from src.code_combiner import write_output
from unittest.mock import patch, mock_open

@patch('builtins.open', new_callable=mock_open)
def test_write_output_permission_error(mock_file_open, tmp_path, capsys):
    # Simulate a PermissionError when trying to write
    mock_file_open.side_effect = PermissionError("Permission denied")

    output_file = tmp_path / "output.txt"
    content = "test content"

    write_output(output_file, content, force=True)

    captured = capsys.readouterr()
    assert "Error creating or writing to output file" in captured.out
    assert "Permission denied" in captured.out

    assert "Permission denied" in captured.out
