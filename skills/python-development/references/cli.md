# Command-Line Interfaces

How to build CLI parsing and the application entry point. Full file skeletons are in [templates.md](templates.md).

## Structure

| File | Responsibility |
| --- | --- |
| `cli.py` | `CommandLine` class: builds the `argparse` parser, validates input, returns a typed settings object |
| `config.py` | Frozen dataclasses for settings (`RunSettings`) |
| `__main__.py` | `Application` class: `main()` classmethod wires logging, settings, and services; catches `AppError` and sets the exit code |

The entry point is a classmethod, referenced as `package_name.__main__:Application.main` in `[project.scripts]`. `uv run package-name` and `uv run python -m package_name` both work.

## Rules

- Use `argparse` from the standard library unless the user asks for another framework.
- Parsing lives in `CommandLine`; business logic never touches `argparse`.
- `CommandLine.parse(argv: Sequence[str] | None = None) -> RunSettings` — accepting `argv` makes parsing testable.
- Convert the `Namespace` into a frozen settings dataclass inside `parse()`; nothing past `cli.py` sees a `Namespace` (its attributes are untyped).
- `type=Path` for paths; `choices=` for enumerated values; `%(default)s` in help text for defaults.
- Boolean switches use `action="store_true"` / `argparse.BooleanOptionalAction`.
- Report user errors with `parser.error(...)` (exits with code 2 and usage text).
- Always offer `--log-level` (or `-v/--verbose`) and send logs to stderr.
- Exit codes: `0` success, `1` handled application error (`AppError`), `2` usage error (argparse), `130` on `KeyboardInterrupt`.
- Subcommands: `parser.add_subparsers(dest="command", required=True)`, one settings dataclass per subcommand, and one handler class per subcommand.

## Pattern

```python
class CommandLine:
    """Command-line parser that produces typed run settings."""

    def __init__(self) -> None:
        self._parser = self._build_parser()

    def parse(self, argv: Sequence[str] | None = None) -> RunSettings:
        """Parse arguments and return validated settings."""
        args = self._parser.parse_args(argv)

        # Validate user input
        input_path = Path(args.input_path)
        if not input_path.exists():
            self._parser.error(f"Input path does not exist: {input_path}")

        return RunSettings(
            input_path=input_path,
            max_retries=int(args.max_retries),
            log_level=str(args.log_level),
        )

    @staticmethod
    def _build_parser() -> argparse.ArgumentParser:
        """Define the arguments."""
        ...
```

Entry point:

```python
class Application:
    """Command-line application entry point."""

    @classmethod
    def main(cls, argv: Sequence[str] | None = None) -> None:
        """Run the application and exit with its status code."""
        sys.exit(cls().run(argv))

    def run(self, argv: Sequence[str] | None = None) -> int:
        """Parse arguments, run the processor, and return an exit code."""
        ...
```

Splitting `main()` (exits) from `run()` (returns an int) lets tests call `Application().run([...])` and assert the exit code without catching `SystemExit`.

## Testing CLIs

- Test `CommandLine().parse([...])` directly with argument lists.
- Assert usage errors with `pytest.raises(SystemExit)` and check `excinfo.value.code == 2`.
- Test `Application().run([...])` end to end on `tmp_path`; capture stdout with `capsys` and logs with `caplog`.
