@echo off
chcp 65001 >nul
echo Running WordPress API Test...
echo.
python test_wp_fetch.py
echo.
pause




