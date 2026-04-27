import logging
import sys
from unittest.mock import patch

import pytest

from src.observers import (
    FileProcessedData,
    LineCounterObserver,
    ProcessingEvent,
    TelemetryObserver,
    TokenCounterObserver,
)


@pytest.fixture
def mock_file_processed_data():
    return FileProcessedData(path="test/file.py")


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
    with patch.dict(sys.modules, {"tiktoken": None}):
        # Simulate tiktoken not being importable
        with caplog.at_level(logging.WARNING):
            observer = TokenCounterObserver()
            assert observer.tiktoken_module is None
            assert "tiktoken not found. Token counting will be skipped." in caplog.text
            # Ensure update does nothing if tiktoken_module is None
            observer.update(
                ProcessingEvent.FILE_CONTENT_PROCESSED,
                {"content_chunk": "some content"},
            )
