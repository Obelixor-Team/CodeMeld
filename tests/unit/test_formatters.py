from pathlib import Path
import pytest
from src.formatters import (
    FormatterFactory,
    TextFormatter,
    MarkdownFormatter,
    JSONFormatter,
    XMLFormatter,
    OutputFormatter,
)


def test_create_text_formatter():
    formatter = FormatterFactory.create("text")
    assert isinstance(formatter, TextFormatter)

def test_create_text_formatter_with_header_width():
    formatter = FormatterFactory.create("text", header_width=100)
    assert isinstance(formatter, TextFormatter)
    

def test_create_json_formatter():
    formatter = FormatterFactory.create("json")
    assert isinstance(formatter, JSONFormatter)



def test_create_xml_formatter():
    formatter = FormatterFactory.create("xml")
    assert isinstance(formatter, XMLFormatter)



def test_create_unknown_formatter_raises_error():
    with pytest.raises(ValueError):
        FormatterFactory.create("unknown_format")


class CustomFormatter(OutputFormatter):
    format_name = "custom"

    def format_file(self, relative_path: Path, content: str) -> str:
        return f"Custom formatted file: {relative_path}"

    def begin_output(self) -> str:
        return ""

    def end_output(self) -> str:
        return ""

    def supports_streaming(self) -> bool:
        return True


def test_register_and_create_custom_formatter():
    FormatterFactory.register("custom", CustomFormatter)
    formatter = FormatterFactory.create("custom")
    assert isinstance(formatter, CustomFormatter)

def test_create_text_formatter_with_unknown_arg_raises_error():
    with pytest.raises(TypeError, match="Unknown arguments for text formatter: unknown_arg"):
        FormatterFactory.create("text", header_width=80, unknown_arg="value")

def test_create_markdown_formatter_with_unknown_arg_raises_error():
    with pytest.raises(TypeError, match="Unknown arguments for markdown formatter: unknown_arg"):
        FormatterFactory.create("markdown", unknown_arg="value")

def test_create_json_formatter_with_unknown_arg_raises_error():
    with pytest.raises(TypeError, match="Unknown arguments for json formatter: unknown_arg"):
        FormatterFactory.create("json", unknown_arg="value")

def test_create_xml_formatter_with_unknown_arg_raises_error():
    with pytest.raises(TypeError, match="Unknown arguments for xml formatter: unknown_arg"):
        FormatterFactory.create("xml", unknown_arg="value")

def test_text_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(TypeError, match="Unknown arguments for text formatter: unknown_arg"):
        TextFormatter(header_width=80, unknown_arg="value")

def test_markdown_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(TypeError, match="Unknown arguments for markdown formatter: unknown_arg"):
        MarkdownFormatter(unknown_arg="value")

def test_json_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(TypeError, match="Unknown arguments for json formatter: unknown_arg"):
        JSONFormatter(unknown_arg="value")

def test_xml_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(TypeError, match="Unknown arguments for xml formatter: unknown_arg"):
        XMLFormatter(unknown_arg="value")

def test_text_formatter_with_custom_header():
    custom_headers = {"py": "# Python File: {path}"}
    formatter = FormatterFactory.create("text", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    expected_output = "# Python File: my_script.py\nprint('Hello')\n\n"
    assert formatter.format_file(relative_path, content) == expected_output

def test_markdown_formatter_with_custom_header():
    custom_headers = {"js": "```javascript\n// JavaScript File: {path}"}
    formatter = FormatterFactory.create("markdown", custom_file_headers=custom_headers)
    relative_path = Path("my_script.js")
    content = "console.log('Hello');"
    expected_output = "```javascript\n// JavaScript File: my_script.js\nconsole.log('Hello');\n```\n\n"
    assert formatter.format_file(relative_path, content) == expected_output

def test_text_formatter_with_no_matching_custom_header():
    custom_headers = {"java": "// Java File: {path}"}
    formatter = FormatterFactory.create("text", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    # Should fall back to default text header
    expected_output = (
        f"\n{'=' * 80}\n"
        f"FILE: my_script.py\n"
        f"{'=' * 80}\n\n"
        f"print('Hello')\n\n"
    )
    assert formatter.format_file(relative_path, content) == expected_output

def test_markdown_formatter_with_no_matching_custom_header():
    custom_headers = {"java": "// Java File: {path}"}
    formatter = FormatterFactory.create("markdown", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    # Should fall back to default markdown header
    expected_output = "## FILE: my_script.py\n\n```py\nprint('Hello')\n```\n\n"
    assert formatter.format_file(relative_path, content) == expected_output
