"""Defines the observer pattern for progress reporting and token counting."""

import logging
from abc import ABC, abstractmethod
from types import ModuleType
from typing import Any


class Observer(ABC):
    """Abstract base class for observers."""

    @abstractmethod
    def update(self, event: str, data: Any):
        """Receive update from subject."""
        pass


class Publisher:
    """Publisher class for the observer pattern."""

    def __init__(self):
        """Initialize the Publisher."""
        self.observers: list[Observer] = []

    def subscribe(self, observer: Observer):
        """Subscribe an observer to the publisher."""
        self.observers.append(observer)

    def unsubscribe(self, observer: Observer):
        """Unsubscribe an observer from the publisher."""
        self.observers.remove(observer)

    def notify(self, event: str, data: Any):
        """Notify all subscribed observers of an event."""
        for observer in self.observers:
            observer.update(event, data)


class ProgressBarObserver(Observer):
    """Observer for updating the progress bar."""

    def __init__(self, total_files: int, description: str):
        """Initialize the ProgressBarObserver."""
        from tqdm import tqdm

        self.progress_bar = tqdm(total=total_files, desc=description)

    def update(self, event: str, data: Any):
        """Update the progress bar based on the event."""
        if event == "file_processed":
            self.progress_bar.update(1)
            self.progress_bar.write(f"Processed: {data}")
        elif event == "processing_complete":
            self.progress_bar.close()


class LineCounterObserver(Observer):
    """Observer for counting lines."""

    def __init__(self):
        """Initialize the LineCounterObserver."""
        self.total_lines = 0

    def update(self, event: str, data: Any):
        """Count lines based on the event."""
        if event == "output_generated":
            self.total_lines = data.count("\n") + 1 if data else 0
            print(f"Total lines in formatted output: {self.total_lines}")


class TokenCounterObserver(Observer):
    """Observer for counting tokens."""

    def __init__(self):
        """Initialize the TokenCounterObserver."""
        self.total_tokens = 0
        self.tiktoken_module: ModuleType | None = None
        try:
            import tiktoken

            self.tiktoken_module = tiktoken
        except ImportError:
            logging.warning("tiktoken not found. Token counting will be skipped.")

    def update(self, event: str, data: Any):
        """Count tokens based on the event."""
        if event == "output_generated" and self.tiktoken_module is not None:
            try:
                encoding = self.tiktoken_module.get_encoding("cl100k_base")
                tokens: list[int] = encoding.encode(data)
                self.total_tokens = len(tokens)
                print(f"Total tokens in formatted output: {self.total_tokens}")
            except ValueError as e:
                logging.error(f"Error counting tokens: {e}")
