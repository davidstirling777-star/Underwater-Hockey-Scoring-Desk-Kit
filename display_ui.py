import tkinter as tk
from tkinter import ttk
import display_manager

def create_display_window(app):
    """Create or bring forward the external scoreboard display window."""
    try:
        if (
            hasattr(app, "display_window")
            and app.display_window is not None
            and app.display_window.winfo_exists()
        ):
            app.display_window.lift()
            app.display_window.focus_force()
            return

    except tk.TclError:
        app.display_window = None

    app.display_window = tk.Toplevel(app.master)
    if not hasattr(app, "display_windows"):
        app.display_windows = []
    app.display_windows.append(app.display_window)
    app.display_window.title("Display Window")
    app.display_window.geometry("1200x800")
    app.display_window.protocol(
        "WM_DELETE_WINDOW",
        app._on_display_window_close
    )

    tab = ttk.Frame(app.display_window)
    tab.pack(fill="both", expand=True)

    # Match the main Scoreboard tab:
    # 9 equal columns, making White / Centre / Black equal thirds.
    for row in range(11):
        tab.grid_rowconfigure(row, weight=1)

    # Initial layout. Actual widths are copied from the main Scoreboard
    # tab once both layouts have been calculated.
    for column in range(9):
        tab.grid_columnconfigure(
            column,
            weight=1,
            minsize=1
        )

    # Keep team-name and centre-information rows stable.
    tab.grid_rowconfigure(2, minsize=58)
    tab.grid_rowconfigure(3, minsize=58)

    # Court time.
    app.display_court_time_label = tk.Label(
        tab,
        textvariable=app.court_time_var,
        font=app.display_fonts["court_time"],
        bg="lightgrey"
    )
    app.display_court_time_label.grid(
        row=0,
        column=0,
        columnspan=9,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Current period label.
    app.display_half_label = tk.Label(
        tab,
        textvariable=app.half_label_var,
        font=app.display_fonts["half"],
        bg="lightcoral"
    )
    app.display_half_label.grid(
        row=1,
        column=0,
        columnspan=9,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # White / Black colour labels.
    app.display_white_label = tk.Label(
        tab,
        textvariable=app.white_team_var,
        font=app.display_fonts["team"],
        bg="white",
        fg="black",
        anchor="center"
    )
    app.display_white_label.grid(
        row=2,
        column=0,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.display_black_label = tk.Label(
        tab,
        textvariable=app.black_team_var,
        font=app.display_fonts["team"],
        bg="black",
        fg="white",
        anchor="center"
    )
    app.display_black_label.grid(
        row=2,
        column=6,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Fixed centre area for penalties / Next Game banner.
    app.display_penalty_area_frame = tk.Frame(
        tab,
        bg="lightgrey",
        bd=0,
        highlightthickness=0
    )
    app.display_penalty_area_frame.grid(
        row=2,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )
    app.display_penalty_area_frame.grid_rowconfigure(
        0,
        weight=1
    )
    app.display_penalty_area_frame.grid_columnconfigure(
        0,
        weight=1
    )
    app.display_penalty_area_frame.grid_propagate(False)

    app.display_penalty_grid_frame, app.display_penalty_labels = (
        app.create_penalty_grid_widget(
            app.display_penalty_area_frame,
            is_display=True
        )
    )
    app.display_penalty_grid_frame.grid(
        row=0,
        column=0,
        sticky="nsew"
    )
    app.display_penalty_grid_frame.grid_remove()

    # Team names.
    app.display_white_team_name_widget = tk.Label(
        tab,
        text="",
        font=app.display_fonts["team"],
        bg="white",
        fg="black",
        anchor="center",
        width=1
    )
    app.display_white_team_name_widget.grid(
        row=3,
        column=0,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.display_black_team_name_widget = tk.Label(
        tab,
        text="",
        font=app.display_fonts["team"],
        bg="black",
        fg="white",
        anchor="center",
        width=1
    )
    app.display_black_team_name_widget.grid(
        row=3,
        column=6,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Current game number.
    app.display_game_label = tk.Label(
        tab,
        textvariable=app.game_number_var,
        font=app.display_fonts["game_no"],
        bg="lightgrey",
        fg="black",
        anchor="center"
    )
    app.display_game_label.grid(
        row=3,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Scores.
    app.display_white_score = tk.Label(
        tab,
        textvariable=app.white_score_var,
        font=app.display_fonts["score"],
        bg="white",
        fg="black",
        anchor="center"
    )
    app.display_white_score.grid(
        row=4,
        column=0,
        rowspan=7,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.display_black_score = tk.Label(
        tab,
        textvariable=app.black_score_var,
        font=app.display_fonts["score"],
        bg="black",
        fg="white",
        anchor="center"
    )
    app.display_black_score.grid(
        row=4,
        column=6,
        rowspan=7,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Main countdown timer.
    app.display_timer_label = tk.Label(
        tab,
        textvariable=app.timer_var,
        font=app.display_fonts["timer"],
        bg="lightgrey",
        fg="black",
        anchor="center"
    )
    app.display_timer_label.grid(
        row=4,
        column=3,
        rowspan=7,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Referee time-out overlay.
    app.display_referee_timeout_timer_label = tk.Label(
        tab,
        textvariable=app.referee_timeout_timer_var,
        font=app.display_fonts["referee_timeout_timer"],
        bg="red",
        fg="white",
        anchor="center"
    )
    app.display_referee_timeout_timer_label.grid(
        row=10,
        column=3,
        columnspan=3,
        padx=0,
        pady=1,
        sticky="nsew"
    )
    app.display_referee_timeout_timer_label.grid_remove()
    def match_main_scoreboard_columns(event=None):
        """
        Copy the current nine calculated column widths from the main
        Scoreboard tab, scaled to fit the Display Window width.
        """
        try:
            source_tab = getattr(app, "scoreboard_tab", None)

            if (
                source_tab is None
                or not source_tab.winfo_exists()
                or not tab.winfo_exists()
            ):
                return

            source_tab.update_idletasks()
            tab.update_idletasks()

            source_widths = []

            for column in range(9):
                _, _, width, _ = source_tab.grid_bbox(
                    column,
                    0,
                    column,
                    10
                )
                source_widths.append(width)

            source_total = sum(source_widths)
            display_width = tab.winfo_width()

            if source_total <= 0 or display_width <= 0:
                return

            new_widths = []
            remaining_width = display_width

            for column, source_width in enumerate(source_widths):
                if column == 8:
                    width = max(1, remaining_width)
                else:
                    width = max(
                        1,
                        round(
                            display_width
                            * source_width
                            / source_total
                        )
                    )
                    remaining_width -= width

                new_widths.append(width)

            if (
                getattr(app, "_display_column_widths", None)
                == new_widths
            ):
                return

            app._display_column_widths = new_widths

            for column, width in enumerate(new_widths):
                tab.grid_columnconfigure(
                    column,
                    minsize=width,
                    weight=0,
                    uniform=""
                )

        except tk.TclError:
            pass
    app.display_window.bind(
        "<Configure>",
        app.scale_display_fonts
    )
    app.display_window.bind(
        "<Configure>",
        match_main_scoreboard_columns,
        add="+"
    )

    # Calculate dimensions only after widgets have been laid out.
    app.display_window.update_idletasks()
    match_main_scoreboard_columns()

    app.display_initial_width = max(
        app.display_window.winfo_width(),
        1200
    )

    app.scale_display_fonts(None)
    app.sync_display_widgets()

    def refresh_display_team_names():
        """Refresh names after CSV and tournament settings are ready."""
        try:
            if (
                not hasattr(app, "display_window")
                or app.display_window is None
                or not app.display_window.winfo_exists()
            ):
                return

            app.update_team_names_display()
            app.toggle_display_team_names()

        except tk.TclError:
            pass

    # Refresh immediately and again during startup, after the Tournament
    # List and selected game may have loaded.
    refresh_display_team_names()
    app.master.after(250, refresh_display_team_names)
    app.master.after(750, refresh_display_team_names)



def _get_monitor_geometries(app):
    """Return monitor work areas as dictionaries, preferring native OS APIs."""
    monitors = []

    # Windows: reliable per-monitor work areas and primary flag.
    try:
        import ctypes
        from ctypes import wintypes

        MONITORINFOF_PRIMARY = 1

        class MONITORINFOEXW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
                ("szDevice", wintypes.WCHAR * 32),
            ]

        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        )

        def callback(hmonitor, hdc, rect, data):
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(MONITORINFOEXW)
            if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                r = info.rcWork
                monitors.append({
                    "x": r.left,
                    "y": r.top,
                    "width": r.right - r.left,
                    "height": r.bottom - r.top,
                    "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                    "name": info.szDevice or "Windows display",
                })
            return 1

        ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback_type(callback), 0)
    except Exception:
        pass

    # Linux/X11: xrandr gives connected monitor geometry. Wayland may not expose it.
    if not monitors:
        try:
            import re
            import subprocess
            output = subprocess.check_output(
                ["xrandr", "--query"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            pattern = re.compile(
                r"^\S+ connected(?: primary)? (\d+)x(\d+)\+(-?\d+)\+(-?\d+)"
            )
            for line in output.splitlines():
                match = pattern.search(line)
                if not match:
                    continue
                width, height, x, y = map(int, match.groups())
                monitor_name = line.split()[0] if line.split() else "Linux display"
                monitors.append({
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "primary": " connected primary " in line,
                    "name": monitor_name,
                })
        except Exception:
            pass

    if not monitors:
        monitors = [{
            "x": 0,
            "y": 0,
            "width": app.master.winfo_screenwidth(),
            "height": app.master.winfo_screenheight(),
            "primary": True,
            "name": "Tk virtual desktop",
        }]

    # Keep the primary/operator screen first, then sort the external screens by position.
    monitors.sort(key=lambda m: (not m["primary"], m["x"], m["y"]))
    return monitors


def close_all_display_windows(app):
    windows = list(getattr(app, "display_windows", []))
    primary = getattr(app, "display_window", None)
    if primary is not None and primary not in windows:
        windows.append(primary)
    for window in windows:
        try:
            if window is not None and window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass
    app.display_windows = []
    app.simple_display_name_labels = []
    app.display_mirror_bundles = []
    app.display_window = None


def _place_window(window, monitor, aspect=None):
    x = monitor["x"]
    y = monitor["y"]
    width = monitor["width"]
    height = monitor["height"]

    if aspect:
        target = aspect[0] / aspect[1]
        available = width / max(height, 1)
        if available > target:
            fitted_width = int(height * target)
            x += (width - fitted_width) // 2
            width = fitted_width
        else:
            fitted_height = int(width / target)
            y += (height - fitted_height) // 2
            height = fitted_height

    window.geometry(f"{max(640, width)}x{max(360, height)}+{x}+{y}")


def _operator_monitor(app, monitors):
    try:
        root_x = app.master.winfo_rootx()
        root_y = app.master.winfo_rooty()
        for monitor in monitors:
            if (
                monitor["x"] <= root_x < monitor["x"] + monitor["width"]
                and monitor["y"] <= root_y < monitor["y"] + monitor["height"]
            ):
                return monitor
    except tk.TclError:
        pass
    return next((m for m in monitors if m["primary"]), monitors[0])


def _external_monitors(app, monitors):
    operator = _operator_monitor(app, monitors)
    return [m for m in monitors if m is not operator]


def _apply_operator_layout(app, monitor):
    aspect = (21, 9) if app.operator_layout_var.get() == "Widescreen" else (16, 9)
    _place_window(app.master, monitor, aspect=aspect)
    try:
        app.master.update_idletasks()
        app.initial_width = max(1, app.master.winfo_width())
        app.scale_fonts(None)
    except (tk.TclError, AttributeError):
        pass


def _create_full_mirror_window(app, title, monitor, aspect=(16, 9)):
    """Create a second full scoreboard window that mirrors the normal display."""
    window = tk.Toplevel(app.master)
    window.title(title)
    window.protocol("WM_DELETE_WINDOW", app._on_display_window_close)
    app.display_windows.append(window)
    _place_window(window, monitor, aspect=aspect)

    tab = ttk.Frame(window)
    tab.pack(fill="both", expand=True)
    for row in range(11):
        tab.grid_rowconfigure(row, weight=1)
    for column in range(9):
        tab.grid_columnconfigure(column, weight=1, uniform="mirror_cols")
    tab.grid_rowconfigure(2, minsize=58)
    tab.grid_rowconfigure(3, minsize=58)

    widgets = {}
    widgets["court"] = tk.Label(tab, textvariable=app.court_time_var, bg="lightgrey")
    widgets["court"].grid(row=0, column=0, columnspan=9, sticky="nsew", padx=1, pady=1)
    widgets["half"] = tk.Label(tab, textvariable=app.half_label_var, bg="lightcoral", font=("Arial", 36, "bold"))
    widgets["half"].grid(row=1, column=0, columnspan=9, sticky="nsew", padx=1, pady=1)
    widgets["white_colour"] = tk.Label(tab, textvariable=app.white_team_var, bg="white", fg="black", anchor="center")
    widgets["white_colour"].grid(row=2, column=0, columnspan=3, sticky="nsew", padx=1, pady=1)
    widgets["black_colour"] = tk.Label(tab, textvariable=app.black_team_var, bg="black", fg="white", anchor="center")
    widgets["black_colour"].grid(row=2, column=6, columnspan=3, sticky="nsew", padx=1, pady=1)

    penalty_area = tk.Frame(tab, bg="lightgrey")
    penalty_area.grid(row=2, column=3, columnspan=3, sticky="nsew", padx=1, pady=1)
    penalty_area.grid_columnconfigure(0, weight=1)
    penalty_area.grid_columnconfigure(1, weight=1)
    penalty_labels = [
        tk.Label(penalty_area, bg="lightgrey", fg="black", anchor="center")
        for _ in range(6)
    ]
    for index, label in enumerate(penalty_labels):
        label.grid(row=index % 3, column=index // 3, sticky="nsew")
        penalty_area.grid_rowconfigure(index % 3, weight=1)

    widgets["white_name"] = tk.Label(tab, bg="white", fg="black", anchor="center")
    widgets["white_name"].grid(row=3, column=0, columnspan=3, sticky="nsew", padx=1, pady=1)
    widgets["game"] = tk.Label(tab, textvariable=app.game_number_var, bg="lightgrey", fg="black", anchor="center")
    widgets["game"].grid(row=3, column=3, columnspan=3, sticky="nsew", padx=1, pady=1)
    widgets["black_name"] = tk.Label(tab, bg="black", fg="white", anchor="center")
    widgets["black_name"].grid(row=3, column=6, columnspan=3, sticky="nsew", padx=1, pady=1)
    widgets["white_score"] = tk.Label(tab, textvariable=app.white_score_var, bg="white", fg="black", anchor="center")
    widgets["white_score"].grid(row=4, column=0, rowspan=7, columnspan=3, sticky="nsew", padx=1, pady=1)
    widgets["timer"] = tk.Label(tab, textvariable=app.timer_var, bg="lightgrey", fg="black", anchor="center")
    widgets["timer"].grid(row=4, column=3, rowspan=7, columnspan=3, sticky="nsew", padx=1, pady=1)
    widgets["black_score"] = tk.Label(tab, textvariable=app.black_score_var, bg="black", fg="white", anchor="center")
    widgets["black_score"].grid(row=4, column=6, rowspan=7, columnspan=3, sticky="nsew", padx=1, pady=1)
    widgets["ref"] = tk.Label(tab, textvariable=app.referee_timeout_timer_var, bg="red", fg="white", anchor="center")
    widgets["ref"].grid(row=10, column=3, columnspan=3, sticky="nsew", pady=1)
    widgets["ref"].grid_remove()

    bundle = {"window": window, "widgets": widgets, "penalty_labels": penalty_labels}
    if not hasattr(app, "display_mirror_bundles"):
        app.display_mirror_bundles = []
    app.display_mirror_bundles.append(bundle)

    def refresh():
        try:
            if not window.winfo_exists():
                return
            show_names = app.show_display_team_names_var.get()
            white_name = app.white_team_var.get()
            black_name = app.black_team_var.get()
            if show_names:
                try:
                    white_name = app.white_team_name_widget.cget("text") or white_name
                    black_name = app.black_team_name_widget.cget("text") or black_name
                except (AttributeError, tk.TclError):
                    pass
            widgets["white_name"].config(text=white_name)
            widgets["black_name"].config(text=black_name)
            try:
                widgets["half"].config(bg=app.half_label.cget("bg"))
            except (AttributeError, tk.TclError):
                pass

            active = sorted(
                list(getattr(app.engine, "active_penalties", [])),
                key=lambda item: app._penalty_sort_key(item)
            )[:6]
            for index, label in enumerate(penalty_labels):
                if index < len(active):
                    label.config(text=display_manager.format_penalty_label(active[index]))
                else:
                    label.config(text="")

            try:
                if app.referee_timeout_timer_label.winfo_ismapped():
                    widgets["ref"].grid()
                else:
                    widgets["ref"].grid_remove()
            except (AttributeError, tk.TclError):
                pass
            window.after(250, refresh)
        except tk.TclError:
            pass

    def scale(event=None):
        h = max(360, tab.winfo_height())
        w = max(640, tab.winfo_width())
        widgets["court"].config(font=("Arial", max(18, int(h * 0.045))))
        widgets["half"].config(font=("Arial", max(20, int(h * 0.05)), "bold"))
        for key in ("white_colour", "black_colour", "white_name", "black_name"):
            widgets[key].config(font=("Arial", max(18, int(min(h * 0.045, w * 0.027))), "bold"))
        widgets["game"].config(font=("Arial", max(15, int(h * 0.03))))
        widgets["timer"].config(font=("Arial", max(50, int(min(h * 0.22, w * 0.105))), "bold"))
        widgets["white_score"].config(font=("Arial", max(90, int(min(h * 0.42, w * 0.19))), "bold"))
        widgets["black_score"].config(font=("Arial", max(90, int(min(h * 0.42, w * 0.19))), "bold"))
        widgets["ref"].config(font=("Arial", max(16, int(h * 0.03)), "bold"))
        for label in penalty_labels:
            label.config(font=("Arial", max(11, int(h * 0.018)), "bold"))

    window.bind("<Configure>", scale)
    refresh()
    scale()
    return window


def apply_screen_configuration(app):
    """Apply the operator aspect and create the selected external display windows."""
    monitors = _get_monitor_geometries(app)
    operator = _operator_monitor(app, monitors)
    _apply_operator_layout(app, operator)

    close_all_display_windows(app)
    external = _external_monitors(app, monitors)
    
    layout = app.display_layout_var.get() or "Single Standard"
    widescreen = "Widescreen" in layout
    dual = layout.startswith("Dual")
    aspect = (21, 9) if widescreen else (16, 9)
    
    #
    # SINGLE MONITOR
    #
    if not external:
    
        create_display_window(app)
    
        # Put the display beside the main window for development/testing.
        try:
            app.master.update_idletasks()
    
            root_x = app.master.winfo_x()
            root_y = app.master.winfo_y()
            root_w = app.master.winfo_width()
    
            display_x = root_x + root_w + 20
            display_y = root_y
    
            screen_w = app.master.winfo_screenwidth()
    
            # If there isn't enough room on the right,
            # place it on the left.
            if display_x + 900 > screen_w:
                display_x = max(0, root_x - 920)
    
            app.display_window.geometry(
                f"900x600+{display_x}+{display_y}"
            )
    
        except Exception:
            pass
    
        return
    
    #
    # MULTIPLE MONITORS
    #
    
    create_display_window(app)
    _place_window(app.display_window, external[0], aspect=aspect)
    
    if dual and len(external) >= 2:
        _create_full_mirror_window(
            app,
            "Display Window 2",
            external[1],
            aspect=aspect,
        )

    layout = app.display_layout_var.get() or "Single Standard"
    widescreen = "Widescreen" in layout
    dual = layout.startswith("Dual")
    aspect = (21, 9) if widescreen else (16, 9)

    create_display_window(app)
    _place_window(app.display_window, external[0], aspect=aspect)

    if dual and len(external) >= 2:
        _create_full_mirror_window(
            app,
            "Display Window 2",
            external[1],
            aspect=aspect,
        )


def auto_detect_and_apply(app):
    """Choose layouts from detected monitor aspect ratios and apply them."""
    monitors = _get_monitor_geometries(app)
    operator = _operator_monitor(app, monitors)
    external = _external_monitors(app, monitors)

    operator_ratio = operator["width"] / max(operator["height"], 1)
    app.operator_layout_var.set("Widescreen" if operator_ratio >= 2.05 else "Standard")

    if external:
        use_wide = all(
            monitor["width"] / max(monitor["height"], 1) >= 2.05
            for monitor in external[:2]
        )
        prefix = "Dual" if len(external) >= 2 else "Single"
        app.display_layout_var.set(f"{prefix} {'Widescreen' if use_wide else 'Standard'}")

    # Update the mutually-exclusive checkboxes if the Screens tab exists.
    try:
        app.operator_standard_check_var.set(app.operator_layout_var.get() == "Standard")
        app.operator_widescreen_check_var.set(app.operator_layout_var.get() == "Widescreen")
        for option, var in app.display_layout_check_vars.items():
            var.set(option == app.display_layout_var.get())
    except (AttributeError, tk.TclError):
        pass

    apply_screen_configuration(app)
    update_detected_screens_text(app)



def describe_detected_screens(app):
    """Return a readable summary of the currently detected screens."""
    monitors = _get_monitor_geometries(app)
    operator = _operator_monitor(app, monitors)
    lines = []
    for index, monitor in enumerate(monitors, start=1):
        role = "Operator" if monitor is operator else "Display"
        ratio = monitor["width"] / max(monitor["height"], 1)
        aspect = "21:9 widescreen" if ratio >= 2.05 else "16:9 standard"
        name = monitor.get("name", f"Screen {index}")
        primary = ", primary" if monitor.get("primary") else ""
        lines.append(
            f"Screen {index}: {name} — {monitor['width']} × {monitor['height']} "
            f"({role}, {aspect}{primary})"
        )
    return "\n".join(lines) if lines else "No screens detected."


def update_detected_screens_text(app):
    """Refresh the detected-screen text shown on the Screens tab."""
    text = describe_detected_screens(app)
    try:
        app.detected_screens_var.set(text)
    except (AttributeError, tk.TclError):
        pass
    return text


def test_displays(app, duration_ms=8000):
    """Identify every detected screen with a temporary labelled test window."""
    monitors = _get_monitor_geometries(app)
    operator = _operator_monitor(app, monitors)
    update_detected_screens_text(app)

    old_windows = getattr(app, "display_test_windows", [])
    for window in old_windows:
        try:
            if window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass

    windows = []

    def close_tests(event=None):
        for test_window in list(windows):
            try:
                if test_window.winfo_exists():
                    test_window.destroy()
            except tk.TclError:
                pass
        app.display_test_windows = []

    for index, monitor in enumerate(monitors, start=1):
        role = "OPERATOR SCREEN" if monitor is operator else "DISPLAY SCREEN"
        name = monitor.get("name", f"Screen {index}")
        window = tk.Toplevel(app.master)
        window.title(f"Screen Test {index}")
        window.configure(bg="black")
        window.overrideredirect(True)
        window.geometry(
            f"{monitor['width']}x{monitor['height']}+{monitor['x']}+{monitor['y']}"
        )
        window.attributes("-topmost", True)

        frame = tk.Frame(window, bg="black", highlightbackground="white", highlightthickness=8)
        frame.pack(fill="both", expand=True)
        tk.Label(
            frame,
            text=f"SCREEN {index}",
            bg="black",
            fg="white",
            font=("Arial", 72, "bold"),
        ).pack(expand=True, pady=(80, 10))
        tk.Label(
            frame,
            text=role,
            bg="black",
            fg="white",
            font=("Arial", 38, "bold"),
        ).pack(pady=10)
        tk.Label(
            frame,
            text=f"{name}\n{monitor['width']} × {monitor['height']}\n"
                 "Click anywhere or press Esc to close",
            bg="black",
            fg="white",
            font=("Arial", 24),
            justify="center",
        ).pack(expand=True, pady=(10, 80))

        window.bind("<Button-1>", close_tests)
        window.bind("<Escape>", close_tests)
        window.after(duration_ms, close_tests)
        windows.append(window)

    app.display_test_windows = windows
