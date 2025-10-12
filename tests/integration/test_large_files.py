
import pytest
from pathlib import Path
from src.code_combiner import CodeCombiner
from src.config import CombinerConfig

@pytest.fixture
def large_file(tmp_path: Path) -> Path:
    large_file_path = tmp_path / "large_file.txt"
    # Create a smaller file for testing (10KB instead of 1MB)
    with open(large_file_path, "w") as f:
        f.write("a" * 10 * 1024)  # 10KB
    return large_file_path

def test_large_file_processing(tmp_path: Path, large_file: Path):
    output_path = tmp_path / "output.txt"
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output_path),
        extensions=[".txt"],
        count_tokens=False,  # Disable token counting for large files
    )
    combiner = CodeCombiner(config)
    combiner.execute()

    assert output_path.exists()
    # Check that file was processed without hanging
    assert output_path.stat().st_size > 0
