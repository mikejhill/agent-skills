# Bash Scripting Standards and Patterns

## Core Principles

1. Function-first: all business logic lives in functions; no top-level procedural code beyond setup (strict mode, constants, state, traps, `main "$@"`).
2. Guard clauses: validate inputs at function entry before executing any logic.
3. Fail fast: `set -euo pipefail` ensures any unhandled error terminates the script immediately.
4. Explicit codes: all non-zero `exit` calls use a named `E_`-prefixed constant; successful exits use `exit 0`.
5. ANSI-compliant syntax preferred when equivalent in readability and safety to Bash-specific syntax.

---

## Strict Mode

Every FullScript starts with:

```bash
set -euo pipefail
```

| Flag          | Effect                                                          |
| ------------- | --------------------------------------------------------------- |
| `-e`          | Exit immediately when any command exits with a non-zero status. |
| `-u`          | Treat undefined variables as errors.                            |
| `-o pipefail` | Propagate the first non-zero exit code in a pipeline.           |

> Note: `set -u` requires that optional variables are initialized before use. Initialize all script state variables to a default value at the top of the script.

---

## Shebang

Use the `env`-based shebang for portability:

```bash
#!/usr/bin/env bash
```

Do **not** use `#!/bin/bash` — the `env` form respects `PATH`-managed Bash installations (e.g., Homebrew on macOS).

---

## Header Comment

Every FullScript includes a header comment immediately after the shebang:

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

**Rules:**

- Description is a single sentence on the first `#` line.
- Usage summary shows the most common invocations.
- Changelog lists changes in reverse-chronological order.

---

## Naming Conventions

| Element                | Convention           | Examples                                         |
| ---------------------- | -------------------- | ------------------------------------------------ |
| Script filename        | lowercase-hyphenated | `create-script`, `backup-files`                  |
| Functions              | lowercase_snake_case | `parse_args`, `process_files`, `die`             |
| Local variables        | lowercase_snake_case | `local file_path`, `local result`                |
| Script state variables | lowercase_snake_case | `verbose=0`, `input_dir=""`                      |
| Constants              | UPPER_SNAKE_CASE     | `readonly DEFAULT_LIMIT=10`                      |
| Exit code constants    | `E_` prefix          | `readonly E_USAGE=2`, `readonly E_INTERRUPT=130` |
| Signal handler helpers | `_on_` prefix        | `_on_exit`, `_on_interrupt`, `_on_terminate`     |

**Rules:**

- All constants declared with `readonly`.
- All variables inside functions declared with `local`.
- Signal handler names begin with `_on_` to distinguish them from business logic.

---

## Exit Codes

Declare named constants for all exit codes used in the script:

```bash
readonly E_GENERAL=1      # General/unclassified error
readonly E_USAGE=2        # Invalid arguments or missing required input
readonly E_INTERRUPT=130  # SIGINT (Ctrl+C); standard convention: 128 + signal number (2)
readonly E_TERMINATED=143 # SIGTERM; standard convention: 128 + signal number (15)
```

Use domain-specific codes for anticipated error conditions:

```bash
readonly E_NOT_FOUND=3
readonly E_PERMISSION=4
```

---

## Utility Functions

Every FullScript defines these utility functions:

```bash
die() {
	local message="${1:-An error occurred.}"
	local exit_code="${2:-${E_GENERAL}}"
	echo "${SCRIPT_NAME}: error: ${message}" >&2
	exit "${exit_code}"
}

log_info()  { echo "${SCRIPT_NAME}: $*" >&2; }
log_warn()  { echo "${SCRIPT_NAME}: warning: $*" >&2; }
log_error() { echo "${SCRIPT_NAME}: error: $*" >&2; }
```

**Usage:**

```bash
die "File not found: ${path}" "${E_NOT_FOUND}"
log_info  "Processing ${count} files."
log_warn  "Output directory already exists; contents may be overwritten."
log_error "Failed to copy file: ${src}"
```

---

## Usage Function

- Outputs to **stdout** by default. In argument-error contexts, `parse_args` redirects to stderr before exiting (see table below).
- Uses a heredoc for multi-line content.
- References `${SCRIPT_NAME}` and relevant defaults from constants.

```bash
usage() {
	cat <<EOF
Usage: ${SCRIPT_NAME} [-v] [-n <limit>] <target>
       ${SCRIPT_NAME} -h

One-sentence description of what the script does.

Arguments:
    <target>        Path or name of the item to process.

Options:
    -n <limit>      Maximum results (default: ${DEFAULT_LIMIT}).
    -v              Enable verbose output.
    -h              Show this help message.
EOF
}
```

**When to show usage:**

| Situation                   | Action                                 |
| --------------------------- | -------------------------------------- |
| User passes `-h`            | Print usage to stdout; exit 0.         |
| Missing required argument   | Print usage to stderr; exit `E_USAGE`. |
| Invalid or unknown option   | Print error to stderr; exit `E_USAGE`. |
| Option missing its argument | Print error to stderr; exit `E_USAGE`. |

Do **not** show usage for runtime errors (e.g., file not found, permission denied). Usage is only for argument/invocation problems.

---

## Argument Parsing

Use `getopts` for short options. Define a `parse_args` function that:

1. Iterates options with `getopts`.
2. Handles all cases in a `case` statement including `:` (missing argument) and `\?` (unknown option).
3. Calls `shift $((OPTIND - 1))` after the loop.
4. Validates required positional arguments.
5. Sets script state variables.

```bash
parse_args() {
	local opt
	while getopts ':n:vh' opt; do
		case "${opt}" in
		n)  limit="${OPTARG}" ;;
		v)  verbose=1 ;;
		h)  usage; exit 0 ;;
		:)  die "Option -${OPTARG} requires an argument." "${E_USAGE}" ;;
		\?) die "Invalid option: -${OPTARG}" "${E_USAGE}" ;;
		esac
	done
	shift $((OPTIND - 1))

	[ $# -lt 1 ] && { usage >&2; exit "${E_USAGE}"; }
	target="$1"
	shift
	[ $# -gt 0 ] && die "Unexpected arguments: $*" "${E_USAGE}"
}
```

**Rules:**

- Always use a leading `:` in the `getopts` string to enable silent error mode (`:` and `\?` cases).
- Use `[ ]` (ANSI) for simple integer/string tests; `[[ ]]` is acceptable when compound conditions or pattern matching make it significantly clearer.
- Never use `$[...]` arithmetic; always use `$((...))`.

---

## Signal Handling and Cleanup

Every FullScript defines a `cleanup` function, three signal handler functions, and registers traps:

```bash
cleanup() {
	# Remove temp files or restore state.
	# Keep idempotent — may be called multiple times.
	:
}

_on_exit()      { local c=$?; cleanup || true; exit "${c}"; }
_on_interrupt() { echo "${SCRIPT_NAME}: interrupted." >&2; exit "${E_INTERRUPT}"; }
_on_terminate() { echo "${SCRIPT_NAME}: terminated." >&2; exit "${E_TERMINATED}"; }

trap _on_exit EXIT
trap _on_interrupt INT
trap _on_terminate TERM
```

**Rules:**

- `_on_exit` captures the current exit code (`$?`) before doing anything else and runs cleanup best-effort (`cleanup || true`) so a cleanup failure under `set -e` cannot override the original exit status. It uses the captured `$?` because it fires on any exit and must forward the original exit code; by contrast, `_on_interrupt` and `_on_terminate` use fixed `E_`-prefixed constants because the exit reason is always the signal itself.
- `cleanup` must be idempotent (safe to call more than once).
- Trap registrations go at the top level, after all function definitions, just before `main "$@"`.
- Use temp files via `mktemp` when needed; record the path in a variable and remove it in `cleanup`.

```bash
# Temp file pattern
tmp_file=""
cleanup() {
	[ -n "${tmp_file}" ] && rm -f "${tmp_file}"
}
main() {
	parse_args "$@"
	tmp_file="$(mktemp)"
	...
}
```

---

## Guard Clauses

Validate at function entry before executing logic:

```bash
process_files() {
	local dir="$1"
	[ -d "${dir}" ] || die "Not a directory: ${dir}" "${E_NOT_FOUND}"
	[ -r "${dir}" ] || die "Permission denied: ${dir}" "${E_PERMISSION}"
	# proceed with logic
}
```

---

## Script State Variables

Script state variables (set by `parse_args`, consumed by `main`) are declared at the top level, initialized to their defaults, and mutated inside `parse_args`:

```bash
# Script state — initialized to defaults; set by parse_args.
verbose=0
limit="${DEFAULT_LIMIT}"
target=""
```

**Rules:**

- Initialize all state variables before `set -u` can see them (i.e., at the top level immediately after constants).
- Use integer `0`/`1` for boolean flags, not strings like `"true"`/`"false"`.
- Avoid mutable globals for non-argument state; pass values through function arguments instead.

---

## ANSI vs Bash-Specific Syntax

| Construct            | ANSI/POSIX (preferred) | Bash-specific (use when clearly better) |
| -------------------- | ---------------------- | --------------------------------------- |
| Command substitution | `$(command)`           | `` `command` `` — avoid                 |
| Arithmetic           | `$((expr))`            | `let`, `((...))` — avoid                |
| Conditional test     | `[ ]`                  | `[[ ]]` — use for patterns, regex       |
| Function declaration | `name() { ... }`       | `function name { ... }` — avoid         |
| String length        | `${#var}`              | —                                       |
| Default value        | `${var:-default}`      | —                                       |
| Here-document        | `<<EOF`                | —                                       |

Use `[[ ]]` only when the Bash-specific behavior is materially safer or clearer — e.g., string pattern matching (`=~`, `==` with globs) or avoiding word-splitting risks that `[ ]` cannot handle cleanly.

---

## Section Dividers

Use consistent divider comments to separate logical sections:

```bash
# ---------------------------------------------------------------------------
# Section Name
# ---------------------------------------------------------------------------
```

Standard sections (in order):

1. Constants
2. Script State
3. Utilities
4. Usage
5. Cleanup and Signal Handlers
6. Business Logic
7. Argument Parsing
8. Main

---

## Nesting and Extraction

- Max 3 levels of nesting in any function.
- When a block would exceed 3 levels, extract it into a named helper function.
- Prefer early returns via guard clauses to reduce nesting depth.
