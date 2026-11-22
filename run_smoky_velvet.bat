@echo off
title Smoky Velvet Engine (URX Core75)
cd /d "%~dp0"

echo ========================================================
echo    SMOKY VELVET RGB ENGINE - WINDOWS RUNNER
echo ========================================================

if exist ".venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment .venv...
    ".venv\Scripts\python.exe" main.py %*
) else (
    echo [INFO] Using system Python...
    python main.py %*
)

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Smoky Velvet exited with error code %ERRORLEVEL%.
    pause
)
