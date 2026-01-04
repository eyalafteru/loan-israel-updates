# PowerShell migration script
$ErrorActionPreference = "Stop"
$base = "C:\Users\eyal\loan-israel-updaets\loan-israel-updates"
Set-Location $base

# Create target folders
$mainPath = Join-Path $base "דפים לשינוי\main"
$businessPath = Join-Path $base "דפים לשינוי\business"

if (-not (Test-Path $mainPath)) {
    New-Item -Path $mainPath -ItemType Directory -Force | Out-Null
    Write-Host "Created: $mainPath"
}
if (-not (Test-Path $businessPath)) {
    New-Item -Path $businessPath -ItemType Directory -Force | Out-Null
    Write-Host "Created: $businessPath"
}

# Move folders
$sourcePath = Join-Path $base "דפים לשינוי"
$folders = Get-ChildItem -Path $sourcePath -Directory | Where-Object { $_.Name -notin @('main', 'business') }

$moved = 0
foreach ($folder in $folders) {
    $target = Join-Path $mainPath $folder.Name
    if (-not (Test-Path $target)) {
        Move-Item -Path $folder.FullName -Destination $target
        Write-Host "Moved: $($folder.Name)"
        $moved++
    }
}

Write-Host "Done! Moved $moved folders to main/"

