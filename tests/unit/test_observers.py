
import logging
import importlib
from unittest.mock import MagicMock, patch

import pytest

import src.observers
from src.observers import (
    LineCounterObserver,
    Observer,
    ProgressBarObserver,
    Publisher,
    TokenCounterObserver,
)


class MockObserver(Observer):
    def __init__(self):
        self.update_called = False
        self.event = None
        self.data = None

    def update(self, event: str, data: any):
        self.update_called = True
        self.event = event
        self.data = data


def test_publisher_subscribe_and_notify():
    publisher = Publisher()
    observer = MockObserver()
    publisher.subscribe(observer)
    publisher.notify("test_event", "test_data")
    assert observer.update_called
    assert observer.event == "test_event"
    assert observer.data == "test_data"


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


    observer.update("output_generated", "line 1\nline 2\nline 3")


    assert observer.total_lines == 3








@patch("src.observers.tqdm")


def test_progress_bar_observer(mock_tqdm):


    mock_progress_bar = MagicMock()


    mock_tqdm.return_value = mock_progress_bar


    observer = ProgressBarObserver(total_files=10, description="Processing")


    observer.update("file_processed", "test_file")


    mock_progress_bar.update.assert_called_with(1)


    mock_progress_bar.write.assert_called_with("Processed: test_file")


    observer.update("processing_complete", None)


    mock_progress_bar.close.assert_called()








@patch("src.observers.tiktoken")


def test_token_counter_observer(mock_tiktoken):


    mock_encoding = MagicMock()


    mock_encoding.encode.return_value = [1, 2, 3, 4, 5]


    mock_tiktoken.get_encoding.return_value = mock_encoding


    observer = TokenCounterObserver()


    observer.update("output_generated", "some text")


    assert observer.total_tokens == 5








def test_token_counter_observer_no_tiktoken(caplog):








    with patch.dict("sys.modules", {"tiktoken": None}):








        with caplog.at_level(logging.WARNING):








            importlib.reload(src.observers)








            assert "tiktoken not found" in caplog.text








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


        publisher.notify("test_event", "test_data")


        assert "failed: Test Exception" in caplog.text





    assert working_observer.update_called



