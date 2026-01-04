# -*- coding: utf-8 -*-
# Page Management Dashboard - Full Auto Installer
# מערכת ניהול אתרים - התקנה אוטומטית מלאה

# ============================================
# SECTION 1: Configuration and Helper Functions
# ============================================

# Set output encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Colors for output
$colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Step = "Magenta"
}

# Helper function: Write step message
function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "[$([char]0x25B6)] $Message" -ForegroundColor $colors.Step
    Write-Host ("-" * 50) -ForegroundColor DarkGray
}

# Helper function: Write success message
function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor $colors.Success
}

# Helper function: Write error message
function Write-Err {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor $colors.Error
}

# Helper function: Write info message
function Write-Info {
    param([string]$Message)
    Write-Host "  [INFO] $Message" -ForegroundColor $colors.Info
}

# Helper function: Test if command exists
function Test-Command {
    param([string]$Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $Command) { return $true }
    }
    catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
}

# Helper function: Refresh PATH environment variable
function Update-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + 
                [System.Environment]::GetEnvironmentVariable("Path", "User")
    Write-Info "PATH environment refreshed"
}

# Helper function: Download file with progress
function Download-File {
    param(
        [string]$Url,
        [string]$OutputPath
    )
    try {
        Write-Info "Downloading from $Url..."
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $OutputPath)
        Write-Success "Downloaded to $OutputPath"
        return $true
    }
    catch {
        Write-Err "Download failed: $_"
        return $false
    }
}

# ============================================
# SECTION 2: Prerequisites Check and Install
# ============================================

Write-Host ""
Write-Host "  ======================================================" -ForegroundColor Cyan
Write-Host "       Page Management Dashboard - Auto Installer" -ForegroundColor Cyan
Write-Host "       מערכת ניהול אתרים - התקנה אוטומטית" -ForegroundColor Cyan
Write-Host "  ======================================================" -ForegroundColor Cyan
Write-Host ""

Write-Step "Checking Prerequisites / בודק דרישות מקדימות"

# Check if winget is available
$wingetAvailable = Test-Command "winget"
if ($wingetAvailable) {
    Write-Success "winget is available - will use for installations"
} else {
    Write-Info "winget not available - will use direct downloads"
}

# --- Python Installation ---
Write-Info "Checking Python..."
$pythonInstalled = Test-Command "python"

if (-not $pythonInstalled) {
    Write-Info "Python not found. Installing..."
    
    if ($wingetAvailable) {
        Write-Info "Installing Python via winget..."
        winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
        
        if ($LASTEXITCODE -ne 0) {
            Write-Err "winget install failed. Trying direct download..."
            $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
            $pythonInstaller = "$env:TEMP\python_installer.exe"
            
            if (Download-File -Url $pythonUrl -OutputPath $pythonInstaller) {
                Write-Info "Running Python installer..."
                Start-Process -Wait -FilePath $pythonInstaller -ArgumentList "/quiet", "PrependPath=1", "InstallAllUsers=1"
                Remove-Item $pythonInstaller -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
        $pythonInstaller = "$env:TEMP\python_installer.exe"
        
        if (Download-File -Url $pythonUrl -OutputPath $pythonInstaller) {
            Write-Info "Running Python installer (silent mode)..."
            Start-Process -Wait -FilePath $pythonInstaller -ArgumentList "/quiet", "PrependPath=1", "InstallAllUsers=1"
            Remove-Item $pythonInstaller -Force -ErrorAction SilentlyContinue
        }
    }
    
    Update-Path
    Start-Sleep -Seconds 2
    
    if (Test-Command "python") {
        Write-Success "Python installed successfully"
    } else {
        Write-Err "Python installation may require a restart. Please restart and run again."
    }
} else {
    $pythonVersion = python --version 2>&1
    Write-Success "Python already installed: $pythonVersion"
}

# --- Node.js Installation ---
Write-Info "Checking Node.js..."
$nodeInstalled = Test-Command "node"

if (-not $nodeInstalled) {
    Write-Info "Node.js not found. Installing..."
    
    if ($wingetAvailable) {
        Write-Info "Installing Node.js via winget..."
        winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements
        
        if ($LASTEXITCODE -ne 0) {
            Write-Err "winget install failed. Trying direct download..."
            $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
            $nodeInstaller = "$env:TEMP\node_installer.msi"
            
            if (Download-File -Url $nodeUrl -OutputPath $nodeInstaller) {
                Write-Info "Running Node.js installer..."
                Start-Process -Wait -FilePath "msiexec.exe" -ArgumentList "/i", $nodeInstaller, "/quiet", "/norestart"
                Remove-Item $nodeInstaller -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
        $nodeInstaller = "$env:TEMP\node_installer.msi"
        
        if (Download-File -Url $nodeUrl -OutputPath $nodeInstaller) {
            Write-Info "Running Node.js installer (silent mode)..."
            Start-Process -Wait -FilePath "msiexec.exe" -ArgumentList "/i", $nodeInstaller, "/quiet", "/norestart"
            Remove-Item $nodeInstaller -Force -ErrorAction SilentlyContinue
        }
    }
    
    Update-Path
    Start-Sleep -Seconds 2
    
    if (Test-Command "node") {
        Write-Success "Node.js installed successfully"
    } else {
        Write-Err "Node.js installation may require a restart. Please restart and run again."
    }
} else {
    $nodeVersion = node --version 2>&1
    Write-Success "Node.js already installed: $nodeVersion"
}

# --- Git Installation ---
Write-Info "Checking Git..."
$gitInstalled = Test-Command "git"

if (-not $gitInstalled) {
    Write-Info "Git not found. Installing..."
    
    if ($wingetAvailable) {
        Write-Info "Installing Git via winget..."
        winget install Git.Git --silent --accept-package-agreements --accept-source-agreements
        
        if ($LASTEXITCODE -ne 0) {
            Write-Err "winget install failed. Trying direct download..."
            $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
            $gitInstaller = "$env:TEMP\git_installer.exe"
            
            if (Download-File -Url $gitUrl -OutputPath $gitInstaller) {
                Write-Info "Running Git installer..."
                Start-Process -Wait -FilePath $gitInstaller -ArgumentList "/VERYSILENT", "/NORESTART"
                Remove-Item $gitInstaller -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
        $gitInstaller = "$env:TEMP\git_installer.exe"
        
        if (Download-File -Url $gitUrl -OutputPath $gitInstaller) {
            Write-Info "Running Git installer (silent mode)..."
            Start-Process -Wait -FilePath $gitInstaller -ArgumentList "/VERYSILENT", "/NORESTART"
            Remove-Item $gitInstaller -Force -ErrorAction SilentlyContinue
        }
    }
    
    Update-Path
    Start-Sleep -Seconds 2
    
    if (Test-Command "git") {
        Write-Success "Git installed successfully"
    } else {
        Write-Err "Git installation may require a restart. Please restart and run again."
    }
} else {
    $gitVersion = git --version 2>&1
    Write-Success "Git already installed: $gitVersion"
}

# Final PATH refresh
Update-Path

# ============================================
# SECTION 3: Installation Directory Setup
# ============================================

Write-Step "Setting Up Installation Directory / הגדרת תיקיית ההתקנה"

$defaultDir = "C:\loan-dashboard"
Write-Host ""
Write-Host "  Enter installation directory" -ForegroundColor Yellow
Write-Host "  הזן תיקיית התקנה" -ForegroundColor Yellow
$installDir = Read-Host "  [$defaultDir]"

if ([string]::IsNullOrWhiteSpace($installDir)) {
    $installDir = $defaultDir
}

Write-Info "Installation directory: $installDir"

# Check if directory exists
if (Test-Path $installDir) {
    Write-Host ""
    Write-Host "  Directory already exists!" -ForegroundColor Yellow
    Write-Host "  התיקייה כבר קיימת!" -ForegroundColor Yellow
    $overwrite = Read-Host "  Overwrite? (y/n) [n]"
    
    if ($overwrite -eq "y") {
        Write-Info "Removing existing directory..."
        Remove-Item -Path $installDir -Recurse -Force
    } else {
        Write-Info "Creating backup of existing directory..."
        $backupDir = "${installDir}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Rename-Item -Path $installDir -NewName $backupDir
        Write-Success "Backed up to: $backupDir"
    }
}

# ============================================
# SECTION 4: Clone Repository from GitHub
# ============================================

Write-Step "Cloning Repository from GitHub / משכפל את המאגר מ-GitHub"

# Default repository URL - UPDATE THIS WITH YOUR ACTUAL REPO URL
$defaultRepoUrl = "https://github.com/eyal10/loan-israel-updates.git"

# Get the script's directory (where install.ps1 is located)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if we're running from the repository already (has all files)
$isFullRepo = (Test-Path (Join-Path $scriptDir "dashboard_server.py")) -and 
              (Test-Path (Join-Path $scriptDir "config.json")) -and
              (Test-Path (Join-Path $scriptDir "agents"))

if ($isFullRepo) {
    Write-Host ""
    Write-Host "  Found existing repository files." -ForegroundColor Yellow
    Write-Host "  נמצאו קבצי repository קיימים." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  [1] Clone fresh from GitHub (recommended)" -ForegroundColor Cyan
    Write-Host "      משוך גרסה חדשה מ-GitHub (מומלץ)" -ForegroundColor Cyan
    Write-Host "  [2] Copy local files" -ForegroundColor Cyan
    Write-Host "      העתק קבצים מקומיים" -ForegroundColor Cyan
    Write-Host ""
    $choice = Read-Host "  Choose option / בחר אפשרות [1]"
    
    if ($choice -eq "2") {
        Write-Info "Copying local files to $installDir..."
        
        # Create destination directory
        New-Item -ItemType Directory -Force -Path $installDir | Out-Null
        
        # Copy all files from script directory to install directory
        Copy-Item -Path "$scriptDir\*" -Destination $installDir -Recurse -Force -Exclude @("__pycache__", "*.pyc", "tmp", "logs", "*.log", "running_jobs.json", "full_auto_jobs.json")
        
        Write-Success "Files copied successfully"
    } else {
        # Clone from GitHub
        Write-Host ""
        Write-Host "  Enter GitHub repository URL" -ForegroundColor Yellow
        Write-Host "  הזן כתובת מאגר GitHub" -ForegroundColor Yellow
        $repoUrl = Read-Host "  [$defaultRepoUrl]"
        
        if ([string]::IsNullOrWhiteSpace($repoUrl)) {
            $repoUrl = $defaultRepoUrl
        }
        
        Write-Info "Cloning repository from: $repoUrl"
        git clone $repoUrl $installDir
        
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Git clone failed! Check the URL and try again."
            Write-Err "שכפול נכשל! בדוק את הכתובת ונסה שוב."
            exit 1
        }
        
        Write-Success "Repository cloned successfully"
    }
} else {
    # No local repo - must clone from GitHub
    Write-Host ""
    Write-Host "  ================================================" -ForegroundColor Cyan
    Write-Host "  Cloning from GitHub Repository" -ForegroundColor Cyan
    Write-Host "  משכפל מאגר מ-GitHub" -ForegroundColor Cyan
    Write-Host "  ================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Enter GitHub repository URL" -ForegroundColor Yellow
    Write-Host "  הזן כתובת מאגר GitHub" -ForegroundColor Yellow
    Write-Host ""
    $repoUrl = Read-Host "  [$defaultRepoUrl]"
    
    if ([string]::IsNullOrWhiteSpace($repoUrl)) {
        $repoUrl = $defaultRepoUrl
    }
    
    # Validate URL format
    if (-not ($repoUrl -match "^https?://.*\.git$|^git@.*\.git$")) {
        Write-Info "Adding .git suffix to URL..."
        if (-not $repoUrl.EndsWith(".git")) {
            $repoUrl = "$repoUrl.git"
        }
    }
    
    Write-Info "Cloning repository..."
    Write-Info "URL: $repoUrl"
    Write-Info "Destination: $installDir"
    Write-Host ""
    
    git clone $repoUrl $installDir 2>&1 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Git clone failed!"
        Write-Err "שכפול נכשל!"
        Write-Host ""
        Write-Host "  Possible issues / בעיות אפשריות:" -ForegroundColor Yellow
        Write-Host "  - Wrong URL / כתובת שגויה" -ForegroundColor Yellow
        Write-Host "  - Private repo needs authentication / מאגר פרטי דורש הזדהות" -ForegroundColor Yellow
        Write-Host "  - No internet connection / אין חיבור לאינטרנט" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  For private repos, use:" -ForegroundColor Cyan
        Write-Host "  git clone https://USERNAME:TOKEN@github.com/USER/REPO.git" -ForegroundColor Cyan
        Write-Host ""
        exit 1
    }
    
    Write-Success "Repository cloned successfully!"
    Write-Success "המאגר שוכפל בהצלחה!"
}

# Change to installation directory
Set-Location $installDir
Write-Info "Working directory: $(Get-Location)"

# ============================================
# SECTION 5: Install Python Packages
# ============================================

Write-Step "Installing Python Packages / מתקין חבילות Python"

# Upgrade pip first
Write-Info "Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Info "Installing packages from requirements.txt..."
    pip install -r requirements.txt --quiet
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python packages installed successfully"
    } else {
        Write-Err "Some packages may have failed. Continuing..."
    }
} else {
    Write-Err "requirements.txt not found!"
}

# Verify key packages
Write-Info "Verifying key packages..."
$packages = @("flask", "requests", "python-dotenv", "psutil", "pyperclip")
foreach ($pkg in $packages) {
    $result = pip show $pkg 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] $pkg" -ForegroundColor Green
    } else {
        Write-Host "    [!] $pkg - installing..." -ForegroundColor Yellow
        pip install $pkg --quiet
    }
}

# ============================================
# SECTION 6: Install Claude CLI
# ============================================

Write-Step "Installing Claude CLI / מתקין Claude CLI"

Write-Info "Installing @anthropic-ai/claude-code globally..."
npm install -g @anthropic-ai/claude-code 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Success "Claude CLI installed successfully"
} else {
    Write-Err "Claude CLI installation may have issues. Continuing..."
}

# Find claude.cmd path
$claudePath = Join-Path $env:APPDATA "npm\claude.cmd"

if (-not (Test-Path $claudePath)) {
    # Try to find it
    $claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
    if ($claudeCmd) {
        $claudePath = $claudeCmd.Source
    } else {
        # Try common locations
        $possiblePaths = @(
            "$env:APPDATA\npm\claude.cmd",
            "$env:ProgramFiles\nodejs\claude.cmd",
            "C:\Program Files\nodejs\claude.cmd"
        )
        foreach ($path in $possiblePaths) {
            if (Test-Path $path) {
                $claudePath = $path
                break
            }
        }
    }
}

if (Test-Path $claudePath) {
    Write-Success "Claude CLI found at: $claudePath"
} else {
    Write-Err "Claude CLI path not found. You may need to configure it manually."
    $claudePath = "$env:APPDATA\npm\claude.cmd"
}

# ============================================
# SECTION 7: Update Configuration
# ============================================

Write-Step "Updating Configuration / מעדכן הגדרות"

# Update config.json with claude path
$configPath = Join-Path $installDir "config.json"

if (Test-Path $configPath) {
    Write-Info "Updating config.json..."
    
    try {
        $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
        
        # Update claude_code command path
        if ($config.claude_code) {
            $config.claude_code.command = $claudePath
            Write-Success "Updated claude_code.command"
        }
        
        # Save updated config
        $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
        Write-Success "config.json updated"
    }
    catch {
        Write-Err "Failed to update config.json: $_"
    }
} else {
    Write-Err "config.json not found!"
}

# Set ANTHROPIC_API_KEY environment variable
$apiConfigPath = Join-Path $installDir "api_config.env"

if (Test-Path $apiConfigPath) {
    Write-Info "Setting up API key environment variable..."
    
    $apiContent = Get-Content $apiConfigPath -Raw
    $apiKeyMatch = [regex]::Match($apiContent, 'ANTHROPIC_API_KEY=(.+)')
    
    if ($apiKeyMatch.Success) {
        $apiKey = $apiKeyMatch.Groups[1].Value.Trim()
        
        if (-not [string]::IsNullOrEmpty($apiKey) -and $apiKey -ne "your_api_key_here") {
            [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $apiKey, "User")
            $env:ANTHROPIC_API_KEY = $apiKey
            Write-Success "ANTHROPIC_API_KEY set as user environment variable"
        } else {
            Write-Info "API key not configured in api_config.env"
        }
    }
} else {
    Write-Info "api_config.env not found - you'll need to configure API key manually"
}

# ============================================
# SECTION 8: Create Required Folders
# ============================================

Write-Step "Creating Required Folders / יוצר תיקיות נדרשות"

$foldersToCreate = @(
    "tmp",
    "logs",
    (Join-Path "tmp" "job_locks")
)

foreach ($folder in $foldersToCreate) {
    $folderPath = Join-Path $installDir $folder
    if (-not (Test-Path $folderPath)) {
        New-Item -ItemType Directory -Force -Path $folderPath | Out-Null
        Write-Host "    [+] Created: $folder" -ForegroundColor Green
    } else {
        Write-Host "    [=] Exists: $folder" -ForegroundColor Gray
    }
}

# ============================================
# SECTION 9: Create Desktop Shortcut
# ============================================

Write-Step "Creating Desktop Shortcut / יוצר קיצור דרך"

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $shortcutPath = Join-Path $env:USERPROFILE "Desktop\Dashboard - מערכת ניהול.lnk"
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = Join-Path $installDir "start_dashboard.bat"
    $Shortcut.WorkingDirectory = $installDir
    $Shortcut.IconLocation = "shell32.dll,21"
    $Shortcut.Description = "Page Management Dashboard - מערכת ניהול אתרים"
    $Shortcut.Save()
    
    Write-Success "Desktop shortcut created"
}
catch {
    Write-Err "Failed to create shortcut: $_"
}

# ============================================
# SECTION 10: Optional NLP Installation
# ============================================

Write-Step "Optional: Advanced NLP Installation / התקנת NLP מתקדם (אופציונלי)"

Write-Host ""
Write-Host "  The advanced NLP module enables Hebrew morphology analysis" -ForegroundColor Yellow
Write-Host "  for better keyword density detection." -ForegroundColor Yellow
Write-Host "  מודול NLP מתקדם מאפשר ניתוח מורפולוגי לעברית" -ForegroundColor Yellow
Write-Host ""
Write-Host "  This requires downloading ~2GB of models." -ForegroundColor Yellow
Write-Host "  זה דורש הורדה של כ-2GB של מודלים." -ForegroundColor Yellow
Write-Host ""

$installNLP = Read-Host "  Install advanced NLP? (y/n) [n]"

if ($installNLP -eq "y") {
    Write-Info "Installing PyTorch (CPU version)..."
    pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet
    
    Write-Info "Installing Trankit (Hebrew morphology)..."
    pip install trankit --quiet
    
    Write-Info "Installing Transformers (for DictaBERT)..."
    pip install transformers --quiet
    
    Write-Info "Downloading Hebrew models (this may take a while)..."
    python -c "print('Loading Trankit Hebrew model...'); from trankit import Pipeline; p = Pipeline('hebrew'); print('Trankit ready!')" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "NLP modules installed successfully"
    } else {
        Write-Err "Some NLP components may have failed. The dashboard will still work without them."
    }
} else {
    Write-Info "Skipping NLP installation. You can run install_nlp.bat later if needed."
}

# ============================================
# SECTION 11: Verification and Summary
# ============================================

Write-Step "Installation Complete! / ההתקנה הושלמה!"

Write-Host ""
Write-Host "  ======================================================" -ForegroundColor Green
Write-Host "       Installation Completed Successfully!" -ForegroundColor Green
Write-Host "       ההתקנה הושלמה בהצלחה!" -ForegroundColor Green
Write-Host "  ======================================================" -ForegroundColor Green
Write-Host ""

# Display installed components
Write-Host "  Installed Components / רכיבים שהותקנו:" -ForegroundColor Cyan
Write-Host ""

# Python
$pyVer = python --version 2>&1
Write-Host "    [OK] Python: $pyVer" -ForegroundColor Green

# Node.js
$nodeVer = node --version 2>&1
Write-Host "    [OK] Node.js: $nodeVer" -ForegroundColor Green

# Git
$gitVer = (git --version 2>&1) -replace "git version ", ""
Write-Host "    [OK] Git: $gitVer" -ForegroundColor Green

# Claude CLI
if (Test-Path $claudePath) {
    Write-Host "    [OK] Claude CLI: $claudePath" -ForegroundColor Green
} else {
    Write-Host "    [!] Claude CLI: Not verified" -ForegroundColor Yellow
}

# Python packages count
$pkgCount = (pip list 2>&1 | Measure-Object -Line).Lines - 2
Write-Host "    [OK] Python packages: $pkgCount installed" -ForegroundColor Green

Write-Host ""
Write-Host "  Installation Location / מיקום ההתקנה:" -ForegroundColor Cyan
Write-Host "    $installDir" -ForegroundColor White
Write-Host ""
Write-Host "  Desktop Shortcut / קיצור דרך:" -ForegroundColor Cyan
Write-Host "    Dashboard - מערכת ניהול.lnk" -ForegroundColor White
Write-Host ""
Write-Host "  Dashboard URL:" -ForegroundColor Cyan
Write-Host "    http://localhost:5000" -ForegroundColor White
Write-Host ""

# Ask to launch
Write-Host ""
$launch = Read-Host "  Launch dashboard now? / להפעיל את הדשבורד עכשיו? (y/n) [y]"

if ($launch -ne "n") {
    Write-Info "Launching dashboard..."
    Start-Process -FilePath (Join-Path $installDir "start_dashboard.bat") -WorkingDirectory $installDir
    Start-Sleep -Seconds 3
    Start-Process "http://localhost:5000"
    Write-Success "Dashboard launched! Opening browser..."
}

Write-Host ""
Write-Host "  ======================================================" -ForegroundColor Cyan
Write-Host "       Thank you for installing!" -ForegroundColor Cyan
Write-Host "       !תודה על ההתקנה" -ForegroundColor Cyan
Write-Host "  ======================================================" -ForegroundColor Cyan
Write-Host ""

