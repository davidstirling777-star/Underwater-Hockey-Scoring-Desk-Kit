import tkinter as tk
from tkinter import ttk

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
    """Return monitor work areas as (x, y, width, height), using Win32 when available."""
    geometries = []
    try:
        import ctypes
        from ctypes import wintypes

        MONITORINFOF_PRIMARY = 1

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        callback_type = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        )

        def callback(hmonitor, hdc, rect, data):
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if ctypes.windll.user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                r = info.rcWork
                geometries.append((r.left, r.top, r.right-r.left, r.bottom-r.top, bool(info.dwFlags & MONITORINFOF_PRIMARY)))
            return 1

        ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback_type(callback), 0)
    except Exception:
        pass

    if not geometries:
        geometries = [(0, 0, app.master.winfo_screenwidth(), app.master.winfo_screenheight(), True)]

    # Put non-primary screens first because external windows should prefer them.
    geometries.sort(key=lambda item: item[4])
    return [(x, y, w, h) for x, y, w, h, _ in geometries]


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
    app.display_window = None


def _place_window(window, geometry, fallback_size=None):
    x, y, width, height = geometry
    if fallback_size:
        fw, fh = fallback_size
        width = min(width, fw)
        height = min(height, fh)
    window.geometry(f"{width}x{height}+{x}+{y}")


def _create_simple_public_window(app, title, geometry, standard=False):
    """Create a lightweight display that binds directly to the live Tk variables."""
    window = tk.Toplevel(app.master)
    window.title(title)
    window.configure(bg="lightgrey")
    window.protocol("WM_DELETE_WINDOW", app._on_display_window_close)
    app.display_windows.append(window)
    _place_window(window, geometry)

    root = tk.Frame(window, bg="lightgrey")
    root.pack(fill="both", expand=True)
    for col in range(3):
        root.grid_columnconfigure(col, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=2)
    root.grid_rowconfigure(2, weight=7)

    period = tk.Label(root, textvariable=app.half_label_var, bg="lightcoral", font=("Arial", 30, "bold"))
    period.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=1, pady=1)

    white_name = tk.Label(root, bg="white", fg="black", font=("Arial", 26, "bold"))
    white_name.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
    timer = tk.Label(root, textvariable=app.timer_var, bg="lightgrey", fg="black", font=("Arial", 72, "bold"))
    timer.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)
    black_name = tk.Label(root, bg="black", fg="white", font=("Arial", 26, "bold"))
    black_name.grid(row=1, column=2, sticky="nsew", padx=1, pady=1)
    if not hasattr(app, "simple_display_name_labels"):
        app.simple_display_name_labels = []
    app.simple_display_name_labels.append((white_name, black_name))

    white_score = tk.Label(root, textvariable=app.white_score_var, bg="white", fg="black", font=("Arial", 180, "bold"))
    white_score.grid(row=2, column=0, sticky="nsew", padx=1, pady=1)
    centre = tk.Label(root, textvariable=app.game_number_var, bg="lightgrey", fg="black", font=("Arial", 28, "bold"))
    centre.grid(row=2, column=1, sticky="nsew", padx=1, pady=1)
    black_score = tk.Label(root, textvariable=app.black_score_var, bg="black", fg="white", font=("Arial", 180, "bold"))
    black_score.grid(row=2, column=2, sticky="nsew", padx=1, pady=1)

    def refresh_names(*_):
        if app.show_display_team_names_var.get():
            white_name.config(text=getattr(app, "white_team_name_widget", white_name).cget("text") or app.white_team_var.get())
            black_name.config(text=getattr(app, "black_team_name_widget", black_name).cget("text") or app.black_team_var.get())
        else:
            white_name.config(text=app.white_team_var.get())
            black_name.config(text=app.black_team_var.get())

    def scale(event=None):
        h = max(400, root.winfo_height())
        w = max(700, root.winfo_width())
        timer.config(font=("Arial", max(32, int(min(h*0.13, w*0.07))), "bold"))
        white_score.config(font=("Arial", max(80, int(min(h*0.36, w*0.18))), "bold"))
        black_score.config(font=("Arial", max(80, int(min(h*0.36, w*0.18))), "bold"))
        white_name.config(font=("Arial", max(18, int(min(h*0.055, w*0.025))), "bold"))
        black_name.config(font=("Arial", max(18, int(min(h*0.055, w*0.025))), "bold"))

    window.bind("<Configure>", scale)
    refresh_names()
    window.after(250, refresh_names)
    window.after(750, refresh_names)
    return window


def _resolve_auto_profile(app, monitors):
    # The main application normally occupies one screen. Remaining screens are external.
    external_count = max(0, len(monitors) - 1)
    if external_count >= 2:
        return "Public Dual"
    if external_count == 1:
        return "Public Single"
    return "Single Standard"


def apply_display_profile(app):
    """Create the windows for the selected display profile."""
    close_all_display_windows(app)
    monitors = _get_monitor_geometries(app)
    profile = app.display_profile_var.get() or "Single Standard"
    effective_profile = _resolve_auto_profile(app, monitors) if profile == "Auto" else profile
    app.active_display_profile = effective_profile

    # Prefer non-primary monitors; if there are not enough, reuse the available work area.
    targets = monitors if monitors else [(0, 0, 1200, 800)]

    if effective_profile in ("Single Standard", "Operator Ultrawide"):
        create_display_window(app)
        target = targets[0]
        if effective_profile == "Operator Ultrawide":
            _place_window(app.display_window, target, fallback_size=(2560, 1080))
        else:
            _place_window(app.display_window, target)
        return

    if effective_profile == "Dual Standard":
        create_display_window(app)
        _place_window(app.display_window, targets[0])
        second_target = targets[1] if len(targets) > 1 else targets[0]
        _create_simple_public_window(app, "Display Window 2", second_target, standard=True)
        return

    if effective_profile == "Public Single":
        app.display_window = _create_simple_public_window(app, "Public Display", targets[0])
        return

    if effective_profile == "Public Dual":
        app.display_window = _create_simple_public_window(app, "Public Display 1", targets[0])
        second_target = targets[1] if len(targets) > 1 else targets[0]
        _create_simple_public_window(app, "Public Display 2", second_target)
        return

    # Defensive fallback.
    create_display_window(app)
    _place_window(app.display_window, targets[0])
