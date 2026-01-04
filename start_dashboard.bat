@echo off
chcp 65001 >nul

REM ====== GO TO SCRIPT DIRECTORY ======
cd /d "%~dp0"

echo ========================================
echo    Page Management Dashboard
echo ========================================
echo.
echo [INFO] Working directory: %CD%
echo.

REM ====== FIND PYTHON ======
set PYTHON_CMD=

where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :found_python
)

where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :found_python
)

if exist "C:\Python312\python.exe" (
    set PYTHON_CMD=C:\Python312\python.exe
    goto :found_python
)

if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    goto :found_python
)

if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PYTHON_CMD=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
    goto :found_python
)

echo [ERROR] Python not found!
echo Please install Python from: https://www.python.org/downloads/
pause
exit /b 1

:found_python
echo [INFO] Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM ====== FIX CLAUDE PATH ======
echo [INFO] Fixing Claude CLI path...
%PYTHON_CMD% -c "import json,os; p=os.path.join(os.environ['APPDATA'],'npm','claude.cmd'); c=json.load(open('config.json','r',encoding='utf-8')); c['claude_code']['command']=p; json.dump(c,open('config.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)" 2>nul
echo [INFO] Done.
echo.

REM ====== CLEANUP ======
echo [INFO] Stopping Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo.

echo [INFO] Clearing temp files...
if exist "running_jobs.json" del /f "running_jobs.json" >nul 2>&1
if exist "full_auto_jobs.json" del /f "full_auto_jobs.json" >nul 2>&1
if exist "tmp" rmdir /s /q "tmp" >nul 2>&1
mkdir tmp >nul 2>&1
if exist "job_locks" rmdir /s /q "job_locks" >nul 2>&1
echo.

REM ====== CHECK FLASK ======
%PYTHON_CMD% -m pip show flask >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    %PYTHON_CMD% -m pip install -r requirements.txt
    echo.
)

REM ====== START ======
echo [INFO] Starting: http://localhost:5000
echo [INFO] Press Ctrl+C to stop
echo.

%PYTHON_CMD% dashboard_server.py

pause
