$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$python = Join-Path $root ".venv\Scripts\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt -r requirements-build.txt
& $python -m PyInstaller --clean --noconfirm OpenclaudeStudio.spec

Write-Host ""
Write-Host "Build complete:"
Write-Host "  $root\dist\OpenclaudeStudio.exe"
