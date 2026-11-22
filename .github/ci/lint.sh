#!/usr/bin/env bash
# Run every code linter CI runs, on the same files. Used by CI and the README's local
# recipe. Run from the repository root; needs the tools in requirements.txt, plus pwsh.
set -uo pipefail

status=0
step() {
  echo "== $1"
  shift
  "$@" || status=1
}

# shellcheck disable=SC2329  # called through step
shell_files() {
  {
    git ls-files '*.sh' '*.bash'
    git ls-files | while IFS= read -r f; do
      [ -f "$f" ] && head -n1 "$f" | grep -qE '^#!.*\b(ba|da|k)?sh\b' && echo "$f"
    done
  } | sort -u
}

# shellcheck disable=SC2329
run_shellcheck() {
  local files
  mapfile -t files < <(shell_files)
  echo "shellcheck: ${#files[@]} file(s)"
  [ "${#files[@]}" -eq 0 ] || shellcheck --format=gcc "${files[@]}"
}

step ruff ruff check --output-format="${RUFF_FORMAT:-full}" .
step shellcheck run_shellcheck
step PSScriptAnalyzer pwsh -NoProfile -File .github/ci/psscriptanalyzer.ps1
step yamllint yamllint --strict .
step actionlint actionlint
exit "$status"
