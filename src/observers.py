"""Defines the observer pattern for progress reporting and token counting."""

import logging
from abc import ABC, abstractmethod
from types import ModuleType
from typing import Any

from tqdm import tqdm


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

    def unsubscribe(self, observer: Observer) -> None:
        """Unsubscribe an observer from the publisher."""
        try:
            self.observers.remove(observer)
        except ValueError:
            pass

    def notify(self, event: str, data: Any) -> None:
        """
        Notify all subscribed observers of an event.

        Args:
            event: The event type (e.g., 'file_processed', 'processing_complete')
            data: Event-specific data to pass to observers

        Note:
            Failed observers are logged but don't stop other observers.

        """
        for observer in self.observers[:]:  # Copy list to allow modifications
            try:
                observer.update(event, data)
            except Exception as e:
                logging.error(f"Observer {observer.__class__.__name__} failed: {e}")


class ProgressBarObserver(Observer):
    """Observer for updating the progress bar."""

    def __init__(self, total_files: int, description: str):
        """Initialize the ProgressBarObserver."""
        self.progress_bar = tqdm(total=total_files, desc=description)

    def update(self, event: str, data: Any):
        """Update the progress bar based on the event."""
        if event == "file_processed":
            self.progress_bar.update(1)
            self.progress_bar.write(f"Processed: {data}")
        elif event == "processing_complete":
            self.close()

    def close(self):
        """Clean up the progress bar."""
        if hasattr(self, "progress_bar") and self.progress_bar:
            self.progress_bar.close()

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context related to this object."""
        self.close()
        return False


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

    def __init__(self, token_encoding_model: str = "cl100k_base"):
        """Initialize the TokenCounterObserver."""
        self.total_tokens = 0
        self.token_encoding_model = token_encoding_model
        try:
            import tiktoken

            self.tiktoken_module: ModuleType | None = tiktoken
        except ImportError:
            self.tiktoken_module = None
            logging.warning("tiktoken not found. Token counting will be skipped.")

    def update(self, event: str, data: Any):
        """Count tokens based on the event."""
        if event == "output_generated" and self.tiktoken_module is not None:
            try:
                encoding = self.tiktoken_module.get_encoding(self.token_encoding_model)
                tokens: list[int] = encoding.encode(data)
                self.total_tokens = len(tokens)
                print(f"Total tokens in formatted output: {self.total_tokens}")
            except ValueError as e:
                logging.error(f"Error counting tokens: {e}")
