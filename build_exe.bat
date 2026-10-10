@echo off
cd /d "%~dp0"
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --windowed --name tok.si --onedir main.py
echo The app folder is dist\tok.si\tok.si.exe
pause
