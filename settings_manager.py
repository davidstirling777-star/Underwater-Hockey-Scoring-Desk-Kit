import os
import json


def get_settings_path(base_dir):
    return os.path.join(base_dir, "settings.json")


def migrate_legacy_settings(base_dir):
    """Migrate settings from legacy separate files to unified settings.json."""
    unified_settings = get_default_unified_settings()
    migrated = False

    legacy_sound_file = os.path.join(base_dir, "game_settings.json")
    if os.path.exists(legacy_sound_file):
        try:
            with open(legacy_sound_file, "r") as f:
                legacy_sound_settings = json.load(f)

            unified_settings["soundSettings"].update(legacy_sound_settings)
            migrated = True
            print("Migrated sound settings from game_settings.json")

        except Exception as e:
            print(f"Error migrating game_settings.json: {e}")

    legacy_zigbee_file = os.path.join(base_dir, "zigbee_config.json")
    if os.path.exists(legacy_zigbee_file):
        try:
            with open(legacy_zigbee_file, "r") as f:
                legacy_zigbee_settings = json.load(f)

            unified_settings["zigbeeSettings"].update(legacy_zigbee_settings)
            migrated = True
            print("Migrated Zigbee settings from zigbee_config.json")

        except Exception as e:
            print(f"Error migrating zigbee_config.json: {e}")

    if migrated:
        save_unified_settings(base_dir, unified_settings)
        print("Migration completed. Legacy files preserved.")

    return unified_settings


def load_unified_settings(base_dir):
    """Load unified settings from JSON file."""
    settings_path = get_settings_path(base_dir)

    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return migrate_legacy_settings(base_dir)

    return migrate_legacy_settings(base_dir)


def save_unified_settings(base_dir, settings):
    """Save unified settings to JSON file."""
    settings_path = get_settings_path(base_dir)

    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)


def get_default_unified_settings():
    """Get default unified settings structure."""
    return {
        "soundSettings": {
            "pips_sound": "Default",
            "siren_sound": "Default",
            "pips_volume": 50.0,
            "siren_volume": 50.0,
            "air_volume": 50.0,
            "water_volume": 50.0,
            "enable_sound": True
        },
        "zigbeeSettings": {
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mqtt_username": "",
            "mqtt_password": "",
            "mqtt_topic": "zigbee2mqtt/+",
            "siren_button_devices": ["siren_button"],
            "siren_button_device": "siren_button",
            "connection_timeout": 60,
            "reconnect_delay": 5,
            "enable_logging": True
        },
        "gameSettings": {
            "time_to_start_first_game": "",
            "start_first_game_in": 1,
            "team_timeouts_allowed": True,
            "team_timeout_period": 1,
            "half_period": 1,
            "half_time_break": 1,
            "overtime_allowed": True,
            "overtime_game_break": 1,
            "overtime_half_period": 1,
            "overtime_half_time_break": 1,
            "sudden_death_game_break": 1,
            "between_game_break": 1,
            "record_scorers_cap_number": False,
            "crib_time": 3
        },
        "presetSettings": [
            {
                "text": "CMAS",
                "values": {
                    "team_timeout_period": "1",
                    "half_period": "15",
                    "half_time_break": "3",
                    "overtime_game_break": "3",
                    "overtime_half_period": "5",
                    "overtime_half_time_break": "1",
                    "sudden_death_game_break": "1",
                    "between_game_break": "5",
                    "crib_time": "60"
                },
                "checkboxes": {
                    "team_timeouts_allowed": True,
                    "overtime_allowed": True
                }
            },
            {"text": "2", "values": {}, "checkboxes": {}},
            {"text": "3", "values": {}, "checkboxes": {}},
            {"text": "4", "values": {}, "checkboxes": {}},
            {"text": "5", "values": {}, "checkboxes": {}},
            {"text": "6", "values": {}, "checkboxes": {}}
        ]
    }


def load_sound_settings(base_dir):
    """Load sound settings from unified JSON file."""
    unified_settings = load_unified_settings(base_dir)
    return unified_settings.get("soundSettings", {})


def save_sound_settings(base_dir, settings):
    """Save sound settings to unified JSON file."""
    unified_settings = load_unified_settings(base_dir)
    unified_settings["soundSettings"] = settings
    save_unified_settings(base_dir, unified_settings)


def load_preset_settings(base_dir):
    """Load preset settings from unified JSON file."""
    unified_settings = load_unified_settings(base_dir)
    return unified_settings.get(
        "presetSettings",
        get_default_unified_settings()["presetSettings"]
    )


def save_preset_settings(base_dir, presets):
    """Save preset settings to unified JSON file."""
    unified_settings = load_unified_settings(base_dir)
    unified_settings["presetSettings"] = presets
    save_unified_settings(base_dir, unified_settings)
