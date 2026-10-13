# Windows AI Agent - PowerShell Installer
# Run: powershell -ExecutionPolicy Bypass -File scripts\install.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Windows AI Agent - PowerShell Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Host "Python not found. Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Make sure to check 'Add python.exe to PATH'." -ForegroundColor Yellow
    exit 1
}

$pyVersion = & python --version 2>&1
Write-Host "Found: $pyVersion" -ForegroundColor Green

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
& python -m pip install --upgrade pip
& python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")

if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed." -ForegroundColor Red
    exit 1
}

# Create launchers
Write-Host "`nCreating launcher scripts..." -ForegroundColor Yellow
& python -m src.installer

Write-Host "`n[SUCCESS] Installation finished." -ForegroundColor Green
Write-Host "Run:  .\run_agent.bat   or   python -m src.main"
Write-Host "Check: .\check_prereqs.bat"
