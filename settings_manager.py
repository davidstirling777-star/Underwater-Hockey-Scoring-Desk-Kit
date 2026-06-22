
import os
import json

def load_unified_settings():
    """Load unified settings from JSON file."""
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return migrate_legacy_settings()
    else:
        return migrate_legacy_settings()


def save_unified_settings(settings):
    """Save unified settings to JSON file."""
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


def get_default_unified_settings():
    """Get default unified settings structure."""
    return {
        # your entire existing dictionary
    }


def load_sound_settings():
    """Load sound settings from unified JSON file."""
    unified_settings = load_unified_settings()
    return unified_settings.get("soundSettings", {})


def save_sound_settings(settings):
    """Save sound settings to unified JSON file."""
    unified_settings = load_unified_settings()
    unified_settings["soundSettings"] = settings
    save_unified_settings(unified_settings)


def load_preset_settings():
    unified_settings = load_unified_settings()
    return unified_settings.get("presetSettings", [])


def save_preset_settings(settings):
    unified_settings = load_unified_settings()
    unified_settings["presetSettings"] = settings
    save_unified_settings(unified_settings)


def migrate_legacy_settings():
    # move your existing function unchanged
