@echo off
cd /d "%~dp0"
title TraceBench Backend (Port 8000)

echo ========================================================
echo Starting TraceBench FastAPI Backend Server...
echo ========================================================

REM Find Python 3.11 or system python
set "PY_EXE=C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)

set "PYTHONPATH=."
"%PY_EXE%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

pause
