import pytest
import logging
from unittest.mock import MagicMock, patch, PropertyMock
import sys

from src.observers import ProgressBarObserver, ProcessingEvent, FileProcessedData, TokenCounterObserver, TelemetryObserver, LineCounterObserver, FileContentProcessedData

@pytest.fixture
def mock_file_processed_data():
    return FileProcessedData(path="test/file.py")

def test_progressbar_observer_non_tty_init(caplog):
    """Test ProgressBarObserver initialization in a non-TTY environment."""
    with patch.object(sys.stdout, 'isatty', return_value=False):
        with caplog.at_level(logging.INFO):
            observer = ProgressBarObserver(total_files=10, description="Processing")
            assert observer.progress_bar is None
            assert "Progress: Processing - 0/10" in caplog.text



def test_progressbar_observer_context_manager():
    """Test ProgressBarObserver as a context manager."""
    with patch.object(sys.stdout, 'isatty', return_value=True):
        with patch('src.observers.tqdm') as mock_tqdm:
            with ProgressBarObserver(total_files=5, description="Context") as observer:
                mock_tqdm.assert_called_once_with(total=5, desc="Context")
                assert observer.progress_bar is mock_tqdm.return_value
            mock_tqdm.return_value.close.assert_called_once()

def test_progressbar_observer_context_manager_with_exception():
    """Test ProgressBarObserver as a context manager with an exception."""
    with patch.object(sys.stdout, 'isatty', return_value=True):
        with patch('src.observers.tqdm') as mock_tqdm:
            with pytest.raises(ValueError):
                with ProgressBarObserver(total_files=5, description="Context"):
                    raise ValueError("Test Exception")
            mock_tqdm.return_value.close.assert_called_once()

def test_progressbar_observer_explicit_enter_exit(caplog):
    """Test ProgressBarObserver's __enter__ and __exit__ methods explicitly."""
    with patch.object(sys.stdout, 'isatty', return_value=False):
        with caplog.at_level(logging.INFO):
            observer = ProgressBarObserver(total_files=5, description="Explicit Enter/Exit")
            observer.__enter__()
            assert "Progress: Explicit Enter/Exit - 0/5" in caplog.text
            observer.__exit__(None, None, None)
            # No additional log for exit in non-TTY, but ensure no errors

def test_line_counter_observer_empty_content_chunk():
    """Test LineCounterObserver with an empty content chunk."""
    observer = LineCounterObserver()
    observer.update(ProcessingEvent.FILE_CONTENT_PROCESSED, {"content_chunk": ""})
    assert observer.total_lines == 0

def test_telemetry_observer_init():
    """Test TelemetryObserver initialization."""
    observer = TelemetryObserver()
    assert observer.start_time is None
    assert observer.total_files_processed == 0

def test_token_counter_observer_tiktoken_import_error(caplog):
    """Test TokenCounterObserver handles ImportError when tiktoken is not found."""
    with patch.dict(sys.modules, {'tiktoken': None}): # Simulate tiktoken not being importable
        with caplog.at_level(logging.WARNING):
            observer = TokenCounterObserver()
            assert observer.tiktoken_module is None
            assert "tiktoken not found. Token counting will be skipped." in caplog.text
            # Ensure update does nothing if tiktoken_module is None
            observer.update(ProcessingEvent.FILE_CONTENT_PROCESSED, {"content_chunk": "some content"})

    def test_token_counter_observer_value_error(caplog):
        """Test TokenCounterObserver handles ValueError during token counting."""
        with patch.object(TokenCounterObserver, 'tiktoken_module', new_callable=PropertyMock) as mock_tiktoken_module_prop:
            mock_tiktoken_instance = MagicMock()
            mock_tiktoken_instance.get_encoding.side_effect = ValueError("Test encoding error")
            mock_tiktoken_module_prop.return_value = mock_tiktoken_instance
            with caplog.at_level(logging.ERROR):
                observer = TokenCounterObserver()
                observer.update(ProcessingEvent.FILE_CONTENT_PROCESSED, FileContentProcessedData(content_chunk="some content"))
                assert "Error counting tokens for file content: Test encoding error" in caplog.text
