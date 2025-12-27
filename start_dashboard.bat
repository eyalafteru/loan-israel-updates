@echo off
chcp 65001 >nul
echo ========================================
echo    Page Management Dashboard
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if requirements are installed
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    echo.
)

echo [INFO] Starting server on http://localhost:5000
echo [INFO] Press Ctrl+C to stop
echo.

python dashboard_server.py

pause





