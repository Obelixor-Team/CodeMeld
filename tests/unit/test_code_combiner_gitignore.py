# Copyright (c) 2025 skum

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.code_combiner import CodeMeld


def test_get_gitignore_spec_found_in_current_dir(mock_code_combiner_config):
    mock_code_combiner_config.directory_path.resolve.return_value = Path("/mock/dir")
    with patch.object(
        Path,
        "is_file",
        side_effect=lambda: (
            True
            if (str(Path("/mock/dir/.gitignore")) == str(Path("/mock/dir/.gitignore")))
            else False
        ),
    ):
        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=lambda self: ["*.pyc"], __exit__=MagicMock()
                )
            ),
        ):
            combiner = CodeMeld(mock_code_combiner_config)
            spec = combiner._get_gitignore_spec()
            assert spec is not None
            assert spec.match_file("test.pyc")


def test_get_gitignore_spec_found_in_parent_dir(mock_code_combiner_config):
    # Simulate a directory structure like /mock/parent/dir and .gitignore in
    # /mock/parent
    mock_code_combiner_config.directory_path.resolve.return_value = Path(
        "/mock/parent/dir"
    )

    # Mock Path.is_file for .gitignore in parent directory
    def is_file_side_effect():
        if str(Path("/mock/parent/.gitignore")) == str(Path("/mock/parent/.gitignore")):
            return True
        return False

    with patch.object(Path, "is_file", side_effect=is_file_side_effect):
        with patch(
            "builtins.open",
            MagicMock(
                return_value=MagicMock(
                    __enter__=lambda self: ["*.log"], __exit__=MagicMock()
                )
            ),
        ):
            combiner = CodeMeld(mock_code_combiner_config)
            spec = combiner._get_gitignore_spec()
            assert spec is not None
            assert spec.match_file("test.log")
            assert not spec.match_file("test.py")


def test_get_gitignore_spec_not_found(mock_code_combiner_config):
    mock_code_combiner_config.directory_path.resolve.return_value = Path("/mock/dir")
    with patch.object(Path, "is_file", return_value=False):
        combiner = CodeMeld(mock_code_combiner_config)
        spec = combiner._get_gitignore_spec()
        assert spec is None
