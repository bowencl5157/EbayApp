param(
    [string]$AppTokenPath = "appToken.txt",
    [string]$EnvPath = ".env"
)

$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appTokenFile = Join-Path $ScriptRoot $AppTokenPath
$envFile = Join-Path $ScriptRoot $EnvPath

if (-not (Test-Path $appTokenFile)) {
    Write-Error "Could not find app token file: $appTokenFile"
}

$tokenContent = Get-Content -Path $appTokenFile -Raw

$bearerToken = $null
$marketplaceId = $null
$endUserCtx = $null
$clientId = $null
$clientSecret = $null

if ($tokenContent -match '(?im)^\s*Authorization\s*:\s*Bearer\s+(.+)\s*$') {
    $bearerToken = $Matches[1].Trim()
} elseif ($tokenContent -match '(?im)^\s*Bearer\s+(.+)\s*$') {
    $bearerToken = $Matches[1].Trim()
} elseif ($tokenContent -match '(v\^1\.1#[^\r\n\s]+)') {
    $bearerToken = $Matches[1].Trim()
}

if ($tokenContent -match '(?im)^\s*X-EBAY-C-MARKETPLACE-ID\s*:\s*(.+)\s*$') {
    $marketplaceId = $Matches[1].Trim()
}

if ($tokenContent -match '(?im)^\s*X-EBAY-C-ENDUSERCTX\s*:\s*(.+)\s*$') {
    $endUserCtx = $Matches[1].Trim()
}

if ($tokenContent -match '(?im)^\s*Client ID\s*:\s*(.+)\s*$') {
    $clientId = $Matches[1].Trim()
}

if ($tokenContent -match '(?im)^\s*Client Secret\s*:\s*(.+)\s*$') {
    $clientSecret = $Matches[1].Trim()
}

if (-not $bearerToken) {
    Write-Error "Could not extract a Bearer token from $appTokenFile"
}

$envLines = @()
if (Test-Path $envFile) {
    $envLines = @(Get-Content -Path $envFile)
}

$updates = [ordered]@{
    "EBAY_APP_TOKEN" = $bearerToken
    "EBAY_ACCESS_TOKEN" = $bearerToken
}

if ($marketplaceId) {
    $updates["EBAY_MARKETPLACE_ID"] = $marketplaceId
}

if ($endUserCtx -and $endUserCtx -notmatch '<[^>]+>') {
    $updates["EBAY_ENDUSERCTX"] = $endUserCtx
}

if ($clientId) {
    $updates["EBAY_CLIENT_ID"] = $clientId
}

if ($clientSecret) {
    $updates["EBAY_CLIENT_SECRET"] = $clientSecret
}

foreach ($key in $updates.Keys) {
    $value = $updates[$key]
    $found = $false

    for ($i = 0; $i -lt $envLines.Count; $i++) {
        if ($envLines[$i] -match "^\s*$([regex]::Escape($key))\s*=") {
            $envLines[$i] = "$key=$value"
            $found = $true
            break
        }
    }

    if (-not $found) {
        $envLines += "$key=$value"
    }
}

$envLines = @($envLines | Where-Object {
    $_ -notmatch '^\s*Authorization\s*:' -and
    $_ -notmatch '^\s*X-EBAY-C-MARKETPLACE-ID\s*:' -and
    $_ -notmatch '^\s*X-EBAY-C-ENDUSERCTX\s*:' -and
    $_ -notmatch '^\s*Client ID\s*:' -and
    $_ -notmatch '^\s*Client Secret\s*:'
})

Set-Content -Path $envFile -Value $envLines -Encoding UTF8

Write-Host "Updated $envFile from $appTokenFile"
Write-Host "Updated EBAY_APP_TOKEN and EBAY_ACCESS_TOKEN"
if ($marketplaceId) {
    Write-Host "Updated EBAY_MARKETPLACE_ID=$marketplaceId"
}
if ($clientId) {
    Write-Host "Updated EBAY_CLIENT_ID"
}
if ($clientSecret) {
    Write-Host "Updated EBAY_CLIENT_SECRET"
}
if ($endUserCtx -and $endUserCtx -match '<[^>]+>') {
    Write-Host "Skipped EBAY_ENDUSERCTX because appToken.txt contains placeholder values"
}
