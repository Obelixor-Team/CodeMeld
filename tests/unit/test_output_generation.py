import pytest
from src.code_combiner import convert_to_text

def test_convert_to_text_invalid_json():
    invalid_json = '{"file1.py": "print(\'hello\')" ' 
    result = convert_to_text(invalid_json, "json", 80, "text")
    assert "Error: Could not parse JSON content" in result
