import pytest
from src.code_combiner import scan_and_combine_code_files

def test_scan_and_combine_code_files_invalid_extension_format(temp_project_dir, capsys):
    output_file = temp_project_dir / "combined.txt"
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=["py", ".js"],
        exclude_extensions=[],
    )
    captured = capsys.readouterr()
    assert "Error: Custom extension 'py' must start with a dot" in captured.err
    assert not output_file.is_file()
