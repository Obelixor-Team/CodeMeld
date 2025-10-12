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
    )
    with pytest.raises(CodeCombinerError, match=f"Output directory doesn't exist: {non_existent_dir.parent}"):
        load_and_merge_config(args)