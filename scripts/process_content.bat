@echo off
chcp 65001 >nul
title Proses Upload Konten Pending
cls
echo ====================================================================
echo                 PROSES UPLOAD KONTEN PENDING (MULTI-AKUN)
echo ====================================================================
echo.
python -m src.cli content process
echo.
pause
