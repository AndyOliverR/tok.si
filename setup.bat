@echo off
echo ===================================================
echo             tok.si | Free Auto-Installer
echo ===================================================

:: 1. Verify Core Python Environment Components
echo Verifying system framework configurations...
pip install --upgrade pip
pip install cffi sounddevice numpy PySide6

:: 2. Download the free community edition virtual driver bundle
echo Fetching free system audio routing layers...
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://vb-audio.com' -OutFile 'vbcable.zip'"

:: 3. Extract the driver bundle files
echo Extracting packages...
powershell -Command "Expand-Archive -Path 'vbcable.zip' -DestinationPath 'vbcable_extracted' -Force"

:: 4. Silently install the device driver into the Windows system layer
echo Injecting native system audio bridge (requires admin window confirmation)...
if exist "%SystemRoot%\System32\choice.exe" (
    start /wait vbcable_extracted\VBCABLE_Setup_x64.exe /i
) else (
    start vbcable_extracted\VBCABLE_Setup_x64.exe
)

:: 5. Clean up the installer junk files to keep it raw and clean
echo Cleaning temporary data...
del vbcable.zip
rmdir /s /q vbcable_extracted

echo ===================================================
echo  SETUP COMPLETE! 
echo  1. Launch QUO, Slack, or Zoom.
echo  2. Go to Audio Settings and change your Mic to 'Cable Output'.
echo  3. Double-click 'start.bat' and start speaking!
echo ===================================================
pause
