"""
This module defines the observer pattern for progress reporting and token counting.
"""

from abc import ABC, abstractmethod
import logging
from types import ModuleType

class Observer(ABC):
    """Abstract base class for observers."""

    @abstractmethod
    def update(self, event: str, data: any):
        pass

class Publisher:
    """Publisher class for the observer pattern."""

    def __init__(self):
        self.observers: list[Observer] = []

    def subscribe(self, observer: Observer):
        self.observers.append(observer)

    def unsubscribe(self, observer: Observer):
        self.observers.remove(observer)

    def notify(self, event: str, data: any):
        for observer in self.observers:
            observer.update(event, data)

class ProgressBarObserver(Observer):
    """Observer for updating the progress bar."""

    def __init__(self, total_files: int, description: str):
        from tqdm import tqdm
        self.progress_bar = tqdm(total=total_files, desc=description)

    def update(self, event: str, data: any):
        if event == "file_processed":
            self.progress_bar.update(1)
            logging.info(f"Processed: {data}")
        elif event == "processing_complete":
            self.progress_bar.close()

class TokenCounterObserver(Observer):
    """Observer for counting tokens."""

    def __init__(self):
        self.total_tokens = 0
        self.tiktoken_module: ModuleType | None = None
        try:
            import tiktoken
            self.tiktoken_module = tiktoken
        except ImportError:
            logging.warning("tiktoken not found. Token counting will be skipped.")

    def update(self, event: str, data: any):
        if event == "output_generated" and self.tiktoken_module is not None:
            try:
                encoding = self.tiktoken_module.get_encoding("cl100k_base")
                tokens: list[int] = encoding.encode(data)
                self.total_tokens = len(tokens)
                logging.info(f"Total tokens in formatted output: {self.total_tokens}")
            except ValueError as e:
                logging.error(f"Error counting tokens: {e}")
