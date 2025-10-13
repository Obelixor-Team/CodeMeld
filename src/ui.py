"""User interface for the Code Combiner, providing live progress and a final summary."""

from __future__ import annotations

import logging
import shutil
import sys
import time
from typing import Any

from tqdm import tqdm

_psutil_module: Any | None
try:
    import psutil

    _psutil_module = psutil
except ImportError:
    _psutil_module = None


class LiveUI:
    """A combined live + static text UI for CodeCombiner."""

    def __init__(
        self,
        total_files: int = 0,
        title: str = "CODE COMBINER",
        version: str = "v0.1.0",
    ):
        """Initialize the LiveUI with default values."""
        self.total_files = total_files
        self.title = title
        self.version = version
        self.start_time: float | None = None
        self._progress_bar: tqdm | None = None
        self.processed = 0
        self.skipped = 0
        self.tokens = 0
        self.memory_mb = 0.0
        self.output_file: str = ""
        self.use_gitignore = True
        self.include_hidden = False
        self.count_tokens = True
        self.format = "text"
        self.directory = "."
        self.verbose = False
        self.included_files: list[str] = []
        self.list_files: bool = False

    # ───────────────────────────────
    # Header & Config Display
    # ───────────────────────────────
    def print_header(self):
        """Print the header of the UI, including title and version."""
        width = shutil.get_terminal_size((80, 20)).columns
        bar = "═" * (width - 2)
        print(f"╔{bar}╗")
        print(f"║{self.title.center(width - 2)}║")
        print(f"║{self.version.center(width - 2)}║")
        print(f"╚{bar}╝\n")

    def print_config(self):
        """Print the current configuration settings."""
        width = shutil.get_terminal_size((80, 20)).columns
        separator = "─" * width
        label_width = 18

        label_width = 18

        labels = {
            "Input Directory": self.directory,
            "Output File": self.output_file,
            "Format": self.format,
            "Include Hidden": "yes" if self.include_hidden else "no",
            "Use .gitignore": "yes" if self.use_gitignore else "no",
            "Count Tokens": "yes" if self.count_tokens else "no",
        }

        for label, value in labels.items():
            print(f"{label:<{label_width}} : {value}")
        print(f"\n{separator}")
        print("Scanning files...")

    # ───────────────────────────────
    # Live Progress Handling
    # ───────────────────────────────
    def start(self):
        """Start live progress display."""
        self.start_time = time.time()
        if sys.stdout.isatty():
            self._progress_bar = tqdm(
                total=self.total_files,
                desc="Processing files",
                ncols=shutil.get_terminal_size((80, 20)).columns,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
            )
        elif self.verbose:
            print(f"Processing {self.total_files} files...")

    def update(self, filename: str, skipped: bool = False, tokens: int | None = None):
        """Update progress line-by-line."""
        self.processed += 0 if skipped else 1
        self.skipped += 1 if skipped else 0
        if tokens is not None:
            self.tokens = tokens
        if _psutil_module:
            proc = _psutil_module.Process()
            self.memory_mb = proc.memory_info().rss / (1024 * 1024)
        if self._progress_bar:
            self._progress_bar.update(1)
            self._progress_bar.set_postfix(
                {
                    "file": filename,
                    "mem": f"{self.memory_mb:.0f} MB",
                    "tokens": f"{self.tokens:,}",
                }
            )
        elif self.verbose:
            print(f"Processed: {filename}")

        if not skipped:
            self.included_files.append(filename)
            logging.debug(
                f"LiveUI.update: Added {filename}. Count: {len(self.included_files)}"
            )

    # ───────────────────────────────
    # Final Summary
    # ───────────────────────────────
    def finish(self):
        """Close the live view and show static summary."""
        if self._progress_bar:
            self._progress_bar.close()
        duration = time.time() - (self.start_time or time.time())

        width = shutil.get_terminal_size((80, 20)).columns
        separator = "─" * width
        label_width = 25  # Increased label width for summary

        logging.debug(
            f"LiveUI.finish: list_files={self.list_files}, count={len(self.included_files)}"
        )

        if self.list_files and self.included_files:
            print(f"\n{separator}")
            print("Included Files:")
            for f in sorted(self.included_files):
                print(f"  - {f}")

        summary_items = {
            "Total files processed": self.processed,
            "Skipped (binary)": self.skipped,
            "Output file": self.output_file,
        }
        if self.count_tokens:
            summary_items["Token count"] = f"{self.tokens:,}"
        if _psutil_module:
            summary_items["Peak memory usage"] = f"{self.memory_mb:.0f} MB"
        summary_items["Duration"] = f"{duration:.1f}s"

        print(f"\n{separator}")
        print("Summary:")
        for label, value in summary_items.items():
            print(f"  {label:<{label_width}} : {value}")

        print(f"{separator}")
        print("All done!\n")

    # ───────────────────────────────
    # Utility: Apply from Config
    # ───────────────────────────────
    def apply_config(self, config):
        """Apply CodeCombiner config to the UI display."""
        self.directory = str(config.directory_path)
        self.output_file = config.output
        self.format = config.format
        self.include_hidden = config.include_hidden
        self.use_gitignore = config.use_gitignore
        self.count_tokens = config.count_tokens
        self.verbose = config.verbose
        self.list_files = config.list_files
