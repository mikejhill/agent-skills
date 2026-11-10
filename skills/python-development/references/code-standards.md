# Code Standards

Rules for writing and reviewing Script and FullProject code. Anything ruff or ty enforces is noted as such; the rest is instruction-only and must be checked by inspection.

## File Header

Every `.py` file starts with a docstring describing what the file is for, then the future import:

```python
"""Scan a directory tree and report configuration files that are enabled."""

from __future__ import annotations
```

- One sentence, two at most. Say what the file is responsible for, not how it works.
- Required on `__init__.py`, `__main__.py`, `conftest.py`, and test files too (ruff `D100`, `D104`).
- `from __future__ import annotations` keeps annotations lazy on 3.12–3.13 (ruff `FA`).

## Object-Oriented Design

STRONGLY prefer classes. A module is a home for one or a few cohesive classes, not a bag of functions.

### Rules

- Put behaviour in methods. Avoid module-level functions; if you're about to write one, find or create the class it belongs to.
- Accepted exceptions only:
  - pytest fixtures in `conftest.py` and test files (pytest requires functions).
  - A function required by a third-party API that cannot take a bound method.
- Stateless helpers go on the class that uses them as `@staticmethod`, or into a small dedicated class (e.g. `PathResolver`). Don't create a `utils.py` of loose functions.
- Data:
  - `@dataclass(frozen=True, slots=True)` for configuration, settings, and value objects.
  - Plain `@dataclass(slots=True)` only when mutation is the point (e.g. an accumulator), and keep it private to one owner.
  - `Enum` / `StrEnum` for bounded value sets — never magic strings.
- Services: regular classes that take their dependencies (config, collaborators) in `__init__` and store them as private attributes.
- Encapsulation:
  - Private by default: `_attribute`, `_helper()`. Expose state through `@property`, not public attributes.
  - Public methods form a small, deliberate surface; everything else is private.
- Interfaces: `typing.Protocol` for structural interfaces; `abc.ABC` + `@abstractmethod` when sharing implementation.
- Prefer composition over inheritance; inherit only for genuine *is-a* relationships, max 2 levels deep.
- One responsibility per class. Split classes that grow beyond ~200 lines or mix I/O with domain logic.
- Constructors validate and store; they don't do heavy work (I/O, network). Use a `@classmethod` factory (`from_file`, `from_env`) for construction that needs I/O.
- Module level holds only imports, constants (`UPPER_SNAKE_CASE`, `Final`), `logger = logging.getLogger(__name__)`, type aliases, and class definitions. No mutable module state, no work at import time.
- Import symbols from the module that defines them, not from a module that re-imports them (ty rejects implicit re-exports). Define `__all__` in `__init__.py` for library packages.

### Shape of a service class

```python
"""Process input files under a configured directory."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from package_name.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProcessorConfig:
    """Settings for Processor."""

    input_path: Path
    max_retries: int = 3


class Processor:
    """Process files under the configured input path."""

    def __init__(self, config: ProcessorConfig) -> None:
        self._config = config
        self._validate()

    def run(self) -> list[Path]:
        """Process every file and return the ones handled."""
        files = self._discover()
        logger.info("Processing %d files", len(files))
        return [path for path in files if self._should_process(path)]

    # Internals

    def _validate(self) -> None:
        """Fail fast on invalid configuration."""
        if not self._config.input_path.is_dir():
            msg = f"Input path is not a directory: {self._config.input_path}"
            raise ConfigurationError(msg)

    def _discover(self) -> list[Path]:
        """List candidate files."""
        return sorted(self._config.input_path.iterdir())

    @staticmethod
    def _should_process(path: Path) -> bool:
        """Return True for regular files."""
        return path.is_file()
```

## Docstrings

Enforced present by ruff `D` (Google convention). Content is instruction-only:

- Every file, class, method, and function gets one. `__init__` is exempt; the class docstring covers construction.
- One line by default, in the imperative mood for methods (`"Return the parsed settings."`), as a noun phrase for classes (`"Settings for Processor."`).
- Add `Args:`, `Returns:`, `Raises:`, or `Yields:` sections only when they add information beyond the signature — non-obvious constraints, units, side effects, or raised domain errors.
- Don't repeat type information already in the annotations.
- Test methods get a one-line docstring stating the behaviour under test.

```python
def resolve(self, name: str, *, strict: bool = True) -> Path:
    """Return the absolute path for a registered resource.

    Raises:
        ResourceNotFoundError: If ``strict`` and ``name`` isn't registered.
    """
```

## Comments

- Use short comments as **logical headers** that name the next block of code:

    ```python
    def build(self) -> Report:
        """Assemble the report from loaded records."""
        # Load and filter
        records = self._loader.load()
        active = [r for r in records if r.is_active]

        # Aggregate
        totals = self._aggregate(active)

        # Render
        return Report(totals=totals, generated_at=self._clock.now())
    ```

- Inside a class, a header comment such as `# Internals` or `# Factories` may group related methods.
- Keep every comment to a few words. If a header needs a sentence, the block probably wants to be its own private method.
- No inline comments on code that already says what it does. Reserve inline comments for:
  - niche or non-obvious behaviour (`# Windows returns mtime in local time here`),
  - workarounds with a link (`# Work around httpx#1234`),
  - deliberate exceptions to a rule (`# noqa: S603 — command is a fixed list, no user input`).
- No commented-out code (ruff `ERA`). Delete it; git has history.
- `TODO` comments carry an owner or issue link: `# TODO(#42): drop once v2 API ships`.

## Typing

ty runs with every rule at error; ruff `ANN`, `FA`, `UP`, and `PGH` back it up.

**Required:**

- Annotate every parameter and return, including `-> None`.
- Built-in generics and unions: `list[str]`, `dict[str, int]`, `str | None`.
- Abstract parameter types, concrete return types: accept `Sequence[T]` / `Mapping[K, V]` / `Iterable[T]`, return `list[T]` / `dict[K, V]`.
- `type` statements or `TypeAlias` for complex types: `type PathFilter = Callable[[Path], bool]`.
- `Final` for constants; `ClassVar` for class-level attributes.
- `Protocol` for duck-typed collaborators; `@overload` for multiple distinct signatures; `Self` for fluent / factory returns.
- Keyword-only arguments (`*,`) for booleans and optional settings (ruff `FBT`).
- Parse, don't validate: convert untyped input (argparse `Namespace`, JSON, environment variables, CSV rows) into typed dataclasses at the boundary, then pass only typed objects inward.

**Forbidden:**

- `Any` (ruff `ANN401`), except at an untyped third-party boundary — wrap that boundary in a typed adapter class.
- `# type: ignore` / `# ty: ignore` without a rule code and reason.
- `cast()` without a comment justifying it.
- Mutable default arguments; use `field(default_factory=...)` in dataclasses or `None` + guard.

## Errors

- Define a hierarchy in `exceptions.py` rooted at `AppError`; raise domain errors (`ConfigurationError`, `ProcessingError`) rather than bare built-ins for expected failure modes.
- Built-ins (`ValueError`, `TypeError`, `FileNotFoundError`) are fine for programming errors and guard clauses on public APIs.
- Messages carry context: what failed, what was expected, what was found. Bind the message to `msg` first, then `raise X(msg)`.
- Chain with `raise DomainError(msg) from err`.
- Catch the narrowest exception possible, as close to the cause as possible. Never bare `except:`; never `except Exception:` unless it re-raises or is the top-level boundary in `Application.main`.
- Never swallow an exception silently. At minimum, log it with `logger.exception()` or `logger.warning()`.
- Guard clauses at the top of public methods; return or raise early to keep nesting ≤ 3 levels.
- Validate twice on purpose: friendly CLI errors in `cli.py` (`parser.error()`), invariant checks in domain constructors for non-CLI callers.
- Use context managers (`with`) for every resource: files, locks, sessions, temporary directories.

## Logging and Output

- One logger per module: `logger = logging.getLogger(__name__)`.
- Configure logging once, in `Application.main` (or the script's entry class). Libraries never configure logging.
- Lazy formatting: `logger.info("Loaded %d rows from %s", count, path)` — never f-strings in log calls (ruff `G`).
- Levels: `debug` diagnostics, `info` progress, `warning` recoverable problems, `error` failures, `exception` inside `except` blocks (adds the traceback).
- Diagnostics go to stderr via logging. Program output — the data the user asked for — goes to stdout via `sys.stdout.write(...)`. No `print()` (ruff `T20`).
- Never log secrets, tokens, or full personal data.

## Naming

Enforced by ruff `N`:

| Element | Convention | Example |
| --- | --- | --- |
| Packages, modules | `snake_case` | `data_pipeline`, `file_scanner.py` |
| Classes, type aliases, Protocols | `PascalCase` | `FileScanner`, `PathFilter` |
| Methods, functions, variables | `snake_case` | `load_records()`, `retry_count` |
| Constants, enum members | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT`, `Status.FAILED` |
| Private members | leading underscore | `_validate()`, `_cache` |

Names describe intent: `active_accounts`, not `data2`; `is_expired`, not `check`. Booleans read as predicates (`is_`, `has_`, `should_`).

## General Practices

- Prefer the standard library: `pathlib` over `os.path`, `datetime` with `UTC` (`datetime.now(UTC)`), `importlib.resources` for package data, `subprocess.run([...], check=True)` with a list (never `shell=True` with user input).
- Always pass `encoding="utf-8"` to text I/O.
- Read configuration from arguments or environment at the edge; inject it as typed settings. No hard-coded paths, URLs, or credentials.
- Extract a private method when logic repeats, nesting passes 2 levels, a method passes ~20 lines, or a step deserves a name.
- Keep functions pure where practical; isolate I/O in a few clearly named classes so domain logic is easy to test.
- Use `async` only when the task needs concurrent I/O; don't mix sync and async APIs in one class.
