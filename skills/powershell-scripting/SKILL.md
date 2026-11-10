---
name: powershell-scripting
description: Use when creating, modifying, or refactoring PowerShell scripts that require production-quality standards including OOP architecture, guard-clause validation, fail-fast error handling, comprehensive parameter validation, and parameterized design for reusability.
---

# PowerShell Script Development

## Objective

Produce PowerShell solutions in two modes: full scripts for persisted automation and one-offs for ad-hoc execution. Full scripts must be OOP-first, parameterized, and documented; one-offs must be short and runnable as a one-liner when possible.

## Scope

**In-scope:**

- New .ps1 scripts and refactors
- One-offs and one-liners
- OOP design, guard clauses, fail-fast errors
- Parameter validation and naming conventions
- Script-level documentation

**Out-of-scope:**

- Module manifests (.psd1)
- DSC resources
- Remoting configuration
- PowerShell Workflows
- Cross-platform PowerShell Core nuances

## Inputs

**Required inputs:**

- Purpose and functional requirements
- Target output form: FullScript or OneOff
- New development or refactor

**Optional inputs:**

- Mode selection override
- Existing patterns to mirror
- Domain context (registry, file, API)
- Performance constraints

**Assumptions:**

- PowerShell 7+ on Windows
- Admin access when required
- Standard execution policy

## Outputs

**Format:**

- FullScript: .ps1 file that passes validation
- OneOff: snippet (1 line preferred, max 5 lines)

**Full Script Structure:**

1. Comment-based help at the top with `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER` (for each parameter), `.EXAMPLE`, `.NOTES`
2. Constants (global scope only)
3. Classes (all business logic)
4. Helper functions (all except Main)
5. Main function (defined last)
6. Single Main invocation

**Files produced:**

- FullScript: `[Name].ps1`
- OneOff: no file unless requested

**Formatting requirements (FullScript):**

- PascalCase for parameters and variables
- PascalCase for class names
- Verb-Noun function names (validate with `Get-Verb`)
- Max 3 levels of nesting
- One blank line between functions/classes
- Guard clauses at function entry
- Use `#region <Name>`/`#endregion` for major logical sections (Constants, Classes, Helpers, Main)

## Constraints

**Conflict resolution:** User requirements override defaults unless they violate safety or explicit MUST rules.

**Mode selection rules:**

- OneOff when user asks for a one-liner, quick command, or terminal snippet
- FullScript when user asks for a .ps1 file, reusable automation, or multi-step workflow
- Default to FullScript when ambiguous

**Global MUST:**

- Choose FullScript or OneOff and follow the mode rules
- Return objects unless formatting is explicitly requested
- Use Write-Verbose for diagnostics and Write-Information for user-facing status

**Global MUST NOT:**

- Use Write-Host for diagnostics
- Reimplement built-in cmdlets

**FullScript MUST:**

- Encapsulate business logic in classes
- Validate all parameters with attributes
- Keep global scope free of procedural logic
- Define Main last and invoke it once
- Start with help including `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER` (for each parameter), `.EXAMPLE`, `.NOTES`
- Document all classes and methods with `<# #>`
- Use guard clauses and specific exception types
- Use error messages with process, error, cause, and solution
- Use Set-StrictMode -Version Latest unless disallowed

**FullScript MUST NOT:**

- Hard-code paths or configuration
- Use mid-function `return`
- Catch and ignore errors

**OneOff MUST:**

- Prefer one line, maximum five lines
- Avoid classes and doc blocks
- Use pipeline-friendly cmdlets
- Use -WhatIf or -Confirm for destructive actions unless user opts out

**OneOff MUST NOT:**

- Create a full script scaffold
- Add long-form comments

## Procedure

1. Select mode using the mode rules.
2. FullScript: write script-level help, then structure constants, classes, helpers, Main, and invocation.
3. OneOff: build the minimal pipeline and keep length within limits.
4. Apply validation, guard clauses, error handling, and naming conventions.

## Validation

**Pass Conditions (FullScript):**

- Structure matches the Full Script Structure list
- Help includes `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER` (for each parameter), `.EXAMPLE`, `.NOTES`
- Parameters are validated; classes and methods are documented
- Max nesting depth is 3; strict mode is enabled

**Pass Conditions (OneOff):**

- One line when possible, never more than five lines
- No classes or documentation blocks
- -WhatIf or -Confirm used for destructive actions unless opted out

**Failure Modes:**

- FullScript violates structure, help, or validation rules
- OneOff exceeds five lines without justification

## Examples

**OneOff:**

```powershell
Get-ChildItem -Path $Path -File -Recurse | Sort-Object Length -Descending | Select-Object -First 5 FullName, Length
```

**FullScript (help block only):**

```powershell
<#
.SYNOPSIS
Process items under a path.

.DESCRIPTION
Validates input, executes processing logic, and returns objects for downstream use.

.PARAMETER InputPath
Path to the items to process.

.EXAMPLE
.\Example.ps1 -InputPath "C:\\Data"
Processes items under C:\\Data.

.NOTES
Use for reusable automation. Requires read access to InputPath.
#>
```

## Persona

Persona: Production-quality PowerShell architect

You are a PowerShell architect with deep production experience. You prioritize explicit validation, parameterization, and strict structure. You choose maintainability over shortcuts and keep scripts predictable and testable.

## References

- Modes and selection guide: [references/modes.md](references/modes.md)
- Templates: [references/templates.md](references/templates.md)
- Standards and patterns: [references/standards.md](references/standards.md)
- Examples: [references/examples.md](references/examples.md)
