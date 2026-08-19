@echo off
set ACCOUNT=Aqobah International School
set PROFILE_DIR=%~dp0accounts\aqobah_international_school\profile_instagram

echo ====================================================================
echo Membuka Google Chrome untuk Login Instagram: %ACCOUNT%
echo Folder Sesi: %PROFILE_DIR%
echo ====================================================================

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="%PROFILE_DIR%" --no-first-run --no-default-browser-check "https://www.instagram.com/accounts/login/"

echo.
echo [OK] Jendela Google Chrome telah dibuka di layar Anda!
echo 1. Silakan login ke akun Instagram Anda di jendela Chrome tersebut.
echo 2. Setelah berhasil masuk ke beranda Instagram, Anda boleh menutup jendela ini.
echo ====================================================================
pause
