@echo off
title Smoky Velvet Studio GUI
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" gui.py %*
) else (
    python gui.py %*
)
