@echo off
chcp 65001 >nul
title Manajemen Konten Multi-Akun
cls
echo ====================================================================
echo                 STATUS & MANAJEMEN KONTEN PER AKUN
echo ====================================================================
echo.
python -m src.cli content list
echo.
pause
