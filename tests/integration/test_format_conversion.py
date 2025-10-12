import pytest
from src.code_combiner import load_and_merge_config, run_code_combiner, convert_to_text
import json
from argparse import Namespace

def test_scan_and_combine_code_files_json_format(temp_project_dir):
    output_file = temp_project_dir / "combined.json"
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py", ".js"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="json",
        convert_to="json", # This should be convert_to, not final_output_format
        force=False,
    )
    config = load_and_merge_config(mock_args)
    run_code_combiner(config)
    assert output_file.is_file()
    content = output_file.read_text()
    json_data = json.loads(content)

    assert "file1.py" in json_data
    assert "print('hello')" in json_data["file1.py"]
    assert "file2.js" in json_data
    assert "console.log('world')" in json_data["file2.js"]
    assert "subdir/file3.py" in json_data
    assert "x = 1" in json_data["subdir/file3.py"]
    assert "ignored_file.txt" not in json_data

def test_scan_and_combine_code_files_markdown_format(temp_project_dir):
    output_file = temp_project_dir / "combined.md"
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py", ".js"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="markdown",
        convert_to=None,
        force=False,
    )
    config = load_and_merge_config(mock_args)
    run_code_combiner(config)
    assert output_file.is_file()
    content = output_file.read_text()

    assert "## FILE: file1.py" in content
    assert "```py" in content
    assert "print('hello')" in content
    assert "## FILE: file2.js" in content
    assert "```js" in content
    assert "console.log('world')" in content
    assert "## FILE: subdir/file3.py" in content
    assert "```py" in content
    assert "x = 1" in content
    assert "ignored_file.txt" not in content

def test_convert_to_text_xml_to_text(temp_project_dir):
    text_output_file = temp_project_dir / "combined.txt"
    mock_args_text = Namespace(
        directory=str(temp_project_dir),
        output=str(text_output_file),
        extensions=[ ".py", ".js"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="xml",
        convert_to="text",
        force=True,
    )
    config_text = load_and_merge_config(mock_args_text)
    run_code_combiner(config_text)
    assert text_output_file.is_file()
    text_content = text_output_file.read_text()

    expected_parts = [
        "FILE: file1.py",
        "print('hello')",
        "FILE: file2.js",
        "console.log('world')",
        "FILE: subdir/file3.py",
        "x = 1",
    ]
    for part in expected_parts:
        assert part in text_content

    assert "<file>" not in text_content
    assert "<path>" not in text_content
    assert "<content>" not in text_content

def test_convert_to_text_json_to_markdown(temp_project_dir):
    output_file = temp_project_dir / "combined.json"
    mock_args_json = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py", ".js"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="json",
        convert_to=None,
        force=False,
    )
    config_json = load_and_merge_config(mock_args_json)
    run_code_combiner(config_json)
    assert output_file.is_file()
    json_content = output_file.read_text()

    markdown_output_file = temp_project_dir / "combined.md"
    mock_args_markdown = Namespace(
        directory=str(temp_project_dir),
        output=str(markdown_output_file),
        extensions=[ ".py", ".js"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="json",
        convert_to="markdown",
        force=True, # Changed to True
    )
    config_markdown = load_and_merge_config(mock_args_markdown)
    run_code_combiner(config_markdown)
    assert markdown_output_file.is_file()
    markdown_content = markdown_output_file.read_text()

    expected_parts = [
        "## FILE: file1.py",
        "```py",
        "print('hello')",
        "## FILE: file2.js",
        "```js",
        "console.log('world')",
        "## FILE: subdir/file3.py",
        "```py",
        "x = 1",
    ]
    for part in expected_parts:
        assert part in markdown_content

def test_convert_to_text_xml_to_markdown(temp_project_dir):
    output_file = temp_project_dir / "combined.xml"
    mock_args_xml = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[".py", ".js"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="xml",
        convert_to=None,
        force=False,
    )
    config_xml = load_and_merge_config(mock_args_xml)
    run_code_combiner(config_xml)
    assert output_file.is_file()

    markdown_output_file = temp_project_dir / "combined.md"
    mock_args_markdown = Namespace(
        directory=str(temp_project_dir),
        output=str(markdown_output_file),
        extensions=[".py", ".js"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="xml",
        convert_to="markdown",
        force=True, # Changed to True
    )
    config_markdown = load_and_merge_config(mock_args_markdown)
    run_code_combiner(config_markdown)
    assert markdown_output_file.is_file()
    markdown_content = markdown_output_file.read_text()

    expected_parts = [
        "## FILE: file1.py",
        "```py",
        "print('hello')",
        "## FILE: file2.js",
        "```js",
        "console.log('world')",
        "## FILE: subdir/file3.py",
        "```py",
        "x = 1",
    ]
    for part in expected_parts:
        assert part in markdown_content
