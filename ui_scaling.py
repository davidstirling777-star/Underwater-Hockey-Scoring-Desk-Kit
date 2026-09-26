def scale_fonts(app, event=None):
    """
    Scale operator-window fonts only when necessary.

    Ignore Configure events from child widgets, skip repeated
    window widths, and do not reconfigure fonts whose calculated
    sizes are already correct.
    """

    # A Configure event from a child widget does not mean
    # the main window has changed size.
    if event is not None and event.widget is not app.master:
        return

    try:
        cur_width = app.master.winfo_width()

        if cur_width <= 0:
            cur_width = getattr(app, "initial_width", 1200)

    except Exception:
        cur_width = 1200

    # Skip duplicate Configure events at the same width.
    # Explicit calls with event=None are still allowed to
    # check the font sizes.
    if (
        event is not None
        and cur_width == getattr(
            app,
            "_last_operator_font_width",
            None
        )
    ):
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
        if key not in base_sizes:
            continue

        if key == "timeout_button":
            new_size = int(
                base_sizes[key]
                * scale
                * reduced_button_scale
            )
        else:
            new_size = int(
                base_sizes[key] * scale
            )

        try:
            # Avoid triggering a redraw when the font size
            # is already correct.
            if int(fnt.cget("size")) != new_size:
                fnt.config(size=new_size)

        except Exception:
            pass

    app._last_operator_font_width = cur_width


def scale_display_fonts(app, event=None):
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
            fnt.config(size=new_size)
        except Exception:
            pass
          
