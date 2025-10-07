# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['uwh.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Example: Include all JSON and CSV files at any folder level
        ('*.json', '.'),        # Root level JSON files
        ('data/*.csv', 'data'), # CSV files inside a 'data' folder
        # Add more patterns as needed. For example:
        # ('assets/*.png', 'assets'),
        # ('configs/*.yaml', 'configs'),
    ],
    hiddenimports=[],
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
    console=True,
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