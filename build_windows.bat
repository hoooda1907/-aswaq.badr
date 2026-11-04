@echo off
REM بناء البرنامج محلياً على ويندوز (يحتاج Python 3.10+)
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name AswaqBadrHR --icon assets\icon.ico --add-data "assets;assets" main.py
mkdir dist\portable 2>nul
copy dist\AswaqBadrHR.exe dist\portable\ >nul
echo portable> dist\portable\portable.txt
echo.
echo تم! الملف: dist\AswaqBadrHR.exe  - والنسخة المحمولة: dist\portable
pause
