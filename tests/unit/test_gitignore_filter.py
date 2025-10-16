# Copyright (c) 2025 skum

import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.filters import GitignoreFilter

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
