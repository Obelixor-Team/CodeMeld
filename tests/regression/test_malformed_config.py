import pytest
from src.code_combiner import load_and_merge_config, run_code_combiner, CodeCombinerError
from argparse import Namespace

def test_scan_and_combine_code_files_invalid_extension_format(temp_project_dir, capsys):
    output_file = temp_project_dir / "combined.txt"
    mock_args = Namespace(
        directory=str(temp_project_dir),
        output=str(output_file),
        extensions=["py", ".js"],
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
    with pytest.raises(CodeCombinerError) as excinfo:
        run_code_combiner(config)
    assert "Error: Custom extension 'py' must start with a dot" in str(excinfo.value)
