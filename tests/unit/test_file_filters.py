from pathlib import Path
from unittest.mock import Mock

import pytest

from src.config import CombinerConfig
from src.filters import (
    BinaryFileFilter,
    ExtensionFilter,
    FilterChainBuilder,
    GitignoreFilter,
    HiddenFileFilter,
    OutputFilePathFilter,
    SymlinkFilter,
    SecurityFilter,
    FileSizeFilter, # Added for new test
)


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    (tmp_path / "test.py").touch()
    (tmp_path / "test.js").touch()
    (tmp_path / ".hidden").touch()
    (tmp_path / "sub" / ".subhidden").mkdir(parents=True)
    (tmp_path / "sub" / "test.ts").touch()
    (tmp_path / "output.txt").touch()
    (tmp_path / "binary.bin").write_bytes(b"\x00\x01")
    (tmp_path / "symlink.py").symlink_to(tmp_path / "test.py")
    return tmp_path


class TestExtensionFilter:
    def test_should_process_included_extension(self, temp_dir: Path):
        filter = ExtensionFilter(extensions=[".py"], exclude=[])
        assert filter.should_process(temp_dir / "test.py", {})

    def test_should_not_process_excluded_extension(self, temp_dir: Path):
        filter = ExtensionFilter(extensions=[".py", ".js"], exclude=[".js"])
        assert not filter.should_process(temp_dir / "test.js", {})

    def test_should_not_process_other_extension(self, temp_dir: Path):
        filter = ExtensionFilter(extensions=[".py"], exclude=[])
        assert not filter.should_process(temp_dir / "test.js", {})


class TestHiddenFileFilter:
    def test_should_process_hidden_files_when_included(self, temp_dir: Path):
        filter = HiddenFileFilter(include_hidden=True)
        assert filter.should_process(temp_dir / ".hidden", {"root_path": temp_dir})

    def test_should_not_process_hidden_files_when_not_included(self, temp_dir: Path):
        filter = HiddenFileFilter(include_hidden=False)
        assert not filter.should_process(temp_dir / ".hidden", {"root_path": temp_dir})

    def test_should_not_process_files_in_hidden_dirs_when_not_included(
        self, temp_dir: Path
    ):
        filter = HiddenFileFilter(include_hidden=False)
        assert not filter.should_process(
            temp_dir / "sub" / ".subhidden" / "test.ts", {"root_path": temp_dir}
        )


class TestGitignoreFilter:
    def test_should_process_file_not_in_gitignore(self, temp_dir: Path):
        spec = Mock()
        spec.match_file.return_value = False
        filter = GitignoreFilter(spec=spec)
        assert filter.should_process(temp_dir / "test.py", {"root_path": temp_dir})

    def test_should_not_process_file_in_gitignore(self, temp_dir: Path):
        spec = Mock()
        spec.match_file.return_value = True
        filter = GitignoreFilter(spec=spec)
        assert not filter.should_process(temp_dir / "test.py", {"root_path": temp_dir})


class TestOutputFilePathFilter:
    def test_should_process_other_files(self, temp_dir: Path):
        filter = OutputFilePathFilter(output_path=temp_dir / "output.txt")
        assert filter.should_process(temp_dir / "test.py", {})

    def test_should_not_process_output_file(self, temp_dir: Path):
        filter = OutputFilePathFilter(output_path=temp_dir / "output.txt")
        assert not filter.should_process(temp_dir / "output.txt", {})


class TestBinaryFileFilter:
    def test_should_process_text_file(self, temp_dir: Path):
        filter = BinaryFileFilter()
        assert filter.should_process(temp_dir / "test.py", {})

    def test_should_not_process_binary_file(self, temp_dir: Path):
        filter = BinaryFileFilter()
        assert not filter.should_process(temp_dir / "binary.bin", {})


class TestSymlinkFilter:
    def test_should_process_regular_file(self, temp_dir: Path):
        filter = SymlinkFilter()
        assert filter.should_process(temp_dir / "test.py", {})

    def test_should_not_process_symlink(self, temp_dir: Path):
        filter = SymlinkFilter()
        assert not filter.should_process(temp_dir / "symlink.py", {})


class TestSecurityFilter:
    def test_should_process_path_inside_root(self, temp_dir: Path):
        filter = SecurityFilter()
        assert filter.should_process(temp_dir / "test.py", {"root_path": temp_dir})

    def test_should_not_process_path_outside_root(self, temp_dir: Path):
        filter = SecurityFilter()
        # Create a file outside the temp_dir to simulate path traversal
        outside_dir = temp_dir.parent / "outside_file.txt"
        outside_dir.touch()
        assert not filter.should_process(outside_dir, {"root_path": temp_dir})

    def test_should_not_process_path_traversal_attempt(self, temp_dir: Path):
        filter = SecurityFilter()
        # Simulate a path traversal attempt using '..'
        traversal_path = temp_dir / ".." / "outside_file.txt"
        traversal_path.touch()
        assert not filter.should_process(traversal_path, {"root_path": temp_dir})


class TestFileSizeFilter:
    def test_should_process_small_file(self, temp_dir: Path):
        small_file = temp_dir / "small.txt"
        small_file.write_text("a" * 100) # 100 bytes
        filter = FileSizeFilter(max_file_size_kb=1) # 1 KB limit
        assert filter.should_process(small_file, {})

    def test_should_not_process_large_file(self, temp_dir: Path):
        large_file = temp_dir / "large.txt"
        large_file.write_text("a" * 2000) # 2000 bytes
        filter = FileSizeFilter(max_file_size_kb=1) # 1 KB limit
        assert not filter.should_process(large_file, {})

    def test_should_not_process_non_existent_file(self, temp_dir: Path):
        non_existent_file = temp_dir / "non_existent.txt"
        filter = FileSizeFilter(max_file_size_kb=1)
        assert not filter.should_process(non_existent_file, {})

    def test_should_process_file_at_exact_limit(self, temp_dir: Path):
        exact_file = temp_dir / "exact.txt"
        exact_file.write_text("a" * 1024) # 1 KB
        filter = FileSizeFilter(max_file_size_kb=1) # 1 KB limit
        assert filter.should_process(exact_file, {})


class TestFilterChainBuilder:
    def test_build_default_chain(self, temp_dir: Path):
        config = Mock(spec=CombinerConfig)
        config.output = str(temp_dir / "output.txt")
        config.extensions = [".py"]
        config.exclude_extensions = []
        config.include_hidden = False
        config.use_gitignore = False
        config.count_tokens = False
        config.header_width = 80
        config.format = "text"
        config.final_output_format = None
        config.force = False
        config.always_include = []
        config.token_encoding_model = "cl100k_base"
        config.max_memory_mb = 500
        config.custom_file_headers = {}
        config.max_file_size_kb = None

        chain = FilterChainBuilder.build(config, None)

        assert chain.should_process(temp_dir / "test.py", {"root_path": temp_dir})
        assert not chain.should_process(temp_dir / "test.js", {"root_path": temp_dir})
        assert not chain.should_process(temp_dir / ".hidden", {"root_path": temp_dir})
        assert not chain.should_process(
            temp_dir / "output.txt", {"root_path": temp_dir}
        )
        assert not chain.should_process(
            temp_dir / "binary.bin", {"root_path": temp_dir}
        )
        assert not chain.should_process(
            temp_dir / "symlink.py", {"root_path": temp_dir}
        )


class TestPathResolution:
    def test_absolute_path_resolution(self, temp_dir: Path):
        from src.code_combiner import CodeCombiner
        mock_config = Mock(spec=CombinerConfig, directory_path=temp_dir, format="text", header_width=80, output=str(temp_dir / "output.txt"), extensions=[], exclude_extensions=[], final_output_format=None, token_encoding_model="cl100k_base", max_memory_mb=500, custom_file_headers={}, max_file_size_kb=None)
        combiner = CodeCombiner(mock_config)
        abs_path = temp_dir / "test.py"
        assert combiner._resolve_path(abs_path) == abs_path.resolve()

    def test_relative_path_resolution(self, temp_dir: Path):
        from src.code_combiner import CodeCombiner
        mock_config = Mock(spec=CombinerConfig, directory_path=temp_dir, format="text", header_width=80, output=str(temp_dir / "output.txt"), extensions=[], exclude_extensions=[], final_output_format=None, token_encoding_model="cl100k_base", max_memory_mb=500, custom_file_headers={}, max_file_size_kb=None)
        combiner = CodeCombiner(mock_config)
        rel_path = Path("test.py")
        expected_path = (temp_dir / rel_path).resolve()
        assert combiner._resolve_path(rel_path) == expected_path


class TestPathResolutionEdgeCases:
    def test_relative_output_path_resolution(self, temp_dir: Path):
        output_path = Path("output.txt")
        filter = OutputFilePathFilter(output_path=temp_dir / output_path)
        assert not filter.should_process(temp_dir / output_path, {})

    def test_output_path_with_double_dots(self, temp_dir: Path):
        output_path = temp_dir / "sub" / ".." / "output.txt"
        filter = OutputFilePathFilter(output_path=output_path)
        assert not filter.should_process(temp_dir / "output.txt", {})

    def test_non_existent_output_path(self, temp_dir: Path):
        output_path = temp_dir / "non_existent_dir" / "output.txt"
        filter = OutputFilePathFilter(output_path=output_path)
        # The filter should still work correctly even if the path doesn't exist yet.
        assert not filter.should_process(output_path, {})