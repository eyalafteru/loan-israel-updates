@echo off
chcp 65001 >nul
echo ========================================
echo    Page Management Dashboard
echo ========================================
echo.

REM ====== KILL ALL EXISTING PYTHON PROCESSES ======
echo [INFO] Stopping all running Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

REM Wait a moment for processes to fully terminate
timeout /t 2 /nobreak >nul
echo [INFO] All Python processes stopped.
echo.

REM ====== CLEAR STALE STATE FILES ======
echo [INFO] Clearing stale state files...
if exist "running_jobs.json" del /f "running_jobs.json" >nul 2>&1
if exist "full_auto_jobs.json" del /f "full_auto_jobs.json" >nul 2>&1
echo [INFO] State files cleared.
echo.

REM ====== CLEAR TMP FOLDER ======
echo [INFO] Clearing temp files...
if exist "tmp" rmdir /s /q "tmp" >nul 2>&1
mkdir tmp >nul 2>&1
if exist "job_locks" rmdir /s /q "job_locks" >nul 2>&1
echo [INFO] Temp files cleared.
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
