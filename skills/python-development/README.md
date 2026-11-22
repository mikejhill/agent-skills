# python-development

Python standards on the Astral toolchain, for three sizes of work: inline snippets, single-file scripts with inline dependencies, and packaged projects.

## Use

Loads automatically when the agent writes, refactors, or reviews Python. Examples:

- "Write a script that renames these photos by date."
- "Set up a new Python CLI project."

## Requirements

- [uv](https://docs.astral.sh/uv/) for scripts and projects. uv installs Python, ruff, ty, pytest, and poe per project, so nothing else is installed globally.

## Results

- Scripts: one `.py` file with PEP 723 metadata, run with `uv run`.
- Projects: `src/<package>/` layout, `pyproject.toml` holding all tool config, and `uv run poe check` passing (lint, format, strict types, tests with coverage).
- Code is class-based, fully typed, and documented, with diagnostics on stderr.
