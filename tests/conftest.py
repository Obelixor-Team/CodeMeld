import pytest
import os

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
