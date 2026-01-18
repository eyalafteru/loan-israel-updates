@echo off
REM Weekly Scanner - Quick Run Script
REM Run this manually or schedule with Windows Task Scheduler

cd /d "%~dp0"

echo ========================================
echo Weekly Source Scanner
echo ========================================
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Ollama is running - AI analysis enabled
    py -3 weekly_scanner.py --full-scan
) else (
    echo WARNING: Ollama not running - AI analysis disabled
    echo To enable AI: Run 'ollama serve' first
    echo.
    py -3 weekly_scanner.py --full-scan --no-ai
)

echo.
echo ========================================
echo Scan Complete!
echo ========================================
pause
