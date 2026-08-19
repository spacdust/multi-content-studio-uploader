@echo off
cd /d "%~dp0"
echo ====================================================================
echo MEMBUKA BROWSER VISUAL LOGIN TIKTOK
echo Akun: Aqobah International School
echo ====================================================================

python -m src.cli login --account "Aqobah International School" --platform tiktok

echo ====================================================================
pause
