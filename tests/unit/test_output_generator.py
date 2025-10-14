# Copyright (c) 2025 skum

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging
import psutil

from src.output_generator import InMemoryOutputGenerator, read_file_content
from src.context import GeneratorContext
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

def test_in_memory_generator_memory_warning(mock_files_to_process, mock_root_path, mock_formatter, tmp_path):
    """Ensure MemoryThresholdExceededError is raised when memory exceeds threshold."""
    with patch('psutil.Process') as mock_process_class:
        mock_process_instance = mock_process_class.return_value
        mock_process_instance.memory_info.return_value.rss = 1000 * 1024 * 1024  # 1000MB, very high

        memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)


        with patch('src.output_generator.read_file_content', return_value='some content'):
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=mock_formatter,
                memory_monitor=memory_monitor,
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)
            with pytest.raises(MemoryThresholdExceededError):
                generator.generate()

def test_thread_pool_executor_worker_cap(mock_files_to_process, mock_root_path, mock_formatter, tmp_path):
    """Ensure ThreadPoolExecutor max_workers is capped correctly."""
    with patch('os.cpu_count', return_value=100):
        with patch('src.output_generator.ThreadPoolExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor_instance

            # Mock the submit method to return a real Future that is already done
            from concurrent.futures import Future

            def mock_submit(func, *args, **kwargs):
                future = Future()
                future.set_result((args[0], "dummy content"))
                return future

            mock_executor_instance.submit.side_effect = mock_submit

            memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=mock_formatter,
                memory_monitor=memory_monitor,
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)
            generator.generate()

            mock_executor_class.assert_called_once()
            # The cap is min(32, (os.cpu_count() or 1) + 4)
            # With os.cpu_count() = 100, it should be min(32, 104) which is 32
            assert mock_executor_class.call_args[1]['max_workers'] == 32

    with patch('os.cpu_count', return_value=2):
        with patch('src.output_generator.ThreadPoolExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor_instance

            # Mock the submit method to return a real Future that is already done
            from concurrent.futures import Future

            def mock_submit(func, *args, **kwargs):
                future = Future()
                future.set_result((args[0], "dummy content"))
                return future

            mock_executor_instance.submit.side_effect = mock_submit

            memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=mock_formatter,
                memory_monitor=memory_monitor,
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)
            generator.generate()

            mock_executor_class.assert_called_once()
            # With os.cpu_count() = 2, it should be min(32, 2 + 4) which is 6
            assert mock_executor_class.call_args[1]['max_workers'] == 6

def test_in_memory_generator_failed_files_logging(mock_files_to_process, mock_root_path, mock_formatter, tmp_path):
    """Ensure failed files are logged when _read_file_and_notify raises an exception."""
    with patch('os.cpu_count', return_value=2):
        with patch('src.output_generator.ThreadPoolExecutor') as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = mock_executor_instance

            from concurrent.futures import Future

            def mock_submit_with_exception(func, *args, **kwargs):
                future = Future()
                future.set_exception(Exception("Test exception"))
                return future

            mock_executor_instance.submit.side_effect = mock_submit_with_exception

            memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=mock_formatter,
                memory_monitor=memory_monitor,
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)

            with patch('logging.warning') as mock_warning:
                generator.generate()
                mock_warning.assert_called_once_with(
                    f"Failed to read {len(mock_files_to_process)} files. See log for details."
                )