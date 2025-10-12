"""Provides a builder for creating CombinerConfig objects."""

import argparse
from pathlib import Path
from typing import Any

import toml

from .config import DEFAULT_EXTENSIONS, CodeCombinerError, CombinerConfig


def load_config_from_pyproject(root_path: Path) -> dict[str, Any]:
    """Load configuration from pyproject.toml if available."""
    config: dict[str, Any] = {}
    pyproject_path = root_path / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            pyproject_data: dict[str, Any] = toml.load(pyproject_path)
            if "tool" in pyproject_data and "code_combiner" in pyproject_data["tool"]:
                config = pyproject_data["tool"]["code_combiner"]
        except Exception:
            pass
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

    def with_defaults(self) -> "CombinerConfigBuilder":
        """Use default values."""
        return self

    def with_pyproject_config(self, config: dict[str, Any]) -> "CombinerConfigBuilder":
        """Apply pyproject.toml settings."""
        for key, value in config.items():
            if key in self._config:
                self._config[key] = value
        return self

    def with_cli_args(self, args: argparse.Namespace) -> "CombinerConfigBuilder":
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

        return self

    def validate(self) -> "CombinerConfigBuilder":
        """Validate configuration."""
        # Check extensions start with dot
        for ext in self._config["extensions"]:
            if not ext.startswith("."):
                raise CodeCombinerError(f"Extension must start with '.': {ext}")

        # Check conversion makes sense
        if self._config["final_output_format"]:
            if self._config["format"] not in ["json", "xml"]:
                raise CodeCombinerError("--convert-to only works with json/xml formats")

        return self

    def build(self, directory: str, output: str) -> CombinerConfig:
        """Build the final configuration."""
        return CombinerConfig(
            directory_path=Path(directory), output=output, **self._config
        )


def load_and_merge_config(args: argparse.Namespace) -> CombinerConfig:
    """Load configuration from pyproject.toml and merge with command-line arguments."""
    directory_path = Path(args.directory)

    if not directory_path.is_dir():
        raise CodeCombinerError(f"Error: Directory '{args.directory}' does not exist.")

    pyproject_config = load_config_from_pyproject(directory_path)

    return (
        CombinerConfigBuilder()
        .with_defaults()
        .with_pyproject_config(pyproject_config)
        .with_cli_args(args)
        .validate()
        .build(args.directory, args.output)
    )
