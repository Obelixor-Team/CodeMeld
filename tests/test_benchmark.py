import pytest
from src.code_combiner import CodeMeld
from src.config import CombinerConfig, MemoryThresholdExceededError

@pytest.mark.benchmark(group="codemeld")
def test_inmemory_generation_benchmark(benchmark, tmp_path):
    """Benchmark performance of in-memory generation."""
    small_dir = tmp_path / "src"
    small_dir.mkdir()
    (small_dir / "a.py").write_text("print('a')")
    (small_dir / "b.py").write_text("print('b')")

    base_config = CombinerConfig(directory_path=small_dir)
    def run_in_memory(**kwargs):
        CodeMeld(base_config).execute()

    benchmark.pedantic(run_in_memory)

@pytest.mark.benchmark(group="codemeld")
def test_streaming_generation_benchmark(benchmark, tmp_path):
    """Benchmark performance of streaming generation."""
    small_dir = tmp_path / "src"
    small_dir.mkdir()
    (small_dir / "a.py").write_text("print('a')")
    (small_dir / "b.py").write_text("print('b')")

    stream_cfg = CombinerConfig(directory_path=small_dir, max_memory_mb=1)
    def run_streaming(**kwargs):
        try:
            CodeMeld(stream_cfg).execute()
        except MemoryThresholdExceededError:
            pass  # Expected behavior for streaming fallback

    benchmark.pedantic(run_streaming)