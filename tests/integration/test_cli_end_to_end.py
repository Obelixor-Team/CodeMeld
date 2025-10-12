import subprocess, sys, json

def test_cli_combines(tmp_path):
    (tmp_path / "f.py").write_text("print('ok')")
    output_file_path = tmp_path / "combined_code.txt"
    result = subprocess.run(
        [sys.executable, "src/code_combiner.py", str(tmp_path), "-e", ".py", "-o", str(output_file_path)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "combined_code.txt" in result.stdout
    assert (tmp_path / "combined_code.txt").is_file()
    file_content = (tmp_path / "combined_code.txt").read_text()
    assert "================================================================================" in file_content
    assert "FILE: f.py" in file_content
    assert "print('ok')" in file_content
    assert file_content.find("FILE: f.py") < file_content.find("print('ok')")
