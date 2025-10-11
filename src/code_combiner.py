from pathlib import Path
import argparse


def is_code_file(filename, extensions):
    """Check if file has a code extension"""
    return Path(filename).suffix.lower() in extensions


def scan_and_combine_code_files(root_dir, output_file, extensions=None):
    """Scan directory and combine code files into one output file"""

    root_path = Path(root_dir)
    output_path = Path(output_file)

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
            for file_path in root_path.rglob("*"):
                if file_path.is_file() and is_code_file(file_path.name, extensions):
                    relative_path = file_path.relative_to(root_path)

                    try:
                        with open(file_path, "r", encoding="utf-8") as infile:
                            content = infile.read()

                        # Write file header
                        outfile.write(f"\n{'='*80}\n")
                        outfile.write(f"FILE: {relative_path}\n")
                        outfile.write(f"{ '='*80}\n\n")

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

    except Exception as e:
        print(f"Error creating output file: {e}")


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

    args = parser.parse_args()
    directory_path = Path(args.directory)

    if not directory_path.is_dir():
        print(f"Error: Directory '{args.directory}' does not exist.")
        return

    scan_and_combine_code_files(directory_path, args.output, args.extensions)


if __name__ == "__main__":
    main()