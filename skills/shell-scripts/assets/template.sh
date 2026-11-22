#!/usr/bin/env bash
#
# Does something useful with the given target.
#
# Usage: example-script [-v] [-n <limit>] <target>
#        example-script -h
#
# Changelog:
#   - YYYY-MM-DD: Initial version.

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
readonly E_GENERAL=1
readonly E_USAGE=2
readonly E_NOT_FOUND=3
readonly E_INTERRUPT=130
readonly E_TERMINATED=143
SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
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

	if [ "${verbose}" -eq 1 ]; then
		log_info "Processing ${path} (limit ${limit})"
	fi

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

	if [ $# -lt 1 ]; then
		usage >&2
		exit "${E_USAGE}"
	fi
	target="$1"
	shift
	if [ $# -gt 0 ]; then
		die "Unexpected arguments: $*" "${E_USAGE}"
	fi
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
