# Copyright (c) 2025 skum

"""Provides a validator for the combiner configuration."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import tiktoken

from .config import CodeMeldError


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
        self._validate_max_file_size_kb()
        self._validate_token_encoding_model()
        self._validate_custom_file_headers()

    def _validate_directory(self) -> None:
        directory_path = Path(self._directory)
        if not directory_path.is_dir():
            raise CodeMeldError(f"Error: Directory '{self._directory}' does not exist.")

    def _validate_extensions(self) -> None:
        if not self._config["extensions"]:
            raise CodeMeldError("Error: Extension list cannot be empty.")

        for i, ext in enumerate(self._config["extensions"]):
            if not ext.startswith("."):
                suggested_ext = f".{ext.lower()}"
                raise CodeMeldError(f"Error: Extension '{ext}' must start with '.'. Did you mean '{suggested_ext}'?")
            self._config["extensions"][i] = ext.lower()

    def _validate_header_width(self) -> None:
        if self._config["header_width"] <= 0:
            raise CodeMeldError("Header width must be positive")

    def _validate_output_path(self) -> None:
        output_path = Path(self._output)
        if not output_path.parent.exists():
            logging.info(f"Output directory '{output_path.parent}' does not exist and will be created.")

    def _validate_conversion(self) -> None:
        if self._config["final_output_format"]:
            if self._config["format"] not in ["json", "xml"]:
                raise CodeMeldError("--convert-to can only be used when --format is 'json' or 'xml'")
            if self._config["format"] == self._config["final_output_format"]:
                raise CodeMeldError(f"Error: Cannot convert format '{self._config['format']}' to itself.")

    def _validate_max_file_size_kb(self) -> None:
        max_size = self._config.get("max_file_size_kb")
        if max_size is not None and (not isinstance(max_size, int) or max_size <= 0):
            raise CodeMeldError("Max file size must be a positive integer.")

    def _validate_token_encoding_model(self) -> None:
        if self._config.get("count_tokens"):
            token_encoding_model = self._config.get("token_encoding_model")
            if token_encoding_model:
                try:
                    tiktoken.encoding_for_model(token_encoding_model)
                except KeyError as e:
                    raise CodeMeldError(f"Invalid token encoding model: {token_encoding_model}") from e

    def _validate_custom_file_headers(self) -> None:
        custom_headers_str = self._config.get("custom_file_headers")
        if custom_headers_str:
            try:
                # Attempt to parse the JSON string
                parsed_headers = json.loads(custom_headers_str)
                if not isinstance(parsed_headers, dict):
                    raise ValueError("Custom file headers must be a JSON object.")
                # Optionally, add more specific validation for the content of parsed_headers
                # For example, check if keys are strings and values are strings.
                for key, value in parsed_headers.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        raise ValueError("All keys and values in custom file headers must be strings.")
                # If validation passes, store the parsed dictionary back in _config
                self._config["custom_file_headers"] = parsed_headers
            except json.JSONDecodeError as e:
                raise CodeMeldError(
                    f"Invalid JSON in custom_file_headers: {e}\n"
                    """Example: '{"py": "# Python: {path}"}"""
                ) from e
            except ValueError as e:
                raise CodeMeldError(
                    f"Invalid custom_file_headers format: {e}\n"
                    """Example: '{"py": "# Python: {path}"}"""
                ) from e
