from __future__ import annotations

"""Provides a builder for creating CombinerConfig objects."""

import json
import tomllib as _tomllib_impl
from pathlib import Path
from typing import Any

from .config import DEFAULT_EXTENSIONS, CodeCombinerError, CombinerConfig

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

        # Safely parse custom_file_headers from CLI
        if args.custom_file_headers is not None:
            try:
                self._config["custom_file_headers"] = json.loads(
                    args.custom_file_headers
                )
            except json.JSONDecodeError as e:
                raise CodeCombinerError(
                    f"Invalid JSON in --custom-file-headers: {e}"
                ) from e

        return self

    def validate(self, directory: str, output: str) -> CombinerConfigBuilder:
        """Validate configuration."""
        directory_path = Path(directory)
        if not directory_path.is_dir():
            raise CodeCombinerError(f"Error: Directory '{directory}' does not exist.")

        if not self._config["extensions"]:
            raise CodeCombinerError("Error: Extension list cannot be empty.")

        if self._config["header_width"] <= 0:
            raise CodeCombinerError("Header width must be positive")

        output_path = Path(output)
        if not output_path.parent.exists():
            logging.warning(
                f"Output directory '{output_path.parent}' does not exist. Creating it."
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Check extensions start with dot and provide suggestions
        for i, ext in enumerate(self._config["extensions"]):
            if not ext.startswith("."):
                # If it doesn't start with a dot, suggest with a lowercase dot-prefix
                suggested_ext = f".{ext.lower()}"
                raise CodeCombinerError(
                    f"Error: Extension '{ext}' must start with '.'. "
                    f"Did you mean '{suggested_ext}'?"
                )
            # If it already starts with a dot, just ensure it's lowercase
            self._config["extensions"][i] = ext.lower()

        # Check conversion makes sense
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

        # Remove file extension validation - let users name files as they want
        return self

    def build(self, directory: str, output: str) -> CombinerConfig:
        """Build the final configuration."""
        return CombinerConfig(
            directory_path=Path(directory), output=output, **self._config
        )


def load_and_merge_config(args: argparse.Namespace) -> CombinerConfig:
    """Load configuration from pyproject.toml and merge with command-line arguments."""
    directory_path = Path(args.directory)

    pyproject_config = load_config_from_pyproject(directory_path)

    return (
        CombinerConfigBuilder()
        .with_defaults()
        .with_pyproject_config(pyproject_config)
        .with_cli_args(args)
        .validate(args.directory, args.output)
        .build(args.directory, args.output)
    )
