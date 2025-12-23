# Save current console window positions to tools/console_positions.json
# Usage: run this while your UMD console windows are open and positioned where you want them.

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Win32 {
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")]
  public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
}
"@

function Get-WindowRectForProcess($proc) {
  try {
    if (-not $proc -or $proc.MainWindowHandle -eq 0) { return $null }
    $rect = New-Object Win32+RECT
    if ([Win32]::GetWindowRect($proc.MainWindowHandle, [ref]$rect)) {
      return @{ x = $rect.Left; y = $rect.Top; width = ($rect.Right - $rect.Left); height = ($rect.Bottom - $rect.Top) }
    }
  } catch { }
  return $null
}

# Look for processes with exact titles first
$backendProc = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -eq 'UMD - Backend' } | Select-Object -First 1
$frontendProc = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -eq 'UMD - Frontend' } | Select-Object -First 1

# fallback: find any window with 'UMD' in the title
if (-not $backendProc) { $backendProc = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -match 'UMD' } | Select-Object -First 1 }
if (-not $frontendProc) { $frontendProc = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -match 'UMD' } | Select-Object -First 2 | Select-Object -Last 1 }

$backendRect = Get-WindowRectForProcess $backendProc
$frontendRect = Get-WindowRectForProcess $frontendProc

# If we couldn't find windows, let the user know and exit non-zero
if (-not $backendRect -and -not $frontendRect) {
  Write-Error "Could not find UMD console windows. Make sure they are open with titles 'UMD - Backend' and 'UMD - Frontend'."
  exit 1
}

$data = @{ }
if ($backendRect) { $data.backend = $backendRect }
if ($frontendRect) { $data.frontend = $frontendRect }

$outPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) 'console_positions.json'
$data | ConvertTo-Json -Depth 3 | Set-Content -Path $outPath -Encoding UTF8
Write-Host "Saved console positions to $outPath"
