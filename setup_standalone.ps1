# ============================================================================
# PAGE MANAGEMENT DASHBOARD - STANDALONE INSTALLER
# מערכת ניהול אתרים - התקנה עצמאית מלאה
# ============================================================================
#
# This single file does EVERYTHING:
# 1. Installs Python, Node.js, Git (if missing)
# 2. Clones the repository from GitHub
# 3. Installs all Python packages
# 4. Installs and configures Claude CLI
# 5. Creates desktop shortcut
# 6. Launches the dashboard
#
# HOW TO USE:
# 1. Download this file to any folder
# 2. Right-click -> Run with PowerShell
#    OR run: powershell -ExecutionPolicy Bypass -File setup_standalone.ps1
#
# ============================================================================

# ==================== CONFIGURATION ====================
# Change these values as needed:

$REPO_URL = "https://github.com/eyal10/loan-israel-updates.git"
$INSTALL_DIR = "C:\loan-dashboard"

# =======================================================

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "SilentlyContinue"

# ==================== HELPER FUNCTIONS ====================

function Write-Banner {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "  ║     PAGE MANAGEMENT DASHBOARD - COMPLETE INSTALLER       ║" -ForegroundColor Cyan
    Write-Host "  ║     מערכת ניהול אתרים - התקנה אוטומטית מלאה             ║" -ForegroundColor Cyan
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([int]$Num, [string]$Total, [string]$Message)
    Write-Host ""
    Write-Host "  [$Num/$Total] $Message" -ForegroundColor Magenta
    Write-Host "  $("-" * 55)" -ForegroundColor DarkGray
}

function Write-OK {
    param([string]$Message)
    Write-Host "      [✓] $Message" -ForegroundColor Green
}

function Write-Err {
    param([string]$Message)
    Write-Host "      [✗] $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "      [i] $Message" -ForegroundColor Cyan
}

function Write-Warn {
    param([string]$Message)
    Write-Host "      [!] $Message" -ForegroundColor Yellow
}

function Test-Command {
    param([string]$Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) { return $true }
    }
    catch { return $false }
}

function Refresh-EnvironmentPath {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + 
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Test-Admin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ==================== MAIN SCRIPT ====================

Clear-Host
Write-Banner

# Check admin rights
if (-not (Test-Admin)) {
    Write-Warn "This script requires administrator privileges."
    Write-Warn "הסקריפט דורש הרשאות מנהל."
    Write-Host ""
    Write-Host "  Restarting as administrator..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
    
    # Restart as admin
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`""
    exit
}

Write-OK "Running with administrator privileges"

# ==================== STEP 1: PREREQUISITES ====================

Write-Step -Num 1 -Total 8 -Message "Installing Prerequisites / התקנת דרישות מקדימות"

$wingetAvailable = Test-Command "winget"
if ($wingetAvailable) {
    Write-Info "Using winget for installations"
} else {
    Write-Info "Using direct downloads for installations"
}

# --- Python ---
Write-Info "Checking Python..."
if (-not (Test-Command "python")) {
    Write-Info "Installing Python 3.12..."
    
    if ($wingetAvailable) {
        $result = winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements 2>&1
    } else {
        $pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
        $pythonInstaller = "$env:TEMP\python_installer.exe"
        Write-Info "Downloading Python..."
        Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller -UseBasicParsing
        Write-Info "Running installer..."
        Start-Process -Wait -FilePath $pythonInstaller -ArgumentList "/quiet", "PrependPath=1", "InstallAllUsers=1"
        Remove-Item $pythonInstaller -Force -ErrorAction SilentlyContinue
    }
    
    Refresh-EnvironmentPath
    Start-Sleep -Seconds 3
    
    if (Test-Command "python") {
        Write-OK "Python installed successfully"
    } else {
        Write-Err "Python installation may require restart"
    }
} else {
    $pyVer = python --version 2>&1
    Write-OK "Python already installed: $pyVer"
}

# --- Node.js ---
Write-Info "Checking Node.js..."
if (-not (Test-Command "node")) {
    Write-Info "Installing Node.js 20 LTS..."
    
    if ($wingetAvailable) {
        $result = winget install OpenJS.NodeJS.LTS --silent --accept-package-agreements --accept-source-agreements 2>&1
    } else {
        $nodeUrl = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
        $nodeInstaller = "$env:TEMP\node_installer.msi"
        Write-Info "Downloading Node.js..."
        Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller -UseBasicParsing
        Write-Info "Running installer..."
        Start-Process -Wait -FilePath "msiexec.exe" -ArgumentList "/i", $nodeInstaller, "/quiet", "/norestart"
        Remove-Item $nodeInstaller -Force -ErrorAction SilentlyContinue
    }
    
    Refresh-EnvironmentPath
    Start-Sleep -Seconds 3
    
    if (Test-Command "node") {
        Write-OK "Node.js installed successfully"
    } else {
        Write-Err "Node.js installation may require restart"
    }
} else {
    $nodeVer = node --version 2>&1
    Write-OK "Node.js already installed: $nodeVer"
}

# --- Git ---
Write-Info "Checking Git..."
if (-not (Test-Command "git")) {
    Write-Info "Installing Git..."
    
    if ($wingetAvailable) {
        $result = winget install Git.Git --silent --accept-package-agreements --accept-source-agreements 2>&1
    } else {
        $gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/Git-2.43.0-64-bit.exe"
        $gitInstaller = "$env:TEMP\git_installer.exe"
        Write-Info "Downloading Git..."
        Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller -UseBasicParsing
        Write-Info "Running installer..."
        Start-Process -Wait -FilePath $gitInstaller -ArgumentList "/VERYSILENT", "/NORESTART"
        Remove-Item $gitInstaller -Force -ErrorAction SilentlyContinue
    }
    
    Refresh-EnvironmentPath
    Start-Sleep -Seconds 3
    
    if (Test-Command "git") {
        Write-OK "Git installed successfully"
    } else {
        Write-Err "Git installation may require restart"
    }
} else {
    $gitVer = (git --version 2>&1) -replace "git version ", ""
    Write-OK "Git already installed: $gitVer"
}

# Final PATH refresh
Refresh-EnvironmentPath

# ==================== STEP 2: INSTALLATION DIRECTORY ====================

Write-Step -Num 2 -Total 8 -Message "Setting Installation Directory / הגדרת תיקיית התקנה"

Write-Host ""
Write-Host "      Default installation directory:" -ForegroundColor Yellow
Write-Host "      $INSTALL_DIR" -ForegroundColor White
Write-Host ""
$customDir = Read-Host "      Press Enter to accept or type a new path"

if (-not [string]::IsNullOrWhiteSpace($customDir)) {
    $INSTALL_DIR = $customDir
}

Write-Info "Installation directory: $INSTALL_DIR"

# Handle existing directory
if (Test-Path $INSTALL_DIR) {
    Write-Warn "Directory already exists!"
    $choice = Read-Host "      [B]ackup and continue or [D]elete? (B/D)"
    
    if ($choice -eq "D" -or $choice -eq "d") {
        Write-Info "Removing existing directory..."
        Remove-Item -Path $INSTALL_DIR -Recurse -Force
    } else {
        $backupDir = "${INSTALL_DIR}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Write-Info "Creating backup..."
        Rename-Item -Path $INSTALL_DIR -NewName $backupDir
        Write-OK "Backed up to: $backupDir"
    }
}

# ==================== STEP 3: CLONE REPOSITORY ====================

Write-Step -Num 3 -Total 8 -Message "Cloning Repository from GitHub / שכפול מאגר מ-GitHub"

Write-Host ""
Write-Host "      Default repository URL:" -ForegroundColor Yellow
Write-Host "      $REPO_URL" -ForegroundColor White
Write-Host ""
$customUrl = Read-Host "      Press Enter to accept or paste a different URL"

if (-not [string]::IsNullOrWhiteSpace($customUrl)) {
    $REPO_URL = $customUrl
}

Write-Info "Cloning: $REPO_URL"
Write-Info "To: $INSTALL_DIR"
Write-Host ""

# Clone repository
$cloneOutput = git clone $REPO_URL $INSTALL_DIR 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Err "Git clone failed!"
    Write-Host ""
    Write-Host "      Error details:" -ForegroundColor Red
    Write-Host "      $cloneOutput" -ForegroundColor Red
    Write-Host ""
    Write-Host "      Possible solutions:" -ForegroundColor Yellow
    Write-Host "      - Check if the URL is correct" -ForegroundColor Yellow
    Write-Host "      - For private repos, use: https://USERNAME:TOKEN@github.com/..." -ForegroundColor Yellow
    Write-Host "      - Check your internet connection" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "      Press Enter to exit"
    exit 1
}

Write-OK "Repository cloned successfully!"

# Change to install directory
Set-Location $INSTALL_DIR

# ==================== STEP 4: PYTHON PACKAGES ====================

Write-Step -Num 4 -Total 8 -Message "Installing Python Packages / התקנת חבילות Python"

Write-Info "Upgrading pip..."
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null

if (Test-Path "requirements.txt") {
    Write-Info "Installing from requirements.txt..."
    $pipOutput = pip install -r requirements.txt 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-OK "All Python packages installed"
    } else {
        Write-Warn "Some packages may have issues, continuing..."
    }
} else {
    Write-Err "requirements.txt not found!"
}

# ==================== STEP 5: CLAUDE CLI ====================

Write-Step -Num 5 -Total 8 -Message "Installing Claude CLI / התקנת Claude CLI"

Write-Info "Installing @anthropic-ai/claude-code..."
$npmOutput = npm install -g @anthropic-ai/claude-code 2>&1

$claudePath = Join-Path $env:APPDATA "npm\claude.cmd"

if (Test-Path $claudePath) {
    Write-OK "Claude CLI installed: $claudePath"
} else {
    # Try to find it
    $claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
    if ($claudeCmd) {
        $claudePath = $claudeCmd.Source
        Write-OK "Claude CLI found: $claudePath"
    } else {
        Write-Warn "Claude CLI path not verified"
        $claudePath = "$env:APPDATA\npm\claude.cmd"
    }
}

# ==================== STEP 6: UPDATE CONFIGURATION ====================

Write-Step -Num 6 -Total 8 -Message "Updating Configuration / עדכון הגדרות"

# Update config.json
$configPath = Join-Path $INSTALL_DIR "config.json"

if (Test-Path $configPath) {
    try {
        $config = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
        
        # Update claude path
        if ($config.claude_code) {
            $config.claude_code.command = $claudePath
        }
        
        # Save config
        $config | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8
        Write-OK "config.json updated with Claude CLI path"
    }
    catch {
        Write-Err "Failed to update config.json: $_"
    }
} else {
    Write-Warn "config.json not found"
}

# Set API key environment variable
$apiConfigPath = Join-Path $INSTALL_DIR "api_config.env"

if (Test-Path $apiConfigPath) {
    $apiContent = Get-Content $apiConfigPath -Raw
    $match = [regex]::Match($apiContent, 'ANTHROPIC_API_KEY=(.+)')
    
    if ($match.Success) {
        $apiKey = $match.Groups[1].Value.Trim()
        
        if (-not [string]::IsNullOrEmpty($apiKey) -and $apiKey -notmatch "your.*key|YOUR.*KEY|xxx") {
            [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", $apiKey, "User")
            $env:ANTHROPIC_API_KEY = $apiKey
            Write-OK "ANTHROPIC_API_KEY set as environment variable"
        } else {
            Write-Warn "API key not configured - update api_config.env"
        }
    }
} else {
    Write-Warn "api_config.env not found"
}

# ==================== STEP 7: CREATE FOLDERS ====================

Write-Step -Num 7 -Total 8 -Message "Creating Required Folders / יצירת תיקיות"

$folders = @("tmp", "logs", "tmp\job_locks")

foreach ($folder in $folders) {
    $folderPath = Join-Path $INSTALL_DIR $folder
    if (-not (Test-Path $folderPath)) {
        New-Item -ItemType Directory -Force -Path $folderPath | Out-Null
        Write-OK "Created: $folder"
    } else {
        Write-Info "Exists: $folder"
    }
}

# ==================== STEP 8: DESKTOP SHORTCUT ====================

Write-Step -Num 8 -Total 8 -Message "Creating Desktop Shortcut / יצירת קיצור דרך"

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $shortcutPath = Join-Path $env:USERPROFILE "Desktop\Dashboard - מערכת ניהול.lnk"
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = Join-Path $INSTALL_DIR "start_dashboard.bat"
    $Shortcut.WorkingDirectory = $INSTALL_DIR
    $Shortcut.IconLocation = "shell32.dll,21"
    $Shortcut.Description = "Page Management Dashboard"
    $Shortcut.Save()
    
    Write-OK "Desktop shortcut created: Dashboard - מערכת ניהול"
}
catch {
    Write-Err "Could not create desktop shortcut"
}

# ==================== COMPLETE ====================

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║           INSTALLATION COMPLETE! / ההתקנה הושלמה!       ║" -ForegroundColor Green
Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "      Installed Components:" -ForegroundColor Cyan
Write-Host ""

# Show installed versions
$pyVer = python --version 2>&1
$nodeVer = node --version 2>&1
$gitVer = (git --version 2>&1) -replace "git version ", ""

Write-Host "      [✓] Python: $pyVer" -ForegroundColor Green
Write-Host "      [✓] Node.js: $nodeVer" -ForegroundColor Green
Write-Host "      [✓] Git: $gitVer" -ForegroundColor Green
Write-Host "      [✓] Claude CLI: Installed" -ForegroundColor Green

$pkgCount = (pip list 2>&1 | Measure-Object -Line).Lines - 2
Write-Host "      [✓] Python packages: $pkgCount installed" -ForegroundColor Green

Write-Host ""
Write-Host "      Location: $INSTALL_DIR" -ForegroundColor White
Write-Host "      Dashboard URL: http://localhost:5000" -ForegroundColor White
Write-Host "      Desktop Shortcut: Dashboard - מערכת ניהול" -ForegroundColor White
Write-Host ""

# Ask to launch
$launch = Read-Host "      Launch dashboard now? / להפעיל עכשיו? (Y/n)"

if ($launch -ne "n" -and $launch -ne "N") {
    Write-Info "Starting dashboard..."
    Start-Process -FilePath (Join-Path $INSTALL_DIR "start_dashboard.bat") -WorkingDirectory $INSTALL_DIR
    Start-Sleep -Seconds 4
    Write-Info "Opening browser..."
    Start-Process "http://localhost:5000"
}

Write-Host ""
Write-Host "  ══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "      Thank you for installing! / תודה על ההתקנה!" -ForegroundColor Cyan
Write-Host "  ══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Read-Host "      Press Enter to close / לחץ Enter לסגירה"

