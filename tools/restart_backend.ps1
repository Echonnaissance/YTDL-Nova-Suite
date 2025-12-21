# Restart backend: stop processes on port 8000, then start uvicorn
try {
    $conns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction Stop
} catch {
    $conns = @()
}
$pids = @()
foreach ($c in $conns) { $pids += $c.OwningProcess }
if ($pids.Count -gt 0) {
    foreach ($pitem in $pids) {
            try { Stop-Process -Id $pitem -Force -ErrorAction SilentlyContinue } catch {}
        }
}
# Start uvicorn in background using python from PATH
Start-Process -FilePath python -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000','--reload' -WindowStyle Hidden
Write-Host 'backend restart command issued'
