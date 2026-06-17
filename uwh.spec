# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None

if getattr(sys, "frozen", False):
    spec_dir = os.path.dirname(sys.executable)
else:
    spec_dir = os.getcwd()

a = Analysis(
    [
        "uwh.py",
        "sound.py",
        "zigbee_siren.py",
        "serial_siren_listener.py",
        "game_engine.py",
        "startup_selftest.py",
        "game_logging.py",
        "display_manager.py",
        "game_flow.py",
        "csv_helpers.py",
        "csv_export.py",
        "hardware_detection.py",
    ],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        ("assets/pip-beep.mp3", "assets"),
        ("assets/pip-countdown-beep.mp3", "assets"),
        ("assets/pip-notification.mp3", "assets"),
        ("assets/pip-short-tone.mp3", "assets"),
        ("assets/siren-car-honk.mp3", "assets"),
        ("assets/siren-machinegun.mp3", "assets"),
        ("assets/siren-police.mp3", "assets"),

        ("assets/LICENSE", "."),
        ("assets/settings.json", "."),
        ("assets/Tournament_Draw.csv", "."),
        ("assets/arduino_siren_button.ino", "."),

        ("README.md", "."),
        ("ZIGBEE_SETUP.md", "."),
        ("HARDWARE_SETUP.md", "."),
    ],
    hiddenimports=[
        "pygame",
        "paho.mqtt.client",
        "serial",

        "sound",
        "zigbee_siren",
        "serial_siren_listener",
        "game_engine",
        "startup_selftest",
        "game_logging",
        "display_manager",
        "game_flow",
        "csv_helpers",
        "csv_export",
        "hardware_detection",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="UnderwaterHockeyScoringDesk",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="UnderwaterHockeyScoringDesk"
)
