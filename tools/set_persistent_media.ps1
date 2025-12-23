<#
PowerShell helper to set a persistent media folder for the backend.
Usage:
  pwsh .\tools\set_persistent_media.ps1 -Path "C:\Users\You\Videos\MyFolder"
#>
param(
  [Parameter(Mandatory=$true)]
  [string]$Path
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptDir "..\backend\persistent_media.json"

try {
  $full = Resolve-Path -Path $Path -ErrorAction Stop
  $p = $full.ProviderPath
  $obj = @{ path = $p } | ConvertTo-Json
  New-Item -Path (Split-Path $backendPath -Parent) -ItemType Directory -Force | Out-Null
  Set-Content -Path $backendPath -Value $obj -Encoding UTF8
  Write-Output "Set persistent media path -> $p"
  exit 0
} catch {
  Write-Error "Failed to set persistent media path: $_"
  exit 1
}
