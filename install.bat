@echo off
chcp 65001 >nul
title Page Management Dashboard - Installer
color 0A

echo.
echo  ========================================================
echo       Page Management Dashboard - Installer
echo       מערכת ניהול אתרים - התקנה אוטומטית
echo  ========================================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Requesting administrator privileges...
    echo [!] מבקש הרשאות מנהל...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [OK] Running with administrator privileges
echo.

:: Check if PowerShell is available
where powershell >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] PowerShell not found!
    echo [ERROR] Please install PowerShell first.
    pause
    exit /b 1
)

:: Run PowerShell installer with bypass execution policy
echo [INFO] Starting PowerShell installer...
echo.
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0install.ps1"

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Installation failed with error code %errorLevel%
    echo [ERROR] ההתקנה נכשלה
    pause
    exit /b %errorLevel%
)

echo.
echo [SUCCESS] Installation completed!
echo [SUCCESS] ההתקנה הושלמה בהצלחה!
echo.
pause

