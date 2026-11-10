# Bash Script Templates

## FullScript Skeleton

```bash
#!/usr/bin/env bash
#
# Does something useful with the given target.
#
# Usage: example-script [-v] [-n <limit>] <target>
#        example-script -h
#
# Changelog:
#   - 2025-01-01: Initial version.

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
readonly DEFAULT_LIMIT=10

# ---------------------------------------------------------------------------
# Script State (initialized to defaults; set by parse_args)
# ---------------------------------------------------------------------------
verbose=0
limit="${DEFAULT_LIMIT}"
target=""

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
Usage: ${SCRIPT_NAME} [-v] [-n <limit>] <target>
       ${SCRIPT_NAME} -h

Does something useful with the given target.

Arguments:
    <target>        Path or name of the item to process.

Options:
    -n <limit>      Maximum number of results (default: ${DEFAULT_LIMIT}).
    -v              Enable verbose output.
    -h              Show this help message.
EOF
}

# ---------------------------------------------------------------------------
# Cleanup and Signal Handlers
# ---------------------------------------------------------------------------
cleanup() {
	# Remove temp files or restore state here. Must be idempotent.
	:
}

_on_exit()      { local c=$?; cleanup || true; exit "${c}"; }
_on_interrupt() { echo "${SCRIPT_NAME}: interrupted." >&2; exit "${E_INTERRUPT}"; }
_on_terminate() { echo "${SCRIPT_NAME}: terminated." >&2; exit "${E_TERMINATED}"; }

# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------
process() {
	local path="$1"
	[ -e "${path}" ] || die "Path not found: ${path}" "${E_NOT_FOUND}"

	[ "${verbose}" -eq 1 ] && log_info "Processing: ${path}"

	# ... domain logic ...
}

# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
	parse_args "$@"
	process "${target}"
}

trap _on_exit EXIT
trap _on_interrupt INT
trap _on_terminate TERM

main "$@"
```

---

## Temp File Pattern

Use when the script creates intermediate files that must be cleaned up on any exit path:

```bash
# Add to script state section:
tmp_file=""

# Replace the no-op cleanup:
cleanup() {
	[ -n "${tmp_file}" ] && rm -f "${tmp_file}"
}

# Inside a business logic function:
prepare_data() {
	local source="$1"
	tmp_file="$(mktemp)"
	# Work with "${tmp_file}" ...
}
```

---

## One-Off Templates

**Find and remove old files:**

```bash
# Preview files that would be removed (dry run):
find . -type f -name "*.log" -mtime +7 -print

# Remove after confirming the list above:
# find . -type f -name "*.log" -mtime +7 -exec rm -f {} +
```

**Summarize file sizes by extension:**

```bash
find . -type f | awk -F/ '{print $NF}' | awk -F. 'NF>1 {print $NF} NF==1 {print "[no-ext]"}' | sort | uniq -c | sort -rn
```

**Extract unique values from a CSV column (simple/unquoted CSV):**

```bash
awk -F, 'NR>1 {print $2}' data.csv | sort -u
```
