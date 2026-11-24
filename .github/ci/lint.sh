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
# core.quotePath=false keeps non-ASCII names raw, so the -f test and shellcheck see real paths.
shell_files() {
  {
    git -c core.quotePath=false ls-files '*.sh' '*.bash'
    git -c core.quotePath=false ls-files | while IFS= read -r f; do
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
  while IFS= read -r f; do files+=("$f"); done < <(git -c core.quotePath=false ls-files '*.yml' '*.yaml')
  echo "yamllint: ${#files[@]} file(s)"
  [ "${#files[@]}" -eq 0 ] || yamllint --strict "${files[@]}"
}

# Tracked Python files passed explicitly, so Ruff's default excludes (_build, dist, ...) cannot
# hide a file the language-coverage test counts as covered.
# shellcheck disable=SC2329
run_ruff() {
  local files=() f
  while IFS= read -r f; do files+=("$f"); done < <(git -c core.quotePath=false ls-files '*.py' '*.pyi' '*.ipynb')
  echo "ruff: ${#files[@]} file(s)"
  [ "${#files[@]}" -eq 0 ] || ruff check --output-format="${RUFF_FORMAT:-full}" "${files[@]}"
}

step ruff run_ruff
step shellcheck run_shellcheck
step PSScriptAnalyzer pwsh -NoProfile -File .github/ci/psscriptanalyzer.ps1
step yamllint run_yamllint
step actionlint actionlint
exit "$status"
