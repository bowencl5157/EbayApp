# Import eBay App from Transport
# Run this on the destination computer after receiving the export

param(
    [string]$ZipPath = ".\ebay-app-export.zip",
    [string]$ExtractPath = ".\EbayApp",
    [string]$GitBundlePath = $null,
    [string]$GitCloneUrl = $null
)

Write-Host "=== eBay App Import Tool ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check if Docker is installed
Write-Host "Step 1: Checking prerequisites..." -ForegroundColor Yellow
$docker = Get-Command docker -ErrorAction SilentlyContinue
$dockerCompose = Get-Command docker-compose -ErrorAction SilentlyContinue

if (-not $docker) {
    Write-Error "Docker not found. Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
}
if (-not $dockerCompose) {
    # Try 'docker compose' (newer syntax)
    try {
        docker compose version 2>&1 | Out-Null
        Write-Host "Docker Compose (plugin) found." -ForegroundColor Green
    } catch {
        Write-Error "Docker Compose not found. Please install Docker Desktop."
        exit 1
    }
}
Write-Host "Docker is installed." -ForegroundColor Green

# 2. Determine source (zip, bundle, or clone URL)
$sourceType = $null

if ($GitCloneUrl) {
    $sourceType = "clone"
    Write-Host "Source: Git clone from $GitCloneUrl" -ForegroundColor Green
} elseif ($GitBundlePath -and (Test-Path $GitBundlePath)) {
    $sourceType = "bundle"
    Write-Host "Source: Git bundle at $GitBundlePath" -ForegroundColor Green
} elseif (Test-Path $ZipPath) {
    $sourceType = "zip"
    Write-Host "Source: Zip archive at $ZipPath" -ForegroundColor Green
} else {
    Write-Error "No source found. Provide -ZipPath, -GitBundlePath, or -GitCloneUrl"
    Write-Host ""
    Write-Host "Usage examples:" -ForegroundColor Cyan
    Write-Host '  .\import-from-transport.ps1 -ZipPath .\ebay-app-export.zip'
    Write-Host '  .\import-from-transport.ps1 -GitBundlePath .\ebay-app.bundle'
    Write-Host '  .\import-from-transport.ps1 -GitCloneUrl https://github.com/user/repo.git'
    exit 1
}

# 3. Create/extract to destination
Write-Host ""
Write-Host "Step 2: Preparing destination..." -ForegroundColor Yellow

if (Test-Path $ExtractPath) {
    $overwrite = Read-Host "Destination exists: $ExtractPath`nOverwrite? (y/n)"
    if ($overwrite -eq 'y') {
        Remove-Item -Recurse -Force $ExtractPath
    } else {
        Write-Host "Import cancelled."
        exit 0
    }
}

switch ($sourceType) {
    "zip" {
        Write-Host "Extracting zip to $ExtractPath..."
        Expand-Archive -Path $ZipPath -DestinationPath $ExtractPath -Force
        if (-not $?) {
            # Try manual extraction
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            [System.IO.Compression.ZipFile]::ExtractToDirectory((Resolve-Path $ZipPath).Path, (Resolve-Path $ExtractPath).Path)
        }
    }
    "bundle" {
        Write-Host "Cloning from git bundle..."
        git clone $GitBundlePath $ExtractPath
        if (-not $?) {
            Write-Error "Failed to clone from bundle. Ensure git is installed."
            exit 1
        }
        # Add origin if needed
        Set-Location $ExtractPath
        git remote add origin https://github.com/yourusername/ebay-app.git 2>$null
        Set-Location ..
    }
    "clone" {
        Write-Host "Cloning from remote..."
        git clone $GitCloneUrl $ExtractPath
        if (-not $?) {
            Write-Error "Failed to clone from remote. Check the URL and your network."
            exit 1
        }
    }
}

if (-not (Test-Path $ExtractPath)) {
    Write-Error "Failed to create destination directory"
    exit 1
}

Write-Host "Source extracted to: $ExtractPath" -ForegroundColor Green
Set-Location $ExtractPath

# 4. Create .env from template
Write-Host ""
Write-Host "Step 3: Setting up environment..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    if (Test-Path "env.example") {
        Copy-Item env.example .env
        Write-Host ".env created from env.example" -ForegroundColor Green
    } elseif (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host ".env created from .env.example" -ForegroundColor Green
    } else {
        Write-Warning "No env.example found. Creating basic .env..."
        $basicEnv = @"
# eBay API
EBAY_CLIENT_ID=
EBAY_CLIENT_SECRET=
EBAY_REDIRECT_URI=http://localhost:8000/oauth/callback
EBAY_MARKETPLACE_ID=EBAY_US

# Walmart API (optional)
WALMART_CLIENT_ID=
WALMART_CLIENT_SECRET=

# Database
DB_USER=ebayuser
DB_PASSWORD=ebaypass
DB_NAME=ebayapp
DATABASE_URL=postgresql://ebayuser:ebaypass@postgres:5432/ebayapp

# Redis
REDIS_URL=redis://redis:6379/0
"@
        Set-Content .env $basicEnv
    }
    
    Write-Host ""
    Write-Host "IMPORTANT: Edit .env with your real credentials before starting the app!" -ForegroundColor Red -BackgroundColor White
    Write-Host "Required: EBAY_CLIENT_ID and EBAY_CLIENT_SECRET" -ForegroundColor Yellow
    
    $openEnv = Read-Host "`nOpen .env in notepad now? (y/n)"
    if ($openEnv -eq 'y') {
        notepad .env
        Write-Host "Please save and close Notepad when done..."
        pause
    }
} else {
    Write-Host ".env already exists (using existing)" -ForegroundColor Green
}

# 5. Verify .env has required values
Write-Host ""
Write-Host "Step 4: Verifying credentials..." -ForegroundColor Yellow
$envContent = Get-Content .env -Raw
if ($envContent -match 'EBAY_CLIENT_ID=\s*$' -or $envContent -match 'EBAY_CLIENT_ID=your_') {
    Write-Warning "EBAY_CLIENT_ID appears to be empty or placeholder"
}
if ($envContent -match 'EBAY_CLIENT_SECRET=\s*$' -or $envContent -match 'EBAY_CLIENT_SECRET=your_') {
    Write-Warning "EBAY_CLIENT_SECRET appears to be empty or placeholder"
}

# 6. Start Docker services
Write-Host ""
Write-Host "Step 5: Starting Docker services..." -ForegroundColor Yellow

# Determine compose command
try {
    docker compose version 2>&1 | Out-Null
    $composeCmd = "docker compose"
} catch {
    $composeCmd = "docker-compose"
}

Write-Host "Using: $composeCmd"
Write-Host ""
Write-Host "Building and starting services (this may take a few minutes)..." -ForegroundColor Cyan

Invoke-Expression "$composeCmd up --build -d"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker compose failed. Check the error messages above."
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  - Ensure Docker Desktop is running"
    Write-Host "  - Check if port 8000 is available (change in docker-compose.yml if needed)"
    Write-Host "  - Run '$composeCmd logs' to see detailed errors"
    exit 1
}

# 7. Wait for health checks
Write-Host ""
Write-Host "Step 6: Waiting for services to be healthy..." -ForegroundColor Yellow
$maxWait = 60
$waited = 0
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    $status = docker compose ps --format json 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
    $healthy = $status | Where-Object { $_.Health -eq "healthy" -or $_.State -eq "running" }
    $total = $status.Count
    if ($healthy -and $healthy.Count -eq $total) {
        Write-Host "All services are running!" -ForegroundColor Green
        break
    }
    Write-Host "  Waiting... ($waited/$maxWait seconds)"
}

# 8. Final summary
Write-Host ""
Write-Host "=== IMPORT COMPLETE ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application URL: http://localhost:8000" -ForegroundColor Green -BackgroundColor Black
Write-Host ""
Write-Host "Docker services:" -ForegroundColor White
Invoke-Expression "$composeCmd ps"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Open http://localhost:8000 in your browser" -ForegroundColor White
Write-Host "  2. Click 'Connect eBay Account' to authorize" -ForegroundColor White
Write-Host "  3. Go to 'Account' tab to fetch your data" -ForegroundColor White
Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Yellow
Write-Host "  View logs: $composeCmd logs -f" -ForegroundColor Cyan
Write-Host "  Restart:   $composeCmd restart" -ForegroundColor Cyan
Write-Host "  Stop:      $composeCmd down" -ForegroundColor Cyan
Write-Host ""

# 9. Option to verify eBay OAuth setup
$checkOauth = Read-Host "Do you want to verify the eBay OAuth redirect URI now? (y/n)"
if ($checkOauth -eq 'y') {
    $redirectUri = $envContent | Select-String "EBAY_REDIRECT_URI=(.+)$" | ForEach-Object { $_.Matches.Groups[1].Value }
    Write-Host ""
    Write-Host "Your EBAY_REDIRECT_URI: $redirectUri" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verify this matches your eBay Developer Portal settings:" -ForegroundColor Yellow
    Write-Host "  1. Go to https://developer.ebay.com/" -ForegroundColor White
    Write-Host "  2. Navigate to Your Apps" -ForegroundColor White
    Write-Host "  3. Find your app" -ForegroundColor White
    Write-Host "  4. Ensure 'Your auth accepted URL' matches: $redirectUri" -ForegroundColor White
    Write-Host ""
    Write-Host "For local development, use: http://localhost:8000/oauth/callback" -ForegroundColor Cyan
    Write-Host "For external access, use Cloudflare tunnel and update both eBay and .env" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Setup complete! Happy selling! 🚀" -ForegroundColor Green
