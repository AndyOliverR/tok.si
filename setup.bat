@echo off
echo ===================================================
echo             tok.si | Free Auto-Installer
echo ===================================================

:: 1. Download the free community edition virtual driver bundle
echo Fetching free system audio routing layers...
powershell -Command "Invoke-WebRequest -Uri 'https://vb-audio.com' -OutFile 'vbcable.zip'"

:: 2. Extract the driver bundle files
echo Extracting packages...
powershell -Command "Expand-Archive -Path 'vbcable.zip' -DestinationPath 'vbcable_extracted' -Force"

:: 3. Silently install the device driver into the Windows system layer
echo Injecting native system audio bridge (requires admin window confirmation)...
start /wait vbcable_extracted\VBCABLE_Setup_x64.exe /i

:: 4. Clean up the installer junk files to keep it raw and clean
echo Cleaning temporary data...
del vbcable.zip
rmdir /s /q vbcable_extracted

echo ===================================================
echo  SETUP COMPLETE! 
echo  1. Launch Zoom, Meet, or WhatsApp.
echo  2. Go to Audio Settings and change your Mic to 'Cable Output'.
echo  3. Double-click 'start.bat' and start speaking!
echo ===================================================
pause
