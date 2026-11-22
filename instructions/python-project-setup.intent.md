# Intent

Give Python projects one setup profile (uv, required files, layout) that layers onto whatever general project-setup standards are in use.

## Goals

1. Python projects get a consistent, uv-based setup.
2. The profile stands alone: it adds Python specifics without depending on any named skill or instruction file.

## Requirements

- Build tool is `uv`; `pyproject.toml`, `.python-version`, and a committed `uv.lock` are required.
- No coupling: refer to other standards by capability, never by name.

## Log

- 2026-11-22: [agent] Created this intent file. Removed named references to project-setup, python-development, and technical-documentation; other standards are now described by capability so the profile stands alone.
