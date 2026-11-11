---
name: python-development
description: Use when creating, modifying, refactoring, or reviewing Python code — one-off snippets, single-file uv scripts, or packaged projects. Enforces the Astral toolchain (uv, ruff, ty with strict type checking), poe task runners, src/<package>/ layout, class-based OOP design, file/class/method docstrings, concise comments, structured logging, and pytest testing.
---

# Python Development

Produce Python in one of three modes. This file holds the rules that always apply; load the reference files listed under [Progressive Discovery](#progressive-discovery) only when the task needs them.

## Modes

| Mode | Use when | Output |
| --- | --- | --- |
| **OneOff** | Snippet, REPL expression, quick inline answer | 1–5 lines (max 10), no file |
| **Script** | Single reusable file, no package needed | One `.py` file with PEP 723 inline metadata, run with `uv run` |
| **FullProject** | Package, reusable tool, CLI, or multi-file code | `src/<package>/` project managed by uv |

Default to **FullProject** when ambiguous. Details and guardrails: [references/modes.md](references/modes.md).

## Core Rules (Script and FullProject)

**Toolchain**

- uv for Python versions, environments, dependencies, locking, and running (`uv add`, `uv sync`, `uv run`). Never `pip`, `venv`, `poetry`, or `requirements.txt`.
- ruff for linting and formatting; ty for type checking with **every rule set to error** (`[tool.ty.rules] all = "error"`).
- poe (`poethepoet`) for project tasks: `uv run poe check` must pass before delivery.
- All tool config lives in `pyproject.toml`; no separate config files.

**Layout**

- All FullProject source code lives in `src/<package>/` — no flat layouts, no `main.py` at the root.
- Tests live in `tests/`, mirroring the source modules.

**Design**

- STRONGLY prefer classes. Put behaviour in methods; avoid module-level functions.
- The only accepted module-level functions are pytest fixtures in `conftest.py`. Entry points are classmethods (`package.__main__:Application.main`).
- `@dataclass(frozen=True, slots=True)` for configuration and value objects; regular classes for stateful services.
- No module-level mutable state; module level holds only imports, constants, `logger`, and class definitions.
- Guard clauses at method entry; max 3 levels of nesting.

**Typing**

- Annotate every parameter and return type; `from __future__ import annotations` in every module.
- No `Any`, no bare `# type: ignore`, no unexplained `cast()`.
- Convert untyped boundaries (argparse `Namespace`, JSON, env vars) to typed dataclasses immediately.

**Documentation and comments**

- Every file starts with a docstring stating what the file is for.
- Every class, method, and function has a docstring — one line by default; add Google-style `Args:`/`Returns:`/`Raises:` only when they say something the signature doesn't.
- Use short comments as logical headers for blocks of code (`# Validate inputs`, `# Build report`).
- No inline commentary on obvious code. Inline comments only for niche behaviour, workarounds, or surprising exceptions.

**Errors and output**

- Specific exceptions only; custom hierarchy rooted at `AppError` in `exceptions.py`; chain with `raise ... from err`.
- Never bare `except:` or silent suppression.
- Diagnostics go through `logging` (stderr); program output goes to stdout via `sys.stdout.write`. No `print()` outside OneOff.

## Procedure

1. Pick the mode ([modes.md](references/modes.md)).
2. **FullProject:** scaffold with `uv init --package --build-backend uv <name>`, add dev tools with `uv add --dev ruff ty pytest pytest-cov poethepoet`, then apply the `pyproject.toml` settings from [project-setup.md](references/project-setup.md).
3. **Script:** create the file with `uv init --script <file>.py` and add dependencies with `uv add --script <file>.py <dep>`.
4. Write code following [code-standards.md](references/code-standards.md); copy file skeletons from [templates.md](references/templates.md).
5. Write tests following [testing.md](references/testing.md).
6. Verify: `uv run poe fix` then `uv run poe check` (FullProject), or the script commands in [modes.md](references/modes.md). Fix every finding before delivering; never weaken tool config to make it pass.

## Progressive Discovery

Read only what the task needs:

| Read | When |
| --- | --- |
| [references/modes.md](references/modes.md) | Choosing a mode; writing a OneOff or a PEP 723 script |
| [references/project-setup.md](references/project-setup.md) | Creating or reconfiguring a project: uv, layout, `pyproject.toml`, ruff, strict ty, poe tasks, verification |
| [references/code-standards.md](references/code-standards.md) | Writing or reviewing code: OOP rules, docstrings, comments, typing, errors, logging, naming |
| [references/cli.md](references/cli.md) | Building a command-line interface or entry point |
| [references/testing.md](references/testing.md) | Writing or reviewing tests, fixtures, coverage |
| [references/templates.md](references/templates.md) | Copy-paste skeletons for every FullProject file |
| [references/examples.md](references/examples.md) | Worked OneOff, Script, and procedural-to-OOP refactor examples |

## Scope

**In scope:** Python scripts, CLI tools, libraries, and automation; refactors; packaging; testing.

**Out of scope unless requested:** web frameworks (Django, Flask, FastAPI), notebooks, ML pipelines, GUIs, C extensions, Docker or deployment. Async code is in scope only when the task needs concurrency.

User requirements override these defaults unless they break a core rule above; when they do, say so and ask.

## Trade-offs

When ambiguous, choose the left side:

- Maintainability over brevity
- Explicit types over inference
- Classes over procedural convenience
- Tooling-enforced rules over instruction-only rules
- Failing loudly over guessing
