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
- `.github/` (or the host's equivalent) for CI workflows and issue/PR templates
- Source and test directories per language conventions

**MUST NOT:**

- Temporary files in root
- Config inside source/test dirs (unless language requires it)
- Source/test files at root without directory separation

## Standard Directories

| Directory    | Purpose                                           |
| ------------ | ------------------------------------------------- |
| `docs/`      | All documentation beyond root-level files         |
| `.github/`   | CI workflows, issue and PR templates              |
| `.tmp/`      | Temporary agent/developer workspace (untracked)   |
| Source dir   | `src/`, `lib/`, `cmd/`, `internal/`, `pkg/`, root |
| Test dir     | `tests/`, `spec/`, colocated, or `src/test/`      |

Python-specific layout and tooling: see `python-project-setup.instructions.md`.
