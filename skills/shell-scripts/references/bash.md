# Bash FullScript standards

Start from [template.sh](../assets/template.sh). This file explains the parts that need judgment.

## Section order

Shebang, header comment, `set -euo pipefail`, constants, script state, utilities, usage, cleanup and signal handlers, business logic, `parse_args`, `main`, trap registrations, `main "$@"`. Separate sections with a divider comment:

```bash
# ---------------------------------------------------------------------------
# Section Name
# ---------------------------------------------------------------------------
```

## Header

```bash
#!/usr/bin/env bash
#
# One-sentence description of what the script does.
#
# Usage: script-name [-v] <arg>
#        script-name -h
#
# Changelog:
#   - YYYY-MM-DD: Description of change.
```

Use the `env` shebang, not `#!/bin/bash`, so PATH-managed Bash (for example Homebrew) wins.

## Naming

| Element | Convention | Example |
| --- | --- | --- |
| Script file | lowercase-hyphenated, no extension | `backup-files` |
| Functions, locals, state | lower_snake_case | `parse_args`, `input_dir` |
| Constants | UPPER_SNAKE_CASE, `readonly` | `readonly DEFAULT_LIMIT=10` |
| Exit codes | `E_` prefix | `readonly E_USAGE=2` |
| Signal handlers | `_on_` prefix | `_on_exit` |

Indent with tabs.

## Strict mode and state

- `set -u` fails on unset variables, so initialize every state variable at top level, right after the constants.
- Use integer `0`/`1` flags. String booleans such as `"true"` run as commands in `if "$flag"`.
- Pass non-argument values between functions as arguments, not globals.

## Exit codes

```bash
readonly E_GENERAL=1
readonly E_USAGE=2
readonly E_INTERRUPT=130   # 128 + SIGINT
readonly E_TERMINATED=143  # 128 + SIGTERM
```

Add domain codes from 3 upward (`E_NOT_FOUND=3`). Every `exit` names a code.

## Usage and arguments

- `usage` writes a heredoc to stdout.
- `-h`: usage to stdout, exit 0. Missing or invalid arguments: message or usage to stderr, exit `E_USAGE`. Runtime errors never print usage.
- `parse_args` uses `getopts` with a leading `:` and handles both `:` (missing value) and `\?` (unknown option), then `shift $((OPTIND - 1))`, then checks positional arguments and rejects extras.

## Signals and cleanup

```bash
_on_exit()      { local c=$?; cleanup || true; exit "${c}"; }
_on_interrupt() { echo "${SCRIPT_NAME}: interrupted." >&2; exit "${E_INTERRUPT}"; }
_on_terminate() { echo "${SCRIPT_NAME}: terminated." >&2; exit "${E_TERMINATED}"; }
```

- `_on_exit` captures `$?` first and runs cleanup best-effort, so a cleanup failure cannot replace the real exit code.
- `cleanup` is idempotent. Record temp paths from `mktemp` in state variables and remove them there.
- Register traps at top level, after all functions and just before `main "$@"`.

## Syntax choices

Prefer POSIX forms when they are as clear and safe: `$(...)`, `$((...))`, `[ ]`, `name() { ... }`. Use `[[ ]]` for pattern or regex matching, or where it avoids word-splitting risk. Never use backticks, `$[...]`, or `function name`.

Use `if` blocks, not `[ test ] && action`, for checks inside functions. When the test is false as a function's last command, the function returns 1 and `set -e` stops the script.

Declare and assign a command substitution separately (`x="$(cmd)"; readonly x`), so its exit code is not masked (ShellCheck SC2155).

## Review failures

Look for these first: missing `set -euo pipefail`; logic at top level; a trap whose `exit` sits inside a quoted string; `shift` before checking that the argument exists; `usage` always sent to stderr; string booleans; bare `exit`.
