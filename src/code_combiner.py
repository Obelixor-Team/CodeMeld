from pathlib import Path
import argparse
import tiktoken
import pathspec
import os

try:
    import tiktoken
except ImportError:
    tiktoken = None
    print("Warning: tiktoken not found. Token counting will be skipped.")


def is_code_file(filename: str, extensions: list[str], exclude_extensions: list[str]) -> bool:
    """Check if file has a code extension"""
    suffix = Path(filename).suffix.lower()
    if suffix in exclude_extensions:
        return False
    return suffix in extensions


def should_process_file(
    file_path: Path,
    root_path: Path,
    output_path: Path,
    spec: pathspec.PathSpec | None,
    extensions: list[str],
    exclude_extensions: list[str],
    use_gitignore: bool,
    include_hidden: bool,
) -> bool:
    """Determine if a file should be processed based on filtering rules."""
    if file_path.resolve() == output_path.resolve():
        return False

    if not file_path.is_file():
        return False

    if not is_code_file(file_path.name, extensions, exclude_extensions):
        return False

    relative_path = file_path.relative_to(root_path)
    is_hidden = any(part.startswith(".") for part in relative_path.parts)

    # If --no-gitignore is present, we skip all gitignore and hidden file filtering
    if not use_gitignore:
        return True

    # If --no-gitignore is NOT present, apply filtering rules
    # Rule 1: Skip if not including hidden files and it is hidden
    if not include_hidden and is_hidden:
        return False

    # Rule 2: Skip if respecting gitignore and file is matched by gitignore
    # This rule is overridden for hidden files if include_hidden is True
    if spec and spec.match_file(str(relative_path)):
        if not (include_hidden and is_hidden):
            return False

    return True


def get_gitignore_spec(root_path: Path) -> pathspec.PathSpec | None:
    """Get the pathspec from the .gitignore file"""
    current_path = root_path.resolve()
    while current_path != current_path.parent:
        gitignore_path = current_path / ".gitignore"
        if gitignore_path.is_file():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f)
        current_path = current_path.parent
    return None


def scan_and_combine_code_files(
    root_dir: Path,
    output_file: str,
    extensions: list[str] | None = None,
    exclude_extensions: list[str] | None = None,
    use_gitignore: bool = True,
    include_hidden: bool = False,
    count_tokens: bool = True,
    header_width: int = 80,
):
    """Scan directory and combine code files into one output file"""

    root_path = Path(root_dir)
    output_path = Path(output_file)

    if not root_path.is_dir():
        print(f"Error: Directory '{root_path}' does not exist.")
        return

    output_dir = output_path.parent
    if not output_dir.is_dir():
        print(f"Error: Output directory '{output_dir}' does not exist.")
        return
    if not os.access(output_dir, os.W_OK):
        print(f"Error: No write permissions for output directory '{output_dir}'.")
        return

    spec = None
    if use_gitignore:
        spec = get_gitignore_spec(root_path)

    # Default code file extensions
    if extensions is None:
        extensions = [
            ".py",
            ".js",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".ts",
            ".html",
            ".css",
            ".xml",
            ".json",
            ".yml",
            ".yaml",
            ".sql",
            ".sh",
            ".bat",
            ".ps1",
            ".md",
            ".txt",
        ]
    else:
        validated_extensions = []
        for ext in extensions:
            if not ext.startswith("."):
                print(f"Error: Custom extension '{ext}' must start with a dot (e.g., '.{ext}').")
                return
            validated_extensions.append(ext.lower())
        extensions = validated_extensions

    # Normalize exclude extensions
    if exclude_extensions is None:
        exclude_extensions = []
    else:
        normalized_exclude_extensions = []
        for ext in exclude_extensions:
            if not ext.startswith("."):
                print(f"Error: Exclude extension '{ext}' must start with a dot (e.g., '.{ext}').")
                return
            normalized_exclude_extensions.append(ext.lower())
        exclude_extensions = normalized_exclude_extensions

    try:
        combined_content = ""
        all_files = root_path.rglob("*")
        files_to_process = []

        for file_path in all_files:
            if should_process_file(
                file_path,
                root_path,
                output_path,
                spec,
                extensions,
                exclude_extensions,
                use_gitignore,
                include_hidden,
            ):
                files_to_process.append(file_path)

        for file_path in files_to_process:
            relative_path = file_path.relative_to(root_path)

            try:
                with open(file_path, "r", encoding="utf-8") as infile:
                    content = infile.read()

                # Write file header
                combined_content += f"\n{'='*header_width}\n"
                combined_content += f"FILE: {relative_path}\n"
                combined_content += f"{'='*header_width}\n\n"

                # Write file content
                combined_content += content

                # Add some spacing between files
                combined_content += "\n\n"

                print(f"Processed: {relative_path}")

            except UnicodeDecodeError:
                print(f"Skipping binary file: {relative_path}")
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}")

        with open(output_path, "w", encoding="utf-8") as outfile:
            outfile.write(combined_content)

        print(f"\nAll code files have been combined into: {output_path}")

        # Count tokens in the output file
        if count_tokens and tiktoken:
            try:
                encoding = tiktoken.get_encoding("cl100k_base")
                tokens = encoding.encode(combined_content)
                print(f"Total tokens in combined file: {len(tokens)}")
            except ValueError as e:
                print(f"Error counting tokens in combined file: {e}")
        elif count_tokens and not tiktoken:
            print("Token counting skipped: 'tiktoken' library not installed.")

    except Exception as e:
        print(f"Error creating or writing to output file {output_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Combine code files from a directory into a single file."
    )
    parser.add_argument("directory", help="The directory to scan for code files.")
    parser.add_argument(
        "-o",
        "--output",
        default="combined_code.txt",
        help="The output file name (default: combined_code.txt).",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        help="Custom file extensions to include (e.g., .py .js .ts).",
    )
    parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Do not respect the .gitignore file.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and folders (those starting with a dot).",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Custom file extensions to exclude (space separated, e.g., .txt .md). Exclusions take precedence over inclusions.",
    )
    parser.add_argument(
        "--no-tokens",
        action="store_true",
        help="Do not count tokens in the combined output file.",
    )
    parser.add_argument(
        "--header-width",
        type=int,
        default=80,
        help="Width of the separator lines in the combined file header (default: 80).",
    )

    args = parser.parse_args()
    directory_path = Path(args.directory)

    if not directory_path.is_dir():
        print(f"Error: Directory '{args.directory}' does not exist.")
        return

    scan_and_combine_code_files(
        directory_path,
        args.output,
        args.extensions,
        args.exclude,
        not args.no_gitignore,
        args.include_hidden,
        not args.no_tokens,
        args.header_width,
    )


if __name__ == "__main__":
    main()
