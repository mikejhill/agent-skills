# Skill CLIs

Read [scripts.md](scripts.md) first. This file covers deciding whether to build a CLI, how big it may grow, configuration, credentials, and footprint.

A skill CLI is an API boundary between the agent and a domain. It replaces fragile multi-step sequences with one call, keeps credentials away from the agent, and cuts the documentation the agent must load.

## Build one or not

| Situation | Choice |
| --- | --- |
| Needs credentials or tokens the agent must not handle | Build a CLI |
| Multi-step sequence the agent does inconsistently (install, configure, run, parse) | Build a CLI |
| A third-party tool exists but is too broad or complex for the need | Build a CLI that wraps it |
| OS detection, path resolution, or dependency installation is involved | Build a CLI |
| A simple, well-known tool with predictable arguments (`git`, `ruff`) | Call it directly |
| A single command or one-liner, or an existing skill CLI already does it | No CLI |

## Ownership

| CLI owns | Skill (`SKILL.md`) owns |
| --- | --- |
| Tool installation and versions | When and why to call the CLI |
| Input validation and normalization | Which inputs to pass |
| Loading config and credentials | What the output means for the task |
| Environment detection | Sequencing several calls |
| Output format and errors; temp files and cleanup | |

One cohesive domain per CLI. Cover every operation the agent needs in that domain: gaps are the main reason agents bypass a CLI.

## Tiers

**Lightweight:** one file, `scripts/<name>.py` (or `.mjs` to wrap npm tooling). `argparse`, help in the header docstring, no persistent state or credentials. At most 300 lines and two subcommands. Verified by running it. Example: `mermaid-diagrams/scripts/mermaid-export.mjs`.

**Standard:** a project in `scripts/<name>/`, following `python-development` or `typescript-development`: strict types, lint, format, tests (at least a success and an error case per subcommand), a lockfile, a `.gitignore`, and `--version`. All checks pass before each commit.

Graduate to Standard as soon as any holds: over 300 lines, persistent config or credentials, more than two subcommands, logic that needs unit tests, or dependencies that must be installed. Graduation is one-way.

```text
scripts/<name>/                 # Standard, Python
├── pyproject.toml              # deps, ruff and ty config
├── uv.lock
├── src/<package>/{__init__,__main__,cli,<domain>}.py
└── tests/test_<domain>.py
```

Run Standard Python CLIs with `uv run --project "<skill-dir>/scripts/<name>" python -m <package> ...`. Never install skill CLIs globally (`uv tool install`, `pip install`, `npm install -g`); copies drift from the skill.

## Configuration

```text
${XDG_CONFIG_HOME:-~/.config}/agent-skills/<skill-name>/
├── config.toml          # user settings
└── credentials.toml     # secrets, owner-only access
```

- The same base on every OS (Windows: `%USERPROFILE%\.config` unless `XDG_CONFIG_HOME` is set). Ignore a relative `XDG_CONFIG_HOME`.
- TOML (`tomllib`, Python 3.11+; JSON is acceptable for a Lightweight Node CLI).
- Defaults live in code. Config holds only values the user set.
- Validate on load and report the key, the bad value, and the expected form.
- Create the directory on first write, never on first run.

## Credentials

- The CLI reads credentials and exposes only results. Secrets never appear in output, logs, or errors.
- Credential files are owner-only: mode `600` on Unix, an ACL limited to the current user on Windows.
- When credentials are missing, the CLI exits non-zero, saying what is needed and where. The user creates the file; the agent never writes, reads, or quotes credential files.
- `SKILL.md` states: "Use the CLI for all [domain] operations. Do not call the underlying tool directly, and never read credential files."
- High-security setups may add a harness hook that blocks reads of `**/agent-skills/*/credentials.*`.

## Footprint

Skills are copied into many places, so keep them small.

- Never commit `node_modules/`, `.venv/`, `__pycache__/`, or build output.
- Install on demand (`uv run --with`, `npx --yes`). Commit lockfiles for Standard CLIs only.
- No bundled binaries. Build from source or download on first run.
