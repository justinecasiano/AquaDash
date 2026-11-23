<#
.SYNOPSIS
Packages backend/src/*.py into dist/lambda-deploy.zip for direct AWS Lambda Console upload.
Uses Python zipfile so paths inside the archive use Linux-compatible forward slashes.
#>
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $RepoRoot "dist"
$ZipPath = Join-Path $DistDir "lambda-deploy.zip"
$SrcDir = Join-Path $RepoRoot "backend\src"

if (-not (Test-Path $DistDir)) {
    New-Item -ItemType Directory -Path $DistDir | Out-Null
}
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

python -c @"
import pathlib, zipfile

src = pathlib.Path(r'$SrcDir')
out = pathlib.Path(r'$ZipPath')
with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
    for file in sorted(src.rglob('*.py')):
        if '__pycache__' in file.parts:
            continue
        arcname = file.relative_to(src).as_posix()
        zf.write(file, arcname)
        print(f'  + {arcname}')
print(f'\nCreated: {out} ({out.stat().st_size / 1024:.1f} KB)')
"@

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Next step: Upload dist\lambda-deploy.zip in AWS Lambda Console -> umak-elec3-bcsad-g02-orders-api -> Code -> Upload from -> .zip file."
