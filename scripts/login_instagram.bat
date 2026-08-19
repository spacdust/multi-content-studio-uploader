@echo off
cd /d "%~dp0.."
set ACCOUNT=Demo Account
set /p USER_ACC="Masukkan Nama Akun target [tekan Enter untuk '%ACCOUNT%']: "
if not "%USER_ACC%"=="" set ACCOUNT=%USER_ACC%

echo ====================================================================
echo MEMBUKA BROWSER LOGIN INSTAGRAM WEB DIRECT
echo Akun: %ACCOUNT%
echo ====================================================================

python -m src.cli login --account "%ACCOUNT%" --platform instagram

echo ====================================================================
pause
