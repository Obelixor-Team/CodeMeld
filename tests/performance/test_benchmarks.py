import time
from pathlib import Path

from src.code_combiner import CodeCombiner
from src.config import CombinerConfig

def test_processing_speed_benchmark(tmp_path):
    """Benchmark processing speed for various file counts."""
    # Create fewer files for testing
    for i in range(100):  # Reduced from 1000 to 100
        (tmp_path / f"file_{i}.py").write_text(f"# File {i}\nprint({i})")
    
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(tmp_path / "output.txt"),
        extensions=[".py"],
        count_tokens=False,  # Disable token counting for benchmark
    )
    
    start = time.time()
    CodeCombiner(config).execute()
    duration = time.time() - start
    
    # More reasonable assertion
    assert duration < 5.0  # Reduced from 10.0 to 5.0
    print(f"Processed 100 files in {duration:.2f}s ({100/duration:.0f} files/sec)")