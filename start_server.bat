@echo off
chcp 65001 >nul
title ระบบการเงินโรงเรียนบ้านบางน้ำจืด

echo ========================================
echo   ระบบการเงินโรงเรียนบ้านบางน้ำจืด
echo ========================================
echo.

echo [1/4] กำลังตรวจสอบ Python...
python --version 2>NUL
if errorlevel 1 goto NoPython
echo      ✓ พบ Python

echo.
echo [2/4] กำลังตรวจสอบ Virtual Environment...
if not exist ".venv" (
    echo      กำลังสร้าง Virtual Environment ใหม่...
    python -m venv .venv
    if errorlevel 1 goto VenvFailed
)
echo      ✓ Virtual Environment พร้อมใช้งาน

echo.
echo [3/4] กำลังติดตั้ง/ตรวจสอบ Dependencies...
.venv\Scripts\python.exe -m pip install --quiet --upgrade pip >nul 2>&1
.venv\Scripts\python.exe -m pip install --quiet Flask Flask-SQLAlchemy Flask-Login pandas openpyxl python-dateutil Werkzeug
if errorlevel 1 goto InstallFailed
echo      ✓ Dependencies ติดตั้งเรียบร้อย

echo.
echo [4/4] กำลังเริ่มระบบ...
echo.
echo ========================================
echo   ระบบพร้อมใช้งานแล้ว!
echo   เปิดเบราว์เซอร์ไปที่: http://127.0.0.1:5000
echo   กด Ctrl+C เพื่อหยุดระบบ
echo ========================================
echo.

timeout /t 2 /nobreak >nul
start http://127.0.0.1:5000
.venv\Scripts\python.exe app.py

echo.
echo ระบบหยุดทำงานแล้ว กด Enter เพื่อปิด...
pause >nul
exit

:NoPython
echo.
echo ========================================
echo   [ERROR] ไม่พบ Python ในเครื่อง
echo ========================================
echo.
echo กรุณาติดตั้ง Python จาก:
echo   https://www.python.org/downloads/
echo.
echo *สำคัญ* ตอนติดตั้ง ต้องติ๊กเลือก:
echo   [x] Add Python to PATH
echo.
pause
exit

:VenvFailed
echo.
echo ========================================
echo   [ERROR] ไม่สามารถสร้าง Virtual Environment ได้
echo ========================================
echo กรุณาลองรันใหม่อีกครั้ง หรือติดต่อผู้ดูแลระบบ
echo.
pause
exit

:InstallFailed
echo.
echo ========================================
echo   [ERROR] ไม่สามารถติดตั้ง Dependencies ได้
echo ========================================
echo กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต
echo และลองรันใหม่อีกครั้ง
echo.
pause
exit
