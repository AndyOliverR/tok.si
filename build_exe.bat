@echo off
cd /d "%~dp0"
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --windowed --name tok.si --onedir --collect-all sherpa_onnx --hidden-import cryptography --hidden-import cffi launcher.py
copy /Y main.py dist\tok.si\
copy /Y fetch_assets.py dist\tok.si\
copy /Y beta_worker.py dist\tok.si\
copy /Y setup.bat dist\tok.si\
copy /Y start.bat dist\tok.si\
copy /Y README.md dist\tok.si\
copy /Y toksi_update_key.pub dist\tok.si\
copy /Y release_manifest.json dist\tok.si\
copy /Y release_manifest.sig dist\tok.si\
echo The app folder is dist\tok.si\tok.si.exe
pause
