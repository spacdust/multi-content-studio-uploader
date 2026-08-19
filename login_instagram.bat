@echo off
cd /d "%~dp0"
set ACCOUNT=Demo Account
set /p USER_ACC="Masukkan Nama Akun target [tekan Enter untuk '%ACCOUNT%']: "
if not "%USER_ACC%"=="" set ACCOUNT=%USER_ACC%

echo ====================================================================
echo Membuka Browser Login Meta Business Suite / Instagram
echo Akun: %ACCOUNT%
echo ====================================================================

python -m src.cli login --account "%ACCOUNT%" --platform meta

echo ====================================================================
pause
