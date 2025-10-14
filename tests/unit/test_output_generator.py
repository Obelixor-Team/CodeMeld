# Copyright (c) 2025 skum

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
    with patch('psutil.Process') as mock_process_class:
        mock_process_instance = mock_process_class.return_value
        mock_process_instance.memory_info.return_value.rss = 1000 * 1024 * 1024  # 1000MB, very high

        memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)


        with patch('src.output_generator.read_file_content', return_value='some content'):
            generator = InMemoryOutputGenerator(
                mock_files_to_process, mock_root_path, mock_formatter, memory_monitor, MagicMock(), Path("/tmp/output.txt"), MagicMock(), MagicMock(), MagicMock() # /tmp is used for testing temporary file creation
            )
            with pytest.raises(MemoryThresholdExceededError):
                generator.generate()