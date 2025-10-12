from pathlib import Path

def test_complete_refactored_flow(tmp_path):
    """Test the entire refactored architecture end-to-end."""
    # Create test files
    (tmp_path / "file1.py").write_text("print('test')")
    (tmp_path / "file2.js").write_text("console.log('test')")
    (tmp_path / ".gitignore").write_text("*.log")
    (tmp_path / "debug.log").write_text("should be ignored")
    
    output = tmp_path / "output.txt"
    
    # Run with various options
    from src.code_combiner import CodeCombiner
    from src.config import CombinerConfig
    
    config = CombinerConfig(
        directory_path=tmp_path,
        output=str(output),
        extensions=[".py", ".js"],
        use_gitignore=True,
        count_tokens=False,
    )
    
    combiner = CodeCombiner(config)
    combiner.execute()
    
    # Verify
    assert output.exists()
    content = output.read_text()
    assert "print('test')" in content
    assert "console.log('test')" in content
    assert "should be ignored" not in content