# Python Development Modes

## Mode Selection

Use these rules when the user does not choose a mode:

| Signal in the request | Mode |
| --- | --- |
| "snippet", "one-liner", "quick command", REPL expression, inline answer | OneOff |
| "script", single file, automation task, no package or tests requested | Script |
| "package", "tool", "CLI", "library", multi-file, tests, or anything long-lived | FullProject |
| Ambiguous | FullProject |

Promote a Script to a FullProject once it needs a second module, tests, or more than ~300 lines.

## OneOff

- 1–5 lines preferred, 10 maximum.
- No classes, docstrings, or scaffolding; `print()` is fine here.
- Use comprehensions, generators, `pathlib`, and other stdlib idioms.
- Type hints on any function definitions.
- Stdlib only, unless the user's context already has the dependency.
- To run with a third-party package without installing it: `uv run --with <package> python -c "..."`.

## Script

A single file that carries its own dependencies via [PEP 723](https://peps.python.org/pep-0723/) inline metadata. uv builds an isolated environment for it on demand.

### Guardrails

- Create with `uv init --script <name>.py --python 3.12`; add dependencies with `uv add --script <name>.py <package>`. Never hand-write `pip install` instructions.
- Optional shebang for direct execution: `#!/usr/bin/env -S uv run --script`.
- All core rules from SKILL.md apply: file docstring, classes over functions, strict typing, docstrings, concise header comments, `logging` for diagnostics, `sys.stdout.write` for output.
- Entry point is a classmethod called from the `__main__` guard; no top-level `main()` function. `uv init --script` generates a `main()` function — replace it.
- Parse arguments with `argparse` inside a class, as in [cli.md](cli.md).
- Lock for reproducibility when the script is shared: `uv lock --script <name>.py` (writes `<name>.py.lock`).

### Run and verify

```bash
uv run <name>.py --help                       # Run (builds the environment on first use)
uvx ruff format <name>.py
uvx ruff check --select A,ANN,ARG,B,BLE,C4,C90,D,DTZ,E,ERA,F,FA,FBT,G,I,LOG,N,PERF,PGH,PIE,PL,PT,PTH,RET,RSE,RUF,S,SIM,T20,TID,TRY,UP,W --ignore D107,TRY003 --config "lint.pydocstyle.convention='google'" <name>.py
uv sync --script <name>.py                    # Materialise the script environment for ty
uvx ty check --python "$(uv python find --script <name>.py)" --error all <name>.py
```

If the script sits inside a project with a `pyproject.toml`, ruff picks up that config instead and the `--select` list is unnecessary.

See [examples.md](examples.md) → *Script* for a complete file.

## FullProject

- `src/<package>/` layout created by `uv init --package --build-backend uv`.
- `pyproject.toml`, `.python-version`, and `uv.lock` committed.
- Dev tools in `[dependency-groups] dev` (PEP 735), never `[project.optional-dependencies]`.
- Tasks defined in `[tool.poe.tasks]`; `uv run poe check` passes clean.
- Business logic in classes; entry point is `Application.main` in `__main__.py`.
- pytest tests in `tests/` with coverage enforced.

Setup and configuration: [project-setup.md](project-setup.md). File skeletons: [templates.md](templates.md).
