---
name: Project Structure
description: Directory organization and file placement conventions.
---

# Project Structure Standards

Separate documentation, configuration, temporary work, and source code
into designated directories following language/framework conventions.

## Rules

**MUST:**

- Configuration at root or `config/`
- Documentation in `docs/` with `README.md` at root
- `.tmp/` for temporary artifacts (never committed, must be in `.gitignore`)
- `.github/` for workflows, issue templates, Copilot customization
- Source and test directories per language conventions

**MUST NOT:**

- Temporary files in root
- Config inside source/test dirs (unless language requires it)
- Source/test files at root without directory separation

## Standard Directories

| Directory    | Purpose                                           |
| ------------ | ------------------------------------------------- |
| `docs/`      | All documentation beyond root-level files         |
| `.github/`   | Workflows, issue templates, Copilot customization |
| `.tmp/`      | Temporary agent/developer workspace (untracked)   |
| Source dir   | `src/`, `lib/`, `cmd/`, `internal/`, `pkg/`, root |
| Test dir     | `tests/`, `spec/`, colocated, or `src/test/`      |

## Python Projects

- **Build tool**: `uv` (always). No exceptions except throwaway scripts.
- **Required**: `pyproject.toml`, `.python-version`, `uv.lock` (committed)
- **Forbidden**: `main.py`, `setup.py`, `setup.cfg`, `Pipfile`, `requirements.txt`
- **Layout**: `src/<package>/` for source, `tests/` for tests
- **Deps**: `[dependency-groups]` (PEP 735) for dev tools, not `[project.optional-dependencies]`
- **Execution**: `uv run <command>` always; `uv tool install` for global CLIs
- **Venv**: managed by uv via `uv sync` — never create manually
