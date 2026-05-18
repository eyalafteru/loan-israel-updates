# Weekly Scanner Script for Windows Task Scheduler
# Run weekly to scan all data sources and detect changes

# Set working directory
Set-Location -Path $PSScriptRoot

# Log file
$logFile = "logs\weekly_scan_$(Get-Date -Format 'yyyy-MM-dd').log"

# Create logs directory if not exists
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force
}

# Function to write log
function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "Starting weekly scan..."

# Check if Ollama is running
try {
    $ollamaCheck = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($ollamaCheck.StatusCode -eq 200) {
        Write-Log "Ollama is running"
        $useAI = $true
    } else {
        Write-Log "WARNING: Ollama not responding, running without AI"
        $useAI = $false
    }
} catch {
    Write-Log "WARNING: Ollama not available, running without AI analysis"
    $useAI = $false
}

# Run the scanner
try {
    if ($useAI) {
        Write-Log "Running full scan with AI analysis..."
        py -3 weekly_scanner.py --full-scan 2>&1 | Tee-Object -Append -FilePath $logFile
    } else {
        Write-Log "Running full scan without AI..."
        py -3 weekly_scanner.py --full-scan --no-ai 2>&1 | Tee-Object -Append -FilePath $logFile
    }
    
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0) {
        Write-Log "Scan completed successfully"
    } else {
        Write-Log "ERROR: Scan failed with exit code $exitCode"
    }
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
}

Write-Log "Weekly scan finished"

# Optional: Start Ollama if not running (uncomment if needed)
# Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
