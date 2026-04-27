# tests/unit/conftest.py
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.config import CombinerConfig


@pytest.fixture
def create_common_file_structure(tmp_path):
    file1 = tmp_path / "file1.py"
    file1.touch()
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.js"
    file2.touch()
    hidden_file = tmp_path / ".hidden_file.txt"
    hidden_file.touch()
    hidden_dir = tmp_path / ".hidden_dir"
    hidden_dir.mkdir()
    hidden_dir_file = hidden_dir / "secret.txt"
    hidden_dir_file.touch()
    return file1, file2, hidden_file, hidden_dir_file, tmp_path


@pytest.fixture
def mock_code_combiner_config():
    config = MagicMock(spec=CombinerConfig)
    # Create a mock Path object for directory_path
    mock_dir_path: Any = MagicMock()
    mock_dir_path.rglob = MagicMock(return_value=iter([]))  # Default empty rglob
    mock_dir_path.__truediv__.side_effect = lambda x: Path(
        str(mock_dir_path) + "/" + str(x)
    )  # Allow division for path joining
    mock_dir_path.is_absolute.return_value = True
    mock_dir_path.resolve.return_value = mock_dir_path  # Assume it resolves to itself
    mock_dir_path.__str__.return_value = "/mock/dir"  # For string representation

    config.directory_path = mock_dir_path
    config.extensions = [".py"]
    config.exclude_extensions = []
    config.use_gitignore = False
    config.include_hidden = False
    config.count_tokens = False
    config.header_width = 80
    config.format = "text"
    config.final_output_format = None
    config.force = False
    config.always_include = []
    config.output = "output.txt"
    config.token_encoding_model = "cl100k_base"
    config.max_memory_mb = 500
    config.custom_file_headers = {}
    config.max_file_size_kb = None  # Added
    return config


@pytest.fixture
def mock_filter_config():
    return CombinerConfig(
        directory_path=Path("/mock/root"),
        output="output.txt",
        extensions=[".py", ".js"],
        exclude_extensions=[".tmp"],
        use_gitignore=True,
        include_hidden=False,
        follow_symlinks=False,
        max_file_size_kb=100,
    )


@pytest.fixture
def mock_context():
    return {"root_path": Path("/mock/root")}


@pytest.fixture
def mock_file_path():
    return Path("/mock/root/test.py")


@pytest.fixture
def mock_spec():
    spec = MagicMock()
    spec.match_file.side_effect = lambda p: p == "ignored.py"
    return spec
