@echo off
chcp 65001 >nul
title Content Uploader Studio Dashboard
cls
echo ====================================================================
echo             MEMULAI CONTENT UPLOADER STUDIO DASHBOARD
echo ====================================================================
echo.
echo [1/2] Membuka server FastAPI di http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000
echo [2/2] Server aktif dengan auto-reload! Tekan Ctrl+C di terminal ini jika ingin menutup.
echo.

set "PY_EXE=C:\Users\spacdust\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)

"%PY_EXE%" -m uvicorn src.server:app --host 127.0.0.1 --port 8000 --reload
pause
