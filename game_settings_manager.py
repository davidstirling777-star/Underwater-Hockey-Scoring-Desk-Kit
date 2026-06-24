import tkinter as tk

def save_game_settings(app):
    """Save current game settings to unified JSON file."""
    unified_settings = app.load_unified_settings()
    game_settings = {}

    for var_name, var_info in app.variables.items():
        if var_info.get("checkbox", False):
            has_entry = False

            for widget in app.widgets:
                if widget["name"] == var_name and widget["entry"] is not None:
                    has_entry = True
                    break

            if has_entry:
                value = var_info.get("value", var_info["default"])

                if var_name != "time_to_start_first_game":
                    try:
                        game_settings[var_name] = (
                            float(value) if "." in str(value) else int(value)
                        )
                    except (ValueError, TypeError):
                        game_settings[var_name] = var_info["default"]
                else:
                    game_settings[var_name] = value

            else:
                game_settings[var_name] = var_info.get(
                    "used",
                    var_info["default"]
                )

        else:
            value = var_info.get("value", var_info["default"])

            if var_name != "time_to_start_first_game":
                try:
                    game_settings[var_name] = (
                        float(value) if "." in str(value) else int(value)
                    )
                except (ValueError, TypeError):
                    game_settings[var_name] = value
            else:
                game_settings[var_name] = value

    unified_settings["gameSettings"] = game_settings
    app.save_unified_settings(unified_settings)

def load_game_settings(app):
    """Load saved game settings from the unified JSON file."""
    unified_settings = app.load_unified_settings()
    game_settings = unified_settings.get("gameSettings", {})

    for var_name, var_info in app.variables.items():
        if var_name not in game_settings:
            continue

        value = game_settings[var_name]

        has_checkbox = var_info.get("checkbox", False)
        has_entry = False

        for widget in app.widgets:
            if widget["name"] == var_name and widget["entry"] is not None:
                has_entry = True
                break

        if has_checkbox and has_entry:
            # Mixed checkbox + numeric-entry variables.
            if isinstance(value, bool):
                # Old settings format: checkbox value only.
                app.variables[var_name]["value"] = str(var_info["default"])
                app.variables[var_name]["used"] = value
            else:
                app.variables[var_name]["value"] = str(value)
                app.variables[var_name]["used"] = True

        elif has_checkbox:
            # Checkbox-only variables.
            app.variables[var_name]["used"] = value

        else:
            # Entry-only variables.
            app.variables[var_name]["value"] = str(value)

        for widget in app.widgets:
            if widget["name"] != var_name:
                continue

            if widget["entry"] is not None:
                widget["entry"].delete(0, tk.END)

                if has_checkbox and has_entry:
                    widget["entry"].insert(
                        0,
                        app.variables[var_name]["value"]
                    )
                else:
                    widget["entry"].insert(0, str(value))

            if widget["checkbox"] is not None:
                if has_checkbox and has_entry:
                    widget["checkbox"].set(
                        app.variables[var_name]["used"]
                    )
                else:
                    widget["checkbox"].set(
                        value if isinstance(value, bool) else True
                    )

            break
