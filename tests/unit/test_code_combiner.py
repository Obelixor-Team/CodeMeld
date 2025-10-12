import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging
import os

from src.config import CombinerConfig, CodeCombinerError
from src.code_combiner import CodeCombiner

def create_mock_path(path_str: str, is_file: bool = True) -> MagicMock:
    mock_path = MagicMock(spec=Path, name=path_str)
    mock_path.is_file.return_value = is_file
    mock_path.__str__.return_value = path_str
    mock_path.resolve.return_value = mock_path
    mock_path.__truediv__.side_effect = lambda x: Path(path_str + "/" + str(x))
    mock_path.__lt__.side_effect = lambda other: str(mock_path) < str(other) # Make sortable
    return mock_path

@pytest.fixture
def mock_config():
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
    return config

def test_scan_files_permission_error(mock_config):
    # Simulate PermissionError during Path.rglob() iteration
    mock_config.directory_path.rglob.side_effect = PermissionError("Permission denied")

    combiner = CodeCombiner(mock_config)
    with pytest.raises(CodeCombinerError, match="Insufficient permissions to read files"):
        combiner._scan_files()

def test_scan_files_os_error(mock_config):
    # Simulate OSError during Path.rglob() iteration
    mock_config.directory_path.rglob.side_effect = OSError("OS error occurred")

    combiner = CodeCombiner(mock_config)
    with pytest.raises(CodeCombinerError, match="File system error: OS error occurred"):
        combiner._scan_files()

def test_scan_files_no_error(mock_config):
    # Test normal operation without errors
    mock_file1 = create_mock_path("/mock/dir/file1.py")
    mock_file2 = create_mock_path("/mock/dir/subdir/file2.py")

    # Set the return value for rglob on the mocked directory_path
    mock_config.directory_path.rglob.return_value = [mock_file1, mock_file2]

    with patch.object(CodeCombiner, '_resolve_path', side_effect=lambda p: p):
        # Patch _build_filter_chain to return a mock filter_chain
        with patch.object(CodeCombiner, '_build_filter_chain') as mock_build_filter_chain:
            mock_filter_chain = MagicMock()
            mock_filter_chain.should_process.return_value = True
            mock_build_filter_chain.return_value = mock_filter_chain

            combiner = CodeCombiner(mock_config)
            files = combiner._scan_files()
            assert len(files) == 2
            assert mock_file1 in files
            assert mock_file2 in files





def test_iter_files_rglob_no_hidden(mock_config):
    mock_config.include_hidden = False
    mock_file1 = create_mock_path("/mock/dir/file1.py")
    mock_file2 = create_mock_path("/mock/dir/subdir/file2.js")
    mock_hidden_file = create_mock_path("/mock/dir/.hidden_file.txt")
    mock_hidden_dir_file = create_mock_path("/mock/dir/.hidden_dir/secret.txt")

    # rglob will return all files, including hidden ones and those in hidden dirs
    mock_config.directory_path.rglob.return_value = [mock_file1, mock_file2, mock_hidden_file, mock_hidden_dir_file]

    combiner = CodeCombiner(mock_config)
    files = list(combiner._iter_files())
    # _iter_files itself should only yield files, not filter hidden based on config
    # The filtering of hidden files/dirs is done by HiddenFileFilter
    assert len(files) == 4
    assert mock_file1 in files
    assert mock_file2 in files
    assert mock_hidden_file in files
    assert mock_hidden_dir_file in files

def test_iter_files_rglob_include_hidden(mock_config):
    mock_config.include_hidden = True
    mock_file1 = create_mock_path("/mock/dir/file1.py")
    mock_file2 = create_mock_path("/mock/dir/subdir/file2.js")
    mock_hidden_file = create_mock_path("/mock/dir/.hidden_file.txt")
    mock_hidden_dir_file = create_mock_path("/mock/dir/.hidden_dir/secret.txt")

    mock_config.directory_path.rglob.return_value = [mock_file1, mock_file2, mock_hidden_file, mock_hidden_dir_file]

    combiner = CodeCombiner(mock_config)
    files = list(combiner._iter_files())
    assert len(files) == 4
    assert mock_file1 in files
    assert mock_file2 in files
    assert mock_hidden_file in files
    assert mock_hidden_dir_file in files