---
name: Python project setup profile
description: Preserve the personal Python tooling and layout profile when setting up or changing Python projects.
applyTo: "**/*.py,**/pyproject.toml,**/uv.lock,**/.python-version"
---

# Python project setup profile

This scoped profile extends project-setup. Use python-development for implementation details. Shared folder and documentation conventions live in project-setup and project-documentation.

- **Build tool**: `uv` (always). No exceptions except throwaway scripts.
- **Required**: `pyproject.toml`, `.python-version`, `uv.lock` (committed)
- **Forbidden**: `main.py`, `setup.py`, `setup.cfg`, `Pipfile`, `requirements.txt`
- **Layout**: `src/<package>/` for source, `tests/` for tests
- **Deps**: `[dependency-groups]` (PEP 735) for dev tools, not `[project.optional-dependencies]`
- **Execution**: `uv run <command>` always; `uv tool install` for global CLIs
- **Venv**: managed by uv via `uv sync` — never create manually
