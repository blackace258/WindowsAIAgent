# Windows AI Agent - Prerequisite Bootstrap Installer
# Run as Administrator for best results:
#   powershell -ExecutionPolicy Bypass -File scripts\install_prerequisites.ps1
#
# This script:
#   1. Checks for Python 3.9+
#   2. Attempts to install Python via winget if missing
#   3. Ensures pip is available
#   4. Installs all required packages from requirements.txt
#   5. Creates launcher scripts

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Windows AI Agent - Prerequisite Installer" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host ""

function Test-Python {
    $candidates = @("python", "python3", "py")
    foreach ($c in $candidates) {
        try {
            $ver = & $c --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $ver -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 9)) {
                    return @{ Ok = $true; Cmd = $c; Version = $ver.Trim() }
                }
            }
        } catch {}
    }
    return @{ Ok = $false; Cmd = $null; Version = $null }
}

# ---- 1. Python detection / install ----
Write-Host "[1/5] Checking for Python 3.9+ ..." -ForegroundColor Yellow
$py = Test-Python

if (-not $py.Ok) {
    Write-Host "  Python 3.9+ not found." -ForegroundColor Red
    Write-Host "  Attempting to install via winget ..." -ForegroundColor Yellow

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        try {
            winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements --silent
            Write-Host "  winget install finished. Refreshing PATH..." -ForegroundColor Green
            # Refresh PATH for current session
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                        [System.Environment]::GetEnvironmentVariable("Path", "User")
            $py = Test-Python
        } catch {
            Write-Host "  winget install failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  winget not available." -ForegroundColor Red
    }

    if (-not $py.Ok) {
        Write-Host ""
        Write-Host "  MANUAL ACTION REQUIRED:" -ForegroundColor Yellow
        Write-Host "  1. Download Python 3.9+ from https://www.python.org/downloads/"
        Write-Host "  2. Run the installer and CHECK 'Add python.exe to PATH'"
        Write-Host "  3. Re-open this terminal and run this script again"
        exit 1
    }
}

Write-Host "  Found: $($py.Version)  (command: $($py.Cmd))" -ForegroundColor Green
$PythonCmd = $py.Cmd

# ---- 2. Ensure pip ----
Write-Host ""
Write-Host "[2/5] Ensuring pip ..." -ForegroundColor Yellow
try {
    & $PythonCmd -m pip --version | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "pip missing" }
    Write-Host "  pip OK" -ForegroundColor Green
} catch {
    Write-Host "  Installing pip via ensurepip ..." -ForegroundColor Yellow
    & $PythonCmd -m ensurepip --upgrade
}

# ---- 3. Upgrade pip / setuptools / wheel ----
Write-Host ""
Write-Host "[3/5] Upgrading pip, setuptools, wheel ..." -ForegroundColor Yellow
& $PythonCmd -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Warning: pip upgrade returned non-zero. Continuing..." -ForegroundColor Yellow
}

# ---- 4. Install project requirements ----
Write-Host ""
Write-Host "[4/5] Installing project dependencies ..." -ForegroundColor Yellow
$req = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $req) {
    & $PythonCmd -m pip install --upgrade -r $req
} else {
    Write-Host "  requirements.txt missing – installing core packages" -ForegroundColor Yellow
    & $PythonCmd -m pip install --upgrade rich psutil requests python-dotenv pywin32 openai pyinstaller
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "  Package install failed. Try running this script as Administrator." -ForegroundColor Red
    exit 1
}
Write-Host "  Dependencies installed." -ForegroundColor Green

# ---- 5. Create launchers via Python installer module ----
Write-Host ""
Write-Host "[5/5] Creating launcher scripts ..." -ForegroundColor Yellow
& $PythonCmd -m src.installer
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Launcher creation had issues, but packages are installed." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SUCCESS – Prerequisites installed" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Next steps:"
Write-Host "  .\check_prereqs.bat     – verify environment"
Write-Host "  .\run_agent.bat         – start the AI agent"
Write-Host "  .\build_exe.bat         – (optional) build standalone EXE"
Write-Host ""
Write-Host "Optional LLM setup:"
Write-Host "  set OPENAI_API_KEY=sk-...   or configure Ollama"
Write-Host ""
