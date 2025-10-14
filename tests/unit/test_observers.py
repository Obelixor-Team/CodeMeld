# Copyright (c) 2025 skum

import logging
import importlib
from unittest.mock import MagicMock, patch
from typing import Any

import pytest

import src.observers
from src.observers import (
    FileContentProcessedData,
    FileProcessedData,
    LineCounterObserver,
    Observer,
    ProgressBarObserver,
    ProcessingEvent,
    ProcessingStartedData,
    Publisher,
    TokenCounterObserver,
)


class MockObserver(Observer[Any]):
    def __init__(self):
        self.update_called = False
        self.event = None
        self.data = None

    def update(self, event: ProcessingEvent, data: Any):
        self.update_called = True
        self.event = event
        self.data = data


def test_publisher_subscribe_and_notify():
    publisher = Publisher()
    observer = MockObserver()
    publisher.subscribe(observer)
    publisher.notify(ProcessingEvent.PROCESSING_STARTED, ProcessingStartedData(total_files=10))
    assert observer.update_called
    assert observer.event == ProcessingEvent.PROCESSING_STARTED
    assert observer.data == ProcessingStartedData(total_files=10)


def test_publisher_unsubscribe():
    publisher = Publisher()
    observer = MockObserver()
    publisher.subscribe(observer)
    publisher.unsubscribe(observer)
    publisher.notify("test_event", "test_data")
    assert not observer.update_called


def test_publisher_notify_multiple_observers():
    publisher = Publisher()
    observer1 = MockObserver()
    observer2 = MockObserver()
    publisher.subscribe(observer1)
    publisher.subscribe(observer2)
    publisher.notify("test_event", "test_data")
    assert observer1.update_called
    assert observer2.update_called



def test_line_counter_observer():
    observer = LineCounterObserver()
    observer.update(ProcessingEvent.FILE_CONTENT_PROCESSED, FileContentProcessedData(content_chunk="line 1\nline 2\nline 3"))
    assert observer.total_lines == 3

    observer.update(ProcessingEvent.FILE_CONTENT_PROCESSED, FileContentProcessedData(content_chunk="line 4\nline 5"))
    assert observer.total_lines == 5





    @patch("src.observers.tqdm")
    @patch("sys.stdout.isatty", return_value=True)
    def test_progress_bar_observer(mock_isatty, mock_tqdm):
        mock_progress_bar = MagicMock()
        mock_tqdm.return_value = mock_progress_bar
        with ProgressBarObserver(total_files=10, description="Processing") as observer:
            observer.update(ProcessingEvent.FILE_PROCESSED, FileProcessedData(path="test_file"))
            mock_progress_bar.update.assert_called_with(1)
            mock_progress_bar.write.assert_called_with("Processed: test_file")
        mock_progress_bar.close.assert_called()




def test_token_counter_observer():




    # Mock tiktoken in sys.modules




    with patch.dict('sys.modules', {'tiktoken': MagicMock()}) as mock_sys_modules:




        mock_tiktoken = mock_sys_modules['tiktoken']




        mock_encoding = MagicMock()




        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # Simulate 5 tokens




        mock_tiktoken.get_encoding.return_value = mock_encoding









        # Create an observer instance after mocking




        observer = TokenCounterObserver()









        observer.update(ProcessingEvent.FILE_CONTENT_PROCESSED, FileContentProcessedData(content_chunk="some text"))









        # Assert that get_encoding was called with the expected encoding type




        mock_tiktoken.get_encoding.assert_called_once_with("cl100k_base")




        # Assert that encode was called with the correct text




        mock_encoding.encode.assert_called_once_with("some text")




        assert observer.total_tokens == 5



















def test_token_counter_observer_no_tiktoken(caplog):




    # Temporarily remove tiktoken from sys.modules to simulate it not being installed




    with patch.dict('sys.modules', {'tiktoken': None}):




        # Reload src.observers to ensure the lazy import logic is re-evaluated




        importlib.reload(src.observers)




        with caplog.at_level(logging.WARNING):




            observer = TokenCounterObserver()




            assert observer.tiktoken_module is None




            assert caplog.records[0].message == "tiktoken not found. Token counting will be skipped."







        # Ensure update does nothing if tiktoken_module is None




        initial_tokens = observer.total_tokens




        observer.update(ProcessingEvent.FILE_CONTENT_PROCESSED, FileContentProcessedData(content_chunk="some text"))




        assert observer.total_tokens == initial_tokens














def test_publisher_unsubscribe_not_subscribed():














    publisher = Publisher()














    observer = MockObserver()














    # Should not raise an error









    publisher.unsubscribe(observer)
























def test_observer_failure_does_not_stop_others(caplog):














    publisher = Publisher()














    failing_observer = MagicMock(spec=Observer)














    failing_observer.update.side_effect = Exception("Test Exception")














    working_observer = MockObserver()
























    publisher.subscribe(failing_observer)














    publisher.subscribe(working_observer)
























    with caplog.at_level(logging.ERROR):














        publisher.notify(ProcessingEvent.PROCESSING_STARTED, ProcessingStartedData(total_files=5))














        assert "failed: Test Exception" in caplog.text
























def test_token_counter_observer_with_custom_encoding():
    custom_encoding_model = "gpt2"

    # Mock tiktoken in sys.modules
    with patch.dict('sys.modules', {'tiktoken': MagicMock()}) as mock_sys_modules:
        # Reload src.observers to ensure the lazy import logic is re-evaluated
        importlib.reload(src.observers)
        from src.observers import (
            FileContentProcessedData,
            ProcessingEvent,
            TokenCounterObserver,
        )

        mock_tiktoken = mock_sys_modules['tiktoken']
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3]  # Simulate 3 tokens
        mock_tiktoken.get_encoding.return_value = mock_encoding

        # Create an observer instance after mocking
        observer = TokenCounterObserver(token_encoding_model=custom_encoding_model)

        observer.update(
            ProcessingEvent.FILE_CONTENT_PROCESSED,
            FileContentProcessedData(content_chunk="some custom text"),
        )

        # Assert that get_encoding was called with the custom encoding type
        mock_tiktoken.get_encoding.assert_called_once_with(custom_encoding_model)

        # Assert that encode was called with the correct text
        mock_encoding.encode.assert_called_once_with("some custom text")

        assert observer.total_tokens == 3