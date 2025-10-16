# Copyright (c) 2025 skum

import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.filters import (
    FileFilter,
    FilterChainBuilder,
    CompositeFilter,
    SecurityFilter,
    SymlinkFilter,
    BinaryFileFilter,
    OutputFilePathFilter,
    FileSizeFilter,
    ExtensionFilter,
    HiddenFileFilter,
    GitignoreFilter,
)
from src.code_combiner import CodeMeld

class TestCompositeFilter:
    def test_all_filters_pass(self):
        mock_filter1 = MagicMock(spec=FileFilter)
        mock_filter1.should_process.return_value = True
        mock_filter2 = MagicMock(spec=FileFilter)
        mock_filter2.should_process.return_value = True

        composite = CompositeFilter([mock_filter1, mock_filter2])
        assert composite.should_process(Path("file.txt"), {})
        mock_filter1.should_process.assert_called_once()
        mock_filter2.should_process.assert_called_once()

    def test_one_filter_fails(self):
        mock_filter1 = MagicMock(spec=FileFilter)
        mock_filter1.should_process.return_value = True
        mock_filter2 = MagicMock(spec=FileFilter)
        mock_filter2.should_process.return_value = False

        composite = CompositeFilter([mock_filter1, mock_filter2])
        assert not composite.should_process(Path("file.txt"), {})
        mock_filter1.should_process.assert_called_once()
        mock_filter2.should_process.assert_called_once()

    def test_empty_composite(self):
        composite = CompositeFilter([])
        assert composite.should_process(Path("file.txt"), {})


class TestFilterChainBuilder:
    def test_build_safety_chain(self, mock_filter_config, tmp_path):
        mock_filter_config.output = str(tmp_path / "output.txt")
        mock_filter_config.max_file_size_kb = 50
        safety_chain = FilterChainBuilder.build_safety_chain(mock_filter_config)
        assert isinstance(safety_chain, CompositeFilter)
        # Further assertions to check the types of filters within the composite
        assert any(isinstance(f, SecurityFilter) for f in safety_chain.filters)
        assert any(isinstance(f, SymlinkFilter) for f in safety_chain.filters)
        assert any(isinstance(f, BinaryFileFilter) for f in safety_chain.filters)
        assert any(isinstance(f, OutputFilePathFilter) for f in safety_chain.filters)
        assert any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_safety_chain_no_file_size(self, mock_filter_config, tmp_path):
        mock_filter_config.output = str(tmp_path / "output.txt")
        mock_filter_config.max_file_size_kb = None
        safety_chain = FilterChainBuilder.build_safety_chain(mock_filter_config)
        assert not any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_safety_chain_with_file_size(self, mock_filter_config, tmp_path):
        mock_filter_config.output = str(tmp_path / "output.txt")
        mock_filter_config.max_file_size_kb = 50
        safety_chain = FilterChainBuilder.build_safety_chain(mock_filter_config)
        assert isinstance(safety_chain, CompositeFilter)
        assert any(isinstance(f, FileSizeFilter) for f in safety_chain.filters)

    def test_build_full_chain(self, mock_filter_config, mock_spec, tmp_path):
        mock_filter_config.output = str(tmp_path / "output.txt")
        safety_chain = FilterChainBuilder.build_safety_chain(mock_filter_config)
        full_chain = FilterChainBuilder.build_full_chain(mock_filter_config, mock_spec, safety_chain, [])
        assert isinstance(full_chain, CompositeFilter)
        # Check the order and types of filters
        filters = full_chain.filters
        assert isinstance(filters[0], ExtensionFilter)
        assert isinstance(filters[1], HiddenFileFilter)
        assert isinstance(filters[2], GitignoreFilter)
        assert isinstance(filters[3], CompositeFilter) # The safety chain itself is a composite

    def test_code_combiner_integration(self, mock_filter_config, tmp_path):
        # This is an integration-style test for the filter chain within CodeCombiner
        mock_filter_config.directory_path = tmp_path
        mock_filter_config.output = str(tmp_path / "output.txt")
        mock_filter_config.extensions = [".py"]
        mock_filter_config.exclude_extensions = []
        mock_filter_config.use_gitignore = False
        mock_filter_config.include_hidden = False
        mock_filter_config.follow_symlinks = False
        mock_filter_config.max_file_size_kb = None

        # Create some dummy files
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")
        (tmp_path / ".hidden.py").write_text("hidden content")

        combiner = CodeMeld(mock_filter_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 1
        assert filtered_files[0].name == "file1.py"

    def test_code_combiner_integration_with_gitignore(self, mock_filter_config, tmp_path):
        mock_filter_config.directory_path = tmp_path
        mock_filter_config.output = str(tmp_path / "output.txt")
        mock_filter_config.extensions = [".py"]
        mock_filter_config.use_gitignore = True
        (tmp_path / ".gitignore").write_text("*.py") # Ignore all python files

        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")

        combiner = CodeMeld(mock_filter_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 0

    def test_code_combiner_integration_with_always_include(self, mock_filter_config, tmp_path):
        mock_filter_config.directory_path = tmp_path
        mock_filter_config.output = str(tmp_path / "output.txt")
        mock_filter_config.extensions = [".py"]
        mock_filter_config.always_include = [str(tmp_path / "file2.js")] # Include a non-python file
        
        (tmp_path / "file1.py").write_text("print('hello')")
        (tmp_path / "file2.js").write_text("console.log('world')")

        combiner = CodeMeld(mock_filter_config)
        filtered_files = combiner._get_filtered_files()

        assert len(filtered_files) == 2
        assert Path(tmp_path / "file1.py") in filtered_files
        assert Path(tmp_path / "file2.js") in filtered_files
