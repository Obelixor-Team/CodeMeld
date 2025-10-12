import pytest
from pathlib import Path
import logging
from src.code_combiner import CodeCombiner
from src.config import CombinerConfig
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