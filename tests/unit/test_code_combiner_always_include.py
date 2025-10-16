# Copyright (c) 2025 skum

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging

from tests.unit.conftest import create_mock_path
from src.code_combiner import CodeMeld


def test_get_filtered_files_always_include_non_existent(mock_code_combiner_config, caplog):
    mock_code_combiner_config.always_include = [Path("/non/existent/file.py")]
    combiner = CodeMeld(mock_code_combiner_config)
    with caplog.at_level(logging.WARNING):
        combiner.execute()
    assert "Warning: --always-include path '/non/existent/file.py' is not a file or does not exist. Skipping." in caplog.text

def test_get_filtered_files_always_include_directory(mock_code_combiner_config, caplog):
    mock_dir = create_mock_path("/mock/dir/always_include_dir", is_file=False)
    mock_code_combiner_config.always_include = [mock_dir]
    combiner = CodeMeld(mock_code_combiner_config)
    with caplog.at_level(logging.WARNING):
        combiner.execute()
    assert "Warning: --always-include path '/mock/dir/always_include_dir' is not a file or does not exist. Skipping." in caplog.text