# Scripts

Add a script when the agent would otherwise repeat a fragile multi-step sequence, handle credentials, or need exact output. Do not add one for a single well-known command.

## Placement and execution

```text
scripts/<name>.py         # single-file CLI (default)
scripts/<name>.mjs        # Node.js, only to wrap npm tooling
scripts/<name>/           # full project, once a CLI outgrows one file
tests/test_<name>.py      # stdlib unittest
```

Document the exact invocation in `SKILL.md`, resolving from the skill folder:

```bash
python3 "<skill-dir>/scripts/<name>.py" <args>    # Windows: py -3 or python
node "<skill-dir>/scripts/<name>.mjs" <args>
```

- Run from source. Never install a skill script globally, because the copy drifts from the skill.
- If third-party Python packages are unavoidable, declare them inline with PEP 723 and run with `uv run "<skill-dir>/scripts/<name>.py"`. State the `uv` requirement in `README.md` and `compatibility`.

## Languages

| Order | Language | Use |
| --- | --- | --- |
| 1 | Python 3.9+, stdlib only | Default. Portable across OSes, and present on most developer machines. |
| 2 | Node.js 18+ (`.mjs`) | Only to wrap npm packages or JavaScript-centric tooling. |
| 3 | POSIX sh or Bash | Only for wrappers under about 50 lines. Unix only, so ship a PowerShell twin if Windows matters. |
| 4 | PowerShell 7 | Only for Windows-only system integration. |

## Interface

- Accept arguments only, with no prompts. Provide `--help` with one example.
- Write results to stdout. Use JSON when an agent parses the output, and keep it small and stable.
- Write diagnostics and actionable errors to stderr. Exit `0` on success and non-zero on failure.
- Derive defaults from context, so common calls need few arguments.
- Make reruns safe: detect existing state rather than duplicating it.
- Never print secrets. Read credentials from the config location and expose only results.
- Bound runtime and output: use timeouts on network and subprocess calls, and truncate large output with a note.

## Operating systems

- Branch on `sys.platform` or `os.name`. Do not assume `/` paths, `bash`, or GNU flags.
- List supported OSes in the script's header docstring and in `README.md`. Where one OS needs a different command, give it next to the default in `SKILL.md`.
- Test path handling on Windows when the script touches the filesystem.

## Larger CLIs

Once a script needs persistent config, credentials, more than two subcommands, or more than about 300 lines, read [cli.md](cli.md).
