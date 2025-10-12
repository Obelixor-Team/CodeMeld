import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging
import psutil

from src.output_generator import InMemoryOutputGenerator, read_file_content
from src.formatters import TextFormatter

@pytest.fixture
def mock_files_to_process():
    return [Path("/mock/file1.py"), Path("/mock/file2.py")]

@pytest.fixture
def mock_root_path():
    return Path("/mock")

@pytest.fixture
def mock_formatter():
    return TextFormatter()

def test_in_memory_generator_memory_warning(mock_files_to_process, mock_root_path, mock_formatter):
    # Mock psutil.Process().memory_info().rss to simulate high memory usage
    with patch.object(psutil.Process, 'memory_info') as mock_memory_info:
        mock_memory_info.return_value.rss = 600 * 1024 * 1024  # 600MB, above 500MB threshold

        generator = InMemoryOutputGenerator(mock_files_to_process, mock_root_path, mock_formatter)

        # Mock read_file_content to return some content
        with patch('src.output_generator.read_file_content', return_value='some content'):
            with patch('logging.warning') as mock_logging_warning:
                generator.generate()
                mock_logging_warning.assert_called_with("High memory usage detected (RSS: 600.0MB)")

def test_in_memory_generator_no_memory_warning(mock_files_to_process, mock_root_path, mock_formatter):
    # Mock psutil.Process().memory_info().rss to simulate normal memory usage
    with patch.object(psutil.Process, 'memory_info') as mock_memory_info:
        mock_memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB, below 500MB threshold

        generator = InMemoryOutputGenerator(mock_files_to_process, mock_root_path, mock_formatter)

        with patch('src.output_generator.read_file_content', return_value='some content'):
            with patch('logging.warning') as mock_logging_warning:
                generator.generate()
                mock_logging_warning.assert_not_called()

def test_read_file_content_is_a_directory_error():
    # Simulate IsADirectoryError when trying to read a directory as a file
    mock_dir_path = MagicMock(spec=Path)
    # Mock the is_likely_binary function from src.utils directly
    with patch('src.utils.is_likely_binary', return_value=False):
        with patch('builtins.open', side_effect=IsADirectoryError):
            result = read_file_content(mock_dir_path)
            assert result is None
