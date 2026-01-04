@echo off
chcp 65001 >nul
title Import Test - 5 Pages Only
color 0E
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║           בדיקה: ייבוא 5 עמודים ראשונים                 ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
cd /d "%~dp0"
python import_business_pages.py --limit 5 --delay 2
echo.
echo ════════════════════════════════════════════════════════════
echo.
pause

