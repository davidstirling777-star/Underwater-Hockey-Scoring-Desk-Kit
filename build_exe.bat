@echo off
REM Build script for Windows executable using PyInstaller
REM This script packages the Underwater Hockey Scoring Desk Kit as a standalone .exe

echo Building Underwater Hockey Scoring Desk Kit executable for Windows...
echo.

REM Enable delayed variable expansion
setlocal enabledelayedexpansion

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller is not installed. Installing now...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM List of files to include
set DATAFILES=LICENSE README.md "Tournament Draw.csv" ZIGBEE_SETUP.md pip-beep.mp3 pip-countdown-beep.mp3 pip-notification.mp3 pip-short-tone.mp3 requirements.txt settings.json siren-car-honk.mp3 siren-machinegun.mp3 siren-police.mp3 sound.py uwh.py zigbee_siren.py

REM Build the --add-data argument for PyInstaller
set ADDDATA=
for %%F in (%DATAFILES%) do (
    set ADDDATA=!ADDDATA! --add-data "%%F;."
)

REM Build the executable (change uwh.py to your main entrypoint if needed)
pyinstaller --clean --onefile !ADDDATA! uwh.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable can be found in: dist\uwh.exe
echo.
pause
