import pytest
import os
from pathlib import Path
from src.code_combiner import run_code_combiner, load_and_merge_config, CombinerConfig
from argparse import Namespace


def test_symlink_handling(tmp_path):
    # Create a dummy file
    (tmp_path / "file1.py").write_text("print('hello')")

    # Create a symlink to the file
    symlink_path = tmp_path / "symlink_to_file1.py"
    os.symlink(tmp_path / "file1.py", symlink_path)

    output_file = tmp_path / "combined.txt"

    mock_args = Namespace(
        directory=str(tmp_path),
        output=str(output_file),
        extensions=[".py"],
        exclude=[],
        no_gitignore=False,
        include_hidden=False,
        no_tokens=False,
        header_width=80,
        format="text",
        convert_to=None,
        force=False,
    )
    config: CombinerConfig = load_and_merge_config(mock_args)
    run_code_combiner(config)

    assert output_file.is_file()
    content = output_file.read_text()
    assert "FILE: file1.py" in content
    assert "print('hello')" in content
    # Ensure symlink itself is not treated as a separate file if it points to an already processed file
    assert "FILE: symlink_to_file1.py" not in content
