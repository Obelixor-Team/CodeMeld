# Copyright (c) 2025 skum

import pytest
import subprocess
from pathlib import Path

import sys
import pty
import os

def test_cli_basic_run(tmp_path):
    """Test a basic CLI run with default options."""
    (tmp_path / "file1.py").write_text("print('hello')")
    (tmp_path / "file2.txt").write_text("just text")

    output_file = tmp_path / "combined_code.txt"
    
    # Construct the command to run the script
    command = [
        sys.executable,
        "-m",
        "src.code_combiner",
        str(tmp_path),
        "-o",
        str(output_file),
        "-e",
        ".py",
        ".txt",
        "--force"
    ]

    # Execute the command in a pseudo-terminal
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    output = result.stdout

    # Assertions
    assert result.returncode == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "FILE: file1.py" in content
    assert "print('hello')" in content
    assert "FILE: file2.txt" in content
    assert "just text" in content
    assert "Summary:" in output
    assert "All done!" in output
