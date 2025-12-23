param(
    [string]$RepoRoot = "./",
    [string]$ConfigPath
)

# PowerShell helper to start backend/frontend in new consoles and position/size windows
# Config JSON (optional): tools/console_positions.json
# {
#   "backend": { "x": 10, "y": 30, "width": 900, "height": 700 },
#   "frontend": { "x": 930, "y": 30, "width": 900, "height": 700 }
# }

try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    if (-not (Test-Path $RepoRoot)) { $RepoRoot = (Get-Location).Path }
    $repoRoot = (Resolve-Path $RepoRoot).Path

    if (-not $ConfigPath) { $ConfigPath = Join-Path $repoRoot 'tools\console_positions.json' }

    $config = $null
    if (Test-Path $ConfigPath) {
        try { $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json } catch { $config = $null }
    }

    Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@

    $SW_SHOWNORMAL = 1
    $SWP_NOZORDER = 0x0004
    $SWP_NOACTIVATE = 0x0010

    function Start-And-Position {
        param(
            [string]$Title,
            [string]$WorkDir,
            [string]$Cmd,
            [psobject]$Pos
        )
        Write-Host "Starting $Title in $WorkDir"
        $startInfo = @{ FilePath = 'cmd.exe'; ArgumentList = "/k $Cmd"; WorkingDirectory = $WorkDir; WindowStyle = 'Normal' }
        $proc = Start-Process @startInfo -PassThru

        # Wait for the window handle to be available
        $hWnd = [IntPtr]0
        for ($i=0; $i -lt 40; $i++) {
            Start-Sleep -Milliseconds 150
            try { $p = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue } catch { $p = $null }
            if ($p -and $p.MainWindowHandle -ne 0) { $hWnd = $p.MainWindowHandle; break }
        }
        if ($hWnd -eq [IntPtr]0) {
            Write-Host "Warning: could not obtain window handle for $Title (pid=$($proc.Id)). Skipping positioning."
            return $proc
        }

        if ($Pos) {
            try {
                [Win32]::ShowWindow($hWnd, $SW_SHOWNORMAL) | Out-Null
                [Win32]::SetWindowPos($hWnd, [IntPtr]::Zero, [int]$Pos.x, [int]$Pos.y, [int]$Pos.width, [int]$Pos.height, $SWP_NOZORDER -bor $SWP_NOACTIVATE) | Out-Null
                Write-Host "Positioned $Title at $($Pos.x),$($Pos.y) ${($Pos.width)}x${($Pos.height)}"
            } catch {
                Write-Host ("Failed to position {0}: {1}" -f $Title, $_)
            }
        }
        return $proc
    }

    # Default fallback placement: split screen left/right
    Add-Type -AssemblyName System.Windows.Forms
    $workArea = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
    $halfWidth = [math]::Floor($workArea.Width / 2) - 20
    $defaultBackendPos = @{ x = 8; y = 48; width = $halfWidth; height = $workArea.Height - 80 }
    $defaultFrontendPos = @{ x = $halfWidth + 32; y = 48; width = $halfWidth; height = $workArea.Height - 80 }

    $backendPos = $null; $frontendPos = $null
    if ($config) {
        if ($config.backend) { $backendPos = @{ x = $config.backend.x; y = $config.backend.y; width = $config.backend.width; height = $config.backend.height } }
        if ($config.frontend) { $frontendPos = @{ x = $config.frontend.x; y = $config.frontend.y; width = $config.frontend.width; height = $config.frontend.height } }
    }
    if (-not $backendPos) { $backendPos = $defaultBackendPos }
    if (-not $frontendPos) { $frontendPos = $defaultFrontendPos }

    # Start backend and frontend using Start-And-Position
    $backendCmd = "venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
    $frontendCmd = "npm run dev"

    $backendProc = Start-And-Position -Title 'UMD - Backend' -WorkDir (Join-Path $repoRoot 'backend') -Cmd $backendCmd -Pos $backendPos
    Start-Sleep -Milliseconds 400
    $frontendProc = Start-And-Position -Title 'UMD - Frontend' -WorkDir (Join-Path $repoRoot 'frontend') -Cmd $frontendCmd -Pos $frontendPos

    Write-Host "Started backend PID $($backendProc.Id) and frontend PID $($frontendProc.Id)"
} catch {
    Write-Error "Failed to run start-dev helper: $_"
    exit 1
}
