@echo off
title Windows AI Agent - Prerequisite Check
cd /d "%~dp0"
python -m src.prereq_checker
pause
