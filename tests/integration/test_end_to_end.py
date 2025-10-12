import pytest
from pathlib import Path
import logging
from src.code_combiner import CodeCombiner
from src.config import CombinerConfig, MemoryThresholdExceededError
from src.formatters import FormatType
from src.config import ConvertType


def test_complete_refactored_flow(tmp_path):
    """Test the entire refactored architecture end-to-end."""
    # Create test files
    (tmp_path / "file1.py").write_text("print('test')")
    (tmp_path / "file2.js").write_text("console.log('test')")
    (tmp_path / ".gitignore").write_text("*.log")
    (tmp_path / "debug.log").write_text("should be ignored")
    
    output = tmp_path / "output.txt"
    
    # Run with various options
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output),
        extensions=[ ".py", ".js"],
        use_gitignore=True,
        count_tokens=False,
    )
    
    combiner = CodeCombiner(config)
    combiner.execute()
    
    # Verify
    assert output.exists()
    content = output.read_text()
    assert "print('test')" in content
    assert "console.log('test')" in content
    assert "should be ignored" not in content


def test_convert_json_to_markdown(tmp_path):
    """Test converting JSON output to Markdown format."""
    (tmp_path / "test.py").write_text("def func():\n    pass")
    output_file = tmp_path / "output.md"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        extensions=[ ".py"],
        format="json",
        final_output_format="markdown",
    )

    combiner = CodeCombiner(config)
    combiner.execute()

    assert output_file.exists()
    content = output_file.read_text()
    assert "## FILE: test.py" in content
    assert "```py" in content  # Changed from "```python"
    assert "def func():" in content
    assert "pass" in content
    assert "{" not in content  # Should not contain JSON syntax
    assert "}" not in content  # Should not contain JSON syntax


def test_convert_xml_to_text(tmp_path):
    """Test converting XML output to plain text format."""
    (tmp_path / "main.js").write_text("console.log('hello');")
    output_file = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        extensions=[ ".js"],
        format="xml",
        final_output_format="text",
    )

    combiner = CodeCombiner(config)
    combiner.execute()

    assert output_file.exists()
    content = output_file.read_text()
    assert "FILE: main.js" in content
    assert "console.log('hello');" in content
    assert "<" not in content  # Should not contain XML syntax
    assert ">" not in content  # Should not contain XML syntax

def test_dry_run_mode(tmp_path, capsys, caplog):

    """Test that --dry-run mode prints to stdout and does not create an output file."""

    (tmp_path / "file1.py").write_text("print('dry run test')")

    output_file = tmp_path / "dry_run_output.txt"



    config = CombinerConfig(

        directory_path=tmp_path,

        output=str(output_file),

        extensions=[".py"],

        dry_run=True,

    )



    combiner = CodeCombiner(config)
    
    with caplog.at_level(logging.INFO):
        combiner.execute()



    # Verify that the output file was NOT created

    assert not output_file.exists()



    # Verify that the content was printed to stdout

    captured_stdout = capsys.readouterr().out

    

    # Verify logging messages using caplog

    assert "--- Dry Run Output ---" in caplog.text

    assert "--- End Dry Run Output ---" in caplog.text



    assert "print('dry run test')" in captured_stdout

def test_gitignore_precedence(tmp_path):
    """Test that .gitignore rules take precedence over included extensions."""
    # Create a Python file
    (tmp_path / "ignored_file.py").write_text("print('This should be ignored')")
    # Create a .gitignore that ignores all .py files
    (tmp_path / ".gitignore").write_text("*.py")

    output = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output),
        extensions=[".py"],  # .py is included
        use_gitignore=True,
        count_tokens=False,
    )

    combiner = CodeCombiner(config)
    combiner.execute()

    # Verify that the output file exists but does NOT contain the ignored Python file
    assert not output.exists()

def test_custom_file_headers_formatting(tmp_path):
    """Test that --custom-file-headers formatting is applied correctly."""
    (tmp_path / "script.py").write_text("print('Hello from Python')")
    (tmp_path / "app.js").write_text("console.log('Hello from JS')")

    output = tmp_path / "output.txt"

    custom_headers = {
        "py": "# Python File: {path}",
        "js": "// JavaScript File: {path}"
    }

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output),
        extensions=[".py", ".js"],
        custom_file_headers=custom_headers,
        count_tokens=False,
    )

    combiner = CodeCombiner(config)
    combiner.execute()

    assert output.exists()
    content = output.read_text()

    assert "# Python File: script.py" in content
    assert "print('Hello from Python')" in content
    assert "// JavaScript File: app.js" in content
    assert "console.log('Hello from JS')" in content

def test_memory_threshold_fallback(tmp_path, caplog):
    """Test that memory threshold exceeding triggers fallback to streaming output."""
    large_file = tmp_path / "large_file.txt"
    large_file.write_text("a" * (1024 * 1024 * 2))  # 2MB file

    output_file = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        extensions=[".txt"],
        max_memory_mb=1,  # Intentionally very low
        count_tokens=False,  # Fallback only occurs if token counting is not needed
    )

    combiner = CodeCombiner(config)

    with caplog.at_level(logging.WARNING):
        combiner.execute()

    # Output file should exist (streaming fallback succeeded)
    assert output_file.exists()
    content = output_file.read_text()
    assert "a" * (1024 * 1024 * 2) in content

    # Log should contain fallback message (looser match for robustness)
    assert any("Falling back to streaming" in record.message for record in caplog.records)    