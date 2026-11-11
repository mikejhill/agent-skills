# Bash Script Examples

## One-Off Examples

**List the five largest files in the current directory tree:**

```bash
find . -type f -exec du -k {} + | sort -rn | head -5
```

**Count lines of Bash source across a project:**

```bash
find . -type f \( -name "*.sh" -o -name "*.bash" \) -print0 | xargs -0 wc -l | sort -rn | head
```

**Kill all processes matching a name (without using pkill by name):**

```bash
pids=$(ps aux | awk '/my-process/ && !/awk/ {print $2}')
if [ -n "$pids" ]; then
  kill $pids
fi
```

---

## FullScript Refactor Example

**Scenario:** Refactor `createscript`, a script that creates an executable CLI script from a template.

### Before (issues highlighted)

```bash
#!/bin/bash
# Creates an executable script file on the build path.

# Error-handling
set -e
# BUG: exit 130 is inside the echo string — it will never execute as a command.
trap 'echo "Script terminated. ; exit 130" >&2' INT TERM

# Constants
declare -r SCRIPTS_DIR=~/'Documents/scripts'
declare -r SCRIPTS_TEMPLATE="${SCRIPTS_DIR}/template.txt"
declare -r DEFAULT_EDIT_TOOL='vim'
# BAD: String booleans — non-idiomatic, error-prone in conditionals.
declare -r TRUE='true'
declare -r FALSE='false'

usage() {
    cat >&2 <<-EOF
        Creates an executable script file in the scripts directory.
        Usage:
            $(basename "$0") [-e <file editor>] <script name>
        ...
    EOF
}

# BAD: Top-level variable declarations mixed with logic.
declare scriptName
declare scriptPath
declare editTool="${DEFAULT_EDIT_TOOL}"
declare scriptExists="${FALSE}"

# BAD: Top-level procedural argument parsing — not in a function.
while getopts ':e:h' opt; do
    case "${opt}" in
    e) editTool="${OPTARG}" ;;
    h) usage; exit 0 ;;
    \?) echo "Invalid option: -${OPTARG}" >&2; exit 1 ;;
    :)  echo "Option -${OPTARG} requires an argument." >&2; exit 1 ;;
    esac
done
shift "$((OPTIND - 1))"

scriptName="$1"
if [ "${scriptName:0:1}" == '/' ]; then
    scriptPath="${scriptName}"
else
    scriptPath="${SCRIPTS_DIR}/${scriptName}"
fi
shift 1

# BAD: Validation after assignment; missing -u and -o pipefail.
if [ -z "${scriptName}" ]; then
    usage
    exit 1
fi

# BAD: String boolean used in conditional — relies on "true"/"false" being valid commands.
if [ -e "${scriptPath}" ]; then
    scriptExists="${TRUE}"
fi

if ! "${scriptExists}"; then
    cp "${SCRIPTS_TEMPLATE}" "${scriptPath}"
    chmod u+x "${scriptPath}"
fi

"${editTool}" "${scriptPath}"

if ! "${scriptExists}" && cmp -s "${scriptPath}" "${SCRIPTS_TEMPLATE}"; then
    echo 'No changes from template detected. Removing script.'
    rm "${scriptPath}"
fi

dos2unix "${scriptPath}" &>/dev/null
```

**Issues:**

- Broken trap: `exit 130` is inside the echo string and never executes.
- Missing `set -u` and `set -o pipefail`.
- No `main` function — all logic runs at the top level.
- String booleans (`TRUE`/`FALSE`) used as command names in conditionals (`! "${scriptExists}"`).
- Argument parsing and business logic both run at top level.
- `usage` sends output to stderr unconditionally; `-h` should print to stdout.
- `shift 1` before the emptiness check — crashes if `$1` is unset under `set -u`.
- No `local` variables since there are no helper functions.
- No `EXIT` trap for cleanup.

### After (refactored)

```bash
#!/usr/bin/env bash
#
# Creates an executable script file in the scripts directory.
#
# Usage: create-script [-e <editor>] <name>
#        create-script -h
#
# Changelog:
#   - 2025-01-01: Refactor to function-based architecture.
#   - 2022-11-04: Conform to latest shell script standards.

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
readonly E_GENERAL=1
readonly E_USAGE=2
readonly E_NOT_FOUND=3
readonly E_INTERRUPT=130
readonly E_TERMINATED=143
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPTS_DIR="${HOME}/Documents/scripts"
readonly SCRIPTS_TEMPLATE="${SCRIPTS_DIR}/template.txt"
readonly DEFAULT_EDITOR="vim"

# ---------------------------------------------------------------------------
# Script State (initialized to defaults; set by parse_args)
# ---------------------------------------------------------------------------
editor="${DEFAULT_EDITOR}"
script_name=""

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
die() {
	local message="${1:-An error occurred.}"
	local exit_code="${2:-${E_GENERAL}}"
	echo "${SCRIPT_NAME}: error: ${message}" >&2
	exit "${exit_code}"
}

log_info()  { echo "${SCRIPT_NAME}: $*" >&2; }
log_warn()  { echo "${SCRIPT_NAME}: warning: $*" >&2; }
log_error() { echo "${SCRIPT_NAME}: error: $*" >&2; }

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
	cat <<EOF
Usage: ${SCRIPT_NAME} [-e <editor>] <name>
       ${SCRIPT_NAME} -h

Creates an executable script file in the scripts directory.

Arguments:
    <name>          Name of the script to create.

Options:
    -e <editor>     Editor used to open the script (default: '${DEFAULT_EDITOR}').
    -h              Show this help message.

Scripts directory: ${SCRIPTS_DIR}
EOF
}

# ---------------------------------------------------------------------------
# Cleanup and Signal Handlers
# ---------------------------------------------------------------------------
cleanup() {
	:
}

_on_exit()      { local c=$?; cleanup || true; exit "${c}"; }
_on_interrupt() { echo "${SCRIPT_NAME}: interrupted." >&2; exit "${E_INTERRUPT}"; }
_on_terminate() { echo "${SCRIPT_NAME}: terminated." >&2; exit "${E_TERMINATED}"; }

# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------
resolve_script_path() {
	local name="$1"
	case "${name}" in
	/*)  echo "${name}" ;;
	*)   echo "${SCRIPTS_DIR}/${name}" ;;
	esac
}

create_from_template() {
	local path="$1"
	[ -f "${SCRIPTS_TEMPLATE}" ] || die "Template not found: ${SCRIPTS_TEMPLATE}" "${E_NOT_FOUND}"
	cp "${SCRIPTS_TEMPLATE}" "${path}"
	chmod u+x "${path}"
}

remove_if_unchanged() {
	local path="$1"
	if cmp -s "${path}" "${SCRIPTS_TEMPLATE}"; then
		log_info "No changes from template detected. Removing script."
		rm "${path}"
	fi
}

run_editor() {
	local tool="$1"
	local path="$2"
	command -v "${tool}" > /dev/null 2>&1 || die "Editor not found: ${tool}" "${E_NOT_FOUND}"
	"${tool}" "${path}"
}

create_script() {
	local name="$1"
	[ -n "${name}" ] || die "Script name required." "${E_USAGE}"
	local script_path
	script_path="$(resolve_script_path "${name}")"

	local already_exists=0
	[ -e "${script_path}" ] && already_exists=1

	[ "${already_exists}" -eq 0 ] && create_from_template "${script_path}"

	run_editor "${editor}" "${script_path}"

	[ "${already_exists}" -eq 0 ] && remove_if_unchanged "${script_path}"

	if [ -f "${script_path}" ]; then
		dos2unix "${script_path}" > /dev/null 2>&1 || true  # Best-effort; non-critical
	fi
}

# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------
parse_args() {
	local opt
	while getopts ':e:h' opt; do
		case "${opt}" in
		e)  editor="${OPTARG}" ;;
		h)  usage; exit 0 ;;
		:)  die "Option -${OPTARG} requires an argument." "${E_USAGE}" ;;
		\?) die "Invalid option: -${OPTARG}" "${E_USAGE}" ;;
		esac
	done
	shift $((OPTIND - 1))

	[ $# -lt 1 ] && { usage >&2; exit "${E_USAGE}"; }
	script_name="$1"
	shift
	[ $# -gt 0 ] && die "Unexpected arguments: $*" "${E_USAGE}"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
	parse_args "$@"
	create_script "${script_name}"
}

trap _on_exit EXIT
trap _on_interrupt INT
trap _on_terminate TERM

main "$@"
```

**Changes made:**

- Fixed trap: handler functions `_on_interrupt` and `_on_terminate` call `exit` as a command, not inside a string.
- Added `set -u` and `set -o pipefail`.
- All logic moved into functions; `main` is the only top-level call.
- String booleans replaced with integer flag (`already_exists=0`/`1`).
- `parse_args` handles argument parsing; validation (`$# -lt 1`) happens before assignment.
- `usage` prints to stdout; error paths redirect `usage >&2`.
- Business logic decomposed into `resolve_script_path`, `create_from_template`, `run_editor`, `remove_if_unchanged`, `create_script`.
- `EXIT` trap ensures cleanup runs on any exit path.
- `dos2unix` failure ignored with `|| true` since it is non-critical post-processing.
