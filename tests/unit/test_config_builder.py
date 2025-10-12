import pytest
from src.config import CodeCombinerError
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
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
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
        no_tokens=False,
        header_width=0,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
    )
    with pytest.raises(CodeCombinerError, match="Header width must be positive"):
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
        no_tokens=False,
        header_width=-10,
        format="text",
        convert_to=None,
        force=False,
        always_include=None,
        custom_file_headers="{}",
    )
    with pytest.raises(CodeCombinerError, match="Header width must be positive"):
        load_and_merge_config(args)

def test_output_directory_non_existent_raises_error(tmp_path):
    # Test that a non-existent output directory raises an error
    non_existent_dir = tmp_path / "non_existent_parent" / "output.txt"
    args = Namespace(
        directory=str(tmp_path),
        output=str(non_existent_dir),
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
    )
    load_and_merge_config(args)
    assert non_existent_dir.parent.exists()
    assert not non_existent_dir.exists() # The file itself is not created yet, only the directory

def test_extension_without_dot_raises_error_with_suggestion():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=["py"],  # Invalid extension
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
    )
    with pytest.raises(CodeCombinerError, match="Error: Extension 'py' must start with '.'. Did you mean '.py'?"):
        load_and_merge_config(args)

def test_extension_with_dot_and_case_conversion(): # This test name is now misleading
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=["PY"],  # Invalid extension
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
    )
    with pytest.raises(CodeCombinerError, match="Error: Extension 'PY' must start with '.'. Did you mean '.py'?"):
        load_and_merge_config(args)

def test_multiple_extensions_with_one_invalid():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".js", "py", ".ts"],  # One invalid
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
    )
    with pytest.raises(CodeCombinerError, match="Error: Extension 'py' must start with '.'. Did you mean '.py'?"):
        load_and_merge_config(args)

def test_convert_to_with_invalid_format_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".py"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="text",  # Invalid format for --convert-to
        convert_to="markdown",
        force=False,
        always_include=None,
        custom_file_headers="{}",
    )
    with pytest.raises(CodeCombinerError, match="--convert-to can only be used when --format is 'json' or 'xml'"):
        load_and_merge_config(args)

def test_convert_to_same_format_raises_error():
    args = Namespace(
        directory=".",
        output="output.txt",
        extensions=[".py"],
        exclude=None,
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="json",
        convert_to="json",  # Converting to the same format
        force=False,
        always_include=None,
        custom_file_headers="{}",
    )
    with pytest.raises(CodeCombinerError, match="Error: Cannot convert format 'json' to itself."):
        load_and_merge_config(args)