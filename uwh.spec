# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_all

block_cipher = None

ttkbootstrap_datas, ttkbootstrap_binaries, ttkbootstrap_hiddenimports = (
    collect_all("ttkbootstrap")
)

if getattr(sys, "frozen", False):
    spec_dir = os.path.dirname(sys.executable)
else:
    spec_dir = os.getcwd()

a = Analysis(
    [
        "csv_export.py",
        "csv_helpers.py",
        "csv_ui.py",
        "tournament_files.py",
        "tournament_sync.py",
        "display_manager.py",
        "display_ui.py",
        "game_engine.py",
        "game_flow.py",
        "game_logging.py",
        "game_settings_manager.py",
        "penalties_ui.py",
        "preset_manager.py",
        "scoreboard_ui.py",
        "serial_siren_listener.py",
        "settings_manager.py",
        "settings_ui.py",
        "sound.py",
        "sounds_ui.py",
        "startup_selftest.py",
        "hardware_detection.py",
        "ui_scaling.py",
        "ui_theme.py",
        "uwh.py",
        "zigbee_control.py",
        "zigbee_hardware_ui.py",
        "zigbee_siren.py",
        "zigbee_ui.py",
    ],
    pathex=[spec_dir],
    binaries=ttkbootstrap_binaries,
    datas=[
        ("assets/pip-beep.mp3", "assets"),
        ("assets/pip-countdown-beep.mp3", "assets"),
        ("assets/pip-notification.mp3", "assets"),
        ("assets/pip-short-tone.mp3", "assets"),
        ("assets/siren-car-honk.mp3", "assets"),
        ("assets/siren-machinegun.mp3", "assets"),
        ("assets/siren-police.mp3", "assets"),
        ("assets/About_hero_logo.png", "assets"),

        ("assets/LICENSE", "."),
        ("assets/settings.json", "."),
        ("assets/Tournament_Draw.csv", "."),
        ("assets/arduino_siren_button.ino", "."),

        ("README.md", "."),
        ("tournament_results_server.py", "."),
        ("HARDWARE_SETUP.md", "."),
    ] + ttkbootstrap_datas,
    hiddenimports=[
        "pygame",
        "paho.mqtt.client",
        "serial",
        "csv_helpers",
        "csv_export",
        "csv_ui",
        "tournament_files",
        "tournament_sync",
        "display_manager",
        "display_ui",
        "hardware_detection",
        "game_engine",
        "game_flow",
        "game_logging",
        "game_settings_manager",
        "penalties_ui",
        "preset_manager",
        "settings_ui",
        "scoreboard_ui",
        "serial_siren_listener",
        "settings_manager",
        "sound",
        "sounds_ui",
        "startup_selftest",
        "ui_scaling",
        "ui_theme",
        "ttkbootstrap",
        "zigbee_ui",
        "zigbee_hardware_ui",
        "zigbee_control",
        "zigbee_siren",
    ] + ttkbootstrap_hiddenimports,
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
