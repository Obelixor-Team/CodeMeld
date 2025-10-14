# Copyright (c) 2025 skum

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging
import os

import src.code_combiner

from src.config import CombinerConfig, CodeCombinerError, MemoryThresholdExceededError
from src.code_combiner import CodeCombiner
from src.filters import FilterChainBuilder
from src.output_generator import InMemoryOutputGenerator

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
    config.token_encoding_model = "cl100k_base"
    config.max_memory_mb = 500
    config.custom_file_headers = {}
    config.max_file_size_kb = None # Added
    return config

def test_scan_files_permission_error(mock_config):
    # Simulate PermissionError during Path.rglob() iteration
    mock_config.directory_path.rglob.side_effect = PermissionError("Permission denied")

    combiner = CodeCombiner(mock_config)
    with pytest.raises(CodeCombinerError, match="Insufficient permissions to read files"):
        combiner._get_filtered_files()

def test_scan_files_os_error(mock_config):
    # Simulate OSError during Path.rglob() iteration
    mock_config.directory_path.rglob.side_effect = OSError("OS error occurred")

    combiner = CodeCombiner(mock_config)
    with pytest.raises(CodeCombinerError, match="File system error: OS error occurred"):
        combiner._get_filtered_files()

def test_scan_files_no_error(mock_config):
    # Test normal operation without errors
    mock_file1 = create_mock_path("/mock/dir/file1.py")
    mock_file2 = create_mock_path("/mock/dir/subdir/file2.py")

    # Set the return value for rglob on the mocked directory_path
    mock_config.directory_path.rglob.return_value = [mock_file1, mock_file2]

    with patch.object(CodeCombiner, '_resolve_path', side_effect=lambda p: p):
        with patch.object(FilterChainBuilder, 'build_safety_chain') as mock_build_safety_chain:
            mock_safety_filter_chain = MagicMock()
            mock_safety_filter_chain.should_process.return_value = True
            mock_build_safety_chain.return_value = mock_safety_filter_chain
            with patch.object(CodeCombiner, '_build_full_filter_chain') as mock_build_full_filter_chain:
                mock_full_filter_chain = MagicMock()
                mock_full_filter_chain.should_process.return_value = True
                mock_build_full_filter_chain.return_value = mock_full_filter_chain

                combiner = CodeCombiner(mock_config)
                files = combiner._get_filtered_files()
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
    assert mock_hidden_dir_file in files


def test_execute_output_written_by_streaming_path(mock_config):
    mock_config.count_tokens = False
    mock_config.output = "output.txt"
    combiner = CodeCombiner(mock_config)

    with patch('src.output_generator.InMemoryOutputGenerator') as MockInMemoryOutputGenerator:
        mock_in_memory_generator_instance = MockInMemoryOutputGenerator.return_value
        mock_in_memory_generator_instance.generate.side_effect = MemoryThresholdExceededError("Memory exceeded")

        with patch('src.output_generator.StreamingOutputGenerator') as MockStreamingOutputGenerator:
            mock_streaming_generator_instance = MockStreamingOutputGenerator.return_value
            mock_streaming_generator_instance.generate.return_value = None # Simulate streaming writing directly

            with patch('src.code_combiner.write_output') as mock_write_output:
                combiner.execute()
                mock_write_output.assert_not_called()

import src.code_combiner # Import the module to patch its object

# ... (rest of the file) ...

def test_execute_processing_complete_notification(mock_config, caplog):
    mock_config.output = "output.txt"
    mock_config.directory_path.rglob.return_value = [create_mock_path("/mock/dir/file1.py")]

    # 👇 PATCH is_likely_binary to avoid MagicMock/int comparison error
    with patch('src.output_generator.is_likely_binary', return_value=False):
        with patch.object(src.code_combiner.CodeCombiner, '_get_filtered_files', return_value=[create_mock_path('/mock/dir/file1.py')]) as _mock_get_filtered_files:
            with patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=lambda self: MagicMock(read=MagicMock(side_effect=["file content", ""])), __exit__=MagicMock()))):
                with patch('src.code_combiner.InMemoryOutputGenerator') as MockInMemoryOutputGeneratorClass:
                    mock_in_memory_generator_instance = MockInMemoryOutputGeneratorClass.return_value
                    mock_in_memory_generator_instance.generate.return_value = ("output_content", "raw_content")
                    with patch('src.code_combiner.Publisher') as MockPublisherClass:
                        mock_publisher_instance = MockPublisherClass.return_value
                        # Configure the __exit__ method of the mock instance
                        def mock_exit(exc_type, exc_val, exc_tb):
                            mock_publisher_instance.notify("processing_complete", None)
                            return False
                        mock_publisher_instance.__exit__.side_effect = mock_exit

                        mock_formatter = MagicMock()
                        mock_formatter.supports_streaming.return_value = True
                        combiner = CodeCombiner(mock_config)
                        with patch('src.formatters.FormatterFactory.create', return_value=mock_formatter):
                            with patch('psutil.Process') as MockProcess:
                                mock_process_instance = MockProcess.return_value
                                mock_process_instance.memory_info.return_value.rss = 100 * 1024 * 1024 # Mock 100MB RSS
                                combiner.execute()
                            MockInMemoryOutputGeneratorClass.assert_called_once()
                            mock_in_memory_generator_instance.generate.assert_called_once()
                            mock_publisher_instance.notify.assert_called_with(
                                "processing_complete", None
                            )
    mock_config.directory_path.rglob.return_value = []  # Simulate empty directory
    mock_config.output = "non_existent_output.txt" # Ensure output file doesn't exist

    combiner = CodeCombiner(mock_config)

    with caplog.at_level(logging.INFO):
        combiner.execute()

    assert "No files found to process. Exiting." in caplog.text
    # Ensure write_output was not called
    assert not Path(mock_config.output).exists()

def test_execute_write_output_called_when_not_streaming(mock_config):
    mock_config.always_include = []
    mock_config.output = "output.txt"
    mock_config.force = True
    mock_config.dry_run = False
    mock_config.dry_run_output = None

    combiner = CodeCombiner(mock_config)

    with patch.object(src.code_combiner.CodeCombiner, '_get_filtered_files', return_value=[create_mock_path('/mock/dir/file1.py')]) as _mock_get_filtered_files:
        with patch('src.code_combiner.InMemoryOutputGenerator') as MockInMemoryOutputGeneratorClass:
            mock_in_memory_generator_instance = MockInMemoryOutputGeneratorClass.return_value
            mock_in_memory_generator_instance.generate.return_value = ("some content", "raw content")
            with patch('src.code_combiner.write_output') as mock_write_output:
                combiner.execute()
                mock_write_output.assert_called_once_with(
                    Path(mock_config.output),
                    "some content",
                    mock_config.force,
                    mock_config.dry_run,
                    None, # dry_run_output_path
                )

def test_execute_no_files_to_process(mock_config, caplog):
    mock_config.always_include = []
    # Simulate _get_filtered_files returning an empty list
    with patch.object(CodeCombiner, '_get_filtered_files', return_value=[]):
        combiner = CodeCombiner(mock_config)
        with caplog.at_level(logging.INFO):
            combiner.execute()
        assert "No files found to process. Exiting." in caplog.text

def test_get_filtered_files_always_include_non_existent(mock_config, caplog):
    mock_config.always_include = [Path("/non/existent/file.py")]
    combiner = CodeCombiner(mock_config)
    with caplog.at_level(logging.WARNING):
        combiner.execute()
    assert "Warning: --always-include path '/non/existent/file.py' is not a file or does not exist. Skipping." in caplog.text

def test_get_filtered_files_always_include_directory(mock_config, caplog):
    mock_dir = create_mock_path("/mock/dir/always_include_dir", is_file=False)
    mock_config.always_include = [mock_dir]
    combiner = CodeCombiner(mock_config)
    with caplog.at_level(logging.WARNING):
        combiner.execute()
    assert "Warning: --always-include path '/mock/dir/always_include_dir' is not a file or does not exist. Skipping." in caplog.text

def test_get_gitignore_spec_found_in_current_dir(mock_config):
    mock_config.directory_path.resolve.return_value = Path("/mock/dir")
    with patch.object(Path, 'is_file', side_effect=lambda: True if str(Path("/mock/dir/.gitignore")) == str(Path("/mock/dir/.gitignore")) else False):
        with patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=lambda self: ["*.pyc"], __exit__=MagicMock()))):
            combiner = CodeCombiner(mock_config)
            spec = combiner._get_gitignore_spec()
            assert spec is not None
            assert spec.match_file("test.pyc")

def test_get_gitignore_spec_found_in_parent_dir(mock_config):
    # Simulate a directory structure like /mock/parent/dir and .gitignore in /mock/parent
    mock_config.directory_path.resolve.return_value = Path("/mock/parent/dir")

    # Mock Path.is_file for .gitignore in parent directory
    def is_file_side_effect():
        if str(Path("/mock/parent/.gitignore")) == str(Path("/mock/parent/.gitignore")):
            return True
        return False

    with patch.object(Path, 'is_file', side_effect=is_file_side_effect):
        with patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=lambda self: ["*.log"], __exit__=MagicMock()))):
            combiner = CodeCombiner(mock_config)
            spec = combiner._get_gitignore_spec()
            assert spec is not None
            assert spec.match_file("test.log")
            assert not spec.match_file("test.py")

def test_get_gitignore_spec_not_found(mock_config):
    mock_config.directory_path.resolve.return_value = Path("/mock/dir")
    with patch.object(Path, 'is_file', return_value=False):
        combiner = CodeCombiner(mock_config)
        spec = combiner._get_gitignore_spec()
        assert spec is None

def test_iter_files_rglob_no_hidden_files(mock_config, tmp_path):
    # Create a temporary directory structure
    (tmp_path / "file1.py").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file2.js").touch()
    (tmp_path / ".hidden_file.txt").touch()
    (tmp_path / ".hidden_dir").mkdir()
    (tmp_path / ".hidden_dir" / "secret.txt").touch()

    mock_config.directory_path = tmp_path
    mock_config.include_hidden = False

    combiner = CodeCombiner(mock_config)
    files = list(combiner._iter_files())

    # _iter_files itself should yield all files, filtering happens later
    assert len(files) == 4
    assert (tmp_path / "file1.py") in files
    assert (tmp_path / "subdir" / "file2.js") in files
    assert (tmp_path / ".hidden_file.txt") in files
    assert (tmp_path / ".hidden_dir" / "secret.txt") in files

def test_iter_files_rglob_with_hidden_files(mock_config, tmp_path):
    # Create a temporary directory structure
    (tmp_path / "file1.py").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file2.js").touch()
    (tmp_path / ".hidden_file.txt").touch()
    (tmp_path / ".hidden_dir").mkdir()
    (tmp_path / ".hidden_dir" / "secret.txt").touch()

    mock_config.directory_path = tmp_path
    mock_config.include_hidden = True

    combiner = CodeCombiner(mock_config)
    files = list(combiner._iter_files())

    assert len(files) == 4
    assert (tmp_path / "file1.py") in files
    assert (tmp_path / "subdir" / "file2.js") in files
    assert (tmp_path / ".hidden_file.txt") in files
    assert (tmp_path / ".hidden_dir" / "secret.txt") in files