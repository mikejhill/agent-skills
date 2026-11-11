# PowerShell Examples

## One-Off One-Liner

**Scenario:** Find the five largest files under a path

```powershell
Get-ChildItem -Path $Path -File -Recurse | Sort-Object Length -Descending | Select-Object -First 5 FullName, Length
```

## Full Script (Skeleton)

Use the full script skeleton in [templates.md](templates.md) as the baseline. Keep major sections in `#region <Name>`/`#endregion` blocks (Constants, Classes, Main) and add domain-specific classes and methods in the class section while keeping orchestration in `Main`.

## Full Script (Refactor Example)

**Before:**

```powershell
$BasePath = "HKLM:\Software\MyApp"
$items = Get-ChildItem $BasePath
foreach ($item in $items) {
  $name = $item.PSChildName
  $value = Get-ItemProperty -Path $item.PSPath
  if ($value.Enabled -eq 1) {
    Write-Host "Found: $name"
  }
}
```

**After (Refactored):**

```powershell
<#
.SYNOPSIS
Enumerate enabled registry items.

.DESCRIPTION
Refactors the procedural enumeration into a parameterized, class-based
implementation with validation and verbose diagnostics.

.PARAMETER RegistryPath
Base registry path containing items to scan for enabled entries.
#>
[CmdletBinding()]
param(
  [Parameter()]
  [ValidateScript({ Test-Path $_ -PathType Container })]
  [string]$RegistryPath = "HKLM:\Software\MyApp"
)

Set-StrictMode -Version Latest

#region Classes
class RegistryScanner {
  [string]$BasePath

  RegistryScanner([string]$path) {
    if (-not (Test-Path $path)) {
      throw "Process: Validate input. Error: Path not found. Cause: Missing path. Solution: Provide a valid path."
    }
    $this.BasePath = $path
  }

  <#
  .SYNOPSIS
  Find all enabled items in the registry path.
  #>
  [array] FindEnabledItems() {
    $items = Get-ChildItem -Path $this.BasePath -ErrorAction Stop
    $enabledItems = @()

    foreach ($item in $items) {
      if ($this._IsItemEnabled($item.PSPath)) {
        $enabledItems += $item.PSChildName
      }
    }

    return $enabledItems
  }

  hidden [bool] _IsItemEnabled([string]$itemPath) {
    $value = Get-ItemProperty -Path $itemPath -Name "Enabled" -ErrorAction SilentlyContinue
    return $null -ne $value -and $value.Enabled -eq 1
  }
}
#endregion Classes

#region Main
function Main {
  param([string]$RegistryPath)

  $scanner = [RegistryScanner]::new($RegistryPath)
  return $scanner.FindEnabledItems()
}

Main @PSBoundParameters
#endregion Main
```
