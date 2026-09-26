@echo off
chcp 65001 >nul
title Proses Upload Konten Pending
cls
echo ====================================================================
echo                 PROSES UPLOAD KONTEN PENDING (MULTI-AKUN)
echo ====================================================================
echo.
set "PY_EXE=C:\Users\spacdust\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"
"%PY_EXE%" -m src.cli content process
echo.
pause
