#!/bin/bash

# --- Configuration ---
MAIN_SCRIPT="uwh.py"
APP_NAME="uwh"
DATA_FILES=(
    "LICENSE"
    "README.md"
    "Tournament Draw.csv"
    "ZIGBEE_SETUP.md"
    "pip-beep.mp3"
    "pip-countdown-beep.mp3"
    "pip-notification.mp3"
    "pip-short-tone.mp3"
    "requirements.txt"
    "settings.json"
    "siren-car-honk.mp3"
    "siren-machinegun.mp3"
    "siren-police.mp3"
    "sound.py"
    "zigbee_siren.py"
)

# --- Step 1: Create and activate virtual environment ---
echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# --- Step 2: Install PyInstaller in the venv ---
echo "Installing PyInstaller..."
pip install --upgrade pip
pip install pyinstaller

# --- Step 3: Build the --add-data arguments ---
ADD_DATA_ARGS=""
for file in "${DATA_FILES[@]}"
do
    # For each file, add --add-data 'filename:.'
    ADD_DATA_ARGS+=" --add-data '$file:.'"
done

# --- Step 4: Run PyInstaller ---
echo "Running PyInstaller to build binary..."
eval "pyinstaller --name $APP_NAME --onefile $ADD_DATA_ARGS $MAIN_SCRIPT"

# --- Step 5: Show result ---
echo ""
echo "Build complete!"
echo "Find your executable in the dist/ directory:"
echo "  dist/$APP_NAME"
echo "To run it: ./dist/$APP_NAME"
echo ""
echo "Deactivate the virtual environment with: deactivate"
