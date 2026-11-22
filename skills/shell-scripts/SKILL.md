---
name: shell-scripts
description: >-
  Standards for Bash and PowerShell scripts and one-liners: structure, strict
  error handling, argument parsing, validation, and output streams. Use when
  writing, refactoring, or reviewing a .sh/.bash or .ps1 script or a terminal
  one-off.
---

# Shell scripts

Write shell code in one of two modes, in the language the target system runs.

## Pick the mode

| Mode | Use when | Output |
| --- | --- | --- |
| OneOff | A one-liner, quick command, ad-hoc check, or terminal snippet | Snippet: Bash 1-5 lines (max 10), PowerShell 1 line (max 5). No file unless asked. |
| FullScript | A script file, reusable CLI tool, or multi-step workflow | One file built from the template |

Default to FullScript when the ask is ambiguous.

## Pick the language

- Follow the user's ask or the repository's existing scripts.
- Otherwise use Bash for Linux and macOS targets, and PowerShell 7 for Windows targets. When a script must run on both, write both, or suggest Python instead.
- Bash scripts assume Bash 4+. macOS ships 3.2 at `/bin/bash`, so say so when a script uses Bash 4 features.

## Rules for both languages

- Validate all inputs before any work. Use guard clauses and keep nesting to three levels.
- Send primary output to stdout. Send logs, status, warnings, and errors to stderr (PowerShell: `Write-Verbose`, `Write-Information`, `Write-Error`; never `Write-Host` for diagnostics).
- Fail fast. Never ignore a non-zero exit or swallow an error without a comment saying why it is safe.
- Do not hard-code paths or configurable values. Use parameters or named constants.
- Keep business logic out of top-level code. Top level holds only declarations, setup, and one call to `main` (`Main`).
- Give errors enough to act on: what was being done, what failed, and how to fix it.
- In a OneOff that deletes or changes things, show a preview first (`-print`, `--dry-run`, `-WhatIf`) and leave the destructive form for the user to run.
- Write temp files with `mktemp` or `New-TemporaryFile`, and remove them on exit.

## FullScript essentials

**Bash** ([bash.md](references/bash.md), template [template.sh](assets/template.sh)):

- `#!/usr/bin/env bash`, a header comment (description, usage, changelog), then `set -euo pipefail`.
- `readonly` constants, `local` variables in functions, integer `0`/`1` flags, named `E_*` exit codes.
- `die`, `log_*`, `usage`, `parse_args` (using `getopts` with a leading `:`), and `main`, defined last.
- Traps for `EXIT` (idempotent cleanup), `INT` (exit 130), and `TERM` (exit 143).

**PowerShell** ([powershell.md](references/powershell.md), template [template.ps1](assets/template.ps1)):

- Comment-based help first (`.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER` for each parameter, `.EXAMPLE`, `.NOTES`), then `[CmdletBinding()]`, `param()`, and `Set-StrictMode -Version Latest`.
- Validation attributes on every parameter. Business logic in documented classes. A `Main` function, defined last and invoked once.
- Return objects, not formatted text. Use `SupportsShouldProcess` for destructive actions.
- `#region` blocks for Constants, Classes, Helpers, and Main.

## Checklist

- [ ] Mode and language match the ask.
- [ ] FullScript follows the template's section order.
- [ ] Bash passes `shellcheck` and `bash -n`. PowerShell passes `Invoke-ScriptAnalyzer` when available.
- [ ] `-h` / `Get-Help` shows usage. Invalid arguments exit with the usage error code.

## References

- [bash.md](references/bash.md): read when writing or reviewing a Bash FullScript.
- [powershell.md](references/powershell.md): read when writing or reviewing a PowerShell FullScript.
- [template.sh](assets/template.sh), [template.ps1](assets/template.ps1): copy to start a FullScript.
