@echo off
title Ban Bang Nam Chuet Financial System

echo checking python...
python --version 2>NUL
if errorlevel 1 goto NoPython

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing dependencies...
.venv\Scripts\python.exe -m pip install Flask Flask-SQLAlchemy Flask-Login pandas openpyxl python-dateutil

echo Starting server...
start http://127.0.0.1:5000
.venv\Scripts\python.exe app.py

pause
exit

:NoPython
echo [ERROR] Python not found.
echo Please install Python from python.org and check "Add to PATH".
pause
exit
