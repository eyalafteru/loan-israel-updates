@echo off
chcp 65001 >nul
title Dashboard Setup
color 0A

echo.
echo  ============================================================
echo       PAGE MANAGEMENT DASHBOARD - ONE CLICK SETUP
echo  ============================================================
echo.
echo  This will:
echo    1. Install Python, Node.js, Git (if needed)
echo    2. Clone repository from GitHub
echo    3. Install all dependencies
echo    4. Configure Claude CLI
echo    5. Create desktop shortcut
echo    6. Launch the dashboard
echo.
echo  ============================================================
echo.
echo  Press any key to start or Ctrl+C to cancel...
pause >nul

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo  [!] Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Run PowerShell installer
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0setup_standalone.ps1"

echo.
echo  ============================================================
echo       Setup finished!
echo  ============================================================
echo.
pause
