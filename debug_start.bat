@echo off
echo Step 1: Checking Python...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python and check "Add to PATH".
    pause
    exit /b
)
echo Python found.
pause

echo Step 2: Creating/Checking venv...
if not exist ".venv" (
    echo Creating .venv...
    python -m venv .venv
)
echo venv checked.
pause

echo Step 3: Installing dependencies...
.venv\Scripts\python.exe -m pip install Flask Flask-SQLAlchemy Flask-Login pandas openpyxl python-dateutil
echo Dependencies installed.
pause

echo Step 4: Starting Server...
start http://127.0.0.1:5000
.venv\Scripts\python.exe app.py
echo Server finished.
pause
