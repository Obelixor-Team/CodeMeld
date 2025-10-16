# tests/unit/test_simple_filters.py
import os
import pytest
from pathlib import Path
from unittest.mock import patch
from src.filters import (
    BinaryFileFilter,
    ExtensionFilter,
    HiddenFileFilter,
    OutputFilePathFilter,
    SymlinkFilter,
    FileSizeFilter,
)

class TestExtensionFilter:
    def test_include_extension(self, mock_file_path):
        extension_filter = ExtensionFilter([".py"], [])
        assert extension_filter.should_process(mock_file_path, {})

    def test_exclude_extension(self, mock_file_path):
        extension_filter = ExtensionFilter([".js"], [".py"])
        assert not extension_filter.should_process(mock_file_path, {})

    def test_no_match(self, mock_file_path):
        extension_filter = ExtensionFilter([".js"], [])
        assert not extension_filter.should_process(mock_file_path, {})

    def test_case_insensitivity(self):
        extension_filter = ExtensionFilter([".PY"], [])
        assert extension_filter.should_process(Path("file.py"), {})

    def test_empty_extensions_list(self):
        extension_filter = ExtensionFilter([], [])
        assert not extension_filter.should_process(Path("file.py"), {})


class TestHiddenFileFilter:
    def test_include_hidden_true(self, mock_file_path):
        hidden_file_filter = HiddenFileFilter(include_hidden=True)
        assert hidden_file_filter.should_process(Path("/mock/root/.hidden_file"), {"root_path": Path("/mock/root")})

    def test_include_hidden_false_visible_file(self, mock_file_path):
        hidden_file_filter = HiddenFileFilter(include_hidden=False)
        assert hidden_file_filter.should_process(Path("/mock/root/visible_file.py"), {"root_path": Path("/mock/root")})

    def test_include_hidden_false_hidden_file(self, mock_file_path):
        hidden_file_filter = HiddenFileFilter(include_hidden=False)
        assert not hidden_file_filter.should_process(Path("/mock/root/.hidden_file"), {"root_path": Path("/mock/root")})

    def test_include_hidden_false_hidden_dir(self, mock_file_path):
        hidden_file_filter = HiddenFileFilter(include_hidden=False)
        assert not hidden_file_filter.should_process(Path("/mock/root/.hidden_dir/file.py"), {"root_path": Path("/mock/root")})

    def test_no_root_path_context(self):
        hidden_file_filter = HiddenFileFilter(include_hidden=False)
        assert hidden_file_filter.should_process(Path("/mock/root/.hidden_file"), {})


class TestOutputFilePathFilter:
    def test_output_file_is_filtered(self, tmp_path):
        output_file = tmp_path / "output.txt"
        output_filter = OutputFilePathFilter(output_file)
        assert not output_filter.should_process(output_file, {})

    def test_other_file_is_not_filtered(self, tmp_path):
        output_file = tmp_path / "output.txt"
        other_file = tmp_path / "other.py"
        output_filter = OutputFilePathFilter(output_file)
        assert output_filter.should_process(other_file, {})


class TestBinaryFileFilter:
    @patch("src.filters.is_likely_binary", return_value=True)
    def test_binary_file_is_filtered(self, mock_is_likely_binary):
        binary_filter = BinaryFileFilter()
        assert not binary_filter.should_process(Path("binary.bin"), {})

    @patch("src.filters.is_likely_binary", return_value=False)
    def test_text_file_is_not_filtered(self, mock_is_likely_binary):
        binary_filter = BinaryFileFilter()
        assert binary_filter.should_process(Path("text.txt"), {})


class TestSymlinkFilter:
    @pytest.fixture
    def mock_symlink_file(self, tmp_path):
        target = tmp_path / "target.txt"
        target.write_text("target content")
        symlink = tmp_path / "link.txt"
        os.symlink(target, symlink)
        return symlink

    def test_symlink_filtered_when_not_following(self, mock_symlink_file):
        symlink_filter = SymlinkFilter(follow_symlinks=False)
        assert not symlink_filter.should_process(mock_symlink_file, {})

    def test_symlink_not_filtered_when_following(self, mock_symlink_file):
        symlink_filter = SymlinkFilter(follow_symlinks=True)
        assert symlink_filter.should_process(mock_symlink_file, {})

    def test_non_symlink_not_filtered(self, tmp_path):
        non_symlink = tmp_path / "regular.txt"
        non_symlink.write_text("regular content")
        symlink_filter = SymlinkFilter(follow_symlinks=False)
        assert symlink_filter.should_process(non_symlink, {})


class TestFileSizeFilter:
    def test_file_within_size_limit(self, tmp_path):
        file_path = tmp_path / "small.txt"
        file_path.write_text("a" * 50 * 1024)  # 50KB
        file_size_filter = FileSizeFilter(max_file_size_kb=100)
        assert file_size_filter.should_process(file_path, {})

    def test_file_exceeds_size_limit(self, tmp_path):
        file_path = tmp_path / "large.txt"
        file_path.write_text("a" * 150 * 1024)  # 150KB
        file_size_filter = FileSizeFilter(max_file_size_kb=100)
        assert not file_size_filter.should_process(file_path, {})

    def test_file_not_found(self):
        file_size_filter = FileSizeFilter(max_file_size_kb=100)
        assert not file_size_filter.should_process(Path("non_existent.txt"), {})
