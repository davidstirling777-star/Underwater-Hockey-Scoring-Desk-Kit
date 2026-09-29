import os
import json
import datetime
import tempfile
import threading


# All in-process settings writers share one lock. Each committed settings.json
# remains readable while a complete replacement is prepared beside it.
_SETTINGS_IO_LOCK = threading.RLock()


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


def _validate_settings_document(raw, settings_path):
    """Refuse to overwrite corrupt settings or a non-object JSON document."""
    try:
        document = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise ValueError(
            f"Cannot read {settings_path}; it has not been overwritten. "
            "Restore a valid settings_old_*.json backup after making a copy "
            "of the damaged file."
        ) from error

    if not isinstance(document, dict):
        raise ValueError(
            f"Cannot read {settings_path}: expected a JSON object. "
            "The file has not been overwritten."
        )
    return document


def _write_staged_file(base_dir, prefix, payload):
    """Write and flush a temporary file on the same filesystem as settings."""
    descriptor, staged_path = tempfile.mkstemp(
        dir=base_dir, prefix=prefix, suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "wb") as staged:
            staged.write(payload)
            staged.flush()
            os.fsync(staged.fileno())
    except BaseException:
        if os.path.exists(staged_path):
            os.unlink(staged_path)
        raise
    return staged_path


def _previous_settings_backup_path(base_dir):
    """Unique, Windows-safe, sortable date-and-time backup filename."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    stem = f"settings_old_{timestamp}"
    path = os.path.join(base_dir, stem + ".json")
    counter = 1
    while os.path.exists(path):
        path = os.path.join(base_dir, f"{stem}_{counter}.json")
        counter += 1
    return path


def load_unified_settings(base_dir):
    """Load the active settings; never silently reset unreadable settings."""
    settings_path = get_settings_path(base_dir)
    with _SETTINGS_IO_LOCK:
        if os.path.exists(settings_path):
            with open(settings_path, "rb") as settings_file:
                return _validate_settings_document(
                    settings_file.read(), settings_path
                )

        # Preserve the existing first-run / legacy-migration behaviour only
        # when there is genuinely no active settings file.
        return migrate_legacy_settings(base_dir)


def save_unified_settings(base_dir, settings):
    """Replace settings.json safely; archive its predecessor before committing.

    The previous file is retained as settings_old_DATE_TIME.json. A complete
    new file is staged first, then atomically replaces settings.json; there
    is no interval with the active file missing (including on Windows).
    """
    if not isinstance(settings, dict):
        raise TypeError("Unified settings must be a JSON object.")

    # Fail serialization before touching either the active file or backups.
    payload = json.dumps(settings, indent=2).encode("utf-8")
    settings_path = get_settings_path(base_dir)

    with _SETTINGS_IO_LOCK:
        previous = None
        if os.path.exists(settings_path):
            with open(settings_path, "rb") as settings_file:
                previous = settings_file.read()
            previous_document = _validate_settings_document(
                previous, settings_path
            )
            # Startup synchronisation and duplicate save calls need not
            # create a new backup when nothing has changed.
            if previous_document == settings:
                return

        staged_new = None
        staged_backup = None
        try:
            staged_new = _write_staged_file(
                base_dir, ".settings_new_", payload
            )
            if previous is not None:
                staged_backup = _write_staged_file(
                    base_dir, ".settings_old_", previous
                )
                backup_path = _previous_settings_backup_path(base_dir)
                os.replace(staged_backup, backup_path)
                staged_backup = None

            # Atomic on the same filesystem: readers always see either the
            # old complete JSON file or the new complete JSON file.
            os.replace(staged_new, settings_path)
            staged_new = None
        finally:
            for staged_path in (staged_new, staged_backup):
                if staged_path is not None and os.path.exists(staged_path):
                    os.unlink(staged_path)


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
            "enable_sound": True,
            "max_siren_duration": 10.0
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
        "screenSettings": {
            "show_team_names": True,
            "operator_layout": "Standard",
            "display_layout": "Single Standard"
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
