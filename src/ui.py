# src/ui.py
from __future__ import annotations
import logging
import shutil
import sys
import time
from typing import Any, Optional

from tqdm import tqdm

try:
    import psutil
except ImportError:
    psutil = None


class LiveUI:
    """A combined live + static text UI for CodeCombiner."""

    def __init__(self, total_files: int = 0, title: str = "CODE COMBINER", version: str = "v0.1.0"):
        self.total_files = total_files
        self.title = title
        self.version = version
        self.start_time: float | None = None
        self._progress_bar: Optional[tqdm] = None
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
        width = shutil.get_terminal_size((80, 20)).columns
        bar = "═" * (width - 2)
        print(f"╔{bar}╗")
        print(f"║{self.title.center(width - 2)}║")
        print(f"║{self.version.center(width - 2)}║")
        print(f"╚{bar}╝\n")

    def print_config(self):
        width = shutil.get_terminal_size((80, 20)).columns
        separator = "─" * width
        label_width = 18

        print(f"{'Input Directory':<{label_width}} : {self.directory}")
        print(f"{'Output File':<{label_width}} : {self.output_file}")
        print(f"{'Format':<{label_width}} : {self.format}")
        print(f"{'Include Hidden':<{label_width}} : {'yes' if self.include_hidden else 'no'}")
        print(f"{'Use .gitignore':<{label_width}} : {'yes' if self.use_gitignore else 'no'}")
        print(f"{'Count Tokens':<{label_width}} : {'yes' if self.count_tokens else 'no'}")
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
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]"
            )
        elif self.verbose:
            print(f"Processing {self.total_files} files...")

    def update(self, filename: str, skipped: bool = False, tokens: Optional[int] = None):
        """Update progress line-by-line."""
        self.processed += 0 if skipped else 1
        self.skipped += 1 if skipped else 0
        if tokens is not None:
            self.tokens = tokens
        if psutil:
            proc = psutil.Process()
            self.memory_mb = proc.memory_info().rss / (1024 * 1024)
        if self._progress_bar:
            self._progress_bar.update(1)
            self._progress_bar.set_postfix({
                "file": filename,
                "mem": f"{self.memory_mb:.0f} MB",
                "tokens": f"{self.tokens:,}"
            })
        elif self.verbose:
            print(f"Processed: {filename}")

        if not skipped:
            self.included_files.append(filename)

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
        label_width = 25 # Increased label width for summary

        if self.list_files and self.included_files:
            print(f"\n{separator}")
            print("Included Files:")
            for f in sorted(self.included_files):
                print(f"  - {f}")

        print(f"\n{separator}")
        print("Summary:")
        print(f"  {'Total files processed':<{label_width}} : {self.processed}")
        print(f"  {'Skipped (binary)':<{label_width}} : {self.skipped}")
        print(f"  {'Output file':<{label_width}} : {self.output_file}")
        if self.count_tokens:
            print(f"  {'Token count':<{label_width}} : {self.tokens:,}")
        if psutil:
            print(f"  {'Peak memory usage':<{label_width}} : {self.memory_mb:.0f} MB")
        print(f"  {'Duration':<{label_width}} : {duration:.1f}s")

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