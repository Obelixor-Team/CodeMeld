# Documentation

This directory contains project documentation.

## Architecture Decision Records (ADRs)

ADRs are located in the `adr` directory. They document important architectural decisions made throughout the project's lifecycle.

*   [ADR-001: Use Makefile for Build Automation](./adr/001-use-makefile-for-build-automation.md)

## Performance

The `CodeMeld` script is designed to be efficient, but its performance can be affected by several factors:

*   **Number of files:** The more files to process, the longer it will take.
*   **File size:** Large files consume more memory and take longer to read.
*   **Token counting:** Enabling token counting adds overhead, as it requires an extra processing step.
*   **Memory usage:** The script can operate in two modes: in-memory and streaming. The in-memory mode is faster but consumes more memory. The streaming mode is slower but can handle a larger number of files and larger file sizes without running out of memory.

## Security

Security is an important consideration for `CodeMeld`.

*   **File system access:** The script reads files from the local file system. It includes a security filter to prevent it from accessing files outside the specified project directory. This is a crucial safeguard against accidentally including sensitive files from other parts of the system.
*   **Symbolic links:** By default, the script does not follow symbolic links. This is a security measure to prevent it from following a link to a sensitive file or directory outside the project.
*   **Dependencies:** The project has a minimal set of dependencies, which are regularly scanned for vulnerabilities using `dependabot`.
