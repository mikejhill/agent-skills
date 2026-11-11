# PowerShell Scripting Modes

## Mode Selection Rules

Use these rules when the user does not explicitly choose a mode:

- OneOff: User asks for a one-liner, quick command, ad-hoc check, or terminal snippet.
- FullScript: User asks for a .ps1 file, reusable automation, or multi-step workflow.
- Default: If ambiguous, use FullScript.

## Mode Summary

| Mode | When to Use | Output | Core Expectations |
| --- | --- | --- | --- |
| FullScript | Persisted, reusable automation | .ps1 file | OOP, parameterization, strict validation, documentation |
| OneOff | Ad-hoc, immediate execution | snippet | short, pipeline-first, safe defaults |

## OneOff Guardrails

- One line preferred, max five lines
- No classes or documentation blocks
- Use -WhatIf or -Confirm for destructive actions unless user opts out
- Return objects unless display formatting is requested

## FullScript Guardrails

- Strict structure: constants, classes, helpers, Main, invocation
- Business logic in classes only
- Guard clauses and parameter validation
- Specific exception types in catch blocks
- Set-StrictMode -Version Latest unless explicitly disallowed
