# Copyright (c) 2025 skum

from unittest.mock import patch

from src.code_combiner import CodeMeld
from src.config import CombinerConfig


def test_only_files_skips_directory_scan(tmp_path):
    # Setup: Create some files in the directory
    file1 = tmp_path / "file1.py"
    file1.touch()
    file2 = tmp_path / "file2.py"
    file2.touch()

    # Only want file1
    config = CombinerConfig(
        directory_path=tmp_path,
        only_files=[str(file1)],
        always_include=[],
    )

    with patch.object(CodeMeld, "_collect_all_files") as mock_collect:
        combiner = CodeMeld(config)
        files = combiner._prepare_files()

        # Verify directory scan was skipped
        mock_collect.assert_not_called()
        # Verify only file1 is processed
        assert len(files) == 1
        assert files[0] == file1.resolve()


def test_only_files_with_always_include(tmp_path):
    # Setup: Create some files
    file1 = tmp_path / "file1.py"
    file1.touch()
    file2 = tmp_path / "file2.py"
    file2.touch()
    file3 = tmp_path / "file3.py"
    file3.touch()

    # Only want file1 AND always include file3
    config = CombinerConfig(
        directory_path=tmp_path,
        only_files=[str(file1)],
        always_include=[str(file3)],
    )

    with patch.object(CodeMeld, "_collect_all_files") as mock_collect:
        combiner = CodeMeld(config)
        files = combiner._prepare_files()

        mock_collect.assert_not_called()
        assert len(files) == 2
        assert file1.resolve() in files
        assert file3.resolve() in files
        assert file2.resolve() not in files


def test_only_files_respects_safety_filters(tmp_path):
    # Create a binary file (simulated)
    bin_file = tmp_path / "binary.dat"
    bin_file.write_bytes(b"\x00\xff\x00\xff")

    config = CombinerConfig(
        directory_path=tmp_path,
        only_files=[str(bin_file)],
    )

    combiner = CodeMeld(config)
    files = combiner._prepare_files()

    # Binary file should be filtered out by safety chain
    assert len(files) == 0
