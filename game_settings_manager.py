"""Save and restore Game Variables, including mixed checkbox/number fields."""

import tkinter as tk


def save_game_settings(app):
    """Save game settings without losing checkbox states on numeric fields."""
    # Setting tkinter variables during load fires their trace callbacks.
    # Never let a partially restored screen overwrite the saved configuration.
    if getattr(app, "_loading_game_settings", False):
        return

    unified_settings = app.load_unified_settings()
    game_settings = {}
    mixed_checkboxes = {}

    for var_name, var_info in app.variables.items():
        widget = next(
            (item for item in app.widgets if item["name"] == var_name), None
        )
        has_entry = widget is not None and widget["entry"] is not None
        has_checkbox = bool(var_info.get("checkbox", False))

        if has_checkbox and has_entry:
            value = var_info.get("value", var_info["default"])
            try:
                # Preserve the existing flat numeric gameSettings format.
                game_settings[var_name] = (
                    float(value) if "." in str(value) else int(value)
                )
            except (ValueError, TypeError):
                game_settings[var_name] = var_info["default"]

            # The numeric value and enabled state are independent. Use the
            # visible Tk variable so this also works after a preset click.
            mixed_checkboxes[var_name] = bool(widget["checkbox"].get())

        elif has_checkbox:
            # Checkbox-only fields remain ordinary booleans for compatibility.
            game_settings[var_name] = bool(
                widget["checkbox"].get() if widget is not None
                and widget["checkbox"] is not None
                else var_info.get("used", var_info["default"])
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

    # Mirrors the already-used preset "checkboxes" convention. The original
    # numeric keys are unchanged, and presets remain stored separately.
    game_settings["checkboxes"] = mixed_checkboxes
    unified_settings["gameSettings"] = game_settings
    app.save_unified_settings(unified_settings)


def load_game_settings(app):
    """Restore values and checkbox states without saving partial UI updates."""
    unified_settings = app.load_unified_settings()
    game_settings = unified_settings.get("gameSettings", {})
    if not isinstance(game_settings, dict):
        return

    saved_checkboxes = game_settings.get("checkboxes", {})
    if not isinstance(saved_checkboxes, dict):
        saved_checkboxes = {}

    previous_loading = getattr(app, "_loading_game_settings", False)
    app._loading_game_settings = True
    try:
        for var_name, var_info in app.variables.items():
            if var_name not in game_settings:
                continue

            value = game_settings[var_name]
            widget = next(
                (item for item in app.widgets if item["name"] == var_name),
                None
            )
            has_checkbox = bool(var_info.get("checkbox", False))
            has_entry = widget is not None and widget["entry"] is not None

            if has_checkbox and has_entry:
                if isinstance(value, bool):
                    # Legacy installations sometimes stored only a checkbox.
                    # Keep its on/off setting and use the numeric default.
                    var_info["value"] = str(var_info["default"])
                    var_info["used"] = value
                else:
                    # Legacy numeric-only settings imply enabled, matching the
                    # behaviour of versions before this persistence fix.
                    var_info["value"] = str(value)
                    saved_used = saved_checkboxes.get(var_name, True)
                    var_info["used"] = (
                        saved_used if isinstance(saved_used, bool) else True
                    )

            elif has_checkbox:
                var_info["used"] = value

            else:
                var_info["value"] = str(value)

            if widget is None:
                continue

            if widget["entry"] is not None:
                widget["entry"].delete(0, tk.END)
                widget["entry"].insert(0, var_info["value"])

            if widget["checkbox"] is not None:
                widget["checkbox"].set(var_info["used"])

    finally:
        app._loading_game_settings = previous_loading

    # The checkbox trace callbacks were intentionally suppressed during
    # loading; apply their visual effects once all fields are restored.
    if not previous_loading:
        app.update_team_timeouts_allowed()
        app.update_overtime_variables_state()
