import pytest
from pathlib import Path
import os
from src.code_combiner import CodeCombiner
from src.config import CombinerConfig, CodeCombinerError

# Helper function to create a dummy binary file
def create_dummy_binary(file_path: Path):
    with open(file_path, 'wb') as f:
        f.write(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09')

def test_always_include_blocks_symlink_outside_root(tmp_path, caplog):
    """
    Test that --always-include blocks symlinks pointing outside the root directory.
    """
    # Create a dummy sensitive file outside the project root
    sensitive_file = tmp_path.parent / "sensitive_data.txt"
    sensitive_file.write_text("secret content")

    # Create a symlink inside the project root pointing to the sensitive file
    symlink_path = tmp_path / "link_to_sensitive.txt"
    os.symlink(sensitive_file, symlink_path)

    output_file = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        always_include=[str(symlink_path)],
    )

    combiner = CodeCombiner(config)
    combiner.execute()

    assert not output_file.exists()
    assert f"Warning: --always-include path '{symlink_path}' was filtered out by safety checks." in caplog.text

def test_always_include_blocks_binary_file(tmp_path, caplog):
    """
    Test that --always-include blocks binary files.
    """
    binary_file = tmp_path / "image.bin"
    create_dummy_binary(binary_file)

    output_file = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        always_include=[str(binary_file)],
    )

    combiner = CodeCombiner(config)
    combiner.execute()

    assert not output_file.exists()
    assert f"Warning: --always-include path '{binary_file}' was filtered out by safety checks." in caplog.text

def test_always_include_blocks_path_traversal(tmp_path, caplog):
    """
    Test that --always-include blocks path traversal attempts (e.g., ../).
    """
    # Create a dummy sensitive file outside the project root
    sensitive_file = tmp_path.parent / "another_secret.txt"
    sensitive_file.write_text("another secret")

    output_file = tmp_path / "output.txt"

    # Attempt to include the file using path traversal
    always_include_path = str(Path("..") / "another_secret.txt")

    # The warning message will contain the original path, not the resolved one.
    # resolved_always_include_path = (tmp_path / always_include_path).resolve() # This line is no longer needed for the assertion


    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        always_include=[always_include_path],
    )

    combiner = CodeCombiner(config)
    combiner.execute()

    assert not output_file.exists()
    # Check for the warning message containing the original path
    assert f"Warning: --always-include path '{always_include_path}' was filtered out by safety checks." in caplog.text

def test_always_include_allows_valid_file(tmp_path, caplog):
    """
    Test that --always-include allows a valid file.
    """
    valid_file = tmp_path / "valid_code.py"
    valid_file.write_text("print('hello')")

    output_file = tmp_path / "output.txt"

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_file),
        always_include=[str(valid_file)],
    )

    combiner = CodeCombiner(config)
    combiner.execute()

    assert output_file.exists()
    content = output_file.read_text()
    assert "print('hello')" in content
    assert "Warning" not in caplog.text # Ensure no warnings for valid files
