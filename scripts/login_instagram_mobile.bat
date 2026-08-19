@echo off
cd /d "%~dp0.."
set ACCOUNT=Gus Kikin Official
set /p USER_ACC="Masukkan Nama Akun target [tekan Enter untuk '%ACCOUNT%']: "
if not "%USER_ACC%"=="" set ACCOUNT=%USER_ACC%

echo ====================================================================
echo LOGIN INSTAGRAM MOBILE PROTOCOL (Android API / Auto FB Share)
echo Akun: %ACCOUNT%
echo ====================================================================

python -m src.cli login --account "%ACCOUNT%" --platform instagram-mobile

echo ====================================================================
pause
