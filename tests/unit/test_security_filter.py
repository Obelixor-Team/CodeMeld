# Copyright (c) 2025 skum

from pathlib import Path
from src.filters import SecurityFilter

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
