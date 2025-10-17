# Copyright (c) 2025 skum


from src.code_combiner import CodeMeld
from src.config import CombinerConfig


def test_processing_speed_benchmark(benchmark, tmp_path):
    """Benchmark processing speed for 1K files."""
    num_files = 1000
    for i in range(num_files):
        (tmp_path / f"file_{i}.py").write_text(f"# File {i}\nprint({i})")

    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(tmp_path / "output.txt"),
        extensions=[".py"],
        count_tokens=False,  # Disable token counting for benchmark
    )

    # Benchmark the execute method
    benchmark(CodeMeld(config).execute)

    # Assert that the output file exists
    output_path = tmp_path / "output.txt"
    assert output_path.exists()
