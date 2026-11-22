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

# Bash 3.2 (macOS default) has no mapfile, so fill arrays with a read loop.
# shellcheck disable=SC2329
run_shellcheck() {
  local files=() f
  while IFS= read -r f; do files+=("$f"); done < <(shell_files)
  echo "shellcheck: ${#files[@]} file(s)"
  [ "${#files[@]}" -eq 0 ] || shellcheck --format=gcc "${files[@]}"
}

# Tracked files only, so ignored scratch folders locally do not change the result.
# shellcheck disable=SC2329
run_yamllint() {
  local files=() f
  while IFS= read -r f; do files+=("$f"); done < <(git ls-files '*.yml' '*.yaml')
  echo "yamllint: ${#files[@]} file(s)"
  [ "${#files[@]}" -eq 0 ] || yamllint --strict "${files[@]}"
}

step ruff ruff check --output-format="${RUFF_FORMAT:-full}" .
step shellcheck run_shellcheck
step PSScriptAnalyzer pwsh -NoProfile -File .github/ci/psscriptanalyzer.ps1
step yamllint run_yamllint
step actionlint actionlint
exit "$status"
