# FullProject Templates

Copy-paste skeletons for a FullProject. Replace `package_name` / `package-name` with the real names. Every file here passes `uv run poe check` with the configuration in [project-setup.md](project-setup.md).

## pyproject.toml

`uv init --package --build-backend uv` writes `[project]` and `[build-system]`; `uv add --dev ...` writes `[dependency-groups]`. Merge in the rest:

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

[build-system]
requires = ["uv_build>=0.11.32,<0.12.0"]  # Keep the range uv init generated
build-backend = "uv_build"

[dependency-groups]
dev = [
    "poethepoet>=0.48",
    "pytest>=8.4",
    "pytest-cov>=7.0",
    "ruff>=0.16",
    "ty>=0.0.84",
]

[tool.ruff]
target-version = "py312"
line-length = 88
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "A", "ANN", "ARG", "B", "BLE", "C4", "C90", "D", "DTZ", "E", "ERA", "F",
    "FA", "FBT", "G", "I", "LOG", "N", "PERF", "PGH", "PIE", "PL", "PT", "PTH",
    "RET", "RSE", "RUF", "S", "SIM", "T20", "TID", "TRY", "UP", "W",
]
ignore = ["D107", "TRY003"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "PLR2004"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.flake8-tidy-imports]
ban-relative-imports = "all"

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.format]
docstring-code-format = true

[tool.ty.rules]
all = "error"

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

## src/package_name/\_\_init\_\_.py

```python
"""Package-name: short description of what the package does."""

from __future__ import annotations
```

Libraries also get an empty `src/package_name/py.typed` (PEP 561) and an `__all__` listing the public API.

## src/package_name/exceptions.py

```python
"""Exception hierarchy for the application."""

from __future__ import annotations


class AppError(Exception):
    """Base class for all expected application errors."""


class ConfigurationError(AppError):
    """Configuration is invalid or missing."""


class ProcessingError(AppError):
    """Processing a single item failed."""

    def __init__(self, item: str, reason: str) -> None:
        super().__init__(f"Failed to process '{item}': {reason}")
        self.item = item
        self.reason = reason
```

## src/package_name/config.py

```python
"""Typed settings for the application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RunSettings:
    """Settings for one application run, parsed from the command line."""

    input_path: Path
    max_retries: int = 3
    log_level: str = "INFO"
```

## src/package_name/models.py

```python
"""Data models for processing results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class Status(StrEnum):
    """Outcome of processing one item."""

    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """Result of processing a single item."""

    source: Path
    status: Status
    message: str = ""


@dataclass(slots=True)
class ProcessingSummary:
    """Accumulated results of a processing run."""

    results: list[ProcessingResult] = field(default_factory=list)

    @property
    def succeeded(self) -> int:
        """Number of successful results."""
        return sum(1 for result in self.results if result.status is Status.SUCCESS)

    @property
    def failed(self) -> int:
        """Number of failed results."""
        return sum(1 for result in self.results if result.status is Status.FAILED)

    def add(self, result: ProcessingResult) -> None:
        """Record a result."""
        self.results.append(result)
```

## src/package_name/core.py

```python
"""Core processing logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from package_name.exceptions import ConfigurationError, ProcessingError
from package_name.models import ProcessingResult, ProcessingSummary, Status

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProcessorConfig:
    """Settings for Processor."""

    input_path: Path
    max_retries: int = 3


class Processor:
    """Process every entry under the configured input directory."""

    def __init__(self, config: ProcessorConfig) -> None:
        self._config = config
        self._validate()

    @property
    def config(self) -> ProcessorConfig:
        """The processor's configuration."""
        return self._config

    def run(self) -> ProcessingSummary:
        """Process all entries and return a summary."""
        summary = ProcessingSummary()
        items = self._discover()
        logger.info("Processing %d items in %s", len(items), self._config.input_path)

        for item in items:
            summary.add(self._process(item))

        logger.info("Done: %d succeeded, %d failed", summary.succeeded, summary.failed)
        return summary

    # Internals

    def _validate(self) -> None:
        """Fail fast on invalid configuration."""
        if not self._config.input_path.is_dir():
            msg = f"Input path is not a directory: {self._config.input_path}"
            raise ConfigurationError(msg)
        if self._config.max_retries < 0:
            msg = f"max_retries must be >= 0, got {self._config.max_retries}"
            raise ConfigurationError(msg)

    def _discover(self) -> list[Path]:
        """List entries to process, sorted for stable output."""
        return sorted(self._config.input_path.iterdir())

    def _process(self, item: Path) -> ProcessingResult:
        """Process one entry."""
        if not item.is_file():
            return ProcessingResult(source=item, status=Status.SKIPPED)
        try:
            size = item.stat().st_size
        except OSError as err:
            raise ProcessingError(item=str(item), reason=str(err)) from err
        return ProcessingResult(
            source=item, status=Status.SUCCESS, message=f"{size} bytes"
        )
```

## src/package_name/cli.py

```python
"""Command-line argument parsing."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from package_name.config import RunSettings

LOG_LEVELS: Final = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class CommandLine:
    """Command-line parser that produces typed run settings."""

    def __init__(self) -> None:
        self._parser = self._build_parser()

    def parse(self, argv: Sequence[str] | None = None) -> RunSettings:
        """Parse arguments and return validated settings.

        Args:
            argv: Arguments to parse; defaults to ``sys.argv[1:]``.
        """
        args = self._parser.parse_args(argv)

        # Validate user input
        input_path = Path(args.input_path)
        if not input_path.is_dir():
            self._parser.error(f"Input path is not a directory: {input_path}")
        max_retries = int(args.max_retries)
        if max_retries < 0:
            self._parser.error(f"--max-retries must be >= 0, got {max_retries}")

        # Convert to typed settings
        return RunSettings(
            input_path=input_path,
            max_retries=max_retries,
            log_level=str(args.log_level),
        )

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        """Define the command-line arguments."""
        parser = argparse.ArgumentParser(
            prog="package-name",
            description="Process files under a directory.",
        )
        parser.add_argument("input_path", type=Path, help="Directory to process.")
        parser.add_argument(
            "--max-retries",
            type=int,
            default=3,
            help="Maximum retry attempts (default: %(default)s).",
        )
        parser.add_argument(
            "--log-level",
            default="INFO",
            choices=LOG_LEVELS,
            help="Logging verbosity (default: %(default)s).",
        )
        return parser
```

## src/package_name/\_\_main\_\_.py

```python
"""Application entry point."""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence

from package_name.cli import CommandLine
from package_name.config import RunSettings
from package_name.core import Processor, ProcessorConfig
from package_name.exceptions import AppError

logger = logging.getLogger(__name__)


class Application:
    """Command-line application: wires settings, logging, and services."""

    @classmethod
    def main(cls, argv: Sequence[str] | None = None) -> None:
        """Run the application and exit with its status code."""
        sys.exit(cls().run(argv))

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Run once and return a process exit code."""
        settings = CommandLine().parse(argv)
        self._configure_logging(settings)

        # Process
        config = ProcessorConfig(
            input_path=settings.input_path, max_retries=settings.max_retries
        )
        try:
            summary = Processor(config).run()
        except AppError:
            logger.exception("Run failed")
            return 1
        except KeyboardInterrupt:
            logger.warning("Interrupted")
            return 130

        # Program output
        for result in summary.results:
            sys.stdout.write(f"{result.source.name}\t{result.status}\n")
        return 0

    @staticmethod
    def _configure_logging(settings: RunSettings) -> None:
        """Send log records to stderr at the requested level."""
        logging.basicConfig(
            level=settings.log_level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            stream=sys.stderr,
        )


if __name__ == "__main__":
    Application.main()
```

## tests/conftest.py

```python
"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def sample_dir(tmp_path: Path) -> Path:
    """Directory with two text files and one subdirectory."""
    (tmp_path / "file1.txt").write_text("content", encoding="utf-8")
    (tmp_path / "file2.txt").write_text("content", encoding="utf-8")
    (tmp_path / "subdir").mkdir()
    return tmp_path
```

## tests/test_core.py

```python
"""Tests for the core processing logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from package_name.core import Processor, ProcessorConfig
from package_name.exceptions import ConfigurationError
from package_name.models import Status


class TestProcessor:
    """Tests for Processor."""

    def test_run_processes_files_and_skips_directories(self, sample_dir: Path) -> None:
        """Files succeed and directories are skipped."""
        processor = Processor(ProcessorConfig(input_path=sample_dir))

        summary = processor.run()

        statuses = {result.source.name: result.status for result in summary.results}
        assert statuses == {
            "file1.txt": Status.SUCCESS,
            "file2.txt": Status.SUCCESS,
            "subdir": Status.SKIPPED,
        }

    def test_rejects_missing_directory(self, tmp_path: Path) -> None:
        """A missing input directory raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="not a directory"):
            Processor(ProcessorConfig(input_path=tmp_path / "missing"))

    def test_rejects_negative_retries(self, tmp_path: Path) -> None:
        """Negative max_retries raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="max_retries"):
            Processor(ProcessorConfig(input_path=tmp_path, max_retries=-1))

    @pytest.mark.parametrize("count", [0, 1, 5])
    def test_counts_every_file(self, tmp_path: Path, count: int) -> None:
        """Every file produces one successful result."""
        for index in range(count):
            (tmp_path / f"file{index}.txt").write_text("data", encoding="utf-8")

        summary = Processor(ProcessorConfig(input_path=tmp_path)).run()

        assert summary.succeeded == count
        assert summary.failed == 0
```

## tests/test_cli.py

```python
"""Tests for command-line parsing and the application entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from package_name.__main__ import Application
from package_name.cli import CommandLine


class TestCommandLine:
    """Tests for CommandLine."""

    def test_parses_defaults(self, tmp_path: Path) -> None:
        """Only the input path is required; other settings use defaults."""
        settings = CommandLine().parse([str(tmp_path)])

        assert settings.input_path == tmp_path
        assert settings.max_retries == 3
        assert settings.log_level == "INFO"

    def test_parses_options(self, tmp_path: Path) -> None:
        """Options override the defaults."""
        settings = CommandLine().parse(
            [str(tmp_path), "--max-retries", "5", "--log-level", "DEBUG"]
        )

        assert settings.max_retries == 5
        assert settings.log_level == "DEBUG"

    def test_rejects_missing_directory(self, tmp_path: Path) -> None:
        """A missing input directory exits with usage error code 2."""
        with pytest.raises(SystemExit) as excinfo:
            CommandLine().parse([str(tmp_path / "missing")])

        assert excinfo.value.code == 2

    @pytest.mark.parametrize(
        "options",
        [
            pytest.param(["--max-retries", "-1"], id="negative-retries"),
            pytest.param(["--max-retries", "many"], id="non-integer-retries"),
            pytest.param(["--log-level", "LOUD"], id="unknown-log-level"),
        ],
    )
    def test_rejects_invalid_options(self, tmp_path: Path, options: list[str]) -> None:
        """Invalid options exit with usage error code 2."""
        with pytest.raises(SystemExit) as excinfo:
            CommandLine().parse([str(tmp_path), *options])

        assert excinfo.value.code == 2


class TestApplication:
    """Tests for Application."""

    def test_run_writes_results_to_stdout(
        self, sample_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A successful run writes one line per entry and returns 0."""
        exit_code = Application().run([str(sample_dir)])

        assert exit_code == 0
        assert capsys.readouterr().out.splitlines() == [
            "file1.txt\tsuccess",
            "file2.txt\tsuccess",
            "subdir\tskipped",
        ]

    def test_main_exits_with_run_status(self, sample_dir: Path) -> None:
        """Main exits with the code returned by run."""
        with pytest.raises(SystemExit) as excinfo:
            Application.main([str(sample_dir)])

        assert excinfo.value.code == 0
```

## .gitignore

See [project-setup.md](project-setup.md) → *.gitignore*.

## README.md (installation and development section)

````markdown
## Installation

Install as a global tool with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install .
```

## Development

```bash
uv sync              # Create .venv and install all dependencies
uv run package-name  # Run the CLI
uv run poe           # List available tasks
uv run poe fix       # Format and auto-fix lint
uv run poe check     # Format check, lint, strict type check, tests with coverage
```
````

- Link to the [uv docs](https://docs.astral.sh/uv/) on first mention.
- Document `uv` and `poe` commands only — no `pip install`, `PYTHONPATH`, or `main.py` instructions.
