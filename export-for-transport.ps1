# Export eBay App for Transport via Git
# Run this on the source computer before transporting

param(
    [string]$ExportPath = ".\ebay-app-export.zip",
    [switch]$PushToRemote = $false,
    [switch]$CreateBundle = $false
)

Write-Host "=== eBay App Export Tool ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check if we're in a git repo
$gitDir = git rev-parse --git-dir 2>$null
if (-not $gitDir) {
    Write-Error "Not a git repository. Please run from the EbayApp directory."
    exit 1
}

# 2. Check git status for uncommitted changes
Write-Host "Step 1: Checking git status..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "Uncommitted changes detected:" -ForegroundColor Yellow
    Write-Host $status
    $commit = Read-Host "Commit these changes before export? (y/n)"
    if ($commit -eq 'y') {
        $msg = Read-Host "Enter commit message"
        git add .
        git commit -m "$msg"
        Write-Host "Changes committed." -ForegroundColor Green
    } else {
        Write-Warning "Proceeding with uncommitted changes..."
    }
} else {
    Write-Host "Working directory clean." -ForegroundColor Green
}

# 3. Verify .env is in .gitignore
Write-Host ""
Write-Host "Step 2: Verifying .env is excluded from git..." -ForegroundColor Yellow
$gitignore = Get-Content .gitignore -ErrorAction SilentlyContinue
$envExcluded = $gitignore | Where-Object { $_ -match "^\.env$" -or $_ -match "\.env" }
if (-not $envExcluded) {
    Write-Warning ".env not found in .gitignore! Adding it..."
    Add-Content .gitignore "`n.env`n*.env"
    Write-Host ".env added to .gitignore. Please commit this change." -ForegroundColor Green
} else {
    Write-Host ".env is properly excluded from git." -ForegroundColor Green
}

# 4. Check for sensitive files
Write-Host ""
Write-Host "Step 3: Checking for sensitive files..." -ForegroundColor Yellow
$sensitivePatterns = @('.env', '*.env', '*.key', '*.pem', '*.p12', '*.pfx', 'secrets.*', 'credentials.*')
$foundSensitive = @()
foreach ($pattern in $sensitivePatterns) {
    $files = Get-ChildItem -Path . -Filter $pattern -Hidden -ErrorAction SilentlyContinue
    if ($files) {
        $foundSensitive += $files.Name
    }
}
if ($foundSensitive) {
    Write-Host "Sensitive files found (ensure these are in .gitignore):" -ForegroundColor Yellow
    $foundSensitive | ForEach-Object { Write-Host "  - $_" }
} else {
    Write-Host "No obvious sensitive files detected in working directory." -ForegroundColor Green
}

# 5. Push to remote if requested
if ($PushToRemote) {
    Write-Host ""
    Write-Host "Step 4: Pushing to remote..." -ForegroundColor Yellow
    $currentBranch = git branch --show-current
    try {
        git push origin $currentBranch
        Write-Host "Pushed to origin/$currentBranch" -ForegroundColor Green
    } catch {
        Write-Error "Failed to push to remote. Check your git remote configuration."
        Write-Host "Current remotes:"
        git remote -v
    }
}

# 6. Create git bundle (alternative to remote push)
if ($CreateBundle) {
    Write-Host ""
    Write-Host "Step 4: Creating git bundle..." -ForegroundColor Yellow
    $bundlePath = ".\ebay-app.bundle"
    git bundle create $bundlePath --all
    if (Test-Path $bundlePath) {
        Write-Host "Git bundle created: $bundlePath" -ForegroundColor Green
        Write-Host "Transfer this file with the zip to the new computer." -ForegroundColor Cyan
    }
}

# 7. Clean up before zipping
Write-Host ""
Write-Host "Step 5: Cleaning up unnecessary files..." -ForegroundColor Yellow
$itemsToExclude = @('__pycache__', '*.pyc', '.pytest_cache', '.venv', 'venv', 'postgres_data', 'redis_data', '*.db', '*.sqlite3', '.git', '.DS_Store', 'node_modules')
foreach ($item in $itemsToExclude) {
    $paths = Get-ChildItem -Path . -Filter $item -Recurse -Force -ErrorAction SilentlyContinue
    if ($paths) {
        Write-Host "  Found: $item (will be excluded from zip)"
    }
}

# 8. Create zip archive (excluding sensitive items)
Write-Host ""
Write-Host "Step 6: Creating zip archive..." -ForegroundColor Yellow

$itemsToZip = Get-ChildItem -Path . | Where-Object {
    $name = $_.Name
    # Exclude patterns
    -not ($name -match '^__pycache__$') -and
    -not ($name -match '^\.env$') -and
    -not ($name -match '^\.git$') -and
    -not ($name -match '^postgres_data$') -and
    -not ($name -match '^redis_data$') -and
    -not ($name -match '^\.venv$') -and
    -not ($name -match '^venv$') -and
    -not ($name -match '\.pyc$') -and
    -not ($name -match '\.db$') -and
    -not ($name -match '\.sqlite3$')
}

# Create temp directory for clean zip
$tempDir = "$(Get-Location)\_export_temp"
if (Test-Path $tempDir) { Remove-Item -Recurse -Force $tempDir }
New-Item -ItemType Directory -Path $tempDir | Out-Null

foreach ($item in $itemsToZip) {
    Copy-Item -Path $item.FullName -Destination $tempDir -Recurse -Force
}

# Create the zip
Compress-Archive -Path "$tempDir\*" -DestinationPath $ExportPath -Force
Remove-Item -Recurse -Force $tempDir

if (Test-Path $ExportPath) {
    $size = (Get-Item $ExportPath).Length / 1MB
    Write-Host "Export complete: $ExportPath ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
} else {
    Write-Error "Failed to create zip file"
    exit 1
}

# 9. Generate credentials template for secure transfer
$credTemplatePath = ".\CREDENTIALS-NEEDED.txt"
$credContent = @"
eBay App - Credentials Needed
================================

Copy this file to the new computer and fill in real values in .env

REQUIRED:
---------
EBAY_CLIENT_ID=
EBAY_CLIENT_SECRET=

OPTIONAL (Walmart):
-------------------
WALMART_CLIENT_ID=
WALMART_CLIENT_SECRET=

DATABASE (defaults work for local Docker):
-------------------------------------------
DB_USER=ebayuser
DB_PASSWORD=ebaypass
DB_NAME=ebayapp

NOTES:
------
- EBAY_REDIRECT_URI must match your eBay Developer Portal settings
- Use http://localhost:8000/oauth/callback for local development
- Use https://your-tunnel.trycloudflare.com/oauth/callback if using Cloudflare tunnel

After filling credentials:
1. Run: docker compose up --build
2. Open: http://localhost:8000
3. Click "Connect eBay Account"
"@

Set-Content -Path $credTemplatePath -Value $credContent
Write-Host ""
Write-Host "Credentials template created: $credTemplatePath" -ForegroundColor Cyan

# 10. Summary
Write-Host ""
Write-Host "=== EXPORT SUMMARY ===" -ForegroundColor Cyan
Write-Host "Files created:" -ForegroundColor White
Write-Host "  - $ExportPath (main app)" -ForegroundColor Green
if (Test-Path ".\ebay-app.bundle") {
    Write-Host "  - ebay-app.bundle (git bundle)" -ForegroundColor Green
}
Write-Host "  - $credTemplatePath (credentials guide)" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Securely transfer these files to the new computer" -ForegroundColor Yellow
Write-Host "  2. DO NOT email .env or real credentials together with the zip" -ForegroundColor Red
Write-Host "  3. On new computer, run: import-from-transport.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "If using git remote:" -ForegroundColor White
$remoteUrl = git remote get-url origin 2>$null
if ($remoteUrl) {
    Write-Host "  Repository URL: $remoteUrl" -ForegroundColor Cyan
    Write-Host "  On new computer: git clone $remoteUrl" -ForegroundColor Cyan
}
