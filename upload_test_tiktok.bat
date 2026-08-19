@echo off
cd /d "%~dp0"
set ACCOUNT=Demo Account
set /p USER_ACC="Masukkan Nama Akun target [tekan Enter untuk '%ACCOUNT%']: "
if not "%USER_ACC%"=="" set ACCOUNT=%USER_ACC%

echo ====================================================================
echo MEMULAI UPLOAD TIKTOK STUDIO
echo Akun: %ACCOUNT%
echo ====================================================================

python -m src.cli content process --account "%ACCOUNT%" --platform tiktok

echo ====================================================================
pause
