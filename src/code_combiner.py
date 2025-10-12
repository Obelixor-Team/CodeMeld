"""A script to combine code files from a directory into a single output file."""

import argparse
import json
import logging
from pathlib import Path

import pathspec

from .config import CodeCombinerError, CombinerConfig, MemoryThresholdExceededError
from .filters import FileFilter, FilterChainBuilder
from .formatters import (
    FormatterFactory,
)
from .observers import LineCounterObserver, ProgressBarObserver, TokenCounterObserver
from .output_generator import (
    InMemoryOutputGenerator,
    StreamingOutputGenerator,
)


def write_output(
    output_path: Path, output_content: str, force: bool, dry_run: bool = False
):
    """Write the combined output content to the specified file."""
    if dry_run:
        logging.info("\n--- Dry Run Output ---")
        print(output_content)
        logging.info("--- End Dry Run Output ---")
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
        type=json.loads,
        default="{}",
        help=(
            """JSON string of custom file headers per extension (e.g., """
            """'{"py": "# FILE: {path}", "js": "// FILE: {path}"}')."""
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
        self.filter_chain = self._build_filter_chain()

    def _build_filter_chain(self) -> FileFilter:
        spec = self._get_gitignore_spec() if self.config.use_gitignore else None
        return FilterChainBuilder.build(self.config, spec)

    def _get_gitignore_spec(self) -> pathspec.PathSpec | None:
        current_path: Path = self.config.directory_path.resolve()
        while current_path != current_path.parent:
            gitignore_path: Path = current_path / ".gitignore"
            if gitignore_path.is_file():
                with open(gitignore_path, encoding="utf-8") as f:
                    return pathspec.PathSpec.from_lines("gitwildmatch", f)
            current_path = current_path.parent
        return None

    def _scan_files(self) -> list[Path]:
        """Scan directory for matching files, respecting always_include and filters."""
        all_files: set[Path] = set()
        context = {"root_path": self.config.directory_path}

        # Process always_include files, applying safety filters
        for p in self.config.always_include:
            path = Path(p)
            full_path: Path
            if path.is_absolute():
                full_path = self._resolve_path(path)
            else:
                full_path = self._resolve_path(self.config.directory_path / path)

            if full_path.is_file():
                # Apply the full filter chain to always_include files
                # This ensures safety filters are applied
                if self.filter_chain.should_process(full_path, context):
                    all_files.add(full_path)
                else:
                    logging.warning(
                        f"Warning: --always-include path '{p}' was filtered out "
                        "by safety checks."
                    )
            else:
                logging.warning(
                    f"Warning: --always-include path not found or not a file: {p}"
                )

        # Add filtered files, avoiding duplicates
        try:
            for file_path in self._iter_files():
                resolved_file_path = self._resolve_path(file_path)
                if resolved_file_path in all_files:
                    # Already added as an always_include file
                    continue

                if self.filter_chain.should_process(file_path, context):
                    all_files.add(resolved_file_path)
        except PermissionError as e:
            logging.error(f"Permission denied during file scan: {e}")
            raise CodeCombinerError("Insufficient permissions to read files") from e
        except OSError as e:
            logging.error(f"OS error during file scan: {e}")
            raise CodeCombinerError(f"File system error: {e}") from e

        return sorted(list(all_files))

    def _iter_files(self):
        """Iterate over files in the directory using pathlib.Path.rglob()."""
        # rglob will traverse all directories, including hidden ones.
        # The HiddenFileFilter will then handle filtering based on
        # self.config.include_hidden.
        for file_path in self.config.directory_path.rglob("*"):
            if file_path.is_file():
                yield file_path

    def _resolve_path(self, path: Path) -> Path:
        """Resolve a path to its absolute form."""
        if path.is_absolute():
            return path.resolve()
        return (self.config.directory_path / path).resolve()

    def execute(self) -> None:
        """Execute the combining process."""
        files = self._scan_files()

        if not files:
            logging.info(
                "No files to process after filtering. Output file will not be created."
            )
            return

        # Use InMemoryOutputGenerator for token counting or JSON/XML output
        # (streaming for JSON/XML requires in-memory aggregation)
        use_in_memory = self.config.count_tokens or (
            (self.config.format == "json" or self.config.format == "xml")
            and not self.config.final_output_format
        )

        if use_in_memory:
            try:
                in_memory_generator = InMemoryOutputGenerator(
                    files,
                    self.config.directory_path,
                    self.formatter,
                    max_memory_mb=self.config.max_memory_mb,
                    count_tokens=self.config.count_tokens,
                )
                with ProgressBarObserver(
                    len(files), "Processing files"
                ) as progress_bar:
                    in_memory_generator.subscribe(progress_bar)
                    if self.config.count_tokens:
                        token_counter = TokenCounterObserver(
                            self.config.token_encoding_model
                        )
                        in_memory_generator.subscribe(token_counter)
                        line_counter = LineCounterObserver()
                        in_memory_generator.subscribe(line_counter)

                    output, raw_content = in_memory_generator.generate()

                    if self.config.count_tokens:
                        in_memory_generator.notify("output_generated", output)
                    write_output(
                        Path(self.config.output),
                        output,
                        self.config.force,
                        dry_run=self.config.dry_run,
                    )
            except MemoryThresholdExceededError as e:
                logging.warning(
                    f"Memory threshold exceeded, falling back to streaming: {e}"
                )
                # Fallback to streaming output
                streaming_generator = StreamingOutputGenerator(
                    files,
                    self.config.directory_path,
                    self.formatter,
                    Path(self.config.output),
                )
                with ProgressBarObserver(
                    len(files), "Processing files"
                ) as progress_bar:
                    streaming_generator.subscribe(progress_bar)
                    streaming_generator.generate()
        else:
            streaming_generator = StreamingOutputGenerator(
                files,
                self.config.directory_path,
                self.formatter,
                Path(self.config.output),
            )
            with ProgressBarObserver(len(files), "Processing files") as progress_bar:
                streaming_generator.subscribe(progress_bar)
                streaming_generator.generate()
