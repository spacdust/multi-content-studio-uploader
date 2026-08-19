@echo off
chcp 65001 >nul
title Content Uploader Studio Dashboard
cls
echo ====================================================================
echo             🚀 MEMULAI CONTENT UPLOADER STUDIO DASHBOARD
echo ====================================================================
echo.
echo [1/2] Membuka server FastAPI di http://localhost:8000 ...
start "" http://localhost:8000
echo [2/2] Server aktif dengan auto-reload! Tekan Ctrl+C di terminal ini jika ingin menutup.
echo.
python -m uvicorn src.server:app --host 127.0.0.1 --port 8000 --reload
pause
