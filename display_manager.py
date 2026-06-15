def sync_penalty_display_to_external(app):
    """
    Sync penalty display updates to the external display window.
    Thin wrapper extracted from uwh.py.
    """

    try:
        if hasattr(app, "display_window") and app.display_window:
            app.update_penalty_display()

    except Exception as e:
        if getattr(app, "DEBUG_MODE", False):
            print(f"Penalty display sync error: {e}")
