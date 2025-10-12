import pytest
from src.code_combiner import scan_and_combine_code_files, convert_to_text
import json

def test_scan_and_combine_code_files_json_format(temp_project_dir):
    output_file = temp_project_dir / "combined.json"
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[ ".py", ".js"],
        exclude_extensions=[],
        format="json",
        final_output_format="json", # Added this line
    )
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
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[ ".py", ".js"],
        exclude_extensions=[],
        format="markdown",
    )
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
    output_file = temp_project_dir / "combined.xml"
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[ ".py", ".js"],
        exclude_extensions=[],
        format="xml",
    )
    assert output_file.is_file()

    text_output_file = temp_project_dir / "combined.txt"
    scan_and_combine_code_files(
        temp_project_dir,
        str(text_output_file),
        extensions=[ ".py", ".js"],
        exclude_extensions=[],
        format="xml",
        final_output_format="text",
    )
    assert text_output_file.is_file()
    text_content = text_output_file.read_text()

    assert "FILE: file1.py" in text_content
    assert "print('hello')" in text_content
    assert "FILE: file2.js" in text_content
    assert "console.log('world')" in text_content
    assert "FILE: subdir/file3.py" in text_content
    assert "x = 1" in text_content
    assert "<file>" not in text_content
    assert "<path>" not in text_content
    assert "<content>" not in text_content

def test_convert_to_text_json_to_text(temp_project_dir):
    output_file = temp_project_dir / "combined.json"
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[ ".py", ".js"],
        exclude_extensions=[],
        format="json",
    )
    assert output_file.is_file()
    json_content = output_file.read_text()

    text_output_file = temp_project_dir / "combined.txt"
    scan_and_combine_code_files(
        temp_project_dir,
        str(text_output_file),
        extensions=[ ".py", ".js"],
        exclude_extensions=[],
        format="json",
        final_output_format="text",
    )
    assert text_output_file.is_file()
    text_content = text_output_file.read_text()

    assert "FILE: file1.py" in text_content
    assert "print('hello')" in text_content
    assert "FILE: file2.js" in text_content
    assert "console.log('world')" in text_content
    assert "FILE: subdir/file3.py" in text_content
    assert "x = 1" in text_content
    assert "{" not in text_content
    assert "}" not in text_content

def test_convert_to_text_json_to_markdown(temp_project_dir):
    output_file = temp_project_dir / "combined.json"
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[ ".py", ".js"],
        exclude_extensions=[],
        format="json",
    )
    assert output_file.is_file()
    json_content = output_file.read_text()

    markdown_output_file = temp_project_dir / "combined.md"
    scan_and_combine_code_files(
        temp_project_dir,
        str(markdown_output_file),
        extensions=[ ".py", ".js"],
        exclude_extensions=[],
        format="json",
        final_output_format="markdown",
    )
    assert markdown_output_file.is_file()
    markdown_content = markdown_output_file.read_text()

    assert "## FILE: file1.py" in markdown_content
    assert "```py" in markdown_content
    assert "print('hello')" in markdown_content
    assert "## FILE: file2.js" in markdown_content
    assert "```js" in markdown_content
    assert "console.log('world')" in markdown_content
    assert "## FILE: subdir/file3.py" in markdown_content
    assert "```py" in markdown_content
    assert "x = 1" in markdown_content

def test_convert_to_text_xml_to_markdown(temp_project_dir):
    output_file = temp_project_dir / "combined.xml"
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py", ".js"],
        exclude_extensions=[],
        format="xml",
    )
    assert output_file.is_file()

    markdown_output_file = temp_project_dir / "combined.md"
    scan_and_combine_code_files(
        temp_project_dir,
        str(markdown_output_file),
        extensions=[".py", ".js"],
        exclude_extensions=[],
        format="xml",
        final_output_format="markdown",
    )
    assert markdown_output_file.is_file()
    markdown_content = markdown_output_file.read_text()

    assert "## FILE: file1.py" in markdown_content
    assert "```py" in markdown_content
    assert "print('hello')" in markdown_content
    assert "## FILE: file2.js" in markdown_content
    assert "```js" in markdown_content
    assert "console.log('world')" in markdown_content
    assert "## FILE: subdir/file3.py" in markdown_content
    assert "```py" in markdown_content
    assert "x = 1" in markdown_content
