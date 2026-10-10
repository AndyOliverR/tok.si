@echo off
cd /d "%~dp0"
echo ===================================================
echo             tok.si setup
echo ===================================================

where python >nul 2>&1
if errorlevel 1 (
    echo Installing Python...
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
)
where python >nul 2>&1
if errorlevel 1 goto fail
python -c "import sys" || goto fail

echo Installing libraries...
python -m pip install cffi sounddevice numpy PySide6 sherpa-onnx || goto fail
python -c "import sherpa_onnx, sounddevice, numpy, PySide6" || goto fail

echo Installing voices and the virtual cable...
python fetch_assets.py
if errorlevel 1 goto fail

echo Starting tok.si...
for /f "delims=" %%P in ('python -c "import pathlib,sys; print(pathlib.Path(sys.executable).with_name('pythonw.exe'))"') do set PYTHONW=%%P
if not exist "%PYTHONW%" set PYTHONW=python
start "" "%PYTHONW%" "%~dp0main.py"

echo ===================================================
echo  SETUP COMPLETE
echo  In your call app, set the microphone to
echo  CABLE Output (VB-Audio Virtual Cable).
echo  Leave the speaker on your headphones.
echo  Search tok.si in Windows to turn it off.
echo ===================================================
pause
exit /b 0

:fail
echo ===================================================
echo  SETUP DID NOT FINISH
echo  Read the message above, then run setup.bat again.
echo ===================================================
pause
exit /b 1
