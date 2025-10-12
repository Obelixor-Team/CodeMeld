
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
