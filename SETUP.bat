@echo off
chcp 65001 >nul
title Complete Dashboard Setup
color 0A

echo.
echo  ================================================================
echo       PAGE MANAGEMENT DASHBOARD - ONE CLICK SETUP
echo       מערכת ניהול אתרים - התקנה בלחיצה אחת
echo  ================================================================
echo.
echo  This will install everything and clone from GitHub.
echo  זה יתקין הכל וישכפל מ-GitHub.
echo.
echo  Press any key to continue or Ctrl+C to cancel...
echo  לחץ מקש כלשהו להמשך או Ctrl+C לביטול...
pause >nul

:: Check for admin and run PowerShell script
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0setup_standalone.ps1"

if %errorLevel% neq 0 (
    echo.
    echo  [!] If there was an error, try running as administrator.
    echo  [!] אם הייתה שגיאה, נסה להריץ כמנהל.
    echo.
)

pause

