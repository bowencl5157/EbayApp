# Start script for eBay Product Research Tool
# This script activates the virtual environment and starts the FastAPI server

# Change to the script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Starting eBay Product Research Tool..." -ForegroundColor Green
Write-Host "Activating virtual environment..." -ForegroundColor Yellow

# Activate virtual environment
& ".venv\Scripts\Activate.ps1"

$existingProcessIds = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique
if ($existingProcessIds) {
    Write-Host "Port 8000 is already in use. Stopping existing server process..." -ForegroundColor Yellow
    foreach ($processId in $existingProcessIds) {
        Stop-Process -Id $processId -Force
    }
    Start-Sleep -Seconds 1
}

Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
Write-Host "Server will be available at http://localhost:8000" -ForegroundColor Cyan
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Gray
Write-Host ""

# Start the FastAPI server
python main.py
