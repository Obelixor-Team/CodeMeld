import time
from pathlib import Path

from src.code_combiner import CodeCombiner
from src.config import CombinerConfig

def test_processing_speed_benchmark(tmp_path):
    """Benchmark processing speed for various file counts."""
    
    # Create 1000 small files
    for i in range(1000):
        (tmp_path / f"file_{i}.py").write_text(f"# File {i}\nprint({i})")
    
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(tmp_path / "output.txt"),
        extensions=[".py"]
    )
    
    start = time.time()
    CodeCombiner(config).execute()
    duration = time.time() - start
    
    # Should process at least 100 files/second
    assert duration < 10.0
    print(f"Processed 1000 files in {duration:.2f}s ({1000/duration:.0f} files/sec)")