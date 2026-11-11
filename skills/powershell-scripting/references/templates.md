# PowerShell Templates

## Full Script Skeleton

```powershell
<#
.SYNOPSIS
Process items under a path.

.DESCRIPTION
Provides a reusable, parameterized script that validates input, executes
the processing logic, and returns objects for downstream use.

.PARAMETER InputPath
Path to process.

.OUTPUTS
[object] Results produced by the processor.

.EXAMPLE
.\Example.ps1 -InputPath "C:\\Data"
Processes items under C:\\Data.

.NOTES
Use for reusable automation. Requires read access to InputPath.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory)]
  [ValidateNotNullOrEmpty()]
  [string]$InputPath
)

Set-StrictMode -Version Latest

#region Constants
# Constants (global scope only)
[string]$ScriptVersion = "1.0.0"
#endregion Constants

<#
.SYNOPSIS
Example class with documented behavior.
#>
#region Classes
class ExampleProcessor {
  [string]$InputPath

  <#
  .SYNOPSIS
  Initialize a new ExampleProcessor.

  .PARAMETER InputPath
  Input path to process.
  #>
  ExampleProcessor([string]$inputPath) {
    $this.InputPath = $inputPath
  }

  <#
  .SYNOPSIS
  Execute the processing action.
  #>
  [object] Execute() {
    if (-not (Test-Path -Path $this.InputPath)) {
      throw "Process: Validate input. Error: Path not found. Cause: Missing path. Solution: Provide a valid path."
    }

    return Get-Item -Path $this.InputPath
  }
}
#endregion Classes

#region Main
function Main {
  param(
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [string]$InputPath
  )

  $processor = [ExampleProcessor]::new($InputPath)
  return $processor.Execute()
}

Main @PSBoundParameters
#endregion Main
```

## One-Off Template

```powershell
Get-ChildItem -Path $Path -File | Sort-Object Length -Descending | Select-Object -First 5 FullName, Length
```
