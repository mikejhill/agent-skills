# Lint every tracked PowerShell file with PSScriptAnalyzer; exit 1 on any parse error, error, or warning.
# Used by CI and by the README's local recipe. Run from the repository root.
$ErrorActionPreference = 'Stop'
$version = '1.24.0'
if (-not (Get-Module -ListAvailable PSScriptAnalyzer | Where-Object Version -EQ $version)) {
  Install-Module PSScriptAnalyzer -RequiredVersion $version -Scope CurrentUser -Force
}
Import-Module PSScriptAnalyzer -RequiredVersion $version
$files = @(git ls-files '*.ps1' '*.psm1' '*.psd1')
if ($LASTEXITCODE) { throw 'git ls-files failed' }
Write-Output "PSScriptAnalyzer: $($files.Count) file(s)"
$findings = @($files | ForEach-Object { Invoke-ScriptAnalyzer -Path $_ -Severity ParseError, Error, Warning })
foreach ($f in $findings) {
  $path = (Resolve-Path -Relative $f.ScriptPath) -replace "^\.[\\/]", "" -replace "\\", "/"
  Write-Output "::error file=$path,line=$($f.Line)::$($f.RuleName): $($f.Message)"
}
exit [int]($findings.Count -gt 0)
