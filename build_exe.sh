#!/bin/bash
# Build script for Linux executable using PyInstaller
# This script packages the Underwater Hockey Scoring Desk Kit as a standalone binary

echo "Building Underwater Hockey Scoring Desk Kit executable for Linux..."
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller is not installed. Installing now..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyInstaller"
        exit 1
    fi
fi

# Build the executable using the .spec file
echo "Building executable..."
pyinstaller --clean uwh.spec

if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

echo ""
echo "Build completed successfully!"
echo "Executable can be found in: dist/uwh"
echo ""
