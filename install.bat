@echo off
title Windows AI Agent - Installer
cd /d "%~dp0"
echo.
echo ============================================================
echo  Windows AI Agent - Installer
echo ============================================================
echo.
echo Prefer the full bootstrap (handles missing Python):
echo   powershell -ExecutionPolicy Bypass -File scripts\install_prerequisites.ps1
echo.
echo Running Python-based installer...
python -m src.installer %*
if errorlevel 1 (
    echo.
    echo Installation failed. Make sure Python 3.9+ is installed and in PATH.
    echo Or run the PowerShell bootstrap script above as Administrator.
    pause
    exit /b 1
)
pause
