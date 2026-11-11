# PowerShell Standards and Patterns

## Core Principles

1. OOP first for full scripts
2. Guard clauses at function entry
3. Fail fast on invalid preconditions
4. Parameterize everything that changes

## Script Start Requirement

- Full scripts MUST start with comment-based help that includes `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER` (for each parameter), `.EXAMPLE`, and `.NOTES`.
- Place the help block before `[CmdletBinding()]` or `param()`.

## Full Script Structure

```powershell
<#
.SYNOPSIS
Short summary.

.DESCRIPTION
Thorough explanation of purpose, behavior, and output.

.PARAMETER ParameterName
Description of each parameter.

.EXAMPLE
Example invocation and what it does.

.NOTES
When to use, when not to use, and any prerequisites.
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest

#region Constants
# Constants
#endregion Constants
#region Classes
# Classes
#endregion Classes
#region HelperFunctions
# Helper functions
#endregion HelperFunctions
#region Main
# Main
# Main invocation
#endregion Main
```

## Object-Oriented Design

- All business logic belongs in classes.
- Use hidden helper methods for nested logic.
- Keep functions as orchestration only.

## Guard Clauses and Error Messages

- Validate inputs first, then execute logic.
- Errors must include: process, error, cause, and solution.

Example format:

```text
Process: Setting value in registry.
Error: Access denied.
Cause: Missing permissions.
Solution: Run as administrator.
```

## Parameter Validation

Use attributes on every parameter:

- `ValidateNotNullOrEmpty`
- `ValidateSet`
- `ValidateRange`
- `ValidateScript`
- `ValidatePattern`

## Naming Conventions

| Element         | Convention        | Examples                        |
| --------------- | ----------------- | ------------------------------- |
| Functions       | Verb-Noun         | `Get-Item`, `Set-RegistryValue` |
| Parameters      | PascalCase        | `$RegistryPath`                 |
| Variables       | PascalCase        | `$BackupPath`                   |
| Classes         | PascalCase        | `RegistryManager`               |
| Private Members | Underscore prefix | `_ValidateInput()`              |

## Nesting and Extraction

- Max 3 levels of nesting.
- Extract deeper logic into class methods.

## Logging and Output

- Use `Write-Verbose` for diagnostics.
- Use `Write-Information` for user-facing status.
- Return objects, not formatted strings, unless requested.

### Verbose Logging (Performance)

Avoid expensive string construction when verbose logging is disabled. Guard heavy work behind a verbose check and only build strings inside that block.

```powershell
if ($VerbosePreference -eq 'Continue') {
  $details = Get-HeavyDiagnostics -Path $Path
  Write-Verbose ("[Scan] Details: {0}" -f $details)
}
```

When you need structured data, compute it only inside the verbose branch or pass a simple identifier until verbose is enabled.

## Advanced Features

- Use `[CmdletBinding(SupportsShouldProcess)]` when the action is destructive.
- Use pipeline support only when it reduces friction.
