# Intent

Codify Python development standards — from one-off snippets to packaged CLI tools and libraries — on the Astral toolchain.

## Goals

1. Every rule enforceable by tooling or verifiable by inspection
2. Three modes: OneOff (inline), Script (single-file PEP 723), FullProject (packaged)
3. Astral toolchain: uv for environments and packaging, ruff for linting and formatting, ty for strict type checking; poe for task running
4. Strongly class-based design: behaviour in methods, module-level functions only where a tool requires them
5. Every file, class, and method documented concisely; comments as short logical headers, not inline narration
6. Templates are copy-paste ready and pass `uv run poe check` unmodified
7. Progressive discovery: SKILL.md holds the always-on rules; topic references load on demand

## Log

- 2026-03-15: Created skill targeting Python CLI tools and automation scripts
- 2026-04-03: Standardized toolchain on uv, Ruff, and ty replacing pip,
  flake8, and mypy
- 2026-04-03: Refined via tribunal (2 iterations, severity 78 → 25) — added
  FA rule, error handling patterns, reduced standards.md duplication
- 2026-04-03 [agent]: Fixed constructor mismatch between SKILL.md example and
  templates.md; added exceptions.py to refactor example; added Namespace typing
  guidance
- 2026-10-02 [agent]: Renamed python-scripting → python-development. Added
  Script mode (PEP 723), poe tasks, strict ty (`all = "error"`), expanded ruff
  rule set, `uv_build` backend, classmethod entry points (no top-level
  functions), file/class/method docstring and comment rules, full repository
  layout (`scripts/`, `docs/`, root docs), coverage gate. Split standards.md
  into project-setup, code-standards, cli, and testing references for
  progressive discovery. Templates verified with ruff 0.16.10, ty 0.0.84,
  uv 0.11.32
