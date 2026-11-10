# Testing

pytest standards for FullProject (and for Scripts that grow tests — at which point promote them to a FullProject).

## Layout

```text
tests/
├── conftest.py         # Shared fixtures
├── fixtures/           # Static data files (sample JSON, CSV, ...)
├── test_cli.py         # Mirrors src/package_name/cli.py
├── test_core.py        # Mirrors src/package_name/core.py
└── subpackage/
    └── test_module.py  # Mirrors src/package_name/subpackage/module.py
```

No `tests/__init__.py`: pytest runs with `--import-mode=importlib` (see [project-setup.md](project-setup.md)), and the package is imported from the installed `src/` layout.

## Rules

- Test files `test_<module>.py`; group tests in classes `Test<ClassUnderTest>` mirroring the source classes.
- Test methods `test_<behaviour>` with a one-line docstring stating the expected behaviour.
- Every public class and method has tests for:
    1. the happy path,
    2. error paths (`pytest.raises(SpecificError, match=...)`),
    3. edge cases (empty input, boundaries, `None`).
- `@pytest.mark.parametrize` when the same logic runs over 3+ inputs; use `ids=` or `pytest.param(..., id=...)` when values aren't self-describing.
- One behaviour per test; several asserts are fine when they check one outcome.
- Arrange / Act / Assert — separate the three with blank lines, no comments needed.
- Use `tmp_path` for filesystem work, `monkeypatch` for env vars and attributes, `capsys` for stdout, `caplog` for logs.
- Test through public APIs; don't test private methods directly.
- Mock only at process boundaries (network, clock, subprocess). Prefer injecting a fake collaborator via the constructor over `unittest.mock.patch`.
- Tests must be deterministic: no real network, no sleeps, no reliance on wall-clock time or test order.
- Coverage ≥ 90% with branch coverage (`uv run poe test`); a drop below fails the run.
- Register custom markers in `[tool.pytest.ini_options] markers`; `--strict-markers` rejects unregistered ones.

## Fixtures

Fixtures are the one place module-level functions are expected.

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

- One concern per fixture; return the resource the test needs.
- Shared fixtures in `conftest.py`; single-file fixtures stay in that test file.
- Use `yield` fixtures for teardown.
- Load static data from `tests/fixtures/` via a fixture that resolves `Path(__file__).parent / "fixtures"`.

## Example

```python
class TestProcessor:
    """Tests for Processor."""

    def test_run_returns_only_files(self, sample_dir: Path) -> None:
        """Run returns regular files and skips directories."""
        processor = Processor(ProcessorConfig(input_path=sample_dir))

        result = processor.run()

        assert [path.name for path in result] == ["file1.txt", "file2.txt"]

    def test_rejects_missing_directory(self, tmp_path: Path) -> None:
        """A missing input directory raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="not a directory"):
            Processor(ProcessorConfig(input_path=tmp_path / "missing"))

    @pytest.mark.parametrize("count", [0, 1, 5])
    def test_handles_any_file_count(self, tmp_path: Path, count: int) -> None:
        """Run returns one entry per file for any count."""
        for index in range(count):
            (tmp_path / f"file{index}.txt").write_text("data", encoding="utf-8")

        result = Processor(ProcessorConfig(input_path=tmp_path)).run()

        assert len(result) == count
```

Complete test files: [templates.md](templates.md).
