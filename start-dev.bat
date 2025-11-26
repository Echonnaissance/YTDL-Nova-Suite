@echo off
echo Starting YouTube Downloader Development Servers...
echo.

REM Start Backend Server in new window
start "YT Downloader - Backend" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate && python -m app.main"

REM Wait a moment for backend to initialize
timeout /t 2 /nobreak >nul

REM Start Frontend Server in new window
start "YT Downloader - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ✓ Backend server starting at http://localhost:8000
echo ✓ Frontend server starting at http://localhost:5173
echo.
echo Both servers are now running in separate windows.
echo Press Ctrl+C in each window to stop the servers.
pause
