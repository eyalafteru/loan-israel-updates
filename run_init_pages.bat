@echo off
chcp 65001 >nul
echo ========================================
echo    Page Info Generator
echo ========================================
echo.
cd /d "%~dp0"
python init_page_info.py
echo.
echo ========================================
pause




