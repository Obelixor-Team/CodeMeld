# Copyright (c) 2025 skum

import pytest
from pathlib import Path
from src.code_combiner import CodeMeld
from src.config import CombinerConfig

@pytest.fixture
def large_file(tmp_path: Path) -> Path:
    large_file_path = tmp_path / "large_file.txt"
    # Create a smaller file for testing (10KB instead of 1MB)
    with open(large_file_path, "w") as f:
        f.write("a" * 10 * 1024)  # 10KB
    return large_file_path

@pytest.fixture
def large_xml_file(tmp_path: Path) -> Path:
    large_file_path = tmp_path / "large_file.xml"
    with open(large_file_path, "w") as f:
        f.write("<data>" + "a" * (10 * 1024) + "</data>")
    return large_file_path

def test_large_file_processing(tmp_path: Path, large_file: Path):
    output_path = tmp_path / "output.txt"
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_path),
        extensions=[".txt"],
        count_tokens=False,  # Disable token counting for large files
    )
    combiner = CodeMeld(config)
    combiner.execute()

    assert output_path.exists()
    # Check that file was processed without hanging
    assert output_path.stat().st_size > 0

def test_large_xml_file_streaming(tmp_path: Path, large_xml_file: Path):
    output_path = tmp_path / "output.xml"
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_path),
        extensions=[".xml"],
        format="xml",
        count_tokens=False,
        max_memory_mb=1, # Force streaming
    )
    combiner = CodeMeld(config)
    combiner.execute()

    assert output_path.exists()
    content = output_path.read_text()
    assert "&lt;data&gt;" + "a" * (10 * 1024) + "&lt;/data&gt;" in content
