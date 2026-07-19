@echo off
setlocal
echo.
echo ============================================
echo   Installing Pokkie v0.2 - AI Terminal Assistant
echo ============================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not in PATH.
        echo Please install Python 3.9+ from https://python.org
        pause
        exit /b 1
    )
    set "PY_CMD=python"
) else (
    set "PY_CMD=py -3"
)

%PY_CMD% --version >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python 3 is not available.
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [1/2] Installing or upgrading Pokkie...
%PY_CMD% -m pip install --upgrade pip >nul
%PY_CMD% -m pip install --upgrade --force-reinstall .

if errorlevel 1 (
    echo [ERROR] Installation failed.
    pause
    exit /b 1
)

echo.
echo [2/2] Done!
echo.
echo   Run pokkie by typing: pokkie
echo   If Groq says Access denied, open Pokkie and run: /doctor
echo.
pause
