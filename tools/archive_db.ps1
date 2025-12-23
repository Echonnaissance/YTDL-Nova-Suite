# Archive the SQLite database by moving it into the Backup folder with a timestamp
param(
    [string]$DbPath = "backend/universal_media_downloader.db",
    [string]$BackupDir = "Backup"
)

Set-StrictMode -Version Latest
try {
    if (-not (Test-Path $DbPath)) {
        Write-Error "Database file not found: $DbPath"
        exit 2
    }

    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir | Out-Null
    }

    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $base = [System.IO.Path]::GetFileNameWithoutExtension($DbPath)
    $ext = [System.IO.Path]::GetExtension($DbPath)
    $dest = Join-Path $BackupDir ("${base}_${ts}${ext}")

    Move-Item -Path $DbPath -Destination $dest -Force
    Write-Output "Archived $DbPath -> $dest"
    exit 0
} catch {
    Write-Error "Failed to archive DB: $_"
    exit 1
}
