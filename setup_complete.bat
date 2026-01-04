@echo off
chcp 65001 >nul
title Page Management Dashboard - Complete Setup
color 0A

echo.
echo  ================================================================
echo       Page Management Dashboard - Complete Auto Setup
echo       מערכת ניהול אתרים - התקנה אוטומטית מלאה
echo  ================================================================
echo.
echo  This script will:
echo  הסקריפט הזה יעשה:
echo.
echo    1. Install Python, Node.js, Git (if needed)
echo       יתקין Python, Node.js, Git (אם חסרים)
echo.
echo    2. Clone the repository from GitHub
echo       ישכפל את המאגר מ-GitHub
echo.
echo    3. Install all dependencies
echo       יתקין את כל התלויות
echo.
echo    4. Configure Claude CLI
echo       יגדיר את Claude CLI
echo.
echo    5. Create desktop shortcut and launch
echo       ייצור קיצור דרך ויפעיל
echo.
echo  ================================================================
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

:: Run the PowerShell script embedded below
powershell -ExecutionPolicy Bypass -NoProfile -Command ^
"& {" ^
"" ^
"# ============================================" ^
"# COMPLETE AUTO INSTALLER - STANDALONE" ^
"# ============================================" ^
"" ^
"[Console]::OutputEncoding = [System.Text.Encoding]::UTF8" ^
"$OutputEncoding = [System.Text.Encoding]::UTF8" ^
"" ^
"# Configuration" ^
"$RepoUrl = 'https://github.com/eyal10/loan-israel-updates.git'" ^
"$DefaultInstallDir = 'C:\loan-dashboard'" ^
"" ^
"function Write-Step { param([string]$Msg); Write-Host \"`n[>] $Msg\" -ForegroundColor Magenta; Write-Host ('-' * 50) -ForegroundColor DarkGray }" ^
"function Write-OK { param([string]$Msg); Write-Host \"  [OK] $Msg\" -ForegroundColor Green }" ^
"function Write-Err { param([string]$Msg); Write-Host \"  [ERROR] $Msg\" -ForegroundColor Red }" ^
"function Write-Info { param([string]$Msg); Write-Host \"  [INFO] $Msg\" -ForegroundColor Cyan }" ^
"" ^
"function Test-Cmd { param([string]$Cmd); try { if (Get-Command $Cmd -ErrorAction Stop) { return $true } } catch { return $false } }" ^
"" ^
"function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') }" ^
"" ^
"Write-Host '' " ^
"Write-Host '  ============================================' -ForegroundColor Cyan" ^
"Write-Host '  Complete Auto Installer' -ForegroundColor Cyan" ^
"Write-Host '  התקנה אוטומטית מלאה' -ForegroundColor Cyan" ^
"Write-Host '  ============================================' -ForegroundColor Cyan" ^
"" ^
"# ====== STEP 1: Install Prerequisites ======" ^
"Write-Step 'Installing Prerequisites / מתקין דרישות מקדימות'" ^
"" ^
"$winget = Test-Cmd 'winget'" ^
"" ^
"# Python" ^
"if (-not (Test-Cmd 'python')) {" ^
"    Write-Info 'Installing Python...'" ^
"    if ($winget) { winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null }" ^
"    else {" ^
"        $url = 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe'" ^
"        $installer = \"$env:TEMP\\python_installer.exe\"" ^
"        Invoke-WebRequest -Uri $url -OutFile $installer" ^
"        Start-Process -Wait -FilePath $installer -ArgumentList '/quiet','PrependPath=1','InstallAllUsers=1'" ^
"        Remove-Item $installer -Force -ErrorAction SilentlyContinue" ^
"    }" ^
"    Refresh-Path; Start-Sleep 2" ^
"    if (Test-Cmd 'python') { Write-OK 'Python installed' } else { Write-Err 'Python install failed - restart may be needed' }" ^
"} else { Write-OK \"Python: $(python --version 2>&1)\" }" ^
"" ^
"# Node.js" ^
"if (-not (Test-Cmd 'node')) {" ^
"    Write-Info 'Installing Node.js...'" ^
"    if ($winget) { winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null }" ^
"    else {" ^
"        $url = 'https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi'" ^
"        $installer = \"$env:TEMP\\node_installer.msi\"" ^
"        Invoke-WebRequest -Uri $url -OutFile $installer" ^
"        Start-Process -Wait -FilePath 'msiexec.exe' -ArgumentList '/i',$installer,'/quiet','/norestart'" ^
"        Remove-Item $installer -Force -ErrorAction SilentlyContinue" ^
"    }" ^
"    Refresh-Path; Start-Sleep 2" ^
"    if (Test-Cmd 'node') { Write-OK 'Node.js installed' } else { Write-Err 'Node.js install failed - restart may be needed' }" ^
"} else { Write-OK \"Node.js: $(node --version 2>&1)\" }" ^
"" ^
"# Git" ^
"if (-not (Test-Cmd 'git')) {" ^
"    Write-Info 'Installing Git...'" ^
"    if ($winget) { winget install Git.Git --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null }" ^
"    else {" ^
"        $url = 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe'" ^
"        $installer = \"$env:TEMP\\git_installer.exe\"" ^
"        Invoke-WebRequest -Uri $url -OutFile $installer" ^
"        Start-Process -Wait -FilePath $installer -ArgumentList '/VERYSILENT','/NORESTART'" ^
"        Remove-Item $installer -Force -ErrorAction SilentlyContinue" ^
"    }" ^
"    Refresh-Path; Start-Sleep 2" ^
"    if (Test-Cmd 'git') { Write-OK 'Git installed' } else { Write-Err 'Git install failed - restart may be needed' }" ^
"} else { Write-OK \"Git: $((git --version 2>&1) -replace 'git version ','')\" }" ^
"" ^
"Refresh-Path" ^
"" ^
"# ====== STEP 2: Get Install Directory ======" ^
"Write-Step 'Installation Directory / תיקיית התקנה'" ^
"Write-Host \"  Default: $DefaultInstallDir\" -ForegroundColor Yellow" ^
"$installDir = Read-Host '  Press Enter for default or type path'" ^
"if ([string]::IsNullOrWhiteSpace($installDir)) { $installDir = $DefaultInstallDir }" ^
"" ^
"if (Test-Path $installDir) {" ^
"    Write-Info 'Directory exists. Backing up...'" ^
"    $backup = \"${installDir}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')\"" ^
"    Rename-Item -Path $installDir -NewName $backup" ^
"    Write-OK \"Backed up to: $backup\"" ^
"}" ^
"" ^
"# ====== STEP 3: Clone Repository ======" ^
"Write-Step 'Cloning from GitHub / משכפל מ-GitHub'" ^
"Write-Host \"  Repository: $RepoUrl\" -ForegroundColor Yellow" ^
"Write-Host '  (Press Enter to use default or paste different URL)' -ForegroundColor Gray" ^
"$customUrl = Read-Host '  '" ^
"if (-not [string]::IsNullOrWhiteSpace($customUrl)) { $RepoUrl = $customUrl }" ^
"" ^
"Write-Info \"Cloning: $RepoUrl\"" ^
"Write-Info \"To: $installDir\"" ^
"git clone $RepoUrl $installDir 2>&1 | ForEach-Object { Write-Host \"  $_\" -ForegroundColor Gray }" ^
"" ^
"if ($LASTEXITCODE -ne 0) {" ^
"    Write-Err 'Clone failed! Check URL and internet connection.'" ^
"    Read-Host 'Press Enter to exit'" ^
"    exit 1" ^
"}" ^
"Write-OK 'Repository cloned successfully!'" ^
"" ^
"Set-Location $installDir" ^
"" ^
"# ====== STEP 4: Install Python Packages ======" ^
"Write-Step 'Installing Python Packages / מתקין חבילות Python'" ^
"python -m pip install --upgrade pip --quiet 2>&1 | Out-Null" ^
"pip install -r requirements.txt --quiet 2>&1" ^
"Write-OK 'Python packages installed'" ^
"" ^
"# ====== STEP 5: Install Claude CLI ======" ^
"Write-Step 'Installing Claude CLI / מתקין Claude CLI'" ^
"npm install -g @anthropic-ai/claude-code 2>&1 | Out-Null" ^
"$claudePath = \"$env:APPDATA\\npm\\claude.cmd\"" ^
"if (Test-Path $claudePath) { Write-OK \"Claude CLI: $claudePath\" }" ^
"else { Write-Err 'Claude CLI path not found' }" ^
"" ^
"# ====== STEP 6: Update Config ======" ^
"Write-Step 'Updating Configuration / מעדכן הגדרות'" ^
"if (Test-Path 'config.json') {" ^
"    $config = Get-Content 'config.json' -Raw | ConvertFrom-Json" ^
"    $config.claude_code.command = $claudePath" ^
"    $config | ConvertTo-Json -Depth 10 | Set-Content 'config.json' -Encoding UTF8" ^
"    Write-OK 'config.json updated'" ^
"}" ^
"" ^
"# Set API key" ^
"if (Test-Path 'api_config.env') {" ^
"    $content = Get-Content 'api_config.env' -Raw" ^
"    $match = [regex]::Match($content, 'ANTHROPIC_API_KEY=(.+)')" ^
"    if ($match.Success) {" ^
"        $key = $match.Groups[1].Value.Trim()" ^
"        if ($key -and $key -ne 'your_api_key_here') {" ^
"            [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', $key, 'User')" ^
"            $env:ANTHROPIC_API_KEY = $key" ^
"            Write-OK 'API key configured'" ^
"        }" ^
"    }" ^
"}" ^
"" ^
"# ====== STEP 7: Create Folders ======" ^
"Write-Step 'Creating Folders / יוצר תיקיות'" ^
"New-Item -ItemType Directory -Force -Path 'tmp','logs','tmp\\job_locks' | Out-Null" ^
"Write-OK 'Folders created'" ^
"" ^
"# ====== STEP 8: Desktop Shortcut ======" ^
"Write-Step 'Creating Shortcut / יוצר קיצור דרך'" ^
"try {" ^
"    $shell = New-Object -ComObject WScript.Shell" ^
"    $shortcut = $shell.CreateShortcut(\"$env:USERPROFILE\\Desktop\\Dashboard.lnk\")" ^
"    $shortcut.TargetPath = \"$installDir\\start_dashboard.bat\"" ^
"    $shortcut.WorkingDirectory = $installDir" ^
"    $shortcut.Save()" ^
"    Write-OK 'Desktop shortcut created'" ^
"} catch { Write-Err 'Could not create shortcut' }" ^
"" ^
"# ====== COMPLETE ======" ^
"Write-Host '' " ^
"Write-Host '  ============================================' -ForegroundColor Green" ^
"Write-Host '  Installation Complete!' -ForegroundColor Green" ^
"Write-Host '  ההתקנה הושלמה!' -ForegroundColor Green" ^
"Write-Host '  ============================================' -ForegroundColor Green" ^
"Write-Host '' " ^
"Write-Host \"  Location: $installDir\" -ForegroundColor White" ^
"Write-Host '  URL: http://localhost:5000' -ForegroundColor White" ^
"Write-Host '' " ^
"" ^
"$launch = Read-Host '  Launch now? (y/n) [y]'" ^
"if ($launch -ne 'n') {" ^
"    Start-Process -FilePath \"$installDir\\start_dashboard.bat\" -WorkingDirectory $installDir" ^
"    Start-Sleep 3" ^
"    Start-Process 'http://localhost:5000'" ^
"}" ^
"" ^
"}"

echo.
echo  ================================================================
echo  Setup complete! / ההתקנה הושלמה!
echo  ================================================================
echo.
pause

