# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['uwh.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Audio files from assets folder
        ('assets/pip-beep.mp3', 'assets'),
        ('assets/pip-countdown-beep.mp3', 'assets'),
        ('assets/pip-notification.mp3', 'assets'),
        ('assets/pip-short-tone.mp3', 'assets'),
        ('assets/siren-car-honk.mp3', 'assets'),
        ('assets/siren-machinegun.mp3', 'assets'),
        ('assets/siren-police.mp3', 'assets'),
        # Data files from assets folder
        ('assets/LICENSE', 'assets'),
        ('assets/settings.json', 'assets'),
        ('assets/Tournament Draw.csv', 'assets'),
        ('assets/arduino_siren_button.ino', 'assets'),
        # Documentation files from root
        ('README.md', '.'),
        ('ZIGBEE_SETUP.md', '.'),
        # Python modules in root
        ('sound.py', '.'),
        ('zigbee_siren.py', '.'),
        ('serial_siren_listener.py', '.'),
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
