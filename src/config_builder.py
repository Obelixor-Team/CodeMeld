# Copyright (c) 2025 skum

from __future__ import annotations

"""Provides a builder for creating CombinerConfig objects."""

import argparse
import logging
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .config import DEFAULT_EXTENSIONS, CombinerConfig
from .config_validator import ConfigValidator


def load_toml(path: Path) -> dict[str, Any]:
    """Load TOML data from a file using tomllib (Python 3.11+)."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config_from_pyproject(root_path: Path) -> dict[str, Any]:
    """Load configuration from pyproject.toml if available."""
    config: dict[str, Any] = {}
    pyproject_path = root_path / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            pyproject_data: dict[str, Any] = load_toml(pyproject_path)
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

    def _apply_arg_if_present(
        self,
        args: argparse.Namespace,
        arg_name: str,
        config_key: str | None = None,
        transform_func: Callable | None = None,
    ) -> None:
        if config_key is None:
            config_key = arg_name
        if hasattr(args, arg_name) and getattr(args, arg_name) is not None:
            value = getattr(args, arg_name)
            if transform_func:
                self._config[config_key] = transform_func(value)
            else:
                self._config[config_key] = value

    def with_cli_args(self, args: argparse.Namespace) -> CombinerConfigBuilder:
        """Apply CLI arguments (highest precedence)."""
        self._apply_arg_if_present(args, "extensions")
        self._apply_arg_if_present(args, "exclude", "exclude_extensions")
        if hasattr(args, "no_gitignore") and args.no_gitignore:
            self._config["use_gitignore"] = False
        self._apply_arg_if_present(args, "include_hidden")
        if hasattr(args, "no_tokens") and args.no_tokens:
            self._config["count_tokens"] = False
        if (
            hasattr(args, "header_width") and args.header_width != 80
        ):  # Check against default
            self._config["header_width"] = args.header_width
        self._apply_arg_if_present(args, "format")
        self._apply_arg_if_present(args, "convert_to", "final_output_format")
        self._apply_arg_if_present(args, "force")
        self._apply_arg_if_present(args, "always_include")
        self._apply_arg_if_present(args, "follow_symlinks")
        self._apply_arg_if_present(args, "token_encoding_model")
        self._apply_arg_if_present(args, "max_memory_mb")
        self._apply_arg_if_present(args, "custom_file_headers")
        self._apply_arg_if_present(args, "dry_run")
        self._apply_arg_if_present(args, "max_file_size_kb")
        self._apply_arg_if_present(args, "verbose")
        self._apply_arg_if_present(args, "list_files")
        self._apply_arg_if_present(args, "summary")
        self._apply_arg_if_present(args, "dry_run_output")
        self._apply_arg_if_present(args, "progress_style")

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
