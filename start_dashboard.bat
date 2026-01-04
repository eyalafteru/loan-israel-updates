@echo off
chcp 65001 >nul
echo ========================================
echo    Page Management Dashboard
echo ========================================
echo.

REM ====== FIND PYTHON ======
set PYTHON_CMD=

REM Try python in PATH first
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :found_python
)

REM Try py launcher
where py >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    goto :found_python
)

REM Try common Python installation paths
set PYTHON_PATHS=^
C:\Python312\python.exe;^
C:\Python311\python.exe;^
C:\Python310\python.exe;^
C:\Python39\python.exe;^
%LOCALAPPDATA%\Programs\Python\Python312\python.exe;^
%LOCALAPPDATA%\Programs\Python\Python311\python.exe;^
%LOCALAPPDATA%\Programs\Python\Python310\python.exe;^
%LOCALAPPDATA%\Programs\Python\Python39\python.exe;^
%USERPROFILE%\AppData\Local\Programs\Python\Python312\python.exe;^
%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe;^
%USERPROFILE%\AppData\Local\Programs\Python\Python310\python.exe;^
%ProgramFiles%\Python312\python.exe;^
%ProgramFiles%\Python311\python.exe;^
%ProgramFiles(x86)%\Python312\python.exe

for %%p in (%PYTHON_PATHS%) do (
    if exist "%%p" (
        set PYTHON_CMD=%%p
        goto :found_python
    )
)

REM Python not found
echo [ERROR] Python not found!
echo.
echo Please install Python from: https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:found_python
echo [INFO] Found Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM ====== FIX CLAUDE PATH IN CONFIG ======
echo [INFO] Checking Claude CLI configuration...

set CLAUDE_PATH=%APPDATA%\npm\claude.cmd
if exist "%CLAUDE_PATH%" (
    echo [INFO] Found Claude CLI: %CLAUDE_PATH%
    
    REM Create PowerShell script to fix config.json
    echo $configPath = "%~dp0config.json" > "%TEMP%\fix_config.ps1"
    echo if (Test-Path $configPath) { >> "%TEMP%\fix_config.ps1"
    echo     $content = Get-Content $configPath -Raw -Encoding UTF8 >> "%TEMP%\fix_config.ps1"
    echo     $claudePath = "%CLAUDE_PATH%" -replace '\\', '\\\\' >> "%TEMP%\fix_config.ps1"
    echo     $content = $content -replace '"command":\s*"[^"]*"', "`"command`": `"$claudePath`"" >> "%TEMP%\fix_config.ps1"
    echo     $content ^| Set-Content $configPath -Encoding UTF8 -NoNewline >> "%TEMP%\fix_config.ps1"
    echo } >> "%TEMP%\fix_config.ps1"
    
    powershell -ExecutionPolicy Bypass -File "%TEMP%\fix_config.ps1" >nul 2>&1
    del "%TEMP%\fix_config.ps1" >nul 2>&1
    echo [INFO] Configuration updated.
) else (
    echo [WARNING] Claude CLI not found at: %CLAUDE_PATH%
    echo [INFO] Install with: npm install -g @anthropic-ai/claude-code
)
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

REM ====== CHECK/INSTALL REQUIREMENTS ======
%PYTHON_CMD% -m pip show flask >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    %PYTHON_CMD% -m pip install -r requirements.txt
    echo.
)

REM ====== START SERVER ======
echo [INFO] Starting server on http://localhost:5000
echo [INFO] Press Ctrl+C to stop
echo.

%PYTHON_CMD% dashboard_server.py

pause
