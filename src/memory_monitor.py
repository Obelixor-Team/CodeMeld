# Copyright (c) 2025 skum

"""Monitors system memory usage and raises an error if a threshold is exceeded."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import psutil

from .config import MemoryThresholdExceededError


class MemoryMonitor(ABC):
    """Abstract base class for memory monitoring."""

    def __init__(self, max_memory_mb: int | None = None, count_tokens: bool = True):
        """Initialize the MemoryMonitor."""
        self.max_memory_mb = max_memory_mb
        self.count_tokens = count_tokens

    @abstractmethod
    def check_memory_usage(self) -> None:
        """Check memory usage against threshold; raise error if exceeded."""
        pass


class SystemMemoryMonitor(MemoryMonitor):
    """Concrete implementation of MemoryMonitor using psutil."""

    def check_memory_usage(self) -> None:
        """Check memory usage against threshold; raise error if exceeded."""
        if self.max_memory_mb is None or self.max_memory_mb <= 0:
            return  # No memory limit set

        process = psutil.Process()
        current_memory_rss_mb = process.memory_info().rss / (1024 * 1024)

        if current_memory_rss_mb > self.max_memory_mb:
            logging.warning(
                f"High memory usage detected (RSS: {current_memory_rss_mb:.1f}MB). "
                f"Threshold: {self.max_memory_mb}MB. Falling back to streaming."
            )
            raise MemoryThresholdExceededError(
                f"Memory usage exceeded {self.max_memory_mb}MB. "
                "Falling back to streaming output."
            )
