@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Running DataLayer Agent...
echo Target folder: %~dp0
py "%~dp0run_agent.py" %*
if %errorlevel% neq 0 (
    echo.
    echo Error running script. Trying with python...
    python "%~dp0run_agent.py" %*
)
echo.
echo Done!
pause

