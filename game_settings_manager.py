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
