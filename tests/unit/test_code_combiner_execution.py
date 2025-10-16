# Copyright (c) 2025 skum

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging

from src.config import MemoryThresholdExceededError
from src.code_combiner import CodeMeld


def test_execute_output_written_by_streaming_path(mock_code_combiner_config, tmp_path):
    mock_code_combiner_config.count_tokens = False
    mock_code_combiner_config.output = str(tmp_path / "output.txt")
    combiner = CodeMeld(mock_code_combiner_config)

    with patch('src.output_generator.InMemoryOutputGenerator') as MockInMemoryOutputGenerator:
        mock_in_memory_generator_instance = MockInMemoryOutputGenerator.return_value
        mock_in_memory_generator_instance.generate.side_effect = MemoryThresholdExceededError("Memory exceeded")

        with patch('src.output_generator.StreamingOutputGenerator') as MockStreamingOutputGenerator:
            mock_streaming_generator_instance = MockStreamingOutputGenerator.return_value
            mock_streaming_generator_instance.generate.return_value = None # Simulate streaming writing directly

            with patch('src.code_combiner.write_output') as mock_write_output:
                combiner.execute()
                mock_write_output.assert_not_called()

def test_execute_processing_complete_notification_with_files(mock_code_combiner_config, caplog, tmp_path):
    mock_code_combiner_config.output = str(tmp_path / "output.txt")
    file1 = tmp_path / "file1.py"
    file1.touch()
    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = [file1]

    with patch('src.output_generator.is_likely_binary', return_value=False):
        with patch.object(CodeMeld, '_get_filtered_files', return_value=[file1]) as _mock_get_filtered_files:
            with patch('builtins.open', MagicMock(return_value=MagicMock(__enter__=lambda self: MagicMock(read=MagicMock(side_effect=["file content", ""])), __exit__=MagicMock()))):
                with patch('src.code_combiner.InMemoryOutputGenerator') as MockInMemoryOutputGeneratorClass:
                    mock_in_memory_generator_instance = MockInMemoryOutputGeneratorClass.return_value
                    mock_in_memory_generator_instance.generate.return_value = ("output_content", "raw_content")
                    with patch('src.code_combiner.Publisher') as MockPublisherClass:
                        mock_publisher_instance = MockPublisherClass.return_value
                        # Configure the __exit__ method of the mock instance
                        def mock_exit(exc_type, exc_val, exc_tb):
                            mock_publisher_instance.notify("processing_complete", None)
                            return False
                        mock_publisher_instance.__exit__.side_effect = mock_exit

                        mock_formatter = MagicMock()
                        mock_formatter.supports_streaming.return_value = True
                        combiner = CodeMeld(mock_code_combiner_config)
                        with patch('src.formatters.FormatterFactory.create', return_value=mock_formatter):
                            with patch('psutil.Process') as MockProcess:
                                mock_process_instance = MockProcess.return_value
                                mock_process_instance.memory_info.return_value.rss = 100 * 1024 * 1024 # Mock 100MB RSS
                                combiner.execute()
                            MockInMemoryOutputGeneratorClass.assert_called_once()
                            mock_in_memory_generator_instance.generate.assert_called_once()
                            mock_publisher_instance.notify.assert_called_with(
                                "processing_complete", None
                            )

def test_execute_write_output_called_when_not_streaming(mock_code_combiner_config, tmp_path):
    mock_code_combiner_config.always_include = []
    mock_code_combiner_config.output = str(tmp_path / "output.txt")
    mock_code_combiner_config.force = True
    mock_code_combiner_config.dry_run = False
    mock_code_combiner_config.dry_run_output = None

    file1 = tmp_path / "file1.py"
    file1.touch()

    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = [file1]

    combiner = CodeMeld(mock_code_combiner_config)

    with patch.object(CodeMeld, '_get_filtered_files', return_value=[file1]) as _mock_get_filtered_files:
        with patch('src.code_combiner.InMemoryOutputGenerator') as MockInMemoryOutputGeneratorClass:
            mock_in_memory_generator_instance = MockInMemoryOutputGeneratorClass.return_value
            mock_in_memory_generator_instance.generate.return_value = ("some content", "raw content")
            with patch('src.code_combiner.write_output') as mock_write_output:
                combiner.execute()
                mock_write_output.assert_called_once_with(
                    Path(mock_code_combiner_config.output),
                    "some content",
                    mock_code_combiner_config.force,
                    mock_code_combiner_config.dry_run,
                    None, # dry_run_output_path
                )


def test_execute_no_files_to_process(mock_code_combiner_config, caplog, tmp_path):
    mock_code_combiner_config.always_include = []
    mock_code_combiner_config.directory_path.resolve.return_value = tmp_path
    mock_code_combiner_config.directory_path.rglob.return_value = []
    # Simulate _get_filtered_files returning an empty list
    with patch.object(CodeMeld, '_get_filtered_files', return_value=[]):
        combiner = CodeMeld(mock_code_combiner_config)
        with caplog.at_level(logging.INFO):
            combiner.execute()
        assert "No files found to process. Exiting." in caplog.text
