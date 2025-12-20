@echo off
echo Starting Universal Media Downloader Development Servers...
echo.

REM Start Backend Server in new window (use /D to set working directory)
start "UMD - Backend" /D "%~dp0backend" cmd /k "venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

REM Wait a moment for backend to initialize
timeout /t 2 /nobreak >nul

REM Start Frontend Server in new window (use /D to set working directory)
start "UMD - Frontend" /D "%~dp0frontend" cmd /k "npm run dev"

echo.
echo ✓ Backend server starting at http://localhost:8000
echo ✓ Frontend server starting at http://localhost:5173
echo ✓ API Docs at http://localhost:8000/api/docs
echo.
echo Both servers are now running in separate windows.
echo Press Ctrl+C in each window to stop the servers.
pause
