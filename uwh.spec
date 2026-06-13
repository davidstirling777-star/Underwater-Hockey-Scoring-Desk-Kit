a = Analysis(
    ['uwh.py', 'sound.py', 'zigbee_siren.py', 'serial_siren_listener.py', 'game_engine.py'],
    pathex=[spec_dir],
    binaries=[],
    datas=[
        ('assets/pip-beep.mp3', 'assets'),
        ('assets/pip-countdown-beep.mp3', 'assets'),
        ('assets/pip-notification.mp3', 'assets'),
        ('assets/pip-short-tone.mp3', 'assets'),
        ('assets/siren-car-honk.mp3', 'assets'),
        ('assets/siren-machinegun.mp3', 'assets'),
        ('assets/siren-police.mp3', 'assets'),

        ('assets/LICENSE', '.'),
        ('assets/settings.json', '.'),
        ('assets/Tournament_Draw.csv', '.'),
        ('assets/arduino_siren_button.ino', '.'),

        ('README.md', '.'),
        ('ZIGBEE_SETUP.md', '.'),
        ('HARDWARE_SETUP.md', '.'),
    ],

    hiddenimports=[
        'pygame',
        'paho.mqtt.client',
        'serial',
        'game_engine',
    ],

    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
