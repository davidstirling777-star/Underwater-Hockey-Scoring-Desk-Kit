@echo off
REM Build script for Windows executable using PyInstaller and a .spec file
REM This script packages the Underwater Hockey Scoring Desk Kit as a standalone .exe

echo Building Underwater Hockey Scoring Desk Kit executable for Windows using uwh.spec...
echo.

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

REM Build the executable using the .spec file
pyinstaller --clean --onefile uwh.spec

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
