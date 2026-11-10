# Bash Scripting Modes

## Mode Selection Rules

Use these rules when the user does not explicitly choose a mode:

- OneOff: user asks for a one-liner, quick command, ad-hoc check, or terminal snippet.
- FullScript: user asks for a script file, reusable CLI tool, or multi-step workflow.
- Default: if ambiguous, use FullScript.

## Mode Summary

| Mode       | When to Use                    | Output          | Core Expectations                                                  |
| ---------- | ------------------------------ | --------------- | ------------------------------------------------------------------ |
| FullScript | Persisted, reusable CLI tool   | Executable file | Function-based, strict mode, signal trapping, usage, documentation |
| OneOff     | Ad-hoc, immediate terminal use | Snippet         | Short, pipeline-first, no scaffolding                              |

## OneOff Guardrails

- 1–5 lines preferred; never more than 10 lines.
- No function definitions, header comments, or `set` preamble unless essential.
- Use standard Unix tools and pipeline idioms.
- Prefer `find`, `awk`, `sed`, `sort`, `grep`, `xargs` for data manipulation.
- Avoid destructive actions without a dry-run comment or `-n`/`--dry-run` flag.

## FullScript Guardrails

- Strict structure: header, strict mode, constants, script state, utilities, usage, signal handlers, business logic, `parse_args`, `main`, traps, invocation.
- All business logic inside functions; only minimal top-level setup (strict mode, trap registration, and final `main "$@"` invocation).
- Guard clauses validate inputs before executing.
- `set -euo pipefail` always enabled.
- Traps registered for `EXIT`, `INT`, and `TERM`.
- Named `E_`-prefixed exit code constants used throughout.
