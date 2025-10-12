"""Unit tests for the file filters."""

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
    OutputFileFilter,
    SymlinkFilter,
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


class TestOutputFileFilter:
    def test_should_process_other_files(self, temp_dir: Path):
        filter = OutputFileFilter(output_path=temp_dir / "output.txt")
        assert filter.should_process(temp_dir / "test.py", {})

    def test_should_not_process_output_file(self, temp_dir: Path):
        filter = OutputFileFilter(output_path=temp_dir / "output.txt")
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


class TestFilterChainBuilder:
    def test_build_default_chain(self, temp_dir: Path):
        config = Mock(spec=CombinerConfig)
        config.output = str(temp_dir / "output.txt")
        config.extensions = [".py"]
        config.exclude_extensions = []
        config.include_hidden = False
        config.use_gitignore = False

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
