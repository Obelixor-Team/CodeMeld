from pathlib import Path
import pytest
from src.code_combiner import is_code_file, get_gitignore_spec, scan_and_combine_code_files
import os

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
    (tmp_path / ".gitignore").write_text("ignored_file.txt\n.hidden_file.txt\n.hidden_dir/\nnode_modules/")

    return tmp_path


def test_is_code_file():
    assert is_code_file("test.py", [".py", ".js"], []) is True
    assert is_code_file("test.js", [".py", ".js"], []) is True
    assert is_code_file("test.txt", [".py", ".js"], []) is False
    assert is_code_file("test.PY", [".py"], []) is True # Case-insensitive
    assert is_code_file("test.js", [".py", ".js"], [".js"]) is False # Exclude .js


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
    scan_and_combine_code_files(temp_project_dir, str(output_file), extensions=[ ".py", ".js"], exclude_extensions=[])

    assert output_file.is_file()
    content = output_file.read_text()

    # Should include file1.py, file2.js, subdir/file3.py
    assert "print('hello')" in content
    assert "console.log('world')" in content
    assert "x = 1" in content

    # Should ignore based on .gitignore and hidden files
    assert "ignored content" not in content
    assert "hidden content" not in content
    assert "import os" not in content # hidden_file_in_dir.py
    assert "node module" not in content


def test_scan_and_combine_code_files_no_gitignore(temp_project_dir):
    output_file = temp_project_dir / "combined.txt"
    scan_and_combine_code_files(
        temp_project_dir, str(output_file), extensions=[ ".py", ".js", ".txt"], exclude_extensions=[], use_gitignore=False
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
        temp_project_dir, str(output_file), extensions=[ ".py", ".js", ".txt"], exclude_extensions=[], include_hidden=True
    )

    assert output_file.is_file()
    content = output_file.read_text()

    # Should include hidden files, but still respect .gitignore for non-hidden files
    assert "print('hello')" in content
    assert "console.log('world')" in content
    assert "ignored content" not in content # Still ignored by .gitignore
    assert "hidden content" in content # .hidden_file.txt
    assert "x = 1" in content
    assert "import os" in content # hidden_file_in_dir.py
    assert "node module" not in content # Still ignored by .gitignore


def test_scan_and_combine_code_files_invalid_extension_format(temp_project_dir, capsys):
    output_file = temp_project_dir / "combined.txt"
    scan_and_combine_code_files(
        temp_project_dir, str(output_file), extensions=["py", ".js"], exclude_extensions=[]
    )
    captured = capsys.readouterr()
    assert "Error: Custom extension 'py' must start with a dot" in captured.out
    assert not output_file.is_file()


def test_scan_and_combine_code_files_non_existent_directory(tmp_path, capsys):
    output_file = tmp_path / "combined.txt"
    non_existent_dir = tmp_path / "non_existent"
    scan_and_combine_code_files(non_existent_dir, str(output_file), exclude_extensions=[])
    captured = capsys.readouterr()
    assert f"Error: Directory '{non_existent_dir}' does not exist." in captured.out
    assert not output_file.is_file()

def test_scan_and_combine_code_files_no_write_permissions(temp_project_dir, capsys):
    output_file = temp_project_dir / "combined.txt"
    # Revoke write permissions for the directory
    os.chmod(temp_project_dir, 0o555) # Read and execute only
    scan_and_combine_code_files(temp_project_dir, str(output_file), exclude_extensions=[])
    captured = capsys.readouterr()
    assert f"Error: No write permissions for output directory '{temp_project_dir}'." in captured.out
    assert not output_file.is_file()
    os.chmod(temp_project_dir, 0o755) # Restore permissions


def test_scan_and_combine_code_files_exclude_extensions(temp_project_dir):
    output_file = temp_project_dir / "combined.txt"
    scan_and_combine_code_files(
        temp_project_dir, str(output_file), extensions=[".py", ".js", ".txt"], exclude_extensions=[".js"]
    )

    assert output_file.is_file()
    content = output_file.read_text()

    # Should include .py and .txt files, but exclude .js files
    assert "print('hello')" in content
    assert "ignored content" not in content # ignored by .gitignore
    assert "x = 1" in content
    assert "console.log('world')" not in content


def test_scan_and_combine_code_files_no_tokens(temp_project_dir, capsys):
    output_file = temp_project_dir / "combined.txt"
    scan_and_combine_code_files(
        temp_project_dir, str(output_file), extensions=[".py"], count_tokens=False
    )
    captured = capsys.readouterr()
    assert "Total tokens in combined file:" not in captured.out
    assert output_file.is_file()
