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
        "csv_export.py",
        "csv_helpers.py",
        "csv_ui.py",
        "display_manager.py",
        "game_engine.py",
        "game_flow.py",
        "game_logging.py",
        "serial_siren_listener.py",
        "settings_manager.py",
        "sound.py",
        "sounds_ui.py",
        "startup_selftest.py",
        "hardware_detection.py",
        "uwh.py",
        "zigbee_control.py",
        "zigbee_hardware_ui.py",
        "zigbee_siren.py",
        "zigbee_ui.py",
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
        "csv_helpers",
        "csv_export",
        "csv_ui",
        "sound",
        "sounds_ui",
        "serial_siren_listener",
        "game_engine",
        "startup_selftest",
        "settings_manager",
        "game_logging",
        "display_manager",
        "game_flow",
        "hardware_detection",
        "zigbee_ui",
        "zigbee_hardware_ui",
        "zigbee_control",
        "zigbee_siren",
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
