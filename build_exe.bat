@echo off
title Windows AI Agent - Build EXE
cd /d "%~dp0"
echo Building standalone EXE (this may take a few minutes)...
python -m src.installer --exe
pause
