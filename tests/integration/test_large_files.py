
import pytest
from pathlib import Path
from src.code_combiner import CodeCombiner
from src.config import CombinerConfig

@pytest.fixture
def large_file(tmp_path: Path) -> Path:
    large_file_path = tmp_path / "large_file.txt"
    # Create a 1MB file
    with open(large_file_path, "w") as f:
        f.write("a" * 1024 * 1024)
    return large_file_path

def test_large_file_processing(tmp_path: Path, large_file: Path):
    output_path = tmp_path / "output.txt"
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_path),
        extensions=[".txt"],
    )
    combiner = CodeCombiner(config)
    combiner.execute()

    assert output_path.exists()
    # Check that the output file is roughly the size of the input file
    # It will be slightly larger due to the header
    assert output_path.stat().st_size > 1024 * 1024
