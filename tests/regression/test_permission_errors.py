import pytest
from src.code_combiner import load_and_merge_config, run_code_combiner, CodeCombinerError
from argparse import Namespace
import os

def test_scan_and_combine_code_files_non_existent_directory(tmp_path, capsys):
    output_file = tmp_path / "combined.txt"
    non_existent_dir = tmp_path / "non_existent"
    mock_args = Namespace(
        directory=str(non_existent_dir),
        output=str(output_file),
        extensions=[ ".py"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
    )
    with pytest.raises(CodeCombinerError) as excinfo:
        config = load_and_merge_config(mock_args)
    assert f"Error: Directory '{non_existent_dir}' does not exist." in str(excinfo.value)
    assert not output_file.is_file()

def test_scan_and_combine_code_files_no_write_permissions(temp_project_dir, capsys):
    output_file = temp_project_dir / "combined.txt"
    # Revoke write permissions for the directory
    os.chmod(temp_project_dir, 0o555)  # Read and execute only
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=[ ".py"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
    )
    with pytest.raises(CodeCombinerError) as excinfo:
        config = load_and_merge_config(mock_args)
        run_code_combiner(config)
    assert "Error: No write permissions for output directory" in str(excinfo.value)
    assert not output_file.is_file()
    os.chmod(temp_project_dir, 0o755)  # Restore permissions
