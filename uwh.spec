# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Underwater Hockey Scoring Desk Kit

This spec file defines how to package the application into a standalone executable.
It includes all necessary Python files, data files (sound files, settings, CSV), 
and handles cross-platform builds.

Usage:
    pyinstaller --clean uwh.spec
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Define the main script
main_script = 'uwh.py'

# Data files to include (format: (source, destination_folder))
# All files will be placed in the root directory of the executable
data_files = [
    ('beep-cut.mp3', '.'),
    ('car-honk-cut.mp3', '.'),
    ('charging-machine-cut.mp3', '.'),
    ('countdown-beep-cut.mp3', '.'),
    ('notification-beep-cut.mp3', '.'),
    ('police-siren-cut.mp3', '.'),
    ('short-beep-tone-cut.mp3', '.'),
    ('settings.json', '.'),
    ('tournament Draw.csv', '.'),
]

# Python modules to include
# PyInstaller should auto-detect these from imports, but we list them explicitly
hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.font',
    'datetime',
    're',
    'time',
    'os',
    'subprocess',
    'json',
    'platform',
    'threading',
    'logging',
    'typing',
    # Optional dependencies that may not always be present
    'paho.mqtt.client',
    'serial',
    'serial.tools.list_ports',
    'winsound',
    'playsound',
]

a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=data_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='uwh',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed mode (no console window)
    disable_windowing_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add an icon file here if desired (e.g., 'icon.ico' on Windows)
)
