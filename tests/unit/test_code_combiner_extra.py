# Copyright (c) 2025 skum

from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

from src.code_combiner import write_output, main
from src.config import CombinerConfig

def test_write_output_overwrite_interactive_yes(tmp_path):
    output_path = tmp_path / "output.txt"
    output_path.write_text("old content")

    with patch('builtins.input', return_value='y'), patch('sys.stdin.isatty', return_value=True):
        write_output(output_path, "new content", force=False)

    assert output_path.read_text() == "new content"

def test_write_output_overwrite_interactive_no(tmp_path):
    output_path = tmp_path / "output.txt"
    output_path.write_text("old content")

    with patch('builtins.input', return_value='n'):
        write_output(output_path, "new content", force=False)

    assert output_path.read_text() == "old content"

def test_write_output_no_overwrite_non_interactive(tmp_path):
    output_path = tmp_path / "output.txt"
    output_path.write_text("old content")

    with patch('sys.stdin.isatty', return_value=False):
        write_output(output_path, "new content", force=False)

    assert output_path.read_text() == "old content"

def test_write_output_dry_run_with_output_path(tmp_path):
    output_path = tmp_path / "output.txt"
    dry_run_output_path = tmp_path / "dry_run_output.txt"

    write_output(output_path, "new content", force=False, dry_run=True, dry_run_output_path=dry_run_output_path)

    assert not output_path.exists()
    assert dry_run_output_path.read_text() == "new content"

@patch('src.code_combiner.run_code_combiner')
@patch('src.code_combiner.load_and_merge_config')
@patch('src.code_combiner.parse_arguments')
def test_main(mock_parse_arguments, mock_load_and_merge_config, mock_run_code_combiner):
    mock_args = MagicMock()
    mock_parse_arguments.return_value = mock_args
    mock_config = MagicMock(spec=CombinerConfig)
    mock_load_and_merge_config.return_value = mock_config

    main()

    mock_parse_arguments.assert_called_once()
    mock_load_and_merge_config.assert_called_once_with(mock_args)
    mock_run_code_combiner.assert_called_once_with(mock_config)

@patch('argparse.ArgumentParser.parse_args')
def test_parse_arguments(mock_parse_args):
    from src.code_combiner import parse_arguments
    mock_args = MagicMock()
    mock_parse_args.return_value = mock_args

    args = parse_arguments()

    assert args == mock_args
