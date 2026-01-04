@echo off
chcp 65001 >nul
title Migration - Move Pages to main/
color 0A
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║          העברת עמודים קיימים לתיקיית main              ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
cd /d "%~dp0"
python migrate_existing_to_main.py
echo.
echo ════════════════════════════════════════════════════════════
echo.
pause

