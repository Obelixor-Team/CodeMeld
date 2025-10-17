# Copyright (c) 2025 skum

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.formatters import (
    FormatterFactory,
    JSONFormatter,
    MarkdownFormatter,
    OutputFormatter,
    TextFormatter,
    XMLFormatter,
)


def test_create_text_formatter():
    formatter = FormatterFactory.create("text")
    assert isinstance(formatter, TextFormatter)


def test_create_text_formatter_with_header_width():
    formatter = FormatterFactory.create("text", header_width=100)
    assert isinstance(formatter, TextFormatter)
    assert formatter.header_width == 100


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
    with pytest.raises(
        TypeError,
        match="Formatter 'text' initialization failed: Unknown arguments for text formatter: unknown_arg",
    ):
        FormatterFactory.create("text", header_width=80, unknown_arg="value")


def test_create_markdown_formatter_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError,
        match="Formatter 'markdown' initialization failed: Unknown arguments for markdown formatter: unknown_arg",
    ):
        FormatterFactory.create("markdown", unknown_arg="value")


def test_create_json_formatter_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError,
        match="Formatter 'json' initialization failed: Unknown arguments for json formatter: unknown_arg",
    ):
        FormatterFactory.create("json", unknown_arg="value")


def test_create_xml_formatter_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError,
        match="Formatter 'xml' initialization failed: Unknown arguments for xml formatter: unknown_arg",
    ):
        FormatterFactory.create("xml", unknown_arg="value")


def test_text_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError, match="Unknown arguments for text formatter: unknown_arg"
    ):
        TextFormatter(header_width=80, custom_file_headers={}, unknown_arg="value")


def test_markdown_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError, match="Unknown arguments for markdown formatter: unknown_arg"
    ):
        MarkdownFormatter(custom_file_headers={}, unknown_arg="value")


def test_json_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError, match="Unknown arguments for json formatter: unknown_arg"
    ):
        JSONFormatter(custom_file_headers={}, unknown_arg="value")


def test_xml_formatter_direct_init_with_unknown_arg_raises_error():
    with pytest.raises(
        TypeError, match="Unknown arguments for xml formatter: unknown_arg"
    ):
        XMLFormatter(custom_file_headers={}, unknown_arg="value")


def test_text_formatter_with_custom_header():
    custom_headers = {"py": "# Python File: {path}"}
    formatter = FormatterFactory.create("text", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    expected_output = "# Python File: my_script.py\nprint('Hello')\n\n"
    assert formatter.format_file(relative_path, content) == expected_output


def test_markdown_formatter_with_custom_header():
    custom_headers = {
        "js": "// JavaScript File: {path}"
    }  # Custom header no longer includes ```lang
    formatter = FormatterFactory.create("markdown", custom_file_headers=custom_headers)
    relative_path = Path("my_script.js")
    content = "console.log('Hello');"
    expected_output = "// JavaScript File: my_script.js\n```js\nconsole.log('Hello');\n```\n\n"  # Formatter adds ```js
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



def test_markdown_formatter_custom_header_with_invalid_placeholder():
    custom_headers = {"js": "// JavaScript File: {foo}"}
    formatter = FormatterFactory.create("markdown", custom_file_headers=custom_headers)
    relative_path = Path("my_script.js")
    content = "console.log('Hello');"
    with pytest.raises(KeyError):
        formatter.format_file(relative_path, content)


def test_text_formatter_begin_end_output():
    formatter = TextFormatter()
    assert formatter.begin_output() == ""
    assert formatter.end_output() == ""


def test_markdown_formatter_begin_end_output():
    formatter = MarkdownFormatter()
    assert formatter.begin_output() == ""
    assert formatter.end_output() == ""


def test_json_formatter_streaming():
    formatter = JSONFormatter()
    assert formatter.begin_output() == "{\n"
    assert (
        formatter.format_file(Path("file1.txt"), "content1")
        == '    "file1.txt": "content1"'
    )
    assert (
        formatter.format_file(Path("file2.txt"), "content2")
        == ',\n    "file2.txt": "content2"'
    )
    assert formatter.end_output() == "\n}"


def test_xml_formatter_begin_end_output():
    formatter = XMLFormatter()
    assert (
        formatter.begin_output()
        == '<?xml version="1.0" encoding="UTF-8"?>\n<codebase>\n'
    )
    assert formatter.end_output() == "</codebase>"


def test_xml_formatter_content_escaping():
    formatter = XMLFormatter()
    content = "<tag>&'</tag>"
    formatted_content = formatter.format_file(Path("file.xml"), content)
    assert "&lt;tag&gt;&amp;'&lt;/tag&gt;" in formatted_content


@patch("importlib.metadata.entry_points")
def test_formatter_factory_plugin_loading(mock_entry_points):
    class PluginFormatter(OutputFormatter):
        format_name = "plugin"

        def format_file(self, relative_path: Path, content: str) -> str:
            return ""

        def begin_output(self) -> str:
            return ""

        def end_output(self) -> str:
            return ""

        def supports_streaming(self) -> bool:
            return True

    mock_entry_point = MagicMock()
    mock_entry_point.name = "plugin"
    mock_entry_point.load.return_value = PluginFormatter
    mock_entry_points.return_value = [mock_entry_point]

    FormatterFactory._plugins_loaded = False
    FormatterFactory._formatters = {
        "text": TextFormatter,
        "markdown": MarkdownFormatter,
        "json": JSONFormatter,
        "xml": XMLFormatter,
    }
    formatter = FormatterFactory.create("plugin")
    assert isinstance(formatter, PluginFormatter)


@patch("importlib.metadata.entry_points")
def test_formatter_factory_plugin_loading_error(mock_entry_points, caplog):
    mock_entry_point = MagicMock()
    mock_entry_point.name = "bad_plugin"
    mock_entry_point.load.side_effect = Exception("loading error")
    mock_entry_points.return_value = [mock_entry_point]

    FormatterFactory._plugins_loaded = False
    FormatterFactory._formatters = {
        "text": TextFormatter,
        "markdown": MarkdownFormatter,
        "json": JSONFormatter,
        "xml": XMLFormatter,
    }
    with pytest.raises(ValueError):
        FormatterFactory.create("bad_plugin")
    assert "Failed to load formatter plugin bad_plugin: loading error" in caplog.text


def test_formatter_factory_malformed_json_custom_headers():
    with pytest.raises(ValueError, match="Invalid JSON for custom file headers"):
        FormatterFactory.create("text", custom_file_headers="{invalid json}")


def test_text_formatter_custom_header_with_invalid_placeholder():
    custom_headers = {"py": "# Python File: {lang}"}
    formatter = FormatterFactory.create("text", custom_file_headers=custom_headers)
    relative_path = Path("my_script.py")
    content = "print('Hello')"
    with pytest.raises(KeyError, match="'lang'"):
        formatter.format_file(relative_path, content)
