# Copyright (c) 2025 skum

from __future__ import annotations

"""Provides a builder for creating CombinerConfig objects."""

import argparse
import logging
import tomllib as _tomllib_impl
from pathlib import Path
from typing import Any

from .config import DEFAULT_EXTENSIONS, CombinerConfig
from .config_validator import ConfigValidator

_tomllib: Any

try:
    import tomllib as _tomllib_impl  # stdlib in 3.11+

    _tomllib = _tomllib_impl
except ImportError:
    import toml as _toml_impl

    _tomllib = _toml_impl


def load_config_from_pyproject(root_path: Path) -> dict[str, Any]:
    """Load configuration from pyproject.toml if available."""
    config: dict[str, Any] = {}
    pyproject_path = root_path / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            pyproject_data: dict[str, Any] = _tomllib.load(pyproject_path.open("rb"))
            if "tool" in pyproject_data and "code_combiner" in pyproject_data["tool"]:
                config = pyproject_data["tool"]["code_combiner"]
        except Exception as e:
            logging.warning(f"Error parsing pyproject.toml: {e}")
    return config


class CombinerConfigBuilder:
    """Builder for CombinerConfig with proper precedence."""

    def __init__(self):
        """Initialize the builder with default values."""
        self._config = {
            "extensions": DEFAULT_EXTENSIONS,
            "exclude_extensions": [],
            "use_gitignore": True,
            "include_hidden": False,
            "count_tokens": True,
            "header_width": 80,
            "format": "text",
            "final_output_format": None,
            "force": False,
            "always_include": [],
        }

    def with_defaults(self) -> CombinerConfigBuilder:
        """Use default values."""
        return self

    def with_pyproject_config(self, config: dict[str, Any]) -> CombinerConfigBuilder:
        """Apply pyproject.toml settings."""
        for key, value in config.items():
            if key in self._config:
                self._config[key] = value
        return self

    def with_cli_args(self, args: argparse.Namespace) -> CombinerConfigBuilder:
        """Apply CLI arguments (highest precedence)."""
        # Only override if explicitly provided (not None)
        if args.extensions is not None:
            self._config["extensions"] = args.extensions
        if args.exclude is not None:
            self._config["exclude_extensions"] = args.exclude
        if args.no_gitignore:
            self._config["use_gitignore"] = False
        if args.include_hidden:
            self._config["include_hidden"] = True
        if args.no_tokens:
            self._config["count_tokens"] = False
        if args.header_width != 80:  # Check against default
            self._config["header_width"] = args.header_width
        if args.format != "text":
            self._config["format"] = args.format
        if args.convert_to:
            self._config["final_output_format"] = args.convert_to
        if args.force:
            self._config["force"] = True
        if args.always_include is not None:
            self._config["always_include"] = args.always_include
        if args.follow_symlinks:
            self._config["follow_symlinks"] = True

        # Safely parse custom_file_headers from CLI
        if (
            hasattr(args, "custom_file_headers")
            and args.custom_file_headers is not None
        ):
            self._config["custom_file_headers"] = args.custom_file_headers

        if hasattr(args, "verbose") and args.verbose:
            self._config["verbose"] = True
        if hasattr(args, "list_files") and args.list_files:
            self._config["list_files"] = True
        if hasattr(args, "summary") and args.summary:
            self._config["summary"] = True
        if hasattr(args, "dry_run_output") and args.dry_run_output is not None:
            self._config["dry_run_output"] = args.dry_run_output
        if hasattr(args, "progress_style") and args.progress_style is not None:
            self._config["progress_style"] = args.progress_style

        if hasattr(args, "max_file_size_kb"):
            self._config["max_file_size_kb"] = args.max_file_size_kb

        if hasattr(args, "token_encoding_model"):
            self._config["token_encoding_model"] = args.token_encoding_model

        return self

    def validate(self, directory: str, output: str) -> CombinerConfigBuilder:
        """Validate configuration."""
        validator = ConfigValidator(self._config, directory, output)
        validator.validate()
        return self

    def build(self, directory_path: Path, output: str) -> CombinerConfig:
        """Build the final configuration."""
        return CombinerConfig(
            directory_path=directory_path, output=output, **self._config
        )


def load_and_merge_config(args: argparse.Namespace) -> CombinerConfig:
    """Load configuration from pyproject.toml and merge with command-line arguments."""
    directory_path = Path(args.directory).resolve()

    pyproject_config = load_config_from_pyproject(directory_path)

    return (
        CombinerConfigBuilder()
        .with_defaults()
        .with_pyproject_config(pyproject_config)
        .with_cli_args(args)
        .validate(args.directory, args.output)
        .build(directory_path, args.output)
    )
