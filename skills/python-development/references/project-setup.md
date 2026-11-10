# Project Setup

How to create and configure a FullProject: uv, repository layout, `pyproject.toml`, ruff, strict ty, poe tasks, and verification.

## Bootstrap

```bash
uv init --package --build-backend uv --python 3.12 <project-name>
cd <project-name>
uv add --dev ruff ty pytest pytest-cov poethepoet
uv add <runtime-dependency>          # Runtime dependencies, as needed
```

Then:

1. Replace the generated `src/<package>/__init__.py` (it contains a `main()` function) with the template in [templates.md](templates.md).
2. Point `[project.scripts]` at the class entry point: `<project-name> = "<package>.__main__:Application.main"`.
3. Add the `[tool.ruff]`, `[tool.ty]`, `[tool.pytest]`, `[tool.coverage]`, and `[tool.poe]` sections below.
4. Create the remaining directories from the layout as they become needed — don't add empty ones.
5. Run `uv sync`, then `uv run poe fix` and `uv run poe check`.

Keep the `[build-system]` block that `uv init` writes; it pins `uv_build` to the installed uv's version range.

## Repository Layout

```text
project-name/
├── .github/                    # CI workflows, issue/PR templates
├── .gitignore
├── .python-version             # Python version pin read by uv (e.g. 3.12)
├── pyproject.toml              # Metadata, dependencies, and ALL tool config
├── uv.lock                     # Always committed
├── README.md                   # Conventional root docs stay at the root:
├── LICENSE                     #   README, LICENSE, CHANGELOG, CONTRIBUTING,
├── CHANGELOG.md                #   SECURITY, CODE_OF_CONDUCT, AGENTS.md / CLAUDE.md
├── .env.example                # Documented env vars; real .env is gitignored
├── src/
│   └── package_name/           # Importable package — ALL source code lives here
│       ├── __init__.py
│       ├── __main__.py         # Application entry point class
│       ├── py.typed            # PEP 561 marker (libraries)
│       ├── cli.py              # Argument parsing
│       ├── config.py           # Typed settings dataclasses
│       ├── core.py             # Primary business logic
│       ├── models.py           # Dataclasses and enums
│       ├── exceptions.py       # Exception hierarchy
│       └── subpackage/         # Group related modules as the package grows
│           └── __init__.py
├── tests/
│   ├── conftest.py             # Shared fixtures
│   ├── fixtures/               # Static test data files
│   ├── test_core.py            # Mirrors src/package_name/core.py
│   └── subpackage/             # Mirrors src/package_name/subpackage/
├── docs/                       # All other documentation (guides, ADRs, design notes)
│   └── decisions/
├── scripts/                    # Dev/ops helper scripts not shipped in the package
├── examples/                   # Runnable usage examples (libraries)
├── data/                       # Sample or reference data used at runtime or in dev
└── .venv/                      # Managed by uv; gitignored
```

### Placement Rules

| Asset | Location |
| --- | --- |
| Importable code | `src/<package>/` — never at the repo root, never in `scripts/` |
| Additional top-level packages | Siblings under `src/`, each with `__init__.py` |
| Package data read at runtime (templates, default config) | Inside `src/<package>/` (e.g. `src/<package>/resources/`), loaded with `importlib.resources` |
| Tests | `tests/`, mirroring the `src/<package>/` tree |
| Test data files | `tests/fixtures/` |
| Helper scripts (release, data refresh, codegen, one-off maintenance) | `scripts/`, as PEP 723 scripts (see [modes.md](modes.md)); expose frequently used ones as poe tasks |
| Shell or PowerShell helpers | `scripts/` |
| Documentation other than conventional root files | `docs/` |
| Architecture decision records | `docs/decisions/` |
| Conventional root docs (README, LICENSE, CHANGELOG, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, AGENTS.md, CLAUDE.md) | Repo root |
| CI configuration | `.github/workflows/` |
| Local secrets | `.env` (gitignored); document variables in `.env.example` |
| Build output, caches, venvs | Never committed (`dist/`, `.venv/`, `.ruff_cache/`, `.pytest_cache/`, `.coverage`) |

Do NOT create `main.py`, `setup.py`, `setup.cfg`, `requirements*.txt`, `tox.ini`, `.flake8`, `mypy.ini`, `ruff.toml`, or `pytest.ini`. Everything those files did lives in `pyproject.toml`.

## pyproject.toml

### Metadata and dependencies

```toml
[project]
name = "package-name"
version = "0.1.0"
description = "Short description of the project."
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[project.scripts]
package-name = "package_name.__main__:Application.main"

[dependency-groups]
dev = [
    "poethepoet>=0.48",
    "pytest>=8.4",
    "pytest-cov>=7.0",
    "ruff>=0.16",
    "ty>=0.0.84",
]
```

Let `uv add` / `uv add --dev` write these entries; it records the current minimum versions. Shown versions are illustrative.

**Dependency rules:**

- Runtime dependencies in `[project] dependencies`; dev tools in `[dependency-groups] dev` (PEP 735).
- Libraries: lower-bound pins (`"httpx>=0.28"`) for compatibility. Applications: rely on `uv.lock` for exact reproducibility.
- Upgrade deliberately: `uv lock --upgrade-package <name>` or `uv lock --upgrade`.
- Python versions are managed by uv (`uv python install`, `.python-version`), not by system installers.

### ruff (lint and format)

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "A",     # flake8-builtins: no shadowing builtins
    "ANN",   # flake8-annotations: every signature annotated, no Any
    "ARG",   # unused arguments
    "B",     # flake8-bugbear
    "BLE",   # no blind except
    "C4",    # comprehensions
    "C90",   # mccabe complexity
    "D",     # pydocstyle: file, class, method docstrings
    "DTZ",   # timezone-aware datetimes
    "E",     # pycodestyle errors
    "ERA",   # no commented-out code
    "F",     # pyflakes
    "FA",    # from __future__ import annotations
    "FBT",   # no boolean positional arguments
    "G",     # logging format strings
    "I",     # isort
    "LOG",   # logging misuse
    "N",     # pep8-naming
    "PERF",  # performance anti-patterns
    "PGH",   # no blanket type: ignore / noqa
    "PIE",   # misc lints
    "PL",    # pylint
    "PT",    # pytest style
    "PTH",   # pathlib over os.path
    "RET",   # return statements
    "RSE",   # raise statements
    "RUF",   # ruff-specific
    "S",     # bandit security
    "SIM",   # simplifications
    "T20",   # no print()
    "TID",   # tidy imports
    "TRY",   # exception handling
    "UP",    # pyupgrade
    "W",     # pycodestyle warnings
]
ignore = [
    "D107",    # __init__ docstring: the class docstring covers it
    "TRY003",  # long messages in raise: context-rich messages are required here
]
# TC excluded: moving annotation-only imports into TYPE_CHECKING blocks hurts readability.

[tool.ruff.lint.per-file-ignores]
"tests/**" = [
    "S101",     # assert is how pytest works
    "PLR2004",  # literal expected values are clearer in tests
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.format]
docstring-code-format = true
```

Formatting, import order, naming, docstring presence, annotation presence, and `print()` bans are all enforced here — don't restate them as instructions; fix what ruff reports.

### ty (strict type checking)

```toml
[tool.ty.rules]
all = "error"
```

`all = "error"` raises every ty rule to error, including rules that are off by default (e.g. `redundant-condition-strict`). ty reads `requires-python` and the `src/` layout automatically.

Strictness rules:

- Do NOT downgrade rules to make a check pass. If a rule genuinely doesn't fit, override that one rule after `all` with a comment explaining why:

    ```toml
    [tool.ty.rules]
    all = "error"
    some-rule = "warn"  # Reason this rule doesn't apply to this project
    ```

- Suppress a single line only with a rule code and reason: `# ty: ignore[rule-name]  # reason`.
- Combined with ruff `ANN` (incl. `ANN401` banning `Any`) and `PGH` (banning blanket ignores), this is the project's strict typing gate.

### pytest and coverage

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--strict-markers", "--strict-config", "-ra", "--import-mode=importlib"]
xfail_strict = true

[tool.coverage.run]
source = ["package_name"]
branch = true

[tool.coverage.report]
fail_under = 90
show_missing = true
skip_covered = true
exclude_also = ["if __name__ == .__main__.:"]
```

### poe (task runner)

```toml
[tool.poe.tasks]
format = { cmd = "ruff format .", help = "Format code" }
format-check = { cmd = "ruff format --check .", help = "Check formatting" }
lint = { cmd = "ruff check .", help = "Lint code" }
lint-fix = { cmd = "ruff check . --fix", help = "Lint and auto-fix" }
typecheck = { cmd = "ty check", help = "Type check (strict)" }
test = { cmd = "pytest --cov", help = "Run tests with coverage" }
fix = { sequence = ["format", "lint-fix"], help = "Auto-fix formatting and lint" }
check = { sequence = ["format-check", "lint", "typecheck", "test"], help = "Run every quality gate" }
```

Rules:

- Every repeatable command (quality gates, codegen, data refresh, release steps) is a poe task, so humans, agents, and CI run the same thing.
- Run tasks through uv: `uv run poe <task>`; list them with `uv run poe`.
- Tasks that call a helper script point at `scripts/`: `refresh-data = { cmd = "uv run scripts/refresh_data.py", help = "..." }`.
- CI runs `uv sync --locked` then `uv run poe check`.

## Verification

After generating or changing code:

```bash
uv sync
uv run poe fix     # Format and auto-fix lint
uv run poe check   # format-check, lint, strict ty, tests + coverage: must all pass
```

Fix findings in the code. Never loosen `[tool.ruff]`, `[tool.ty]`, or coverage settings to get a green run.

## .gitignore

```text
__pycache__/
*.py[cod]
.venv/
dist/
build/
*.egg-info/
.ruff_cache/
.pytest_cache/
.coverage
htmlcov/
.env
```
