$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

$python = Join-Path $root ".venv\Scripts\python.exe"

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt -r requirements-build.txt
& $python -m unittest discover -s tests -v
& $python -m PyInstaller --clean --noconfirm OpenclaudeStudio.spec

$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (Test-Path $iscc) {
    & $iscc (Join-Path $root "installer\OpenclaudeStudio.iss")
}

Write-Host ""
Write-Host "Build complete:"
Write-Host "  $root\dist\OpenclaudeStudio.exe"
if (Test-Path "$root\dist\installer\OpenclaudeStudio-Setup.exe") {
    Write-Host "  $root\dist\installer\OpenclaudeStudio-Setup.exe"
}
