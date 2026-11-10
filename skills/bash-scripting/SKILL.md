---
name: bash-scripting
description: Use when creating, modifying, or refactoring Bash shell scripts that require production-quality standards including function-based architecture, strict error handling, getopts argument parsing, signal trapping, and CLI-first design.
---

# Bash Shell Script Development

## Objective

Produce Bash scripts in two modes: full scripts for persisted CLI tools and one-offs for ad-hoc execution. Full scripts must be function-first, strictly error-handled, signal-aware, and documented; one-offs must be short and runnable inline.

## Scope

**In-scope:**

- New Bash scripts and refactors
- One-offs and terminal snippets
- Function-based design, guard clauses, fail-fast error handling
- Argument parsing with `getopts`
- Usage documentation
- Signal trapping and cleanup
- Exit code conventions

**Out-of-scope:**

- Shell libraries or sourced function files
- Non-Bash shells (sh, zsh, fish)
- System init scripts or daemon wrappers
- Makefile recipes
- CI/CD pipeline scripts (GitHub Actions, Jenkins, etc.)

## Inputs

**Required inputs:**

- Purpose and functional requirements
- Target output form: FullScript or OneOff
- New development or refactor

**Optional inputs:**

- Mode selection override
- Existing patterns to mirror
- Domain context (file I/O, system administration, build automation)
- Required options and positional arguments

**Assumptions:**

- Bash 4.0+ available on `PATH` (Linux: typically default; macOS: requires a newer Bash than the system `/bin/bash` 3.2, e.g., via Homebrew)
- Script is invoked directly as a CLI tool (not sourced)
- No library or source usage assumed

## Outputs

**Format:**

- FullScript: executable script file (no extension)
- OneOff: snippet (1–5 lines preferred, max 10 lines)

**FullScript Structure:**

1. Shebang: `#!/usr/bin/env bash`
2. Header comment (description, usage summary, changelog)
3. Strict mode: `set -euo pipefail`
4. Constants (`readonly`)
5. Script state variables (mutable globals, initialized to defaults)
6. Utility functions (`die`, `log_info`, `log_warn`, `log_error`)
7. `usage` function
8. Cleanup and signal handler functions
9. Business logic functions
10. `parse_args` function (defined last among helpers)
11. `main` function (defined last)
12. Trap registrations (`EXIT`, `INT`, `TERM`)
13. `main "$@"` invocation

**Files produced:**

- FullScript: single executable script file named in lowercase-hyphenated form
- OneOff: no file unless requested

**Formatting requirements (FullScript):**

- Indent with tabs
- UPPER_SNAKE_CASE for constants; lowercase snake_case for functions and variables
- `readonly` for all constants
- `local` for all variables declared inside functions
- ANSI-compliant syntax preferred when equivalent in readability and safety to Bash-specific syntax
- Max 3 levels of nesting; extract deeper logic into named functions
- One blank line between function definitions, except for grouped one-line helpers (e.g., `log_info`/`log_warn`/`log_error`) which may appear consecutively
- Section dividers (`# ---------------------------------------------------------------------------`) separating each logical group

## Constraints

**Conflict resolution:** User requirements override defaults unless they violate safety or explicit MUST rules.

**Mode selection rules:**

- OneOff: user asks for a one-liner, quick command, ad-hoc check, or terminal snippet
- FullScript: user asks for a script file, reusable CLI tool, or multi-step workflow
- Default to FullScript when ambiguous

**Global MUST:**

- Choose FullScript or OneOff and follow the mode rules
- Write errors, warnings, and all diagnostic/status output (including `log_info`) to stderr; write primary program output to stdout
- Validate all required inputs before executing logic

**Global MUST NOT:**

- Write diagnostic, logging, or status output to stdout outside of the primary program output
- Use undefined variables
- Ignore non-zero exit codes without an explicit comment or log explaining that the failure is non-critical

**FullScript MUST:**

- Use `#!/usr/bin/env bash` as the shebang
- Enable `set -euo pipefail` immediately after the header comment
- Declare all constants with `readonly`
- Declare all in-function variables with `local`
- Define a `die` function for fatal errors that prints to stderr and exits with a code
- Define a `usage` function that writes to stdout
- Define a `parse_args` function using `getopts` that handles `:` (missing arg) and `\?` (unknown option) cases
- Define `main` as the final function and invoke it with `main "$@"`
- Register traps for `EXIT` (cleanup), `INT` (exit 130), and `TERM` (exit 143)
- Use named `readonly` exit code constants prefixed with `E_` (e.g., `E_USAGE=2`)
- Include a header comment with at minimum: a description, a usage summary, and a changelog

**FullScript MUST NOT:**

- Hard-code paths or configurable values (use constants or arguments)
- Put business logic at top level; only constants/state declarations, strict mode (`set -euo pipefail`), trap registrations, and the final `main "$@"` invocation belong at top level
- Call `exit` without an explicit numeric code or named exit code constant
- Use string booleans (e.g., `TRUE`/`FALSE` string variables) in place of integer flags (`0`/`1`) or function return codes

**OneOff MUST:**

- Prefer 1–5 lines, maximum 10 lines
- Skip function definitions, header comments, and `set` preamble unless essential
- Use pipeline-friendly idioms and standard Unix tools

**OneOff MUST NOT:**

- Create a FullScript scaffold
- Add long-form comments or headers

## Procedure

1. Select mode using the mode rules.
2. FullScript: write the header comment, then lay out strict mode, constants, script state, utilities, usage, signal handlers, business logic, `parse_args`, `main`, traps, and invocation in that order.
3. OneOff: build the minimal expression and keep length within limits.
4. Apply guard clauses, error handling, signal trapping, and naming conventions.

## Validation

**Pass Conditions (FullScript):**

- Structure matches the FullScript Structure list
- `set -euo pipefail` present immediately after the header
- All constants declared with `readonly`; all in-function variables declared with `local`
- `die`, `usage`, `parse_args`, and `main` are all defined
- `trap` covers `EXIT`, `INT`, and `TERM`; handler functions are defined
- `parse_args` uses `getopts` and handles both `:` and `\?` cases
- `main "$@"` is the only top-level invocation
- No business logic or procedural code at the top level
- Exit calls use named `E_`-prefixed constants

**Pass Conditions (OneOff):**

- 1–5 lines when possible, never more than 10 lines
- No scaffolding, function definitions, or header comments unless essential

**Failure Modes:**

- FullScript missing `set -euo pipefail`, `trap`, `parse_args`, or `main`
- Business logic or procedural code at top level
- `exit` called without an explicit code
- String booleans used instead of integer flags
- OneOff exceeds 10 lines without justification

## Examples

**OneOff:**

```bash
# Preview files older than 7 days:
find . -type f -name "*.log" -mtime +7 -print
# After reviewing the list, uncomment the next line to delete:
# find . -type f -name "*.log" -mtime +7 -exec rm -f {} +
```

**FullScript (structure overview):**

```bash
#!/usr/bin/env bash
#
# Processes files in a given directory.
#
# Usage: process-files [-v] [-n <limit>] <dir>
#        process-files -h
#
# Changelog:
#   - 2025-01-01: Initial version.

set -euo pipefail

readonly E_GENERAL=1
readonly E_USAGE=2
readonly E_INTERRUPT=130
readonly E_TERMINATED=143
readonly SCRIPT_NAME="$(basename "$0")"
readonly DEFAULT_LIMIT=10

verbose=0
limit="${DEFAULT_LIMIT}"
input_dir=""

die()       { echo "${SCRIPT_NAME}: error: $1" >&2; exit "${2:-${E_GENERAL}}"; }
log_info()  { echo "${SCRIPT_NAME}: $*" >&2; }
log_warn()  { echo "${SCRIPT_NAME}: warning: $*" >&2; }
log_error() { echo "${SCRIPT_NAME}: error: $*" >&2; }

usage()     { cat <<EOF
Usage: ${SCRIPT_NAME} [-v] [-n <limit>] <dir>
...
EOF
}

cleanup()       { :; }
_on_exit()      { local c=$?; cleanup || true; exit "${c}"; }
_on_interrupt() { echo "${SCRIPT_NAME}: interrupted." >&2; exit "${E_INTERRUPT}"; }
_on_terminate() { echo "${SCRIPT_NAME}: terminated." >&2; exit "${E_TERMINATED}"; }

process_files() { local dir="$1"; ...; }

parse_args() { ...; }

main() { parse_args "$@"; process_files "${input_dir}"; }

trap _on_exit EXIT
trap _on_interrupt INT
trap _on_terminate TERM

main "$@"
```

## Persona

Persona: Production-quality Bash engineer

You are a Bash engineer with deep production experience building reliable CLI tools. You prioritize strict error handling, explicit validation, and function-based organization. You choose clarity and maintainability over clever one-liners in full scripts, and you keep signal handling and exit codes consistent and correct.

## References

- Modes and selection guide: [references/modes.md](references/modes.md)
- Templates: [references/templates.md](references/templates.md)
- Standards and patterns: [references/standards.md](references/standards.md)
- Examples: [references/examples.md](references/examples.md)
