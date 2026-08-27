# Build a clean .zip package for private macOS distribution
# Run this on Windows to create EbayApp-mac.zip

param(
    [string]$OutputPath = ".\EbayApp-mac.zip",
    [switch]$IncludeEnvTemplate = $true
)

Write-Host "=== Building eBay App macOS Distribution Package ===" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Items to exclude from zip
$exclusions = @(
    '.env',
    '.git',
    '__pycache__',
    '*.pyc',
    '.pytest_cache',
    '.venv',
    'venv',
    'postgres_data',
    'redis_data',
    '*.db',
    '*.sqlite3',
    '.DS_Store',
    'node_modules',
    '.ipynb_checkpoints',
    'csv',
    'pic',
    'Untitled*.ipynb',
    'EbayApp-mac.zip',
    'ebay-app-export.zip',
    'ebay-app.bundle'
)

Write-Host "Step 1: Verifying .env is excluded..." -ForegroundColor Yellow
$envFile = Get-ChildItem -Path . -Filter '.env' -Hidden -ErrorAction SilentlyContinue
if ($envFile) {
    Write-Warning ".env file found in source directory. It will NOT be included in the zip."
} else {
    Write-Host ".env file not found - good." -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 2: Creating temporary build directory..." -ForegroundColor Yellow
$tempDir = "$(Get-Location)\_mac_build_temp"
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
New-Item -ItemType Directory -Path $tempDir | Out-Null

# Copy all files except exclusions
$items = Get-ChildItem -Path . | Where-Object {
    $name = $_.Name
    $include = $true
    foreach ($ex in $exclusions) {
        if ($name -like $ex -or $name -match [regex]::Escape($ex) + '$') {
            $include = $false
            break
        }
    }
    if ($name -eq '_mac_build_temp') { $include = $false }
    $include
}

foreach ($item in $items) {
    Copy-Item -Path $item.FullName -Destination $tempDir -Recurse -Force
}

Write-Host "Step 3: Creating env template for recipient..." -ForegroundColor Yellow
if ($IncludeEnvTemplate) {
    $envTemplate = @"
# eBay API Credentials (required)
EBAY_CLIENT_ID=your_ebay_client_id
EBAY_CLIENT_SECRET=your_ebay_client_secret
EBAY_REDIRECT_URI=http://localhost:8000/oauth/callback
EBAY_MARKETPLACE_ID=EBAY_US

# Walmart API Credentials (optional)
WALMART_CLIENT_ID=your_walmart_client_id
WALMART_CLIENT_SECRET=your_walmart_client_secret
WALMART_CONSUMER_ID=your_walmart_consumer_id
WALMART_PRIVATE_KEY_FILE=walmartKeyGen/walmart_key

# Database (defaults work for local dev)
DB_USER=ebayuser
DB_PASSWORD=ebaypass
DB_NAME=ebayapp
DATABASE_URL=postgresql://ebayuser:ebaypass@postgres:5432/ebayapp

# Redis (defaults work for local dev)
REDIS_URL=redis://redis:6379/0
"@
    Set-Content -Path "$tempDir\env.example" -Value $envTemplate
    Write-Host "env.example created." -ForegroundColor Green
}

Write-Host ""
Write-Host "Step 4: Creating Mac setup instructions..." -ForegroundColor Yellow
$macReadme = @"
# eBay Product Research Tool - macOS Setup

## Requirements

1. Python 3.10 or 3.11 installed
2. pip
3. PostgreSQL running locally OR Docker Desktop
4. Redis running locally OR Docker Desktop

## Quick Start (with Docker Desktop)

1. Install and start Docker Desktop
2. Open Terminal in this folder
3. Run: docker compose up -d
4. Run: ./start.sh
5. Open browser to http://localhost:8000

## Quick Start (without Docker)

1. Install PostgreSQL and Redis on your Mac (e.g., via Homebrew)
2. Create a virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate
3. Install dependencies:
   pip install -r requirements.txt
4. Copy env.example to .env and fill in credentials
5. Run: ./start.sh

## Using start.command

You can double-click start.command to start the app in a new Terminal window.
You may need to run this first to make it executable:
  chmod +x start.command

## Notes

- The .env file was not included in this package for security.
- You must create your own .env from env.example.
- For eBay OAuth, update the redirect URI in both .env and the eBay Developer Portal.
"@
Set-Content -Path "$tempDir\README-MAC.md" -Value $macReadme
Write-Host "README-MAC.md created." -ForegroundColor Green

Write-Host ""
Write-Host "Step 5: Building zip archive..." -ForegroundColor Yellow
if (Test-Path $OutputPath) {
    Remove-Item -Force $OutputPath
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $OutputPath -Force

# Clean up temp directory
Remove-Item -Recurse -Force $tempDir

if (Test-Path $OutputPath) {
    $size = (Get-Item $OutputPath).Length / 1MB
    Write-Host ""
    Write-Host "=== BUILD COMPLETE ===" -ForegroundColor Cyan
    Write-Host "Package: $OutputPath" -ForegroundColor Green
    Write-Host "Size: $([math]::Round($size, 2)) MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "Send this zip privately. Do not include .env." -ForegroundColor Yellow
} else {
    Write-Error "Failed to create zip package"
    exit 1
}
