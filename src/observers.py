# Copyright (c) 2025 skum

"""Defines the observer pattern for progress reporting and token counting."""

from __future__ import annotations

import logging
import sys
import threading
import time
from builtins import BaseException
from enum import Enum, auto
from types import ModuleType, TracebackType
from typing import Any, Literal, Protocol, Self, TypedDict, TypeVar, overload



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

    def __enter__(self) -> Self:
        """Enter runtime context; notify observers processing started."""
        self.notify(
            ProcessingEvent.PROCESSING_STARTED,
            ProcessingStartedData(total_files=self.total_files),
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        """Exit the runtime context and notify observers that processing is complete."""
        self.notify(ProcessingEvent.PROCESSING_COMPLETE, None)
        return False

    def subscribe(self, observer: Observer[Any]) -> None:
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
        self,
        event: Literal[ProcessingEvent.PROCESSING_STARTED],
        data: ProcessingStartedData,
    ) -> None: ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.FILE_PROCESSED],
        data: FileProcessedData,
    ) -> None: ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.FILE_CONTENT_PROCESSED],
        data: FileContentProcessedData,
    ) -> None: ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.PROCESSING_COMPLETE],
        data: None,
    ) -> None: ...

    @overload
    def notify(
        self,
        event: Literal[ProcessingEvent.OUTPUT_GENERATED],
        data: OutputGeneratedData,
    ) -> None: ...

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


class LineCounterObserver(Observer[FileContentProcessedData]):
    """Observer for counting lines."""

    def __init__(self) -> None:
        """Initialize the LineCounterObserver."""
        self._total_lines: int = 0
        self._lock = threading.Lock()

    @property
    def total_lines(self) -> int:
        """Return the total number of lines counted."""
        return self._total_lines

    def update(self, event: ProcessingEvent, data: FileContentProcessedData) -> None:
        """Count lines based on the event."""
        if event == ProcessingEvent.FILE_CONTENT_PROCESSED:
            with self._lock:
                chunk = data["content_chunk"]
                self._total_lines += chunk.count("\n") + 1 if chunk else 0


class TelemetryObserver(Observer[ProcessingStartedData | None]):
    """Observer for logging telemetry data like total files processed and time taken."""

    def __init__(self) -> None:
        """Initialize the TelemetryObserver."""
        self.start_time: float | None = None
        self.total_files_processed: int = 0

    def update(
        self, event: ProcessingEvent, data: ProcessingStartedData | None
    ) -> None:
        """Receive update from subject and log telemetry."""
        if event == ProcessingEvent.PROCESSING_STARTED:
            self.start_time = time.time()
            if data:
                self.total_files_processed = data.get("total_files", 0)
        elif (
            event == ProcessingEvent.PROCESSING_COMPLETE and self.start_time is not None
        ):
            duration = time.time() - self.start_time
            logging.info(f"Processing complete. Duration: {duration:.2f}s")


class TokenCounterObserver(Observer[FileContentProcessedData]):
    """Observer for counting tokens."""

    def __init__(self, token_encoding_model: str = "cl100k_base") -> None:
        """Initialize the TokenCounterObserver."""
        self.total_tokens = 0
        self.token_encoding_model = token_encoding_model
        self._lock = threading.Lock()
        self._tiktoken_module: ModuleType | None = None

    @property
    def tiktoken_module(self) -> ModuleType | None:
        """Lazily import and return the tiktoken module."""
        if self._tiktoken_module is None:
            try:
                import tiktoken

                self._tiktoken_module = tiktoken
            except ImportError:
                logging.warning("tiktoken not found. Token counting will be skipped.")
        return self._tiktoken_module

    def update(self, event: ProcessingEvent, data: FileContentProcessedData) -> None:
        """Count tokens based on the event."""
        if self.tiktoken_module is None:
            return

        if event == ProcessingEvent.FILE_CONTENT_PROCESSED:
            content = data["content_chunk"]
            try:
                encoding = self.tiktoken_module.get_encoding(self.token_encoding_model)
                tokens: list[int] = encoding.encode(content)
                with self._lock:
                    self.total_tokens += len(tokens)
            except ValueError as e:
                logging.error(f"Error counting tokens for file content: {e}")
