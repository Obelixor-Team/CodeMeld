# Copyright (c) 2025 skum

import pytest
from src.config import CodeMeldError
from src.config_builder import CombinerConfigBuilder, load_and_merge_config
from argparse import Namespace
from pathlib import Path


def test_header_width_validation_positive():
    # Test that a positive header_width passes validation
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    config = load_and_merge_config(args)
    assert config.header_width == 80


def test_header_width_validation_zero_raises_error():
    # Test that a header_width of 0 raises an error
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=0,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(CodeMeldError, match="Header width must be positive"):
        load_and_merge_config(args)


def test_header_width_validation_negative_raises_error():
    # Test that a negative header_width raises an error
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=-1,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(CodeMeldError, match="Header width must be positive"):
        load_and_merge_config(args)


def test_output_directory_is_not_created_during_config(tmp_path):
    # Test that the output directory is not created during the configuration phase.
    non_existent_dir = tmp_path / "non_existent_parent" / "output.txt"
    args = Namespace(
        directory=str(tmp_path),
        output=str(non_existent_dir),
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    load_and_merge_config(args)
    assert not non_existent_dir.parent.exists()


def test_extension_without_dot_raises_error_with_suggestion():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=["py"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError,
        match=r"Error: Extension 'py' must start with '.'. Did you mean '.py'\?",
    ):
        load_and_merge_config(args)


def test_extension_with_dot_and_case_conversion():  # This test name is now misleading
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=["PY"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError,
        match=r"Error: Extension 'PY' must start with '.'. Did you mean '.py'\?",
    ):
        load_and_merge_config(args)


def test_multiple_extensions_with_one_invalid():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".js", "py", ".ts"],  # One invalid
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError,
        match=r"Error: Extension 'py' must start with '.'. Did you mean '.py'\?",
    ):
        load_and_merge_config(args)


def test_convert_to_with_invalid_format_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".py"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",  # Invalid format for --convert-to
        convert_to="markdown",
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError,
        match="--convert-to can only be used when --format is 'json' or 'xml'",
    ):
        load_and_merge_config(args)


def test_convert_to_same_format_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".py"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="json",
        convert_to="json",  # Converting to the same format
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError, match="Error: Cannot convert format 'json' to itself."
    ):
        load_and_merge_config(args)


def test_malformed_custom_file_headers_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers='{"py": "# Python"',  # Invalid JSON
        follow_symlinks=False,
        max_file_size_kb=None,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(CodeMeldError, match="Invalid JSON in custom_file_headers"):
        load_and_merge_config(args)


def test_non_existent_directory_raises_error():
    builder = CombinerConfigBuilder()
    with pytest.raises(
        CodeMeldError, match="Error: Directory 'non_existent_dir' does not exist."
    ):
        builder.validate("non_existent_dir", "output.txt")


def test_max_file_size_kb_validation_zero_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=0,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError, match="Max file size must be a positive integer."
    ):
        load_and_merge_config(args)


def test_max_file_size_kb_validation_negative_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=-10,
        token_encoding_model="gpt-2",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError, match="Max file size must be a positive integer."
    ):
        load_and_merge_config(args)


def test_invalid_token_encoding_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=None,
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
        follow_symlinks=False,
        max_file_size_kb=1024,
        token_encoding_model="invalid_encoding",
        verbose=False,
        list_files=False,
        summary=False,
        dry_run_output=None,
        progress_style=None,
    )
    with pytest.raises(
        CodeMeldError, match="Invalid token encoding model: invalid_encoding"
    ):
        load_and_merge_config(args)
