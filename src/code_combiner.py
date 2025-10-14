# Copyright (c) 2025 skum

"""A script to combine code files from a directory into a single output file."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pathspec

from .config import CodeCombinerError, CombinerConfig, MemoryThresholdExceededError
from .config_builder import load_and_merge_config
from .context import GeneratorContext
from .filters import FileFilter, FilterChainBuilder
from .formatters import FormatterFactory
from .memory_monitor import SystemMemoryMonitor
from .observers import (
    LineCounterObserver,
    Publisher,
    TelemetryObserver,
    TokenCounterObserver,
)
from .output_generator import InMemoryOutputGenerator, StreamingOutputGenerator
from .ui import LiveUI


def write_output(
    output_path: Path,
    output_content: str,
    force: bool,
    dry_run: bool = False,
    dry_run_output_path: Path | None = None,
) -> None:
    """Write the combined output content to the specified file."""
    if dry_run:
        logging.info("\n--- Dry Run Output ---")
        print(output_content)
        logging.info("--- End Dry Run Output ---")
        if dry_run_output_path:
            try:
                dry_run_output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dry_run_output_path, "w", encoding="utf-8") as outfile:
                    outfile.write(output_content)
                logging.info(f"Dry run output also written to: {dry_run_output_path}")
            except Exception as e:
                logging.error(
                    f"Error writing dry run output to {dry_run_output_path}: {e}"
                )
        return

    if output_path.exists() and not force:
        import sys

        if sys.stdin.isatty():
            response = input(
                f"Output file '{output_path}' already exists. Overwrite? (y/N): "
            )
            if response.lower() != "y":
                logging.info("Operation cancelled by user. File not overwritten.")
                return
        else:
            logging.info(
                f"Output file '{output_path}' already exists. "
                "Skipping overwrite in non-interactive mode."
            )
            return

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as outfile:
            outfile.write(output_content)
        logging.info(f"\nAll code files have been combined into: {output_path}")
    except Exception as e:
        logging.error(f"Error writing to output file {output_path}: {e}")
        raise


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments for the code combiner script."""
    parser = argparse.ArgumentParser(
        description="Combine code files from a directory into a single file."
    )
    parser.add_argument("directory", help="The directory to scan for code files.")
    parser.add_argument(
        "-o",
        "--output",
        default="combined_code.txt",
        help="The output file name (default: combined_code.txt).",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        help="Custom file extensions to include (space-separated, e.g., .py .js .ts).",
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Do not respect the .gitignore file.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and folders (those starting with a dot).",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help=(
            "Custom file extensions to exclude (space separated, e.g., .txt .md). "
            "Exclusions take precedence over inclusions."
        ),
    )
    parser.add_argument(
        "--no-tokens",
        action="store_true",
        help="Do not count tokens in the combined output file.",
    )
    parser.add_argument(
        "--header-width",
        type=int,
        default=80,
        help="Width of the separator lines in the combined file header (default: 80).",
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "markdown", "json", "xml"],
        help="Output format (text, markdown, json, xml). Default is text.",
    )
    parser.add_argument(
        "--convert-to",
        choices=["text", "markdown"],
        help="Convert XML/JSON output to text or markdown format.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output file if it already exists without prompting.",
    )
    parser.add_argument(
        "--always-include",
        nargs="+",
        help=(
            "Always include specified files, bypassing other filters "
            "(space-separated paths)."
        ),
    )
    parser.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow symbolic links when scanning directories.",
    )
    parser.add_argument(
        "--token-encoding",
        default="cl100k_base",
        help="The token encoding model to use for token counting "
        "(default: cl100k_base).",
    )
    parser.add_argument(
        "--max-memory-mb",
        type=int,
        default=500,
        help="Maximum memory in MB to use before falling back to streaming "
        "(default: 500). Set to 0 for no limit.",
    )
    parser.add_argument(
        "--custom-file-headers",
        default="{}",
        help=(
            """JSON string of custom file headers per extension (e.g., "
            "'{\"py\": \"# FILE: {path}\", \"js\": \"// FILE: {path}\"}'"""
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without writing any output files.",
    )
    parser.add_argument(
        "--max-file-size-kb",
        type=int,
        help=(
            "Maximum file size in KB to include (e.g., 1024 for 1MB). "
            "Files larger than this will be skipped."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output, showing each file as it's processed.",
    )
    parser.add_argument(
        "--list-files",
        action="store_true",
        help="List all files that were added to the output file.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a summary of the processing results.",
    )
    parser.add_argument(
        "--dry-run-output",
        type=str,
        help="Optional: write the list of files processed during a dry run to this file.",
    )
    parser.add_argument(
        "--progress-style",
        type=str,
        help="Customize the progress bar style (e.g., 'ascii', 'block'). Set to 'none' to disable.",
    )
    return parser.parse_args()


def run_code_combiner(config: CombinerConfig) -> None:
    """Run the code combiner with the given configuration."""
    combiner = CodeCombiner(config)
    combiner.execute()


class CodeCombiner:
    """Orchestrates the code combining process."""

    def __init__(self, config: CombinerConfig):
        """Initialize the CodeCombiner."""
        self.config = config
        self.root_path = self.config.directory_path.resolve()
        # Determine the effective format based on --convert-to
        effective_format = (
            config.final_output_format if config.final_output_format else config.format
        )

        formatter_kwargs = {}
        if effective_format == "text":
            formatter_kwargs["header_width"] = config.header_width

        self.formatter = FormatterFactory.create(
            effective_format,
            custom_file_headers=self.config.custom_file_headers,
            **formatter_kwargs,
        )
        self.safety_filter_chain = FilterChainBuilder.build_safety_chain(self.config)
        self.full_filter_chain = self._build_full_filter_chain(self.safety_filter_chain)

    def _build_full_filter_chain(self, safety_chain_head: FileFilter) -> FileFilter:
        spec = self._get_gitignore_spec() if self.config.use_gitignore else None
        return FilterChainBuilder.build_full_chain(self.config, spec, safety_chain_head)

    def _get_gitignore_spec(self) -> pathspec.PathSpec | None:
        """
        Search for and parse a .gitignore file.

        Searches for a .gitignore file in the current directory or any parent directory
        up to the root. If found, it parses the file and returns a PathSpec object
        for matching. This allows respecting gitignore rules for file filtering.
        """
        current_path: Path = self.config.directory_path.resolve()
        # Traverse up the directory tree to find a .gitignore file
        while current_path != current_path.parent:
            gitignore_path: Path = current_path / ".gitignore"
            if gitignore_path.is_file():
                # If a .gitignore is found, read its contents and create a PathSpec
                with open(gitignore_path, encoding="utf-8") as f:
                    return pathspec.PathSpec.from_lines("gitwildmatch", f)
            # Move to the parent directory
            current_path = current_path.parent
        # If no .gitignore file is found after traversing to the root, return None
        return None

    def _iter_files(self):
        """Iterate over files in the directory using pathlib.Path.rglob()."""
        # rglob will traverse all directories, including hidden ones.
        # The HiddenFileFilter will then handle filtering of hidden files/directories
        # based on self.config.include_hidden in the filter chain.
        for path in self.root_path.rglob("*"):
            if path.is_file():
                yield path

    def _collect_all_files(self) -> list[Path]:
        """Collect all files from the root directory, handling potential errors."""
        all_files: list[Path] = []
        try:
            all_files = list(self._iter_files())
        except PermissionError as e:
            raise CodeCombinerError(
                f"Insufficient permissions to read files: {e}"
            ) from e
        except OSError as e:
            raise CodeCombinerError(f"File system error: {e}") from e
        return all_files

    def _apply_filters_to_files(self, files: list[Path]) -> list[Path]:
        """Apply the full filter chain to a list of files."""
        filtered_files = [
            file
            for file in files
            if self.full_filter_chain.should_process(
                file, {"root_path": self.root_path}
            )
        ]
        return filtered_files

    def _get_filtered_files(self) -> list[Path]:
        """
        Get a list of files to be processed after applying all filters.

        Returns:
            A sorted list of file paths.

        """
        all_files = self._collect_all_files()
        filtered_files = self._apply_filters_to_files(all_files)
        return sorted(filtered_files)

    def _resolve_path(self, path: Path) -> Path:
        """Resolve a path to its absolute form."""
        if path.is_absolute():
            return path.resolve()
        return (self.config.directory_path / path).resolve()

    def _process_always_include_files(self, files: list[Path]) -> list[Path]:
        """Process --always-include files with safety checks."""
        always_included_files: list[Path] = []
        for path_str in self.config.always_include:
            path = Path(path_str)
            resolved_path = self._resolve_path(path)
            if not resolved_path.is_file():
                logging.warning(
                    f"Warning: --always-include path '{path_str}' is not a file "
                    "or does not exist. Skipping."
                )
                continue

            if not self.safety_filter_chain.should_process(
                resolved_path, {"root_path": self.root_path}
            ):
                logging.warning(
                    f"Warning: --always-include path '{path_str}' was filtered out "
                    "by safety checks. Skipping."
                )
                continue
            always_included_files.append(resolved_path)
        return always_included_files

    def execute(self) -> None:
        """Execute the combining process."""
        files = self._get_filtered_files()

        always_included_files = self._process_always_include_files(files)

        # Combine filtered files and always_included_files, ensuring no duplicates
        all_files_to_process = sorted(set(files + always_included_files))

        if not all_files_to_process:
            logging.info("No files found to process. Exiting.")
            return

        # Initialize UI
        ui = LiveUI(total_files=len(all_files_to_process))
        ui.apply_config(self.config)
        ui.print_header()
        ui.print_config()
        ui.start()

        memory_monitor = SystemMemoryMonitor(
            self.config.max_memory_mb, self.config.count_tokens
        )

        with Publisher(total_files=len(all_files_to_process)) as publisher:
            token_counter_observer = None
            if self.config.count_tokens:
                token_counter_observer = TokenCounterObserver(
                    self.config.token_encoding_model
                )
                publisher.subscribe(token_counter_observer)
            line_counter_observer = LineCounterObserver()
            publisher.subscribe(line_counter_observer)
            publisher.subscribe(TelemetryObserver())

            output_written_by_streaming = False
            context = GeneratorContext(
                files_to_process=all_files_to_process,
                root_path=self.config.directory_path,
                formatter=self.formatter,
                publisher=publisher,
                output_path=Path(self.config.output),
                ui=ui,
                token_counter_observer=token_counter_observer,
                line_counter_observer=line_counter_observer,
                memory_monitor=memory_monitor,
                dry_run=self.config.dry_run,
                dry_run_output=self.config.dry_run_output,
            )
            try:
                generator = InMemoryOutputGenerator(context)
                output_content, _ = generator.generate()
                # publisher.notify("processing_complete", (output_content, raw_content)) # Handled by __exit__
            except MemoryThresholdExceededError:
                if not self.config.count_tokens and self.formatter.supports_streaming():
                    logging.warning(
                        "Falling back to streaming due to memory constraints."
                    )
                    streaming_generator = StreamingOutputGenerator(context)
                    streaming_generator.generate()
                    output_written_by_streaming = True
                    output_content = ""  # Clear content as it's already written
                else:
                    raise  # Re-raise if fallback is not allowed

            if not output_written_by_streaming and output_content:
                write_output(
                    Path(self.config.output),
                    output_content,
                    self.config.force,
                    self.config.dry_run,
                    (
                        Path(self.config.dry_run_output)
                        if self.config.dry_run_output
                        else None
                    ),
                )
        ui.finish()  # Finalize UI and print summary


def main():
    """Run the code combiner from the command line."""
    args = parse_arguments()
    config = load_and_merge_config(args)
    run_code_combiner(config)


if __name__ == "__main__":
    main()
