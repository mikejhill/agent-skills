# Intent

Give Python projects one setup profile (uv, required files, layout) that layers onto whatever general project-setup standards are in use.

## Goals

1. Python projects get a consistent, uv-based setup.
2. The profile stands alone: it adds Python specifics without depending on any named skill or instruction file.

## Requirements

- Applies to `**/*.py`, `**/pyproject.toml`, `**/uv.lock`, and `**/.python-version`.
- Build tool is `uv` always, except for throwaway scripts.
- Required files: `pyproject.toml`, `.python-version`, and a committed `uv.lock`.
- Forbidden files: `main.py`, `setup.py`, `setup.cfg`, `Pipfile`, `requirements.txt`.
- Layout: `src/<package>/` for source and `tests/` for tests.
- Dev tools go in `[dependency-groups]` (PEP 735), not `[project.optional-dependencies]`.
- Run everything with `uv run <command>`; global CLIs via `uv tool install`.
- The virtual environment is managed by uv (`uv sync`), never created by hand.
- No coupling: refer to other standards by capability, never by name.

## Log

- 2026-11-22: [agent] Created this intent file. Removed named references to project-setup, python-development, and technical-documentation; other standards are now described by capability so the profile stands alone.
