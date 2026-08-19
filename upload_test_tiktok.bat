@echo off
cd /d "%~dp0"
echo ====================================================================
echo MEMULAI UPLOAD TIKTOK DENGAN TIKTOK STUDIO SOUND EDITOR
echo Akun        : Aqobah International School
echo File        : sample_test.mp4
echo Sound Query : "school"
echo Volume      : -7 dB
echo Browser     : Full Screen Maximized
echo ====================================================================

python -m src.cli upload --account "Aqobah International School" --file "sample_test.mp4" --caption "Testing Upload Aqobah International School #school #education #fyp" --sound-query "school" --sound-db "-7" --platform tiktok

echo ====================================================================
pause
