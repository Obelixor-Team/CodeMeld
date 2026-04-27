from src.code_combiner import CodeMeld
from src.config import CombinerConfig


def test_always_include_with_large_binary_file_blocked(tmp_path):
    """Integration test: --always-include should NOT bypass safety filters"""
    # Create a large binary file
    large_binary = tmp_path / "huge.bin"
    large_binary.write_bytes(b"\x00" * (200 * 1024))

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(tmp_path / "output.txt"),
        always_include=[str(large_binary)],
        max_file_size_kb=100,  # Block files > 100KB
    )

    combiner = CodeMeld(config)
    combiner.execute()

    # The file should be filtered out, so the output file should not be created
    # or should be empty if it was created by some other mechanism.
    output_file_path = tmp_path / "output.txt"
    assert not output_file_path.exists() or output_file_path.read_text() == "", (
        "Output file should not exist or be empty if all files are filtered out."
    )
