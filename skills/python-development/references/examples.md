# Examples

## OneOff

**Five largest files under a path:**

```python
from pathlib import Path
sorted(Path(path).rglob("*"), key=lambda f: f.stat().st_size, reverse=True)[:5]
```

**Unique email domains:**

```python
domains = sorted({email.split("@")[1] for email in emails if "@" in email})
```

**Python files containing a marker:**

```python
from pathlib import Path
[f for f in Path().rglob("*.py") if "TODO" in f.read_text(encoding="utf-8")]
```

**With a third-party package, no install:**

```bash
uv run --with httpx python -c "import httpx; print(httpx.get('https://example.com').status_code)"
```

## Script

A self-contained PEP 723 script: file docstring, classes instead of functions, typed settings, logging to stderr, results to stdout. Created with `uv init --script count_lines.py --python 3.12`, then rewritten.

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Count lines in every file matching a glob pattern under a directory."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CountSettings:
    """Settings for one line-count run."""

    root: Path
    pattern: str
    log_level: str


class LineCounter:
    """Count lines in files under a root directory."""

    def __init__(self, settings: CountSettings) -> None:
        self._settings = settings

    def count(self) -> dict[Path, int]:
        """Return the line count for each matching file."""
        counts: dict[Path, int] = {}
        for path in sorted(self._settings.root.rglob(self._settings.pattern)):
            if not path.is_file():
                continue
            try:
                counts[path] = len(path.read_text(encoding="utf-8").splitlines())
            except (OSError, UnicodeDecodeError):
                logger.warning("Skipping unreadable file: %s", path)
        return counts


class Script:
    """Command-line entry point for the line counter."""

    @classmethod
    def main(cls, argv: Sequence[str] | None = None) -> None:
        """Run the script and exit with its status code."""
        sys.exit(cls().run(argv))

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Parse arguments, count lines, and write results to stdout."""
        settings = self._parse(argv)
        logging.basicConfig(level=settings.log_level, stream=sys.stderr)

        # Count
        counts = LineCounter(settings).count()
        logger.info("Counted %d files", len(counts))

        # Program output
        for path, lines in counts.items():
            sys.stdout.write(f"{lines}\t{path}\n")
        return 0

    @staticmethod
    def _parse(argv: Sequence[str] | None) -> CountSettings:
        """Parse and validate command-line arguments."""
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("root", type=Path, help="Directory to search.")
        parser.add_argument(
            "--pattern", default="*.py", help="Glob (default: %(default)s)."
        )
        parser.add_argument(
            "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING"]
        )
        args = parser.parse_args(argv)

        # Validate user input
        root = Path(args.root)
        if not root.is_dir():
            parser.error(f"Not a directory: {root}")

        return CountSettings(
            root=root, pattern=str(args.pattern), log_level=str(args.log_level)
        )


if __name__ == "__main__":
    Script.main()
```

Run with `uv run count_lines.py src --pattern "*.py"`; verify with the Script commands in [modes.md](modes.md).

## FullProject: Procedural to OOP Refactor

### Before

```python
import os
import json

path = "/data/config"
results = []
for filename in os.listdir(path):
    if filename.endswith(".json"):
        filepath = os.path.join(path, filename)
        with open(filepath) as f:
            data = json.load(f)
        if data.get("enabled"):
            print(f"Found: {filename}")
            results.append(data)
print(f"Total: {len(results)}")
```

### Rules applied

| Before | After | Rule |
| --- | --- | --- |
| Hard-coded `"/data/config"` | `ScannerConfig.search_path` from the CLI | Parameterise; typed settings |
| Loose top-level loop | `ConfigScanner` class with private helpers | Classes over procedural code |
| `os.listdir` + `os.path.join` | `Path.glob()` | Prefer `pathlib` |
| `print()` for status | `logger.info()` / `logger.debug()` | Logging for diagnostics |
| Bare `dict` results | `ScanResult` frozen dataclass | Typed data models |
| No error handling | Narrow `except` + `logger.warning()` | Fail gracefully, never silently |
| No docs | File, class, and method docstrings; header comments | Documentation rules |

### After: src/config_scanner/core.py

```python
"""Find configuration files that have a required field enabled."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from config_scanner.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ScannerConfig:
    """Settings for ConfigScanner."""

    search_path: Path
    pattern: str = "*.json"
    required_field: str = "enabled"


@dataclass(frozen=True, slots=True)
class ScanResult:
    """A configuration file whose required field is enabled."""

    path: Path
    data: dict[str, object]


class ConfigScanner:
    """Scan a directory for enabled configuration files."""

    def __init__(self, config: ScannerConfig) -> None:
        self._config = config
        self._validate()

    def scan(self) -> list[ScanResult]:
        """Return every enabled configuration file under the search path."""
        logger.info(
            "Scanning %s for %s", self._config.search_path, self._config.pattern
        )
        results = [
            result
            for path in sorted(self._config.search_path.glob(self._config.pattern))
            if (result := self._load(path)) is not None
        ]
        logger.info("Found %d enabled configurations", len(results))
        return results

    # Internals

    def _validate(self) -> None:
        """Fail fast when the search path isn't a directory."""
        if not self._config.search_path.is_dir():
            msg = f"Search path is not a directory: {self._config.search_path}"
            raise ConfigurationError(msg)

    def _load(self, path: Path) -> ScanResult | None:
        """Load one file; return a result only if it's valid and enabled."""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Skipping unreadable file: %s", path)
            return None

        if not isinstance(data, dict) or not data.get(self._config.required_field):
            return None

        logger.debug("Enabled config: %s", path.name)
        return ScanResult(path=path, data=data)
```

The remaining files follow [templates.md](templates.md) directly: `exceptions.py` defines `AppError` and `ConfigurationError`; `cli.py` defines a `CommandLine` class returning `ScannerConfig`; `__main__.py` defines `Application.main`, which writes `result.path.name` lines to stdout.

### After: tests/test_core.py

```python
"""Tests for the configuration scanner."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from config_scanner.core import ConfigScanner, ScannerConfig
from config_scanner.exceptions import ConfigurationError


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Directory with enabled, disabled, field-less, and invalid configs."""
    (tmp_path / "enabled.json").write_text(
        json.dumps({"enabled": True}), encoding="utf-8"
    )
    (tmp_path / "disabled.json").write_text(
        json.dumps({"enabled": False}), encoding="utf-8"
    )
    (tmp_path / "no_field.json").write_text(json.dumps({"name": "c"}), encoding="utf-8")
    (tmp_path / "invalid.json").write_text("not json", encoding="utf-8")
    return tmp_path


class TestConfigScanner:
    """Tests for ConfigScanner."""

    def test_finds_only_enabled_configs(self, config_dir: Path) -> None:
        """Only files with the required field enabled are returned."""
        results = ConfigScanner(ScannerConfig(search_path=config_dir)).scan()

        assert [result.path.name for result in results] == ["enabled.json"]

    def test_rejects_missing_directory(self, tmp_path: Path) -> None:
        """A missing search path raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="not a directory"):
            ConfigScanner(ScannerConfig(search_path=tmp_path / "missing"))

    def test_respects_pattern(self, tmp_path: Path) -> None:
        """Files outside the glob pattern are ignored."""
        (tmp_path / "config.yaml").write_text("enabled: true", encoding="utf-8")
        (tmp_path / "config.json").write_text(
            json.dumps({"enabled": True}), encoding="utf-8"
        )

        results = ConfigScanner(ScannerConfig(search_path=tmp_path)).scan()

        assert len(results) == 1
```
