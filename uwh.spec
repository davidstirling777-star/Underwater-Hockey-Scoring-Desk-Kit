# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['uwh.py'],
    pathex=[],
    binaries=[],
    datas=[
         # Audio files
        ('pip-beep.mp3', '.'),
        ('pip-countdown-beep.mp3', '.'),
        ('pip-notification.mp3', '.'),
        ('pip-short-tone.mp3', '.'),
        ('siren-car-honk.mp3', '.'),
        ('siren-machinegun.mp3', '.'),
        ('siren-police.mp3', '.'),
        # Data and config files
        ('LICENSE', '.'),
        ('README.md', '.'),
        ('Tournament Draw.csv', '.'),
        ('ZIGBEE_SETUP.md', '.'),
        ('settings.json', '.'),
        ('arduino_siren_button.ino', '.'),
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
