@echo off
chcp 65001 >nul
echo ========================================
echo   Installing Dependencies
echo ========================================
echo.

echo Installing trafilatura...
py -m pip install trafilatura

echo.
echo Installing lxml...
py -m pip install lxml

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
pause
