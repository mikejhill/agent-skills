# Intent

Make agents write shell code that is safe and maintainable as a reusable script, and short and runnable as a one-off, in Bash or PowerShell. Merges `bash-scripting` and `powershell-scripting`.

## Goals

1. Full scripts are production quality: structured, fail fast, validate input, and document their usage.
2. One-offs stay short and runnable inline, with no scaffolding.
3. Bash and PowerShell share the same principles, and each follows its own idioms.

## Requirements

- Two modes: FullScript for persisted CLI tools and automation, OneOff for ad-hoc execution. Default to FullScript when ambiguous.
- Bash FullScripts are function-based with strict error handling (`set -euo pipefail`), `getopts` argument parsing, signal trapping, named exit codes, and a CLI-first design.
- PowerShell FullScripts use classes for business logic, guard-clause validation, fail-fast error handling, attribute validation on every parameter, comment-based help, and parameterized design for reuse.
- Diagnostics go to stderr (PowerShell: verbose and information streams), primary output to stdout (PowerShell: objects).
- OneOffs: Bash 1-5 lines (max 10), PowerShell one line (max 5). Destructive one-offs use a preview or `-WhatIf`.
- Out of scope: shell libraries, other shells (sh, zsh, fish), init scripts, Makefiles, CI pipeline scripts, PowerShell modules, DSC, and remoting setup.

## Log

- 2026-11-10: Imported into the SkillSinc library layout as `bash-scripting` and `powershell-scripting`. Requirements above are taken from those skills.
- 2026-11-22: [agent] Merged both into `shell-scripts` during the migration to the `skill-development` standard. "scripting" is a gerund, and the two skills shared their mode rules and principles. Dropped the 8-section template, persona, and MUST/MAY lists. Language detail moved to `references/`, and templates to `assets/`.
- 2026-11-22: [agent] Fixed the Bash template: `parse_args` and `process` ended with `[ test ] && action`, so a false test returned 1 and `set -e` exited on every valid run. Fixed ShellCheck SC2155, and a doubled backslash in the PowerShell help example.
