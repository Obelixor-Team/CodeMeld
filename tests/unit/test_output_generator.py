import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging
import psutil

from src.output_generator import InMemoryOutputGenerator, read_file_content
from src.formatters import TextFormatter
from src.config import MemoryThresholdExceededError
from src.memory_monitor import SystemMemoryMonitor

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
    """Ensure MemoryThresholdExceededError is raised when memory exceeds threshold."""
    memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
    with patch.object(psutil.Process, 'memory_info') as mock_memory_info:
        mock_memory_info.return_value.rss = 600 * 1024 * 1024  # 600MB, above 500MB threshold
        generator = InMemoryOutputGenerator(mock_files_to_process, mock_root_path, mock_formatter, memory_monitor, MagicMock(), Path("/tmp/output.txt"), MagicMock(), MagicMock())

        with patch('src.output_generator.read_file_content', return_value='some content'):
            with pytest.raises(MemoryThresholdExceededError):
                generator.generate()

def test_in_memory_generator_no_memory_warning(mock_files_to_process, mock_root_path, mock_formatter):
    # Mock psutil.Process().memory_info().rss to simulate normal memory usage
    with patch.object(psutil.Process, 'memory_info') as mock_memory_info:
        mock_memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB, below 500MB threshold

        memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
        generator = InMemoryOutputGenerator(mock_files_to_process, mock_root_path, mock_formatter, memory_monitor, MagicMock(), Path("/tmp/output.txt"), MagicMock(), MagicMock())

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

def test_in_memory_generator_memory_threshold_exceeded_fallback(mock_files_to_process, mock_root_path, mock_formatter):
    # Simulate high memory usage and no token counting
    with patch.object(psutil.Process, 'memory_info') as mock_memory_info:
        mock_memory_info.return_value.rss = 600 * 1024 * 1024  # 600MB, above 500MB threshold

        memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=False)
        generator = InMemoryOutputGenerator(
            mock_files_to_process, mock_root_path, mock_formatter, memory_monitor, MagicMock(), Path("/tmp/output.txt"), MagicMock(), MagicMock()
        )

        with patch('src.output_generator.read_file_content', return_value='some content'):
            with pytest.raises(MemoryThresholdExceededError, match="Memory usage exceeded 500MB. Falling back to streaming output."):
                generator.generate()

def test_in_memory_generator_memory_threshold_exceeded_no_fallback_with_tokens(
    mock_files_to_process, mock_root_path, mock_formatter, caplog
):
    """When token counting is enabled, memory exceedance raises MemoryThresholdExceededError."""
    memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
    with patch.object(psutil.Process, 'memory_info') as mock_memory_info:
        mock_memory_info.return_value.rss = 600 * 1024 * 1024  # 600MB, above 500MB threshold

        generator = InMemoryOutputGenerator(
            mock_files_to_process, mock_root_path, mock_formatter, memory_monitor, MagicMock(), Path("/tmp/output.txt"), MagicMock(), MagicMock()
        )

        with patch('src.output_generator.read_file_content', return_value='some content'):
            with caplog.at_level(logging.WARNING):
                with pytest.raises(MemoryThresholdExceededError):
                    generator.generate()

        # Optional: confirm warning log present
        assert any("High memory usage detected" in record.message for record in caplog.records)

def test_in_memory_generator_no_memory_limit(mock_files_to_process, mock_root_path, mock_formatter, caplog):
    # Simulate no memory limit (max_memory_mb=0)
    with patch.object(psutil.Process, 'memory_info') as mock_memory_info:
        mock_memory_info.return_value.rss = 1000 * 1024 * 1024  # 1000MB, very high

        memory_monitor = SystemMemoryMonitor(max_memory_mb=0, count_tokens=False)
        generator = InMemoryOutputGenerator(
            mock_files_to_process, mock_root_path, mock_formatter, memory_monitor, MagicMock(), Path("/tmp/output.txt"), MagicMock(), MagicMock()
        )

        with patch('src.output_generator.read_file_content', return_value='some content'):
            with caplog.at_level(logging.WARNING):
                generator.generate()
                # No warning should be logged because max_memory_mb is 0 (no limit)
                assert "High memory usage detected" not in caplog.text
            # Should not raise MemoryThresholdExceededError because max_memory_mb is 0