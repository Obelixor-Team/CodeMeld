# Copyright (c) 2025 skum

import collections
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import MemoryThresholdExceededError
from src.context import GeneratorContext
from src.formatters import TextFormatter
from src.memory_monitor import SystemMemoryMonitor
from src.observers import ProcessingEvent
from src.output_generator import (
    InMemoryOutputGenerator,
    StreamingOutputGenerator,
    read_file_content,
)


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


def test_in_memory_generator_memory_warning(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path
):
    """Ensure MemoryThresholdExceededError is raised when memory exceeds threshold."""
    with patch("psutil.Process") as mock_process_class:
        mock_process_instance = mock_process_class.return_value
        mock_process_instance.memory_info.return_value.rss = (
            1000 * 1024 * 1024
        )  # 1000MB, very high

        memory_monitor = SystemMemoryMonitor(max_memory_mb=500, count_tokens=True)

        with patch(
            "src.output_generator.read_file_content", return_value="some content"
        ):
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


def test_thread_pool_executor_worker_cap(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path
):
    """Ensure ThreadPoolExecutor max_workers is capped correctly."""
    with patch("os.cpu_count", return_value=100):
        with patch("src.output_generator.ThreadPoolExecutor") as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = (
                mock_executor_instance
            )

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
            assert mock_executor_class.call_args[1]["max_workers"] == 32

    with patch("os.cpu_count", return_value=2):
        with patch("src.output_generator.ThreadPoolExecutor") as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = (
                mock_executor_instance
            )

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
            assert mock_executor_class.call_args[1]["max_workers"] == 6


def test_in_memory_generator_failed_files_logging(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path
):
    """Ensure failed files are logged when _read_file_and_notify raises an exception."""
    with patch("os.cpu_count", return_value=2):
        with patch("src.output_generator.ThreadPoolExecutor") as mock_executor_class:
            mock_executor_instance = MagicMock()
            mock_executor_class.return_value.__enter__.return_value = (
                mock_executor_instance
            )

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

            with patch("logging.warning") as mock_warning:
                generator.generate()
                mock_warning.assert_called_once_with(
                    f"Failed to read {len(mock_files_to_process)} files. See log for details."
                )


def test_read_file_content_binary_file(tmp_path, mocker):
    """Test that read_file_content returns an empty generator for binary files."""
    binary_file = tmp_path / "binary.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03")

    mocker.patch("src.output_generator.is_likely_binary", return_value=True)

    content_generator = read_file_content(binary_file)
    assert list(content_generator) == []


def test_read_file_content_unicode_decode_error(tmp_path, mocker):
    """Test that read_file_content handles UnicodeDecodeError."""
    bad_encoding_file = tmp_path / "bad_encoding.txt"
    # Write some bytes that are not valid UTF-8
    bad_encoding_file.write_bytes(b"\x80\x81\x82")

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    # Iterate over the generator to trigger the read and potential error
    collections.deque(read_file_content(bad_encoding_file), maxlen=0)

    mock_log_file_read_error.assert_called_once()
    assert "codec can't decode byte" in str(mock_log_file_read_error.call_args[0][1])


def test_read_file_content_file_not_found_error(tmp_path, mocker):
    """Test that read_file_content handles FileNotFoundError."""
    non_existent_file = tmp_path / "non_existent.txt"

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    collections.deque(read_file_content(non_existent_file), maxlen=0)

    mock_log_file_read_error.assert_called_once()
    assert "No such file or directory" in str(mock_log_file_read_error.call_args[0][1])


def test_read_file_content_permission_error(tmp_path, mocker):
    """Test that read_file_content handles PermissionError."""
    permission_denied_file = tmp_path / "permission_denied.txt"
    permission_denied_file.touch()
    permission_denied_file.chmod(0o000)  # Remove all permissions

    mock_log_file_read_error = mocker.patch("src.output_generator.log_file_read_error")
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    collections.deque(read_file_content(permission_denied_file), maxlen=0)

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

    collections.deque(read_file_content(directory_path), maxlen=0)

    mock_log_file_read_error.assert_called_once()
    assert "Is a directory" in str(mock_log_file_read_error.call_args[0][1])


def test_in_memory_generator_file_not_relative_to_root(
    mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _get_relative_path handles files not relative to root_path."""
    # Create a file outside the mock_root_path
    external_file = tmp_path / "external_dir" / "external_file.txt"
    external_file.parent.mkdir()
    external_file.write_text("external content")

    context = GeneratorContext(
        files_to_process=[external_file],
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = InMemoryOutputGenerator(context)

    mocker.patch(
        "src.output_generator.read_file_content", return_value=["external content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    output, _ = generator.generate()

    # The external file's full path should be used as its relative path
    assert str(external_file) in output
    assert "external content" in output


def test_in_memory_generator_xml_indentation(
    mock_files_to_process, mock_root_path, tmp_path, mocker
):
    """Test that ET.indent is called when using XMLFormatter in InMemoryOutputGenerator."""
    from xml.etree import ElementTree as ET

    from src.formatters import XMLFormatter

    mock_xml_formatter = XMLFormatter()
    mocker.patch.object(mock_xml_formatter, "begin_output", return_value="<root>")
    mocker.patch.object(mock_xml_formatter, "end_output", return_value="</root>")
    mocker.patch.object(mock_xml_formatter, "format_file", return_value="<file/>")
    mock_et_indent = mocker.patch.object(ET, "indent")

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
    mocker.patch(
        "src.output_generator.read_file_content", return_value=["some content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    generator.generate()

    mock_et_indent.assert_called_once_with(generator.xml_root_element)


def test_streaming_output_generator_no_files_no_direct_streaming_formatter(
    mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _handle_actual_streaming logs info and notifies complete when no files and no direct streaming formatter."""
    context = GeneratorContext(
        files_to_process=[],  # Empty list of files
        root_path=mock_root_path,
        formatter=mock_formatter,  # TextFormatter is not a direct streaming formatter
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    mock_logging_info = mocker.patch("logging.info")
    mock_publisher_notify = mocker.patch.object(generator.publisher, "notify")

    generator.generate()

    mock_logging_info.assert_called_once_with("No content to write. File not created.")
    mock_publisher_notify.assert_called_with(ProcessingEvent.PROCESSING_COMPLETE, None)


def test_streaming_output_generator_handle_actual_streaming_exception(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _handle_actual_streaming handles exceptions during file writing."""
    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    mocker.patch(
        "src.output_generator.read_file_content", return_value=["some content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    # Mock the open function to raise an exception when writing to the temporary file
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    mock_open.return_value.__enter__.return_value.write.side_effect = OSError(
        "Disk full"
    )

    with pytest.raises(IOError, match="Disk full"):
        generator._handle_actual_streaming()

    # Ensure the temporary file is unlinked
    mock_open.assert_called_with(tmp_path / "output.tmp", "w", encoding="utf-8")
    assert (
        tmp_path / "output.tmp"
    ).exists() is False  # Should be unlinked by the except block


def test_streaming_output_generator_dry_run_output_path_handling(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _handle_dry_run_streaming writes to dry_run_output_path if set."""
    dry_run_output_file = tmp_path / "dry_run_output.txt"
    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        dry_run=True,
        dry_run_output=str(dry_run_output_file),
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    mocker.patch(
        "src.output_generator.read_file_content", return_value=["some content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)
    mocker.patch(
        "logging.info"
    )  # Mock logging.info to prevent console output during test

    generator._handle_dry_run_streaming()

    assert dry_run_output_file.exists()
    assert "some content" in dry_run_output_file.read_text()


def test_streaming_output_generator_dry_run_output_path_exception(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path, mocker
):
    """Test that _handle_dry_run_streaming handles exceptions when writing to dry_run_output_path."""
    dry_run_output_file = tmp_path / "dry_run_output.txt"
    context = GeneratorContext(
        files_to_process=mock_files_to_process,
        root_path=mock_root_path,
        formatter=mock_formatter,
        publisher=MagicMock(),
        output_path=tmp_path / "output.txt",
        dry_run=True,
        dry_run_output=str(dry_run_output_file),
        ui=MagicMock(),
        token_counter_observer=MagicMock(),
        line_counter_observer=MagicMock(),
    )
    generator = StreamingOutputGenerator(context)

    mocker.patch(
        "src.output_generator.read_file_content", return_value=["some content"]
    )
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)
    mocker.patch(
        "logging.info"
    )  # Mock logging.info to prevent console output during test
    mock_logging_error = mocker.patch("logging.error")

    # Mock the open function to raise an exception when writing to the dry_run_output_path
    _ = mocker.patch("builtins.open", side_effect=OSError("Permission denied"))

    generator._handle_dry_run_streaming()

    mock_logging_error.assert_called_once()
    assert "Error writing dry run output to" in mock_logging_error.call_args[0][0]
    assert "Permission denied" in str(mock_logging_error.call_args[0][0])


def test_streaming_output_generator_dry_run_output_path(
    mock_files_to_process, mock_root_path, mock_formatter, tmp_path
):
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


def test_streaming_output_generator_empty_non_binary_file(
    mock_root_path, mock_formatter, tmp_path, mocker
):
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

    mocker.patch("src.output_generator.read_file_content", return_value=[])
    mocker.patch("src.output_generator.is_likely_binary", return_value=False)

    generator._process_file_streaming(empty_file)

    mock_ui.update.assert_called_once_with(
        str(empty_file.relative_to(mock_root_path)),
        skipped=True,
        tokens=mock_token_counter.total_tokens,
        lines=mock_line_counter.total_lines,
    )
