import pytest
from src.code_combiner import scan_and_combine_code_files, load_config_from_pyproject
from unittest.mock import patch

@patch('src.code_combiner.toml.load')
def test_scan_and_combine_code_files_command_line_override(mock_toml_load, temp_project_dir):
    # Mock the toml.load function to return a predefined configuration
    mock_toml_load.return_value = {
        "tool": {
            "code_combiner": {
                "extensions": [".js"],
                "header_width": 30,
            }
        }
    }

    output_file = temp_project_dir / "combined.txt"

    # Run with command-line arguments that override config
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=[".py"],
        exclude_extensions=[],
        header_width=40,
    )

    assert output_file.is_file()
    content = output_file.read_text()

    # Should use command-line extensions (.py) and header_width (40)
    assert "print('hello')" in content
    assert "console.log('world')" not in content
    assert f"\n{ '='*40}\n" in content

@patch('src.code_combiner.toml.load')
@patch('src.code_combiner.Path.is_file') # Patch Path.is_file
def test_scan_and_combine_code_files_config_file_only(mock_is_file, mock_toml_load, temp_project_dir): # Add mock_is_file
    # The load_config_from_pyproject function will call toml.load, which is mocked
    mock_toml_load.return_value = {
        "tool": {
            "code_combiner": {
                "extensions": [".js"],
                "header_width": 30,
            }
        }
    }
    mock_is_file.return_value = True # Make Path.is_file return True

    output_file = temp_project_dir / "combined_2.txt"
    config = load_config_from_pyproject(temp_project_dir)
    extensions = config.get("extensions", [])
    header_width = config.get("header_width", 80)
    scan_and_combine_code_files(
        temp_project_dir,
        str(output_file),
        extensions=extensions,
        exclude_extensions=[],
        header_width=header_width,
    )

    assert output_file.is_file()
    content_2 = output_file.read_text()

    # Should use config extensions (.js) and header_width (30)
    assert "print('hello')" not in content_2
    assert "console.log('world')" in content_2
    assert f"\n{ '='*30}\n" in content_2
