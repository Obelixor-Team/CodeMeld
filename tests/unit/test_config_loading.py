import pytest
from src.code_combiner import load_config_from_pyproject
from unittest.mock import patch

@patch('src.code_combiner.toml.load')
def test_load_config_from_pyproject_malformed_toml(mock_toml_load, tmp_path, capsys):
    # Simulate a malformed TOML file by raising an exception
    mock_toml_load.side_effect = Exception("Malformed TOML")

    # Create a dummy pyproject.toml file to ensure the path exists
    (tmp_path / "pyproject.toml").write_text("[tool.code_combiner]\nkey = \"value\"")

    config = load_config_from_pyproject(tmp_path)

    # Expect an empty config and a warning message
    assert config == {}
    captured = capsys.readouterr()
    assert "Warning: Could not load pyproject.toml: Malformed TOML" in captured.err
