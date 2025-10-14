# Copyright (c) 2025 skum

"""Defines the context object for output generators."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .formatters import OutputFormatter
    from .memory_monitor import MemoryMonitor
    from .observers import LineCounterObserver, Publisher, TokenCounterObserver
    from .ui import LiveUI


@dataclass
class GeneratorContext:
    """A dataclass to hold the context for output generators."""

    files_to_process: list[Path]
    root_path: Path
    formatter: OutputFormatter
    publisher: Publisher
    output_path: Path
    ui: LiveUI
    token_counter_observer: TokenCounterObserver | None
    line_counter_observer: LineCounterObserver | None
    memory_monitor: MemoryMonitor | None = None  # For InMemory
    dry_run: bool = False  # For Streaming
    dry_run_output: str | None = None  # For Streaming
