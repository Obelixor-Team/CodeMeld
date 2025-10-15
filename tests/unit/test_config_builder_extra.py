# Copyright (c) 2025 skum

from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

from src.config_builder import load_config_from_pyproject, CombinerConfigBuilder

def test_load_config_from_pyproject_malformed(tmp_path):
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text("[tool.code_combiner]\ninvalid_toml")

    with patch('logging.warning') as mock_warning:
        config = load_config_from_pyproject(tmp_path)
        assert config == {}
        mock_warning.assert_called_once()

def test_with_pyproject_config_unknown_key():
    builder = CombinerConfigBuilder()
    config = {"unknown_key": "value"}
    builder.with_pyproject_config(config)
    assert "unknown_key" not in builder._config
