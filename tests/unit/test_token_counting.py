import pytest
from src.code_combiner import scan_and_combine_code_files
from unittest.mock import patch, MagicMock
import re

@patch('tiktoken.get_encoding')
def test_token_counting_accuracy(mock_get_encoding, tmp_path, capsys):
    # Create a dummy file
    file_content = "This is a test sentence for token counting."
    (tmp_path / "test_file.txt").write_text(file_content)

    output_file = tmp_path / "combined.txt"

    # Mock tiktoken.get_encoding and its return value
    mock_encoder = MagicMock()
    mock_encoder.encode.return_value = [1, 2, 3, 4, 5, 6, 7] # Simulate 7 tokens
    mock_get_encoding.return_value = mock_encoder

    scan_and_combine_code_files(
        tmp_path,
        str(output_file),
        extensions=[ ".txt" ],
        exclude_extensions=[],
        count_tokens=True,
    )

    captured = capsys.readouterr()

    # The expected tokens should now come from our mock
    expected_tokens = len(mock_encoder.encode.return_value)

    match = re.search(r"Total tokens in raw combined content: (\d+)", captured.out)
    assert match is not None
    actual_tokens = int(match.group(1))
    assert actual_tokens == expected_tokens
    mock_get_encoding.assert_called_once_with("cl100k_base")
    mock_encoder.encode.assert_called_once_with(file_content)

@patch.dict('sys.modules', {'tiktoken': None})
def test_token_counting_tiktoken_not_installed(tmp_path, capsys):
    file_content = "This is a test sentence."
    (tmp_path / "test_file.txt").write_text(file_content)
    output_file = tmp_path / "combined.txt"

    scan_and_combine_code_files(
        tmp_path,
        str(output_file),
        extensions=[".txt"],
        exclude_extensions=[],
        count_tokens=True,
    )

    captured = capsys.readouterr()
    assert "Warning: tiktoken not found. Token counting will be skipped." in captured.out
    assert "Total tokens in combined content:" not in captured.out
