# 1. Use Makefile for Build Automation

*   **Status:** Accepted
*   **Date:** 2025-10-16

## Context and Problem Statement

The project needs a consistent and easy way to manage common development tasks such as installing dependencies, running tests, linting, and formatting the codebase. Relying on developers to remember and run individual commands can lead to inconsistencies and errors.

## Decision Drivers

*   Simplicity and ease of use.
*   Ubiquity in the Python ecosystem.
*   Ability to chain commands.
*   Desire to have a single entry point for all build and development tasks.

## Considered Options

*   **Makefile:** A classic build automation tool. It's simple, well-understood, and powerful enough for this project's needs.
*   **tox:** A powerful tool for testing in multiple Python environments. It's more complex than a Makefile and might be overkill for this project.
*   **invoke:** A Python-based task execution tool. It's a good alternative to Make, but Make is more common and requires no extra dependencies.
*   **Custom shell scripts:** Can be brittle and less organized than a Makefile.

## Decision Outcome

Chosen option: **Makefile**, because it is simple, effective, and a well-established convention in many projects. It provides a straightforward way to define and run all the necessary development tasks.
