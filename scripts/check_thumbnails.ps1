<#
.SYNOPSIS
  Check that thumbnails in Downloads/Thumbnails are served by the backend.

DESCRIPTION
  Iterates files under Downloads/Thumbnails, URL-encodes each filename and
  performs an HTTP HEAD request to the FastAPI static mount. If HEAD fails,
  performs a GET and prints a truncated response body (useful for JSON tracebacks).

USAGE
  From the repository root (PowerShell):
    .\scripts\check_thumbnails.ps1

  Optionally pass a different base URL:
    .\scripts\check_thumbnails.ps1 -BaseUrl "http://localhost:8000"
#>

param(
  [string]$BaseUrl = "http://127.0.0.1:8000"
)

try {
  $thumbDir = Join-Path -Path $PSScriptRoot -ChildPath "..\Downloads\Thumbnails"
  $thumbDir = (Resolve-Path $thumbDir -ErrorAction Stop).ProviderPath
}
catch {
  Write-Error "Thumbnails directory not found relative to script: $thumbDir"
  exit 1
}

Get-ChildItem -Path $thumbDir -File | ForEach-Object {
  $name = $_.Name
  $enc = [uri]::EscapeDataString($name)
  $url = "$BaseUrl/media/Thumbnails/$enc"

  Write-Host "Checking: $name"
  Write-Host "URL: $url"

  try {
    $head = Invoke-WebRequest -Uri $url -Method Head -ErrorAction Stop
    $status = if ($head.StatusCode) { $head.StatusCode } else { $head.StatusDescription }
    Write-Host "HEAD -> $status"
  }
  catch {
    Write-Host "HEAD failed: $($_.Exception.Message)"
    Write-Host "Fetching full response..."
    try {
      $resp = Invoke-WebRequest -Uri $url -Method Get -ErrorAction Stop
      $status = if ($resp.StatusCode) { $resp.StatusCode } else { $resp.StatusDescription }
      Write-Host "GET -> $status"
      if ($resp.Content) {
        $txt = $resp.Content
        if ($txt.Length -gt 4000) { $txt = $txt.Substring(0, 4000) + "... (truncated)" }
        Write-Host "Response body (truncated):`n$txt"
      }
    }
    catch {
      Write-Host "GET failed: $($_.Exception.Message)"
    }
  }

  Write-Host ('-' * 60)
}
