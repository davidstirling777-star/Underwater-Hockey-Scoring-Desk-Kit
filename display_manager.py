def sync_penalty_display_to_external(app):
    """
    Preserve the original external display sync loop.

    The actual penalty display update remains in uwh.py because it is tightly
    coupled to Tkinter widgets.
    """
    try:
        app.display_window.after(
            1000,
            app.sync_penalty_display_to_external
        )

    except Exception as e:
        if getattr(app, "DEBUG_MODE", False):
            print(f"Penalty display sync error: {e}")

def penalty_sort_key(p):
    return p["seconds_remaining"] if not p["is_rest_of_match"] else 999999

def format_penalty_label(p):
    cap_str = f"#{p['cap']}"

    if p["is_rest_of_match"]:
        time_str = "rest"
    else:
        mins, secs = divmod(p["seconds_remaining"], 60)
        time_str = f"{mins}:{secs:02d}"

    return f"{cap_str}  {time_str}"
