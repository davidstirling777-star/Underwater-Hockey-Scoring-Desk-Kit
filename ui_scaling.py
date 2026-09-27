
def scale_fonts(app, event=None):
    # Binding on a Tk toplevel also receives Configure events from children.
    # Rescale only when the OPERATOR window itself changes geometry.
    if event is not None and getattr(event, "widget", None) is not app.master:
        return

    try:
        cur_width = app.master.winfo_width()

        if cur_width <= 0:
            cur_width = (
                app.initial_width
                if hasattr(app, "initial_width")
                else 1200
            )

    except Exception:
        cur_width = 1200

    # Avoid repeated reconfiguration during relayout of a maximised window.
    if event is not None and getattr(app, "_last_operator_scale_width", None) == cur_width:
        return

    base_width = 1200
    scale = cur_width / base_width
    scale = max(0.5, min(2.0, scale))

    base_sizes = {
        "court_time": 36,
        "half": 36,
        "team": 30,
        "score": 200,
        "timer": 110,
        "game_no": 20,
        "button": 20,
        "timeout_button": 20,
        "referee_timeout_timer": 24,
    }

    reduced_button_scale = 0.7

    for key, fnt in app.fonts.items():
        if key == "timeout_button":
            new_size = int(
                base_sizes[key] * scale * reduced_button_scale
            )
        else:
            new_size = int(base_sizes[key] * scale)

        try:
            # font.config(...) can trigger a fresh round of widget geometry
            # events. Only issue it when the resulting size really changes.
            if int(fnt.cget("size")) != new_size:
                fnt.config(size=new_size)
        except Exception:
            pass

    app._last_operator_scale_width = cur_width


def scale_display_fonts(app, event=None):
    if event is not None and getattr(event, "widget", None) is not app.display_window:
        return

    try:
        cur_width = app.display_window.winfo_width()

        if cur_width <= 0:
            cur_width = (
                app.display_initial_width
                if hasattr(app, "display_initial_width")
                else 1200
            )

    except Exception:
        cur_width = 1200

    # Do not repeat geometry work when the display width is unchanged.
    if event is not None and getattr(app, "_last_display_scale_width", None) == cur_width:
        return

    base_width = 1200
    scale = cur_width / base_width
    scale = max(0.5, min(2.0, scale))

    base_sizes = {
        "court_time": 36,
        "half": 36,
        "team": 30,
        "score": 200,
        "timer": 110,
        "game_no": 20,
        "referee_timeout_timer": 24,
    }

    for key, fnt in app.display_fonts.items():
        new_size = int(base_sizes[key] * scale)

        try:
            if int(fnt.cget("size")) != new_size:
                fnt.config(size=new_size)
        except Exception:
            pass

    app._last_display_scale_width = cur_width

