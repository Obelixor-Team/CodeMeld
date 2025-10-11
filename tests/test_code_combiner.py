import pytest
from src.code_combiner import (
    is_code_file,
    get_gitignore_spec,
    scan_and_combine_code_files,
)
import os
import tiktoken
import re


# Fixture for a temporary directory structure
@pytest.fixture
def temp_project_dir(tmp_path):
    # Create dummy files and directories
    (tmp_path / "file1.py").write_text("print('hello')")
    (tmp_path / "file2.js").write_text("console.log('world')")
    (tmp_path / "ignored_file.txt").write_text("ignored content")
    (tmp_path / ".hidden_file.txt").write_text("hidden content")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "file3.py").write_text("x = 1")
    (tmp_path / ".hidden_dir").mkdir()
    (tmp_path / ".hidden_dir" / "hidden_file_in_dir.py").write_text("import os")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.js").write_text("// node module")

    # Create a .gitignore file
    (tmp_path / ".gitignore").write_text(
        "ignored_file.txt\n.hidden_file.txt\n.hidden_dir/\nnode_modules/"
    )

    return tmp_path


def test_is_code_file():
    assert is_code_file("test.py", [".py", ".js"], []) is True
    assert is_code_file("test.js", [".py", ".js"], []) is True
    assert is_code_file("test.txt", [".py", ".js"], []) is False
    assert is_code_file("test.PY", [".py"], []) is True  # Case-insensitive
    assert is_code_file("test.js", [".py", ".js"], [".js"]) is False  # Exclude .js


def test_get_gitignore_spec(temp_project_dir):
    spec = get_gitignore_spec(temp_project_dir)
    assert spec is not None
    assert spec.match_file("ignored_file.txt") is True
    assert spec.match_file(".hidden_file.txt") is True
    assert spec.match_file(".hidden_dir/hidden_file_in_dir.py") is True
    assert spec.match_file("node_modules/package.js") is True
    assert spec.match_file("file1.py") is False


def test_scan_and_combine_code_files_default(temp_project_dir):

    output_file = temp_project_dir / "combined.txt"

    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py", ".js"],
        exclude_extensions=[],
    )

    assert output_file.is_file()

    content = output_file.read_text()

    # Should include file1.py, file2.js, subdir/file3.py

    assert "print('hello')" in content

    assert "console.log('world')" in content

    assert "x = 1" in content

    # Should ignore based on .gitignore and hidden files

    assert "ignored content" not in content

    assert "hidden content" not in content

    assert "import os" not in content  # hidden_file_in_dir.py

    assert "node module" not in content


def test_scan_and_combine_code_files_no_gitignore(temp_project_dir):

    output_file = temp_project_dir / "combined.txt"

    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py", ".js", ".txt"],
        exclude_extensions=[],
        use_gitignore=False,
    )

    assert output_file.is_file()

    content = output_file.read_text()

    # Should include all files, as .gitignore is ignored

    assert "print('hello')" in content

    assert "console.log('world')" in content

    assert "ignored content" in content

    assert "hidden content" in content

    assert "x = 1" in content

    assert "import os" in content

    assert "node module" in content


def test_scan_and_combine_code_files_include_hidden(temp_project_dir):

    output_file = temp_project_dir / "combined.txt"

    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py", ".js", ".txt"],
        exclude_extensions=[],
        include_hidden=True,
    )

    assert output_file.is_file()

    content = output_file.read_text()

    # Should include hidden files, but still respect .gitignore for non-hidden files

    assert "print('hello')" in content

    assert "console.log('world')" in content

    assert "ignored content" not in content  # Still ignored by .gitignore

    assert "hidden content" in content  # .hidden_file.txt

    assert "x = 1" in content

    assert "import os" in content  # hidden_file_in_dir.py

    assert "node module" not in content  # Still ignored by .gitignore


def test_scan_and_combine_code_files_invalid_extension_format(temp_project_dir, capsys):

    output_file = temp_project_dir / "combined.txt"

    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=["py", ".js"],
        exclude_extensions=[],
    )

    captured = capsys.readouterr()

    assert "Error: Custom extension 'py' must start with a dot" in captured.out

    assert not output_file.is_file()


def test_scan_and_combine_code_files_non_existent_directory(tmp_path, capsys):

    output_file = tmp_path / "combined.txt"

    non_existent_dir = tmp_path / "non_existent"

    scan_and_combine_code_files(
        non_existent_dir, str(output_file), extensions=[".py"], exclude_extensions=[]
    )

    captured = capsys.readouterr()

    assert f"Error: Directory '{non_existent_dir}' does not exist." in captured.out

    assert not output_file.is_file()


def test_scan_and_combine_code_files_no_write_permissions(temp_project_dir, capsys):

    output_file = temp_project_dir / "combined.txt"

    # Revoke write permissions for the directory

    os.chmod(temp_project_dir, 0o555)  # Read and execute only

    scan_and_combine_code_files(
        temp_project_dir, str(output_file), extensions=[".py"], exclude_extensions=[]
    )

    captured = capsys.readouterr()

    assert (
        f"Error: No write permissions for output directory '{temp_project_dir}'."
        in captured.out
    )

    assert not output_file.is_file()

    os.chmod(temp_project_dir, 0o755)  # Restore permissions


def test_scan_and_combine_code_files_exclude_extensions(temp_project_dir):

    output_file = temp_project_dir / "combined.txt"

    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py", ".js", ".txt"],
        exclude_extensions=[".js"],
    )

    assert output_file.is_file()

    content = output_file.read_text()

    # Should include .py and .txt files, but exclude .js files

    assert "print('hello')" in content

    assert "ignored content" not in content  # ignored by .gitignore

    assert "x = 1" in content

    assert "console.log('world')" not in content


def test_scan_and_combine_code_files_no_tokens(temp_project_dir, capsys):

    output_file = temp_project_dir / "combined.txt"

    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py"],
        exclude_extensions=[],
        count_tokens=False,
    )

    captured = capsys.readouterr()

    assert "Total tokens in combined file:" not in captured.out

    assert output_file.is_file()


def test_scan_and_combine_code_files_header_width(temp_project_dir):

    output_file = temp_project_dir / "combined.txt"

    custom_width = 50

    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py"],
        exclude_extensions=[],
        header_width=custom_width,
    )

    assert output_file.is_file()

    content = output_file.read_text()

    # Check if the header separator has the custom width

    assert f"\n{'='*custom_width}\n" in content

def test_token_counting_accuracy(tmp_path, capsys):
    # Create a dummy file
    file_content = "This is a test sentence for token counting."
    (tmp_path / "test_file.txt").write_text(file_content)

    output_file = tmp_path / "combined.txt"

    scan_and_combine_code_files(
        tmp_path,
        str(output_file),
        extensions=[".txt"],
        exclude_extensions=[],
        count_tokens=True,
    )

    captured = capsys.readouterr()

    # Manually calculate expected tokens
    encoding = tiktoken.get_encoding("cl100k_base")
    expected_tokens = len(encoding.encode(file_content))

    import re
    match = re.search(r"Total tokens in combined content: (\d+)", captured.out)
    assert match is not None
    actual_tokens = int(match.group(1))
    assert actual_tokens == expected_tokens

import json

def test_scan_and_combine_code_files_json_format(temp_project_dir):
    output_file = temp_project_dir / "combined.json"
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py", ".js"],
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
        extensions=[".py", ".js"],
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


def test_scan_and_combine_code_files_config_file_and_override(temp_project_dir):

    # Create a pyproject.toml with some settings

    (temp_project_dir / "pyproject.toml").write_text(
        """


[tool.code_combiner]


extensions = [".js"]


header_width = 30


"""
    )

    output_file = temp_project_dir / "combined.txt"

    # Run with command-line arguments that override config

    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py"],
        exclude_extensions=[],
        header_width=40,
    )

    assert output_file.is_file()

    content = output_file.read_text()

    # Should use command-line extensions (.py) and header_width (40)

    assert "print('hello')" in content

    assert "console.log('world')" not in content

    assert f"\n{'='*40}\n" in content

    # Run with no overriding command-line arguments, should use config
    output_file_2 = temp_project_dir / "combined_2.txt"
    from src.code_combiner import load_config_from_pyproject

    config = load_config_from_pyproject(temp_project_dir)
    extensions = config.get("extensions", [])
    header_width = config.get("header_width", 80)
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file_2),
        extensions=extensions,
        exclude_extensions=[],
        header_width=header_width,
    )

    assert output_file_2.is_file()

    content_2 = output_file_2.read_text()

    # Should use config extensions (.js) and header_width (30)

    assert "print('hello')" not in content_2

    assert "console.log('world')" in content_2

    assert f"\n{'='*30}\n" in content_2

def test_convert_to_text_xml_to_text(temp_project_dir):
    output_file = temp_project_dir / "combined.xml"
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py", ".js"],
        exclude_extensions=[],
        format="xml",
    )
    assert output_file.is_file()
    xml_content = output_file.read_text()

    text_output_file = temp_project_dir / "combined.txt"
    scan_and_combine_code_files(
        temp_project_dir,
        str(text_output_file),
        extensions=[".py", ".js"],
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
