<#
.SYNOPSIS
Builds the Vue 3 static frontend pointing to your live AWS API Gateway Invoke URL.
.EXAMPLE
.\scripts\build-frontend.ps1 -ApiUrl "https://abc123.execute-api.ap-southeast-1.amazonaws.com"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$ApiUrl
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
$CleanUrl = $ApiUrl.TrimEnd("/")

Write-Host "Building AquaDash S3 frontend with VITE_API_BASE_URL=$CleanUrl ..."

Push-Location $FrontendDir
try {
    $env:VITE_API_BASE_URL = $CleanUrl
    if (-not (Test-Path "node_modules")) {
        npm install --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    npm run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Build complete! Output is in: frontend\dist\"
Write-Host "IMPORTANT for S3 Console upload:"
Write-Host "  1. Open S3 -> umak-elec3-bcsad-g02-frontend -> Objects -> Upload."
Write-Host "  2. Upload the CONTENTS inside frontend\dist\ (index.html via 'Add files' and assets\ via 'Add folder')."
Write-Host "  3. Do NOT upload the 'dist' folder itself - index.html must sit at the bucket root."
