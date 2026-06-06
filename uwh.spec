# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Get the directory where pyinstaller is being run from (repo root)
if getattr(sys, 'frozen', False):
    spec_dir = os.path.dirname(sys.executable)
else:
    spec_dir = os.getcwd()

a = Analysis(
    ['uwh.py', 'sound.py', 'zigbee_siren.py', 'serial_siren_listener.py'],  # <-- UPDATE THIS LINE HERE
    pathex=[spec_dir],
    binaries=[],
    datas=[
        # 1. Audio files - stay safely hidden inside '_internal/assets'
        ('assets/pip-beep.mp3', 'assets'),
        ('assets/pip-countdown-beep.mp3', 'assets'),
        ('assets/pip-notification.mp3', 'assets'),
        ('assets/pip-short-tone.mp3', 'assets'),
        ('assets/siren-car-honk.mp3', 'assets'),
        ('assets/siren-machinegun.mp3', 'assets'),
        ('assets/siren-police.mp3', 'assets'),

        # 2. Writable data files
        ('assets/LICENSE', '.'),
        ('assets/settings.json', '.'),
        ('assets/Tournament_Draw.csv', '.'),
        ('assets/arduino_siren_button.ino', '.'),
        
        # 3. Documentation files
        ('README.md', '.'),
        ('ZIGBEE_SETUP.md', '.'),
        ('HARDWARE_SETUP.md', '.'),
    ],


    hiddenimports=['pygame', 'paho.mqtt.client', 'serial'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,    # KEY: This tells PyInstaller "don't include binaries in the EXE"
    name='UnderwaterHockeyScoringDesk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(                # KEY: This is what collects everything into the root folder
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UnderwaterHockeyScoringDesk'
)
