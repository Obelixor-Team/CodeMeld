# Copyright (c) 2025 skum

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging

import psutil

from src.output_generator import InMemoryOutputGenerator, StreamingOutputGenerator, read_file_content
from src.context import GeneratorContext
from src.formatters import TextFormatter, XMLFormatter
from src.config import MemoryThresholdExceededError
from src.memory_monitor import SystemMemoryMonitor


@pytest.fixture
def mock_files_to_process():
    return [Path("/mock/file1.py"), Path("/mock/file2.py")]


@pytest.fixture
def mock_root_path():
    return Path("/mock")


@pytest.fixture
def mock_formatter():
    return TextFormatter()


import io

class TestReadFileContent:
    def test_read_file_not_found(self, caplog):
        with caplog.at_level(logging.WARNING):
            content = list(read_file_content(Path("/non/existent/file.txt")))
            assert not content
            assert "No such file or directory" in caplog.text

    def test_read_permission_error(self, tmp_path, caplog):
        with caplog.at_level(logging.WARNING):
            file_path = tmp_path / "no_permission.txt"
            file_path.write_text("test")
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                content = list(read_file_content(file_path))
                assert not content
            assert "Permission denied" in caplog.text

    def test_read_is_a_directory_error(self, tmp_path, caplog):
        with caplog.at_level(logging.WARNING):
            content = list(read_file_content(tmp_path))
            assert not content
            assert "Is a directory" in caplog.text


class TestInMemoryOutputGenerator:
    def test_xml_formatter(self, mock_files_to_process, mock_root_path):
        with patch('src.output_generator.read_file_content', return_value=['some content']):
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=XMLFormatter(),
                publisher=MagicMock(),
                output_path=Path("/tmp/output.xml"),
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = InMemoryOutputGenerator(context)
            output, _ = generator.generate()
            assert '<codebase>' in output
            assert '</codebase>' in output
            assert '<file>' in output
            assert '<path>file1.py</path>' in output
            assert '<content>some content</content>' in output


class TestStreamingOutputGenerator:
    def test_xml_formatter_streaming(self, mock_files_to_process, mock_root_path, tmp_path):
        output_path = tmp_path / "output.xml"

        def process_file_streaming_mock(file_path, outfile):
            outfile.write("<file><path>file1.py</path><content>some content</content></file>")

        with patch.object(StreamingOutputGenerator, '_process_file_streaming', side_effect=process_file_streaming_mock):
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=XMLFormatter(),
                publisher=MagicMock(),
                output_path=output_path,
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = StreamingOutputGenerator(context)
            generator.generate()
            output = output_path.read_text()
            assert '<codebase>' in output
            assert '</codebase>' in output
            assert '<file>' in output
            assert '<path>file1.py</path>' in output
            assert '<content>some content</content>' in output

    def test_dry_run_with_output_file(self, mock_files_to_process, mock_root_path, tmp_path):
        dry_run_output_path = tmp_path / "dry_run_output.txt"

        def process_file_streaming_mock(file_path, outfile):
            if outfile:
                outfile.write("some content")

        with patch.object(StreamingOutputGenerator, '_process_file_streaming', side_effect=process_file_streaming_mock):
            context = GeneratorContext(
                files_to_process=mock_files_to_process,
                root_path=mock_root_path,
                formatter=TextFormatter(),
                publisher=MagicMock(),
                output_path=tmp_path / "output.txt",
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
                dry_run=True,
                dry_run_output=str(dry_run_output_path),
            )
            generator = StreamingOutputGenerator(context)
            generator.generate()

        assert dry_run_output_path.exists()
        assert "some content" in dry_run_output_path.read_text()

    def test_no_files_to_process(self, mock_root_path, tmp_path, caplog):
        output_path = tmp_path / "output.txt"
        with caplog.at_level(logging.INFO):
            context = GeneratorContext(
                files_to_process=[],
                root_path=mock_root_path,
                formatter=TextFormatter(),
                publisher=MagicMock(),
                output_path=output_path,
                ui=MagicMock(),
                token_counter_observer=MagicMock(),
                line_counter_observer=MagicMock(),
            )
            generator = StreamingOutputGenerator(context)
            generator.generate()
            assert not output_path.exists()

    def test_write_error(self, mock_files_to_process, mock_root_path, tmp_path, caplog):
        output_path = tmp_path / "output.txt"
        with caplog.at_level(logging.ERROR):
            with patch("builtins.open", side_effect=PermissionError("Permission denied")):
                context = GeneratorContext(
                    files_to_process=mock_files_to_process,
                    root_path=mock_root_path,
                    formatter=TextFormatter(),
                    publisher=MagicMock(),
                    output_path=output_path,
                    ui=MagicMock(),
                    token_counter_observer=MagicMock(),
                    line_counter_observer=MagicMock(),
                )
                generator = StreamingOutputGenerator(context)
                with pytest.raises(PermissionError):
                    generator.generate()
