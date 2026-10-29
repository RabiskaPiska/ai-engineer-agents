# Install the GraphQL Specialist Agent Pack on Windows (PowerShell).
# Idempotent: re-running creates the venv only if missing and re-syncs deps.
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RootDir

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Error "ERROR: neither 'python' nor 'py' found (need Python >= 3.10)."
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtualenv .venv ..."
    & $python.Source -m venv .venv
}

$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Error "ERROR: .venv\Scripts\python.exe not found after venv creation."
    exit 1
}

Write-Host "Installing dependencies ..."
& $VenvPython -m pip install --upgrade pip | Out-Null
& $VenvPython -m pip install -r (Join-Path $RootDir "INSTALLERS\requirements.txt")

Write-Host ""
Write-Host "Installed. Activate with:  .\.venv\Scripts\Activate.ps1"
Write-Host "Verify with:               .\.venv\Scripts\python.exe -m pytest tests\ -v"
