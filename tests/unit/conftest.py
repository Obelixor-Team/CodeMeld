# tests/unit/conftest.py
import pytest
from unittest.mock import MagicMock
from pathlib import Path
from src.config import CombinerConfig



@pytest.fixture
def mock_code_combiner_config():
    config = MagicMock(spec=CombinerConfig)
    # Create a mock Path object for directory_path
    mock_dir_path = MagicMock(spec=Path)
    mock_dir_path.rglob.return_value = [] # Default empty rglob
    mock_dir_path.__truediv__.side_effect = lambda x: Path(str(mock_dir_path) + "/" + str(x)) # Allow division for path joining
    mock_dir_path.is_absolute.return_value = True # Assume it's absolute for _resolve_path
    mock_dir_path.resolve.return_value = mock_dir_path # Assume it resolves to itself
    mock_dir_path.__str__.return_value = "/mock/dir" # For string representation

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
    config.max_file_size_kb = None # Added
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