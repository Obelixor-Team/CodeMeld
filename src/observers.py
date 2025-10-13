# Copyright (c) 2025 skum

"""Defines the observer pattern for progress reporting and token counting."""

from __future__ import annotations

import logging
import sys
import time
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

    def __init__(self, total_files: int = 0):
        """Initialize the Publisher."""
        self.observers: list[Observer] = []
        self.total_files = total_files

    def __enter__(self):
        """Enter runtime context; notify observers processing started."""
        self.notify("processing_started", {"total_files": self.total_files})
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and notify observers that processing is complete."""
        self.notify("processing_complete", None)
        return False

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
        self.progress_bar: tqdm | None
        if sys.stdout.isatty():
            self.progress_bar = tqdm(total=total_files, desc=description)
        else:
            self.progress_bar = None
            logging.info(f"Progress: {description} - 0/{total_files}")

    def update(self, event: str, data: Any):
        """Update the progress bar based on the event."""
        if event == "file_processed":
            if self.progress_bar:
                self.progress_bar.update(1)
                self.progress_bar.write(f"Processed: {data}")
            else:
                logging.info(f"Processed: {data}")

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


class TelemetryObserver(Observer):
    """Observer for logging telemetry data like total files processed and time taken."""

    def __init__(self):
        """Initialize the TelemetryObserver."""
        self.start_time: float | None = None
        self.total_files_processed: int = 0

    def update(self, event: str, data: Any):
        """Receive update from subject and log telemetry."""
        if event == "processing_started":
            self.start_time = time.time()
            self.total_files_processed = data.get("total_files", 0)
        elif event == "processing_complete" and self.start_time is not None:
            pass


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
        if self.tiktoken_module is None:
            return

        if event == "file_content_processed":
            content = data
            try:
                encoding = self.tiktoken_module.get_encoding(self.token_encoding_model)
                tokens: list[int] = encoding.encode(content)
                self.total_tokens += len(tokens)
            except ValueError as e:
                logging.error(f"Error counting tokens for file content: {e}")
        elif event == "output_generated":
            # This event is now redundant for total_tokens, but can be used for final validation if needed.
            pass
