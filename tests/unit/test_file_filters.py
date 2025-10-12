import pytest
from src.code_combiner import is_code_file, get_gitignore_spec

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
    assert spec.match_file("file1.py") is False
    assert spec.match_file(".hidden_file.txt") is True
    assert spec.match_file(".hidden_dir/hidden_file_in_dir.py") is True
    assert spec.match_file("node_modules/package.js") is True
    assert spec.match_file("subdir/file3.py") is False
