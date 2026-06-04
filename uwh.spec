
# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

# Get the directory where this spec file is located
spec_dir = os.path.dirname(os.path.abspath(__file__))

a = Analysis(
    [os.path.join(spec_dir, 'uwh.py')],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        # Audio files from assets folder
        (os.path.join(spec_dir, 'assets/pip-beep.mp3'), 'assets'),
        (os.path.join(spec_dir, 'assets/pip-countdown-beep.mp3'), 'assets'),
        (os.path.join(spec_dir, 'assets/pip-notification.mp3'), 'assets'),
        (os.path.join(spec_dir, 'assets/pip-short-tone.mp3'), 'assets'),
        (os.path.join(spec_dir, 'assets/siren-car-honk.mp3'), 'assets'),
        (os.path.join(spec_dir, 'assets/siren-machinegun.mp3'), 'assets'),
        (os.path.join(spec_dir, 'assets/siren-police.mp3'), 'assets'),
        # Data files from assets folder
        (os.path.join(spec_dir, 'assets/LICENSE'), 'assets'),
        (os.path.join(spec_dir, 'assets/settings.json'), 'assets'),
        (os.path.join(spec_dir, 'assets/Tournament Draw.csv'), 'assets'),
        (os.path.join(spec_dir, 'assets/arduino_siren_button.ino'), 'assets'),
        # Documentation files from root
        (os.path.join(spec_dir, 'README.md'), '.'),
        (os.path.join(spec_dir, 'ZIGBEE_SETUP.md'), '.'),
        # Python modules in root
        (os.path.join(spec_dir, 'sound.py'), '.'),
        (os.path.join(spec_dir, 'zigbee_siren.py'), '.'),
        (os.path.join(spec_dir, 'serial_siren_listener.py'), '.'),
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
    exclude_binaries=True,
    name='UnderwaterHockeyScoringDesk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UnderwaterHockeyScoringDesk'
)
