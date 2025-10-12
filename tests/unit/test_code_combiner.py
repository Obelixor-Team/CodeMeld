import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging
import os

from src.config import CombinerConfig, CodeCombinerError
from src.code_combiner import CodeCombiner

@pytest.fixture
def mock_config():
    config = MagicMock(spec=CombinerConfig)
    config.directory_path = Path("/mock/dir")
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
    # Simulate PermissionError during os.walk
    with patch('os.walk', side_effect=PermissionError("Permission denied")):
        combiner = CodeCombiner(mock_config)
        with pytest.raises(CodeCombinerError, match="Insufficient permissions to read files"):
            combiner._scan_files()

def test_scan_files_os_error(mock_config):
    # Simulate OSError during os.walk
    with patch('os.walk', side_effect=OSError("OS error occurred")):
        combiner = CodeCombiner(mock_config)
        with pytest.raises(CodeCombinerError, match="File system error: OS error occurred"):
            combiner._scan_files()

def test_scan_files_no_error(mock_config):
    # Test normal operation without errors
    mock_file1 = mock_config.directory_path / "file1.py"
    mock_file2 = mock_config.directory_path / "subdir" / "file2.py"

    # Mock os.walk to return specific files
    mock_os_walk_data = [
        (str(mock_config.directory_path), ["subdir"], ["file1.py"]),
        (str(mock_config.directory_path / "subdir"), [], ["file2.py"]),
    ]
    with patch('os.walk', return_value=mock_os_walk_data):
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

@pytest.fixture
def mock_os_walk_data_filtered():
    # Mock data for os.walk, already filtered for hidden directories
    return [
        ("/mock/dir", ["subdir"], ["file1.py"]),
        ("/mock/dir/subdir", [], ["file2.js"]),
    ]

@pytest.fixture
def mock_os_walk_data_unfiltered():
    # Mock data for os.walk, including hidden directories
    return [
        ("/mock/dir", ["subdir", ".hidden_dir"], ["file1.py", ".hidden_file.txt"]),
        ("/mock/dir/subdir", [], ["file2.js"]),
        ("/mock/dir/.hidden_dir", [], ["secret.txt"]),
    ]

def test_iter_files_with_os_walk_no_hidden(mock_config, mock_os_walk_data_filtered):
    mock_config.include_hidden = False
    with patch('os.walk', return_value=mock_os_walk_data_filtered):
        combiner = CodeCombiner(mock_config)
        files = list(combiner._iter_files())
        assert len(files) == 2
        assert Path("/mock/dir/file1.py") in files
        assert Path("/mock/dir/subdir/file2.js") in files
        assert Path("/mock/dir/.hidden_file.txt") not in files
        assert Path("/mock/dir/.hidden_dir/secret.txt") not in files

def test_iter_files_with_os_walk_include_hidden(mock_config, mock_os_walk_data_unfiltered):
    mock_config.include_hidden = True
    with patch('os.walk', return_value=mock_os_walk_data_unfiltered):
        combiner = CodeCombiner(mock_config)
        files = list(combiner._iter_files())
        assert len(files) == 4
        assert Path("/mock/dir/file1.py") in files
        assert Path("/mock/dir/.hidden_file.txt") in files
        assert Path("/mock/dir/subdir/file2.js") in files
        assert Path("/mock/dir/.hidden_dir/secret.txt") in files