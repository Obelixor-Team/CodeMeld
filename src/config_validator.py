"""Provides a validator for the combiner configuration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .config import CodeCombinerError


class ConfigValidator:
    """Validates the combiner configuration."""

    def __init__(self, config: dict[str, Any], directory: str, output: str):
        """Initialize the ConfigValidator."""
        self._config = config
        self._directory = directory
        self._output = output

    def validate(self) -> None:
        """Run all validation checks."""
        self._validate_directory()
        self._validate_extensions()
        self._validate_header_width()
        self._validate_output_path()
        self._validate_conversion()

    def _validate_directory(self) -> None:
        directory_path = Path(self._directory)
        if not directory_path.is_dir():
            raise CodeCombinerError(
                f"Error: Directory '{self._directory}' does not exist."
            )

    def _validate_extensions(self) -> None:
        if not self._config["extensions"]:
            raise CodeCombinerError("Error: Extension list cannot be empty.")

        for i, ext in enumerate(self._config["extensions"]):
            if not ext.startswith("."):
                suggested_ext = f".{ext.lower()}"
                raise CodeCombinerError(
                    f"Error: Extension '{ext}' must start with '.'. "
                    f"Did you mean '{suggested_ext}'?"
                )
            self._config["extensions"][i] = ext.lower()

    def _validate_header_width(self) -> None:
        if self._config["header_width"] <= 0:
            raise CodeCombinerError("Header width must be positive")

    def _validate_output_path(self) -> None:
        output_path = Path(self._output)
        if not output_path.parent.exists():
            logging.warning(
                f"Output directory '{output_path.parent}' does not exist. Creating it."
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

    def _validate_conversion(self) -> None:
        if self._config["final_output_format"]:
            if self._config["format"] not in ["json", "xml"]:
                raise CodeCombinerError(
                    "--convert-to can only be used when --format is 'json' or 'xml'"
                )
            if self._config["format"] == self._config["final_output_format"]:
                raise CodeCombinerError(
                    f"Error: Cannot convert format '{self._config['format']}' "
                    f"to itself."
                )
