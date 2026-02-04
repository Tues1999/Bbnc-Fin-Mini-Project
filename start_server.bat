@echo off
chcp 65001 >nul
setlocal
cd /d %~dp0

title Ban Bang Nam Chuet Financial System

echo.
echo ========================================================
echo   Starting Financial System Setup & Launcher
echo   (System is checking requirements...)
echo ========================================================
echo.

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo AND make sure to check "Add Python to PATH" during installation.
    echo.
    echo After installing Python, please run this file again.
    echo.
    pause
    exit /b
)

:: 2. Check/Create Virtual Environment
if not exist ".venv" (
    echo [INFO] Creating virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment found.
)

:: 3. Install Dependencies
echo [INFO] Checking and installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install Flask Flask-SQLAlchemy Flask-Login pandas openpyxl python-dateutil
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)
echo [OK] Dependencies ready.

:: 4. Start Server
echo.
echo ========================================================
echo   System is Ready! Starting Server...
echo ========================================================
echo.
echo Server running at: http://127.0.0.1:5000
echo (Browser should open automatically)
echo.
echo [NOTE] Do not close this window while using the system.
echo Press Ctrl+C to stop the server.
echo.

start http://127.0.0.1:5000
.venv\Scripts\python.exe app.py

pause
