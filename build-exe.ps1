# build-exe.ps1
# Automated build script for YT2MP3-Converter executable

param(
    [switch]$Clean,
    [switch]$Test
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  YT2MP3-Converter Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean previous builds
if ($Clean -or $true) {
    Write-Host "[1/4] Cleaning previous builds..." -ForegroundColor Yellow
    
    $itemsToClean = @(
        "build",
        "dist\YT2MP3-Converter.exe",
        "__pycache__"
    )
    
    foreach ($item in $itemsToClean) {
        if (Test-Path $item) {
            Remove-Item -Recurse -Force $item -ErrorAction SilentlyContinue
            Write-Host "  Removed: $item" -ForegroundColor Gray
        }
    }
    
    # Clean .pyc files
    Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    
    Write-Host "  Clean complete!" -ForegroundColor Green
    Write-Host ""
}

# Step 2: Check PyInstaller
Write-Host "[2/4] Checking PyInstaller..." -ForegroundColor Yellow
try {
    $pyinstallerVersion = pyinstaller --version
    Write-Host "  PyInstaller version: $pyinstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: PyInstaller not found!" -ForegroundColor Red
    Write-Host "  Install with: pip install pyinstaller" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Step 3: Build executable
Write-Host "[3/4] Building executable..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray
Write-Host ""

$buildStart = Get-Date

# Check if spec file exists, use it; otherwise build directly
if (Test-Path "YTMP3urlConverter.spec") {
    Write-Host "  Using spec file: YTMP3urlConverter.spec" -ForegroundColor Gray
    pyinstaller --clean YTMP3urlConverter.spec
} else {
    Write-Host "  Building with default options..." -ForegroundColor Gray
    pyinstaller --name "YT2MP3-Converter" `
        --onefile `
        --console `
        --clean `
        --add-data "config.example.json;." `
        YTMP3urlConverter.py
}

$buildEnd = Get-Date
$buildTime = ($buildEnd - $buildStart).TotalSeconds

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "  Build successful! (took $([math]::Round($buildTime, 2)) seconds)" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  Build failed! Check errors above." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 4: Verify and test
Write-Host "[4/4] Verifying executable..." -ForegroundColor Yellow

$exePath = "dist\YT2MP3-Converter.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Host "  Executable found: $exePath" -ForegroundColor Green
    Write-Host "  Size: $([math]::Round($exeSize, 2)) MB" -ForegroundColor Gray
    
    if ($Test) {
        Write-Host ""
        Write-Host "  Testing executable..." -ForegroundColor Yellow
        Write-Host ""
        & $exePath --help
        Write-Host ""
    }
} else {
    Write-Host "  ERROR: Executable not found at $exePath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Executable location: $exePath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test: .\dist\YT2MP3-Converter.exe --help" -ForegroundColor White
Write-Host "  2. Test download: .\dist\YT2MP3-Converter.exe <URL> --cookies-browser firefox" -ForegroundColor White
Write-Host "  3. Distribute: Include yt-dlp.exe and ffmpeg.exe with the executable" -ForegroundColor White
Write-Host ""

