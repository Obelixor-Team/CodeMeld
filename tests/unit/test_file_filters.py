# Copyright (c) 2025 skum

import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.filters import (
    AlwaysIncludeFilter,
    BinaryFileFilter,
    ExtensionFilter,
    FileFilter,
    FilterChainBuilder,
    GitignoreFilter,
    HiddenFileFilter,
    OutputFilePathFilter,
    SecurityFilter,
    SymlinkFilter,
    FileSizeFilter,
    CompositeFilter,
    OrFilter,
)
from src.config import CombinerConfig
from src.code_combiner import CodeMeld


@pytest.fixture
def mock_config():
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


@pytest.fixture
def mock_spec():
    spec = MagicMock()
    spec.match_file.side_effect = lambda p: p == "ignored.py"
    return spec


class TestGitignoreFilter:

    def test_file_ignored(self, mock_spec):
        gitignore_filter = GitignoreFilter(mock_spec)
        assert not gitignore_filter.should_process(Path("/mock/root/ignored.py"), {"root_path": Path("/mock/root")})

    def test_file_not_ignored(self, mock_spec):
        gitignore_filter = GitignoreFilter(mock_spec)
        assert gitignore_filter.should_process(Path("/mock/root/not_ignored.py"), {"root_path": Path("/mock/root")})

    def test_no_spec(self):
        gitignore_filter = GitignoreFilter(None)
        assert gitignore_filter.should_process(Path("/mock/root/test.py"), {})

    def test_no_root_path_context(self, mock_spec):
        gitignore_filter = GitignoreFilter(mock_spec)
        assert gitignore_filter.should_process(Path("/mock/root/ignored.py"), {})


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


class TestSecurityFilter:
    def test_file_within_root(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        file_path = root / "file.txt"
        file_path.write_text("content")
        security_filter = SecurityFilter()
        assert security_filter.should_process(file_path, {"root_path": root})

    def test_file_outside_root(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        file_path = tmp_path / "outside.txt"
        file_path.write_text("content")
        security_filter = SecurityFilter()
        assert not security_filter.should_process(file_path, {"root_path": root})

    def test_no_root_path_context(self, tmp_path):
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        security_filter = SecurityFilter()
        assert security_filter.should_process(file_path, {})


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


class TestCompositeFilter:
    def test_all_filters_pass(self):
        mock_filter1 = MagicMock(spec=FileFilter)
        mock_filter1.should_process.return_value = True
        mock_filter2 = MagicMock(spec=FileFilter)
        mock_filter2.should_process.return_value = True

        composite = CompositeFilter([mock_filter1, mock_filter2])
        assert composite.should_process(Path("file.txt"), {})
        mock_filter1.should_process.assert_called_once()
        mock_filter2.should_process.assert_called_once()

    def test_one_filter_fails(self):
        mock_filter1 = MagicMock(spec=FileFilter)
        mock_filter1.should_process.return_value = True
        mock_filter2 = MagicMock(spec=FileFilter)
        mock_filter2.should_process.return_value = False

        composite = CompositeFilter([mock_filter1, mock_filter2])
        assert not composite.should_process(Path("file.txt"), {})
        mock_filter1.should_process.assert_called_once()
        mock_filter2.should_process.assert_called_once()

    def test_empty_composite(self):
        composite = CompositeFilter([])
        assert composite.should_process(Path("file.txt"), {})

    def test_always_include_bypasses_other_filters(self, tmp_path):
        # Create a large file that should be filtered by size
        large_file = tmp_path / "large_file.bin"
        large_file.write_text("a" * 200 * 1024)  # 200KB

        # Create a filter chain that includes a size filter and an always-include filter
        always_include_filter = AlwaysIncludeFilter(always_include_paths=[large_file])
        file_size_filter = FileSizeFilter(max_file_size_kb=100)  # Max 100KB

        # The composite filter contains both. The bug is that AlwaysIncludeFilter
        # causes the FileSizeFilter to be ignored.
        composite_filter = CompositeFilter(
            [always_include_filter, file_size_filter]
        )

        # The current buggy implementation will return True, because AlwaysIncludeFilter
        # is checked first and the function returns immediately.
        # A correct implementation should return False, because the file is too large.
        assert not composite_filter.should_process(
            large_file, {"root_path": tmp_path}
        ), "AlwaysIncludeFilter should not bypass the FileSizeFilter"


class TestFilterChainBuilder:
    def test_build_safety_chain(self, mock_config, tmp_path):
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.max_file_size_kb = 50
        safety_chain = FilterChainBuilder.build_safety_chain(mock_config)
        assert isinstance(safety_chain, CompositeFilter)
        # Further assertions to check the types of filters within the composite
        assert any(isinstance(f, SecurityFilter) for f in safety_chain.filters)
        assert any(isinstance(f, SymlinkFilter) for f in safety_chain.filters)
        assert any(isinstance(f, BinaryFileFilter) for f in safety_chain.filters)
        assert any(isinstance(f, OutputFilePathFilter) for f in safety_chain.filters)
        assert any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_safety_chain_no_file_size(self, mock_config, tmp_path):
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.max_file_size_kb = None
        safety_chain = FilterChainBuilder.build_safety_chain(mock_config)
        assert not any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_safety_chain_with_file_size(self, mock_config, tmp_path):
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.max_file_size_kb = 50
        safety_chain = FilterChainBuilder.build_safety_chain(mock_config)
        assert isinstance(safety_chain, CompositeFilter)
        assert any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_full_chain(self, mock_config, mock_spec, tmp_path):
        mock_config.output = str(tmp_path / "output.txt")
        safety_chain = FilterChainBuilder.build_safety_chain(mock_config)
        full_chain = FilterChainBuilder.build_full_chain(mock_config, mock_spec, safety_chain, [])
        assert isinstance(full_chain, CompositeFilter)
        # Check the order and types of filters
        filters = full_chain.filters
        assert len(filters) == 2
        assert isinstance(filters[0], OrFilter)
        assert isinstance(filters[1], CompositeFilter) # This is the safety_chain

        or_filters = filters[0].filters
        assert len(or_filters) == 1 # Only content filters, no always_include_paths
        content_filters = or_filters[0].filters # Get the CompositeFilter for content filters

        assert any(isinstance(f, ExtensionFilter) for f in content_filters)
        assert any(isinstance(f, HiddenFileFilter) for f in content_filters)
        assert any(isinstance(f, GitignoreFilter) for f in content_filters)

        # Verify safety_chain is indeed the safety_chain
        assert filters[1] is safety_chain

    def test_code_combiner_integration(self, mock_config, tmp_path):
        # This is an integration-style test for the filter chain within CodeCombiner
        mock_config.directory_path = tmp_path
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.extensions = [".py"]
        mock_config.exclude_extensions = []
        mock_config.use_gitignore = False
        mock_config.include_hidden = False
        mock_config.follow_symlinks = False
        mock_config.max_file_size_kb = None

        # Create some dummy files
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")
        (tmp_path / ".hidden.py").write_text("hidden content")

        combiner = CodeMeld(mock_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 1
        assert filtered_files[0].name == "file1.py"

    def test_code_combiner_integration_with_gitignore(self, mock_config, tmp_path):
        mock_config.directory_path = tmp_path
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.extensions = [".py"]
        mock_config.use_gitignore = True
        (tmp_path / ".gitignore").write_text("*.py") # Ignore all python files

        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")

        combiner = CodeMeld(mock_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 0

    def test_code_combiner_integration_with_always_include(self, mock_config, tmp_path):
        mock_config.directory_path = tmp_path
        mock_config.output = str(tmp_path / "output.txt")
        mock_config.extensions = [".py"]
        mock_config.always_include = [str(tmp_path / "file2.js")] # Include a non-python file
        
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")

        combiner = CodeMeld(mock_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 2
        assert Path(tmp_path / "file1.py") in filtered_files
        assert Path(tmp_path / "file2.js") in filtered_files