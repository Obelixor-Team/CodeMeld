# Copyright (c) 2025 skum

"""Defines the observer pattern for progress reporting and token counting."""

from __future__ import annotations

import logging
import sys
import time
from enum import Enum, auto
from types import ModuleType
from typing import Any, Literal, Protocol, TypedDict, TypeVar, overload

from tqdm import tqdm


class ProcessingEvent(Enum):
    """Enum for different processing events."""

    PROCESSING_STARTED = auto()
    FILE_PROCESSED = auto()
    FILE_CONTENT_PROCESSED = auto()
    PROCESSING_COMPLETE = auto()
    OUTPUT_GENERATED = auto()


class ProcessingStartedData(TypedDict):
    """Data for the processing started event."""

    total_files: int


class FileProcessedData(TypedDict):
    """Data for a file processed event."""

    path: str


class FileContentProcessedData(TypedDict):
    """Data for file content processed event."""

    content_chunk: str


class OutputGeneratedData(TypedDict):
    """Data for the output generated event."""

    output_path: str
    total_tokens: int | None
    total_lines: int | None


_T = TypeVar("_T", contravariant=True)


class Observer(Protocol[_T]):
    """Protocol for observers, generic over the event data type."""

    def update(self, event: ProcessingEvent, data: _T) -> None:
        """Receive update from subject."""
        ...


class Publisher:
    """Publisher class for the observer pattern."""

    def __init__(self, total_files: int = 0):
        """Initialize the Publisher."""
        self.observers: list[Observer[Any]] = []
        self.total_files = total_files

    def __enter__(self):
        """Enter runtime context; notify observers processing started."""
        self.notify(
            ProcessingEvent.PROCESSING_STARTED,
            ProcessingStartedData(total_files=self.total_files),
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context and notify observers that processing is complete."""
        self.notify(ProcessingEvent.PROCESSING_COMPLETE, None)
        return False

    def subscribe(self, observer: Observer[Any]):
        """Subscribe an observer to the publisher."""
        self.observers.append(observer)

    def unsubscribe(self, observer: Observer[Any]) -> None:
        """Unsubscribe an observer from the publisher."""
        try:
            self.observers.remove(observer)
        except ValueError:
            pass

    @overload
    def notify(
        self, event: Literal[ProcessingEvent.PROCESSING_STARTED], data: ProcessingStartedData
    ) -> None:
        ...

    @overload
    def notify(
        self, event: Literal[ProcessingEvent.FILE_PROCESSED], data: FileProcessedData
    ) -> None:
        ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.FILE_CONTENT_PROCESSED],
        data: FileContentProcessedData,
    ) -> None:
        ...

    @overload
    def notify(
        self, event: Literal[ProcessingEvent.PROCESSING_COMPLETE], data: None
    ) -> None:
        ...

    @overload
    def notify(
        self, event: Literal[ProcessingEvent.OUTPUT_GENERATED], data: OutputGeneratedData
    ) -> None:
        ...

    def notify(self, event: ProcessingEvent, data: Any) -> None:
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


class ProgressBarObserver(Observer[FileProcessedData]):
    """Observer for updating the progress bar."""

    def __init__(self, total_files: int, description: str):
        """Initialize the ProgressBarObserver."""
        self.progress_bar: tqdm | None
        if sys.stdout.isatty():
            self.progress_bar = tqdm(total=total_files, desc=description)
        else:
            self.progress_bar = None
            logging.info(f"Progress: {description} - 0/{total_files}")

    def update(self, event: ProcessingEvent, data: FileProcessedData):
        """Update the progress bar based on the event."""
        if event == ProcessingEvent.FILE_PROCESSED:
            if self.progress_bar:
                self.progress_bar.update(1)
                self.progress_bar.write(f"Processed: {data['path']}")
            else:
                logging.info(f"Processed: {data['path']}")

    def close(self):
        """Clean up the progress bar."""
        if self.progress_bar is not None:
            self.progress_bar.close()

    def __enter__(self):
        """Enter the runtime context related to this object."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the runtime context related to this object."""
        self.close()
        return False


class LineCounterObserver(Observer[FileContentProcessedData]):
    """Observer for counting lines."""

    def __init__(self):
        """Initialize the LineCounterObserver."""
        self._total_lines: int = 0

    @property
    def total_lines(self) -> int:
        """Return the total number of lines counted."""
        return self._total_lines

    def update(self, event: ProcessingEvent, data: FileContentProcessedData):
        """Count lines based on the event."""
        if event == ProcessingEvent.FILE_CONTENT_PROCESSED:
            self._total_lines += (
                data["content_chunk"].count("\n") + 1 if data["content_chunk"] else 0
            )


class TelemetryObserver(Observer[ProcessingStartedData | None]):
    """Observer for logging telemetry data like total files processed and time taken."""

    def __init__(self):
        """Initialize the TelemetryObserver."""
        self.start_time: float | None = None
        self.total_files_processed: int = 0

    def update(self, event: ProcessingEvent, data: ProcessingStartedData | None):
        """Receive update from subject and log telemetry."""
        if event == ProcessingEvent.PROCESSING_STARTED:
            self.start_time = time.time()
            if data:
                self.total_files_processed = data.get("total_files", 0)
        elif (
            event == ProcessingEvent.PROCESSING_COMPLETE and self.start_time is not None
        ):
            # Telemetry data can be logged here if needed, but for now, it's intentionally empty.
            # For example: logging.info(f"Processing complete. Duration: {time.time() - self.start_time:.2f}s")
            pass


class TokenCounterObserver(Observer[FileContentProcessedData]):
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

    def update(self, event: ProcessingEvent, data: FileContentProcessedData):
        """Count tokens based on the event."""
        if self.tiktoken_module is None:
            return

        if event == ProcessingEvent.FILE_CONTENT_PROCESSED:
            content = data["content_chunk"]
            try:
                encoding = self.tiktoken_module.get_encoding(self.token_encoding_model)
                tokens: list[int] = encoding.encode(content)
                self.total_tokens += len(tokens)
            except ValueError as e:
                logging.error(f"Error counting tokens for file content: {e}")
        elif event == ProcessingEvent.OUTPUT_GENERATED:
            # This event is now redundant for total_tokens, but can be used for
            # final validation if needed.
            pass
