@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set ACCOUNT=Demo Account
set /p USER_ACC="Masukkan Nama Akun target [tekan Enter untuk '%ACCOUNT%']: "
if not "%USER_ACC%"=="" set ACCOUNT=%USER_ACC%

echo ====================================================================
echo MEMBUKA BROWSER VISUAL LOGIN TIKTOK
echo Akun: %ACCOUNT%
echo ====================================================================

set "PY_EXE=C:\Users\spacdust\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%PY_EXE%" set "PY_EXE=python"
"%PY_EXE%" -m src.cli login --account "%ACCOUNT%" --platform tiktok

echo ====================================================================
pause
