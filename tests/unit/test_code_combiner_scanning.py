# Copyright (c) 2025 skum

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.config import CodeMeldError
from src.code_combiner import CodeMeld
from src.filters import FilterChainBuilder


def test_scan_files_permission_error(mock_code_combiner_config, tmp_path):
    # Simulate PermissionError during Path.rglob() iteration
    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    with patch.object(
        CodeMeld, "_iter_files", side_effect=PermissionError("Permission denied")
    ):
        combiner = CodeMeld(mock_code_combiner_config)
        with pytest.raises(
            CodeMeldError, match="Insufficient permissions to read files"
        ):
            combiner._get_filtered_files()


def test_scan_files_os_error(mock_code_combiner_config, tmp_path):
    # Simulate OSError during Path.rglob() iteration
    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    with patch.object(
        CodeMeld, "_iter_files", side_effect=OSError("OS error occurred")
    ):
        combiner = CodeMeld(mock_code_combiner_config)
        with pytest.raises(CodeMeldError, match="File system error: OS error occurred"):
            combiner._get_filtered_files()


def test_scan_files_no_error(mock_code_combiner_config, tmp_path):
    # Test normal operation without errors
    file1 = tmp_path / "file1.py"
    file1.touch()
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.py"
    file2.touch()

    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    with patch.object(CodeMeld, "_iter_files", return_value=[file1, file2]):
        with patch.object(CodeMeld, "_resolve_path", side_effect=lambda p: p):
            with patch.object(
                FilterChainBuilder, "build_safety_chain"
            ) as mock_build_safety_chain:
                mock_safety_filter_chain = MagicMock()
                mock_safety_filter_chain.should_process.return_value = True
                mock_build_safety_chain.return_value = mock_safety_filter_chain
                with patch.object(
                    CodeMeld, "_build_full_filter_chain"
                ) as mock_build_full_filter_chain:
                    mock_full_filter_chain = MagicMock()
                    mock_full_filter_chain.should_process.return_value = True
                    mock_build_full_filter_chain.return_value = mock_full_filter_chain

                    combiner = CodeMeld(mock_code_combiner_config)
                    files = combiner._get_filtered_files()
                    assert len(files) == 2
                    assert file1 in files
                    assert file2 in files


def test_iter_files_rglob_no_hidden(
    mock_code_combiner_config, create_common_file_structure
):
    file1, file2, hidden_file, hidden_dir_file, tmp_path = create_common_file_structure
    mock_code_combiner_config.include_hidden = False

    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = [
        file1,
        file2,
        hidden_file,
        hidden_dir_file,
    ]

    combiner = CodeMeld(mock_code_combiner_config)
    files = list(combiner._iter_files())
    assert len(files) == 4
    assert file1 in files
    assert file2 in files
    assert hidden_file in files
    assert hidden_dir_file in files


def test_iter_files_rglob_include_hidden(
    mock_code_combiner_config, create_common_file_structure
):
    file1, file2, hidden_file, hidden_dir_file, tmp_path = create_common_file_structure
    mock_code_combiner_config.include_hidden = True

    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = [
        file1,
        file2,
        hidden_file,
        hidden_dir_file,
    ]

    combiner = CodeMeld(mock_code_combiner_config)
    files = list(combiner._iter_files())
    assert len(files) == 4
    assert file1 in files
    assert file2 in files
    assert hidden_dir_file in files


def test_iter_files_rglob_no_hidden_files(
    mock_code_combiner_config, create_common_file_structure
):
    file1, file2, hidden_file, hidden_dir_file, tmp_path = create_common_file_structure

    mock_code_combiner_config.directory_path = tmp_path
    mock_code_combiner_config.include_hidden = False

    combiner = CodeMeld(mock_code_combiner_config)
    files = list(combiner._iter_files())

    # _iter_files itself should only yield all files, filtering happens later
    assert len(files) == 4
    assert file1 in files
    assert file2 in files
    assert hidden_file in files
    assert hidden_dir_file in files


def test_iter_files_rglob_with_hidden_files(
    mock_code_combiner_config, create_common_file_structure
):
    file1, file2, hidden_file, hidden_dir_file, tmp_path = create_common_file_structure

    mock_code_combiner_config.directory_path = tmp_path
    mock_code_combiner_config.include_hidden = True

    combiner = CodeMeld(mock_code_combiner_config)
    files = list(combiner._iter_files())

    assert len(files) == 4
    assert file1 in files
    assert file2 in files
    assert hidden_file in files
    assert hidden_dir_file in files
