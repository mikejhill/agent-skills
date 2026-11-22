# PowerShell FullScript standards

Start from [template.ps1](../assets/template.ps1). Target PowerShell 7 on Windows unless told otherwise. Module manifests, DSC, remoting setup, and workflows are out of scope.

## Section order

Comment-based help, `[CmdletBinding()]`, `param()`, `Set-StrictMode -Version Latest`, then `#region` blocks: Constants, Classes, HelperFunctions, Main. `Main` is defined last and invoked once with `Main @PSBoundParameters`.

## Help

Put help before `[CmdletBinding()]`, with `.SYNOPSIS`, `.DESCRIPTION`, one `.PARAMETER` per parameter, at least one `.EXAMPLE`, and `.NOTES` (when to use it and prerequisites). Document every class and method with a `<# .SYNOPSIS #>` block.

## Design

- Put business logic in classes. Functions only orchestrate.
- Use `hidden` methods with an underscore prefix for internal steps.
- No mid-function `return` for control flow. Use guard clauses that `throw`.
- Throw specific exception types, and catch specific types. Never catch and ignore.

## Parameters

Validate every parameter with attributes: `ValidateNotNullOrEmpty`, `ValidateSet`, `ValidateRange`, `ValidateScript`, or `ValidatePattern`. Use `[CmdletBinding(SupportsShouldProcess)]` and `$PSCmdlet.ShouldProcess()` for destructive actions.

## Naming

| Element | Convention | Example |
| --- | --- | --- |
| Functions | Approved Verb-Noun (`Get-Verb`) | `Set-RegistryValue` |
| Parameters, variables, classes | PascalCase | `$RegistryPath`, `RegistryManager` |
| Private members | Underscore prefix | `_ValidateInput()` |
| Script file | PascalCase | `Export-Report.ps1` |

## Errors

Error messages state the process, the error, the cause, and the fix:

```text
Process: Setting value in registry. Error: Access denied. Cause: Missing permissions. Solution: Run as administrator.
```

## Output and logging

- Return objects. Format only when the user asks.
- `Write-Verbose` for diagnostics, `Write-Information` for user-facing status.
- Build expensive diagnostic strings only inside `if ($VerbosePreference -eq 'Continue') { ... }`.
- Do not reimplement built-in cmdlets.

## OneOff

One pipeline, objects out, no classes or help blocks. Add `-WhatIf` or `-Confirm` to destructive cmdlets unless the user opts out.
