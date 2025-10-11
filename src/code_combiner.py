from pathlib import Path
import argparse
import tiktoken
import pathspec


def is_code_file(filename, extensions):
    """Check if file has a code extension"""
    return Path(filename).suffix.lower() in extensions


def get_gitignore_spec(root_path):
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
    root_dir, output_file, extensions=None, use_gitignore=True, include_hidden=False
):
    """Scan directory and combine code files into one output file"""

    root_path = Path(root_dir)
    output_path = Path(output_file)
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

    try:
        with open(output_path, "w", encoding="utf-8") as outfile:
            all_files = root_path.rglob("*")
            files_to_process = []

            for file_path in all_files:
                if file_path.resolve() == output_path.resolve():
                    continue

                if not file_path.is_file():
                    continue

                if not is_code_file(file_path.name, extensions):
                    continue

                relative_path = file_path.relative_to(root_path)
                is_hidden = any(part.startswith(".") for part in relative_path.parts)

                # If --no-gitignore is present, we skip all gitignore and hidden file filtering
                if not use_gitignore:
                    files_to_process.append(file_path)
                    continue

                # If --no-gitignore is NOT present, apply filtering rules
                # Rule 1: Skip if not including hidden files and it is hidden
                if not include_hidden and is_hidden:
                    continue

                # Rule 2: Skip if respecting gitignore and file is matched by gitignore
                # This rule is overridden for hidden files if include_hidden is True
                if spec and spec.match_file(str(relative_path)):
                    if not (include_hidden and is_hidden):
                        continue

                files_to_process.append(file_path)

            for file_path in files_to_process:
                relative_path = file_path.relative_to(root_path)

                try:
                    with open(file_path, "r", encoding="utf-8") as infile:
                        content = infile.read()

                    # Write file header
                    outfile.write(f"\n{'='*80}\n")
                    outfile.write(f"FILE: {relative_path}\n")
                    outfile.write(f"{'='*80}\n\n")

                    # Write file content
                    outfile.write(content)

                    # Add some spacing between files
                    outfile.write("\n\n")

                    print(f"Processed: {relative_path}")

                except UnicodeDecodeError:
                    print(f"Skipping binary file: {relative_path}")
                except Exception as e:
                    print(f"Error reading {relative_path}: {e}")

        print(f"\nAll code files have been combined into: {output_path}")

        # Count tokens in the output file
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                encoding = tiktoken.get_encoding("cl100k_base")
                tokens = encoding.encode(content)
                print(f"Total tokens in combined file: {len(tokens)}")
        except ValueError as e:
            print(f"Error counting tokens: {e}")

    except Exception as e:
        print(f"Error: {e}")


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

    args = parser.parse_args()
    directory_path = Path(args.directory)

    if not directory_path.is_dir():
        print(f"Error: Directory '{args.directory}' does not exist.")
        return

    scan_and_combine_code_files(
        directory_path,
        args.output,
        args.extensions,
        not args.no_gitignore,
        args.include_hidden,
    )


if __name__ == "__main__":
    main()
