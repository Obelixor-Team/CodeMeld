import pytest
from src.code_combiner import load_and_merge_config, run_code_combiner
from argparse import Namespace
import os

def test_scan_and_combine_code_files_default(temp_project_dir):
    output_file = temp_project_dir / "combined.txt"
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py", ".js"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
    )
    config = load_and_merge_config(mock_args)
    run_code_combiner(config)
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
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py", ".js", ".txt"],
        exclude=[],
        no_gitignore=True,
        include_hidden=True,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
    )
    config = load_and_merge_config(mock_args)
    run_code_combiner(config)
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
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py", ".js", ".txt"],
        exclude=[],
        no_gitignore=False,
        include_hidden=True,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
    )
    config = load_and_merge_config(mock_args)
    run_code_combiner(config)
    assert output_file.is_file()
    content = output_file.read_text()
    # Should not include hidden files that are in .gitignore
    assert "print('hello')" in content
    assert "console.log('world')" in content
    assert "ignored content" not in content  # Still ignored by .gitignore
    assert "hidden content" not in content  # .hidden_file.txt
    assert "x = 1" in content
    assert "import os" not in content  # .hidden_dir is ignored by .gitignore
    assert "node module" not in content  # Still ignored by .gitignore

def test_scan_and_combine_code_files_exclude_extensions(temp_project_dir):
    output_file = temp_project_dir / "combined.txt"
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py", ".js", ".txt"],
        exclude=[ ".js"],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
    )
    config = load_and_merge_config(mock_args)
    run_code_combiner(config)
    assert output_file.is_file()
    content = output_file.read_text()
    # Should include .py and .txt files, but exclude .js files
    assert "print('hello')" in content
    assert "ignored content" not in content  # ignored by .gitignore
    assert "x = 1" in content
    assert "console.log('world')" not in content

def test_scan_and_combine_code_files_no_tokens(temp_project_dir, capsys):
    output_file = temp_project_dir / "combined.txt"
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=True, # Set to True for no_tokens
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
    )
    config = load_and_merge_config(mock_args)
    run_code_combiner(config)
    captured = capsys.readouterr()
    assert "Total tokens in combined file:" not in captured.out
    assert output_file.is_file()

def test_scan_and_combine_code_files_header_width(temp_project_dir):
    output_file = temp_project_dir / "combined.txt"
    custom_width = 50
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=custom_width,
        format="text",
        convert_to=None,
        force=False,
    )
    config = load_and_merge_config(mock_args)
    run_code_combiner(config)
    assert output_file.is_file()
    content = output_file.read_text()
    # Check if the header separator has the custom width
    assert f"\n{ '='*custom_width}\n" in content
