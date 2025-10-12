import pytest
from src.code_combiner import scan_and_combine_code_files
import os

def test_scan_and_combine_code_files_non_existent_directory(tmp_path, capsys):
    output_file = tmp_path / "combined.txt"
    non_existent_dir = tmp_path / "non_existent"
    scan_and_combine_code_files(
        non_existent_dir, str(output_file), extensions=[ ".py"], exclude_extensions=[]
    )
    captured = capsys.readouterr()
    assert f"Error: Directory '{non_existent_dir}' does not exist." in captured.out
    assert not output_file.is_file()

def test_scan_and_combine_code_files_no_write_permissions(temp_project_dir, capsys):
    output_file = temp_project_dir / "combined.txt"
    # Revoke write permissions for the directory
    os.chmod(temp_project_dir, 0o555)  # Read and execute only
    scan_and_combine_code_files(
        temp_project_dir, str(output_file), extensions=[ ".py"], exclude_extensions=[]
    )
    captured = capsys.readouterr()
    assert (
        f"Error: No write permissions for output directory '{temp_project_dir}'."
        in captured.out
    )
    assert not output_file.is_file()
    os.chmod(temp_project_dir, 0o755)  # Restore permissions
