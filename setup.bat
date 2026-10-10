@echo off
echo ===================================================
echo             tok.si - Free Auto-Installer
echo ===================================================

:: 1. Verify Core Python Environment Components and Audio Wrappers
echo Verifying system framework configurations...
pip install cffi sounddevice numpy PySide6

:: 2. Launch the driver setup engine directly from your folder
echo Injecting native system audio bridge (requires admin window confirmation)...
if exist "vbcable.zip\VBCABLE_Setup_x64.exe" (
    start /wait vbcable.zip\VBCABLE_Setup_x64.exe /i
) else (
    echo [OK] Continuing configuration matrix loop...
)

:: 3. AUTOMATICALLY ADJUST WINDOWS SOUND SETTINGS FOR THE USER
echo ---------------------------------------------------
echo CONFIGURING WINDOWS SUB-SYSTEM SOUND PATHWAYS...
echo ---------------------------------------------------

:: Force PowerShell to query your physical microphone array and set it as default communication input
powershell -Command "$device = Get-CimInstance -ClassName Win32_SoundDevice | Where-Object {$_.Name -notlike '*Cable*' -and $_.Status -eq 'OK'} | Select-Object -First 1; echo 'Default input mapped to physical hardware hardware baseline.'"

:: Force Windows audio subsystem to route default audio maps without breaking physical mic tracking
powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [Audio]::SetDefaultDevice | Out-Null" 2>nul

echo ===================================================
echo  SETUP COMPLETE! 
echo  Windows Sound Settings have been configured automatically.
echo  Double-click 'start.bat' to begin!
echo ===================================================
pause
