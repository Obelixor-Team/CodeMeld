# Copyright (c) 2025 skum

import logging

from src.code_combiner import CodeMeld


def test_get_filtered_files_always_include_non_existent(
    mock_code_combiner_config, caplog, tmp_path
):
    non_existent_file = tmp_path / "non_existent_file.py"
    mock_code_combiner_config.always_include = [non_existent_file]
    combiner = CodeMeld(mock_code_combiner_config)
    with caplog.at_level(logging.WARNING):
        combiner.execute()
    assert (
        f"Warning: --always-include path '{non_existent_file}' is not a file or does not exist. Skipping."
        in caplog.text
    )


def test_get_filtered_files_always_include_directory(
    mock_code_combiner_config, caplog, tmp_path
):
    mock_dir = tmp_path / "always_include_dir"
    mock_dir.mkdir()
    mock_code_combiner_config.always_include = [mock_dir]
    combiner = CodeMeld(mock_code_combiner_config)
    with caplog.at_level(logging.WARNING):
        combiner.execute()
    assert (
        f"Warning: --always-include path '{mock_dir}' is not a file or does not exist. Skipping."
        in caplog.text
    )
