from pathlib import Path

# This is a simplified version of the OutputFormatter for the example.
# In a real-world scenario, this would be imported from the code_combiner package.
class OutputFormatter:
    def __init__(self, **kwargs):
        # This method is intentionally empty for this example, as no specific
        # initialization is required for the base OutputFormatter in this context.
        pass

    def format_file(self, relative_path: Path, content: str) -> str:
        raise NotImplementedError

    def begin_output(self) -> str:
        raise NotImplementedError

    def end_output(self) -> str:
        raise NotImplementedError

    def supports_streaming(self) -> bool:
        raise NotImplementedError

class YAMLFormatter(OutputFormatter):
    format_name = "yaml"

    def format_file(self, relative_path: Path, content: str) -> str:
        # Simple YAML-like output
        return f'  - file: "{relative_path}"\n    content: |\n' + "\n".join(f"      {line}" for line in content.splitlines())

    def begin_output(self) -> str:
        return "files:\n"

    def end_output(self) -> str:
        return ""

    def supports_streaming(self) -> bool:
        return True
