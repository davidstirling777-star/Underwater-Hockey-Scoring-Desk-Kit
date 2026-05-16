@echo off
REM Build script for Windows executable using PyInstaller and a .spec file

echo Building Underwater Hockey Scoring Desk Kit executable for Windows...
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller is not installed. Installing dependencies...
    pip install -r requirements.txt
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
)

REM Build the executable using the .spec file
echo Running PyInstaller...
pyinstaller --clean uwh.spec

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
    echo Executable can be found in: 
    dist\UnderwaterHockeyScoringDesk\UnderwaterHockeyScoringDesk.exe
echo.
pause
