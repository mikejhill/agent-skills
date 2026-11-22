# shell-scripts

Standards for Bash and PowerShell scripts and one-liners: when to write a quick snippet versus a full script, and how a full script is structured, validated, and documented.

## Use

Loads automatically when the agent writes, refactors, or reviews a shell script or terminal command. Examples:

- "Write a script that backs up these folders nightly."
- "Give me a one-liner to find the largest files here."

Copy-ready templates are in `assets/`.

## Requirements

- Bash scripts target Bash 4+. macOS ships Bash 3.2, so install a newer Bash (for example with Homebrew) to run them there.
- PowerShell scripts target PowerShell 7 on Windows.
- Optional linters: `shellcheck`, PSScriptAnalyzer.

## Results

The agent writes a script file only when you ask for a script. One-offs that delete or change files are given in preview form first.
