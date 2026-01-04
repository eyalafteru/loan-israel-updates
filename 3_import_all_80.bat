@echo off
chcp 65001 >nul
title Import ALL 80 Business Pages
color 0B
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║          ייבוא כל 80 עמודי העסקים מוורדפרס             ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo זה יקח כמה דקות... אל תסגור את החלון!
echo.
cd /d "%~dp0"
python import_business_pages.py --delay 1.5
echo.
echo ════════════════════════════════════════════════════════════
echo.
pause

