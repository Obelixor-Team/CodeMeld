# Copyright (c) 2025 skum

"""Monitors system memory usage and raises an error if a threshold is exceeded."""

from __future__ import annotations

import logging
import tracemalloc
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
            return

        process = psutil.Process()
        current_memory_rss_mb = process.memory_info().rss / (1024 * 1024)

        if current_memory_rss_mb > self.max_memory_mb:
            logging.warning(
                f"High memory usage detected (RSS: {current_memory_rss_mb:.1f}MB). "
                f"Threshold: {self.max_memory_mb}MB. Falling back to streaming."
            )
            raise MemoryThresholdExceededError(
                f"Memory usage exceeded {self.max_memory_mb}MB. "
                f"Falling back to streaming output."
            )


class TracemallocMemoryMonitor(MemoryMonitor):
    """Memory monitor using tracemalloc for more precise Python-specific tracking."""

    def __init__(
        self,
        max_memory_mb: int | None = None,
        count_tokens: bool = True,
        safety_margin: float = 0.1,
    ):
        """Initialize the TracemallocMemoryMonitor."""
        super().__init__(max_memory_mb, count_tokens)
        self.safety_margin = safety_margin
        if self.max_memory_mb is not None and self.max_memory_mb > 0:
            if not tracemalloc.is_tracing():
                tracemalloc.start()

    def check_memory_usage(self) -> None:
        """Check memory usage against threshold; raise error if exceeded."""
        if self.max_memory_mb is None or self.max_memory_mb <= 0:
            return

        current_size, peak_size = tracemalloc.get_traced_memory()
        current_memory_mb = current_size / (1024 * 1024)

        threshold = self.max_memory_mb * (1 - self.safety_margin)

        if current_memory_mb > threshold:
            peak_memory_mb = peak_size / (1024 * 1024)
            logging.warning(
                "High Python memory usage detected (Current: %.1fMB, Peak: %.1fMB). "
                "Threshold: %.1fMB (Safety Margin: %.0f%%). Falling back to streaming.",
                current_memory_mb,
                peak_memory_mb,
                threshold,
                self.safety_margin * 100,
            )
            raise MemoryThresholdExceededError(
                f"Python memory usage exceeded {threshold:.1f}MB. "
                f"Falling back to streaming output."
            )

    def __del__(self) -> None:
        """Stop tracemalloc if it's running."""
        if tracemalloc.is_tracing():
            tracemalloc.stop()
