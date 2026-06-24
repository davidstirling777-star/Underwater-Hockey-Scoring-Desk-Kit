
def scale_fonts(app, event=None):
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

    base_width = 1200
    scale = cur_width / base_width
    scale = max(0.5, min(2.0, scale))

    base_sizes = {
        "court_time": 36,
        "half": 36,
        "team": 30,
        "score": 200,
        "timer": 90,
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
            fnt.config(size=new_size)
        except Exception:
            pass


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
        "timer": 90,
        "game_no": 20,
        "referee_timeout_timer": 24,
    }

    for key, fnt in app.display_fonts.items():
        new_size = int(base_sizes[key] * scale)

        try:
            fnt.config(size=new_size)
        except Exception:
            pass
          
