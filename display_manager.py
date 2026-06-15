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

def update_penalty_display(app):
    """
    Update penalty display window.
    Extracted from uwh.py.
    """
    try:
        # Paste the ENTIRE current body of
        # update_penalty_display() here
        pass

    except Exception as e:
        if getattr(app, "DEBUG_MODE", False):
            print(f"Display update error: {e}")
