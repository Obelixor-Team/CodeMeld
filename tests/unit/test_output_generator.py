# Copyright (c) 2025 skum

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging
import psutil

from src.output_generator import InMemoryOutputGenerator, read_file_content, log_file_read_error, StreamingOutputGenerator
from src.context import GeneratorContext
from src.formatters import TextFormatter
from src.config import MemoryThresholdExceededError
from src.memory_monitor import SystemMemoryMonitor

@pytest.fixture
def mock_files_to_process():
    return [Path("/mock/file1.py"), Path("/mock/file2.py")]

@pytest.fixture
def mock_root_path(tmp_path):
    root = tmp_path / "mock_root"
    root.mkdir()
    return root

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

def test_read_file_content_unicode_decode_error(tmp_path, mocker):
    """Test that read_file_content handles UnicodeDecodeError."""
    bad_encoding_file = tmp_path / "bad_encoding.txt"
    # Write some bytes that are not valid UTF-8
    bad_encoding_file.write_bytes(b"\x80\x81\x82")

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    # Iterate over the generator to trigger the read and potential error
    for _ in read_file_content(bad_encoding_file):
        pass

    mock_log_file_read_error.assert_called_once()
    assert "codec can't decode byte" in str(mock_log_file_read_error.call_args[0][1])

def test_read_file_content_file_not_found_error(tmp_path, mocker):
    """Test that read_file_content handles FileNotFoundError."""
    non_existent_file = tmp_path / "non_existent.txt"

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    for _ in read_file_content(non_existent_file):
        pass

    mock_log_file_read_error.assert_called_once()
    assert "No such file or directory" in str(mock_log_file_read_error.call_args[0][1])

def test_read_file_content_permission_error(tmp_path, mocker):
    """Test that read_file_content handles PermissionError."""
    permission_denied_file = tmp_path / "permission_denied.txt"
    permission_denied_file.touch()
    permission_denied_file.chmod(0o000)  # Remove all permissions

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    for _ in read_file_content(permission_denied_file):
        pass

    mock_log_file_read_error.assert_called_once()
    assert "Permission denied" in str(mock_log_file_read_error.call_args[0][1])

    # Restore permissions for cleanup
    permission_denied_file.chmod(0o644)

def test_read_file_content_is_a_directory_error(tmp_path, mocker):
    """Test that read_file_content handles IsADirectoryError."""
    directory_path = tmp_path / "a_directory"
    directory_path.mkdir()

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    for _ in read_file_content(directory_path):
        pass

    mock_log_file_read_error.assert_called_once()
    assert "Is a directory" in str(mock_log_file_read_error.call_args[0][1])

def test_read_file_content_generic_exception(tmp_path, mocker):
    """Test that read_file_content handles a generic Exception."""
    problematic_file = tmp_path / "problem.txt"
    problematic_file.touch()

    # Mock open to raise a generic exception
    mocker.patch("builtins.open", side_effect=Exception("Simulated generic error"))

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    for _ in read_file_content(problematic_file):
        pass

    mock_log_file_read_error.assert_called_once()
    assert "Simulated generic error" in str(mock_log_file_read_error.call_args[0][1])

def test_in_memory_generator_xml_indentation(mock_files_to_process, mock_root_path, tmp_path, mocker):
    """Test that ET.indent is called when using XMLFormatter in InMemoryOutputGenerator."""
    from src.formatters import XMLFormatter
    from xml.etree import ElementTree as ET

    mock_xml_formatter = XMLFormatter()
    mocker.patch.object(mock_xml_formatter, 'begin_output', return_value="<root>")
    mocker.patch.object(mock_xml_formatter, 'end_output', return_value="</root>")
    mocker.patch.object(mock_xml_formatter, 'format_file', return_value="<file/>")
    mock_et_indent = mocker.patch.object(ET, 'indent')

    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_xml_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.xml",
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = InMemoryOutputGenerator(context)

    # Mock read_file_content to return some content
    mocker.patch('src.output_generator.read_file_content', return_value=["some content"])
    mocker.patch('src.output_generator.is_likely_binary', return_value=False)

    generator.generate()

    mock_et_indent.assert_called_once_with(generator.xml_root_element)

def test_streaming_output_generator_dry_run_output_path(mock_files_to_process, mock_root_path, mock_formatter, tmp_path):
    """Test that dry_run_output_path is correctly set in StreamingOutputGenerator."""
    dry_run_output_path_str = str(tmp_path / "dry_run_output.txt")
    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        dry_run_output=dry_run_output_path_str,
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    assert generator.dry_run_output_path == Path(dry_run_output_path_str)

def test_streaming_output_generator_empty_non_binary_file(mock_root_path, mock_formatter, tmp_path, mocker):
    """Test that StreamingOutputGenerator._process_file_streaming handles an empty, non-binary file."""
    empty_file = mock_root_path / "empty.txt"
    empty_file.touch()

    mock_ui = MagicMock()
    mock_publisher = MagicMock()
    mock_token_counter = MagicMock()
    mock_line_counter = MagicMock()

    context = GeneratorContext(
        files_to_process=[empty_file],
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=mock_publisher,
        output_path=tmp_path / "output.txt",
        ui=mock_ui,
        token_counter_observer=mock_token_counter,
        line_counter_observer=mock_line_counter,
    )
    generator = StreamingOutputGenerator(context)

    mocker.patch('src.output_generator.read_file_content', return_value=[])
    mocker.patch('src.output_generator.is_likely_binary', return_value=False)

    generator._process_file_streaming(empty_file)

    mock_ui.update.assert_called_once_with(
        str(empty_file.relative_to(mock_root_path)),
        skipped=True,
        tokens=mock_token_counter.total_tokens,
        lines=mock_line_counter.total_lines,
    )