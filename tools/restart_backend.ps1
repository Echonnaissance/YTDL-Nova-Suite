<#
Minimal backend restart script.
- Stops any process holding TCP port 8000
- Starts the FastAPI app with Uvicorn using the repo virtualenv python if present
No prompts, downloads, or other actions.
#>

Set-StrictMode -Version Latest

$ErrorActionPreference = 'Stop'

# Determine repository root (script directory)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Find processes bound to port 8000 and stop them
try {
    $conns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction Stop
}
catch {
    $conns = @()
}

if ($conns) {
    $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($procId in $pids) {
        try { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue } catch {}
    }
}

<# Prefer the venv's uvicorn executable if available. This avoids invoking
   the Python interpreter in a way that could be intercepted by editor
   debug wrappers or accidentally run a different script. If the uvicorn
   executable is not present, fallback to `python -m uvicorn` as before. #>

# Paths to possible executables
$uvicornWin = Join-Path $repoRoot '.venv\Scripts\uvicorn.exe'
$uvicornNix = Join-Path $repoRoot '.venv/bin/uvicorn'
$pythonWin = Join-Path $repoRoot '.venv\Scripts\python.exe'
$pythonNix = Join-Path $repoRoot '.venv/bin/python'

if (Test-Path $uvicornWin) {
    $exec = $uvicornWin
    $args = @('app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload')
}
elseif (Test-Path $uvicornNix) {
    $exec = $uvicornNix
    $args = @('app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload')
}
elseif (Test-Path $pythonWin) {
    $exec = $pythonWin
    $args = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload')
}
elseif (Test-Path $pythonNix) {
    $exec = $pythonNix
    $args = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload')
}
else {
    $exec = 'python'
    $args = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload')
}

Write-Host "Starting backend with: $exec $($args -join ' ')"

# Start Uvicorn in a new background process without any interactive prompts
Start-Process -FilePath $exec -ArgumentList $args -WindowStyle Hidden | Out-Null

Write-Host 'Backend restart requested (uvicorn started).'
