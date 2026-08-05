import tkinter as tk
import tkinter.font as tkfont
import display_manager

DISPLAY_GREY = "#d3d3d3"

def _largest_fitting_font_size(
    widget,
    sample_text,
    font_options,
    width_fraction=0.95,
    height_fraction=0.82,
    minimum=20,
    maximum=420
):
    """
    Return the largest font size that fits within a widget.

    sample_text should represent the widest expected value. For the
    countdown timer, '88:88' is wider than ordinary timer values.
    """
    try:
        available_width = max(
            1,
            int(widget.winfo_width() * width_fraction)
        )
        available_height = max(
            1,
            int(widget.winfo_height() * height_fraction)
        )

        options = dict(font_options)
        options["size"] = minimum

        probe_font = tkfont.Font(
            root=widget,
            **options
        )

        low = minimum
        high = maximum
        best = minimum

        while low <= high:
            candidate = (low + high) // 2
            probe_font.configure(size=candidate)

            text_width = probe_font.measure(sample_text)
            text_height = probe_font.metrics("linespace")

            if (
                text_width <= available_width
                and text_height <= available_height
            ):
                best = candidate
                low = candidate + 1
            else:
                high = candidate - 1

        return best

    except (
        tk.TclError,
        TypeError,
        ValueError
    ):
        return minimum


def _format_presentation_timer_text(raw_text):
    """
    Format the presentation timer without unnecessary leading zeros.

    Examples:
        14:30 -> 14:30
        03:20 -> 3:20
        00:59 -> 59
        00:02 -> 2
        00:00 -> 0
    """
    text = str(raw_text).strip()

    if not text:
        return "0"

    parts = text.split(":")

    try:
        numeric_parts = [
            int(part)
            for part in parts
        ]
    except ValueError:
        # Preserve unexpected non-time text rather than hiding it.
        return text

    if len(numeric_parts) == 3:
        hours, minutes, seconds = numeric_parts
        total_seconds = (
            hours * 3600
            + minutes * 60
            + seconds
        )

    elif len(numeric_parts) == 2:
        minutes, seconds = numeric_parts
        total_seconds = (
            minutes * 60
            + seconds
        )

    elif len(numeric_parts) == 1:
        total_seconds = numeric_parts[0]

    else:
        return text

    total_seconds = max(0, total_seconds)
    total_minutes, seconds = divmod(
        total_seconds,
        60
    )

    if total_minutes > 0:
        return f"{total_minutes}:{seconds:02d}"

    return str(seconds)


def _presentation_timer_fit_sample(display_text):
    """
    Return a stable worst-case sample for the current timer format.

    The fitting size changes only at:
        10:00
        1:00

    It does not recalculate to a different size every second.
    """
    text = str(display_text).strip()

    if ":" not in text:
        return "88"

    minute_text = text.split(":", 1)[0]

    if len(minute_text) >= 2:
        return "88:88"

    return "8:88"


def _ensure_presentation_timer_var(app):
    """Create and initialise the presentation-only timer variable."""
    presentation_timer_var = getattr(
        app,
        "presentation_timer_var",
        None
    )

    if presentation_timer_var is None:
        presentation_timer_var = tk.StringVar(
            master=app.master
        )
        app.presentation_timer_var = (
            presentation_timer_var
        )

    presentation_timer_var.set(
        _format_presentation_timer_text(
            app.timer_var.get()
        )
    )

    return presentation_timer_var


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

    # Use a Tk frame so the background colour is fully controlled.
    # Disabling grid propagation prevents team-name text from changing
    # the requested size of the presentation layout.
    tab = tk.Frame(
        app.display_window,
        bg=DISPLAY_GREY,
        bd=0,
        highlightthickness=0
    )
    tab.pack(fill="both", expand=True)
    tab.grid_propagate(False)

    # Presentation layout:
    #
    # Row 0: White / penalties or Next Game / Black
    # Row 1: White team name / game number / Black team name
    # Row 2: Full-width period banner
    # Rows 3-10: White score / timer / Black score
    #
    # Twelve equal grid columns allow:
    #     4 + 4 + 4 = three equal top blocks
    #     3 + 6 + 3 = 25% score / 50% timer / 25% score
    for row in range(11):
        tab.grid_rowconfigure(row, weight=1)

    for column in range(12):
        tab.grid_columnconfigure(
            column,
            weight=1,
            minsize=1,
            uniform="presentation_columns"
        )

    # Keep the three information rows stable.
    tab.grid_rowconfigure(0, minsize=58)
    tab.grid_rowconfigure(1, minsize=58)
    tab.grid_rowconfigure(2, minsize=68)

    # Current period label.
    app.display_half_label = tk.Label(
        tab,
        textvariable=app.half_label_var,
        font=app.display_fonts["half"],
        bg="lightcoral"
    )
    app.display_half_label.grid(
        row=2,
        column=0,
        columnspan=12,
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
        row=0,
        column=0,
        columnspan=4,
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
        row=0,
        column=8,
        columnspan=4,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Fixed centre area for penalties / Next Game banner.
    app.display_penalty_area_frame = tk.Frame(
        tab,
        bg=DISPLAY_GREY,
        bd=0,
        highlightthickness=0
    )
    
    app.display_penalty_area_frame.grid(
        row=0,
        column=4,
        columnspan=4,
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

    # Keep the penalty-grid background consistent with all other
    # presentation centre panels.
    try:
        app.display_penalty_grid_frame.configure(
            bg=DISPLAY_GREY
        )
    except tk.TclError:
        pass

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
        row=1,
        column=0,
        columnspan=4,
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
        row=1,
        column=8,
        columnspan=4,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Current game number.
    app.display_game_label = tk.Label(
        tab,
        textvariable=app.game_number_var,
        font=app.display_fonts["game_no"],
        bg=DISPLAY_GREY,
        fg="black",
        anchor="center",
        width=1,
        bd=0,
        highlightthickness=0
    )
    app.display_game_label.grid(
        row=1,
        column=4,
        columnspan=4,
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
        anchor="center",
        width=1
    )
    app.display_white_score.grid(
        row=3,
        column=0,
        rowspan=8,
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
        anchor="center",
        width=1
    )
    app.display_black_score.grid(
        row=3,
        column=9,
        rowspan=8,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Presentation-only timer text.
    #
    # This removes unnecessary leading zeros without changing
    # the timer shown in the operator window.
    presentation_timer_var = (
        _ensure_presentation_timer_var(app)
    )

    # Fixed timer panel.
    #
    # The panel is managed by the presentation grid. The timer label
    # is placed inside the panel, so changing its font size cannot
    # resize any rows, columns, scores or neighbouring widgets.
    app.display_timer_panel = tk.Frame(
        tab,
        bg=DISPLAY_GREY,
        bd=0,
        highlightthickness=0
    )
    app.display_timer_panel.grid(
        row=3,
        column=3,
        rowspan=8,
        columnspan=6,
        padx=1,
        pady=1,
        sticky="nsew"
    )
    app.display_timer_panel.grid_propagate(False)

    # Give the presentation timer its own font object. Changing this
    # font cannot affect the operator timer or any other display widget.
    presentation_timer_font_options = (
        app.display_fonts["timer"].actual()
    )
    presentation_timer_font_options["size"] = 40

    presentation_timer_font = tkfont.Font(
        root=app.display_window,
        **presentation_timer_font_options
    )

    app.display_timer_label = tk.Label(
        app.display_timer_panel,
        textvariable=presentation_timer_var,
        font=presentation_timer_font,
        bg=DISPLAY_GREY,
        fg="black",
        anchor="center",
        bd=0,
        highlightthickness=0
    )
    app.display_timer_label.place(
        x=0,
        y=0,
        relwidth=1.0,
        relheight=1.0
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
        columnspan=6,
        padx=0,
        pady=1,
        sticky="nsew"
    )
    app.display_referee_timeout_timer_label.grid_remove()

    # Make every presentation label geometry-neutral.
    #
    # The grid controls the sizes. Changing team names, scores,
    # game numbers or timer text must not alter the grid widths.
    fixed_size_widgets = (
        app.display_half_label,
        app.display_white_label,
        app.display_black_label,
        app.display_white_team_name_widget,
        app.display_game_label,
        app.display_black_team_name_widget,
        app.display_white_score,
        app.display_black_score,
        app.display_referee_timeout_timer_label,
    )

    for widget in fixed_size_widgets:
        widget.configure(width=1)

    last_presentation_size = None

    def scale_presentation_fonts(
        event=None,
        force=False
    ):
        """
        Scale fonts specifically for the presentation layout.

        The timer is intentionally larger than either score.
        Font sizes only change when the actual window dimensions change.
        """
        nonlocal last_presentation_size

        try:
            width = max(1, tab.winfo_width())
            height = max(1, tab.winfo_height())

            # Ignore temporary geometries seen while the window and
            # its grid cells are still being constructed.
            if width < 100 or height < 100:
                return

            timer_panel_width = (
                app.display_timer_panel.winfo_width()
            )
            timer_panel_height = (
                app.display_timer_panel.winfo_height()
            )

            # The outer frame can reach its final dimensions before
            # the timer label receives its final grid allocation.
            # Do not cache a scale result based on a tiny timer cell.
            if (
                timer_panel_width < 100
                or timer_panel_height < 100
            ):
                return

            current_size = (
                width,
                height,
                timer_panel_width,
                timer_panel_height
            )

            # Text refreshes can produce Configure events even when
            # the actual presentation size has not changed.
            if (
                not force
                and current_size == last_presentation_size
            ):
                return

            last_presentation_size = current_size

            scale_factor = min(
                width / 1200.0,
                height / 800.0
            )
            scale_factor = max(
                0.55,
                min(2.0, scale_factor)
            )

            # These presentation fonts continue to scale from the
            # overall window dimensions.
            base_sizes = {
                "half": 40,
                "team": 30,
                "game_no": 22,
                "score": 145,

                # Preserve the existing referee-timeout scale.
                "referee_timeout_timer": 24,
            }

            for font_name, base_size in base_sizes.items():
                display_font = app.display_fonts.get(font_name)

                if display_font is not None:
                    display_font.configure(
                        size=max(
                            10,
                            round(base_size * scale_factor)
                        )
                    )

            # Fit the timer independently to its actual 50%-wide panel.
            # This allows it to become much larger on a full display
            # while still fitting in the 900x600 development window.
            timer_sample = (
                _presentation_timer_fit_sample(
                    presentation_timer_var.get()
                )
            )

            timer_size = _largest_fitting_font_size(
                widget=app.display_timer_panel,
                sample_text=timer_sample,
                font_options=presentation_timer_font.actual(),
                width_fraction=0.95,
                height_fraction=0.82,
                minimum=40,
                maximum=420
            )

            presentation_timer_font.configure(
                size=timer_size
            )

        except (
            tk.TclError,
            AttributeError,
            RuntimeError
        ):
            pass

    last_timer_fit_sample = None

    def refresh_presentation_timer():
        """
        Keep the presentation timer synchronised with app.timer_var.

        Font fitting is forced only when the timer changes between:
            two-digit minutes,
            one-digit minutes,
            seconds only.
        """
        nonlocal last_timer_fit_sample

        try:
            if (
                app.display_window is None
                or not app.display_window.winfo_exists()
            ):
                return

            formatted_text = (
                _format_presentation_timer_text(
                    app.timer_var.get()
                )
            )

            fit_sample = (
                _presentation_timer_fit_sample(
                    formatted_text
                )
            )

            if (
                presentation_timer_var.get()
                != formatted_text
            ):
                presentation_timer_var.set(
                    formatted_text
                )

            if fit_sample != last_timer_fit_sample:
                last_timer_fit_sample = fit_sample

                app.display_window.after_idle(
                    lambda: scale_presentation_fonts(
                        force=True
                    )
                )

            app.display_window.after(
                100,
                refresh_presentation_timer
            )

        except (
            tk.TclError,
            AttributeError,
            RuntimeError
        ):
            pass

    app.display_window.bind(
        "<Configure>",
        scale_presentation_fonts
    )

    # Calculate dimensions only after widgets have been laid out.
    app.display_window.update_idletasks()

    app.display_initial_width = max(
        app.display_window.winfo_width(),
        1200
    )

    app.sync_display_widgets()
    refresh_presentation_timer()

    def force_presentation_rescale():
        """
        Refit the presentation after Tk has finished allocating
        the final grid-cell dimensions.
        """
        try:
            if (
                app.display_window is not None
                and app.display_window.winfo_exists()
            ):
                app.display_window.update_idletasks()

                scale_presentation_fonts(
                    force=True
                )

        except (
            tk.TclError,
            AttributeError,
            RuntimeError
        ):
            pass

    # The first call handles normal creation. The delayed calls cover
    # final monitor placement and later startup data refreshes.
    force_presentation_rescale()

    app.display_window.after_idle(
        force_presentation_rescale
    )
    app.display_window.after(
        100,
        force_presentation_rescale
    )
    app.display_window.after(
        300,
        force_presentation_rescale
    )
    app.display_window.after(
        800,
        force_presentation_rescale
    )

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

    tab = tk.Frame(
        window,
        bg=DISPLAY_GREY,
        bd=0,
        highlightthickness=0
    )
    tab.pack(fill="both", expand=True)
    tab.grid_propagate(False)

    for row in range(11):
        tab.grid_rowconfigure(row, weight=1)

    for column in range(12):
        tab.grid_columnconfigure(
            column,
            weight=1,
            minsize=1,
            uniform="mirror_presentation_columns"
        )

    tab.grid_rowconfigure(0, minsize=58)
    tab.grid_rowconfigure(1, minsize=58)
    tab.grid_rowconfigure(2, minsize=68)

    widgets = {}

    # White / Black colour labels.
    widgets["white_colour"] = tk.Label(
        tab,
        textvariable=app.white_team_var,
        bg="white",
        fg="black",
        anchor="center"
    )
    widgets["white_colour"].grid(
        row=0,
        column=0,
        columnspan=4,
        sticky="nsew",
        padx=1,
        pady=1
    )

    widgets["black_colour"] = tk.Label(
        tab,
        textvariable=app.black_team_var,
        bg="black",
        fg="white",
        anchor="center"
    )
    widgets["black_colour"].grid(
        row=0,
        column=8,
        columnspan=4,
        sticky="nsew",
        padx=1,
        pady=1
    )

    # Penalties / Next Game centre block.
    penalty_area = tk.Frame(
        tab,
        bg=DISPLAY_GREY,
        bd=0,
        highlightthickness=0
    )
    penalty_area.grid(
        row=0,
        column=4,
        columnspan=4,
        sticky="nsew",
        padx=1,
        pady=1
    )
    penalty_area.grid_columnconfigure(0, weight=1)
    penalty_area.grid_columnconfigure(1, weight=1)
    penalty_area.grid_propagate(False)

    penalty_labels = [
        tk.Label(
            penalty_area,
            bg=DISPLAY_GREY,
            fg="black",
            anchor="center"
        )
        for _ in range(6)
    ]

    for index, label in enumerate(penalty_labels):
        label.grid(
            row=index % 3,
            column=index // 3,
            sticky="nsew"
        )
        penalty_area.grid_rowconfigure(
            index % 3,
            weight=1
        )

    # Team names and game number.
    widgets["white_name"] = tk.Label(
        tab,
        bg="white",
        fg="black",
        anchor="center"
    )
    widgets["white_name"].grid(
        row=1,
        column=0,
        columnspan=4,
        sticky="nsew",
        padx=1,
        pady=1
    )

    widgets["game"] = tk.Label(
        tab,
        textvariable=app.game_number_var,
        bg=DISPLAY_GREY,
        fg="black",
        anchor="center",
        width=1,
        bd=0,
        highlightthickness=0
    )
    widgets["game"].grid(
        row=1,
        column=4,
        columnspan=4,
        sticky="nsew",
        padx=1,
        pady=1
    )

    widgets["black_name"] = tk.Label(
        tab,
        bg="black",
        fg="white",
        anchor="center"
    )
    widgets["black_name"].grid(
        row=1,
        column=8,
        columnspan=4,
        sticky="nsew",
        padx=1,
        pady=1
    )

    # Full-width Period banner.
    widgets["half"] = tk.Label(
        tab,
        textvariable=app.half_label_var,
        bg="lightcoral",
        font=("Arial", 36, "bold")
    )
    widgets["half"].grid(
        row=2,
        column=0,
        columnspan=12,
        sticky="nsew",
        padx=1,
        pady=1
    )

    # Scores and timer.
    widgets["white_score"] = tk.Label(
        tab,
        textvariable=app.white_score_var,
        bg="white",
        fg="black",
        anchor="center",
        width=1
    )
    widgets["white_score"].grid(
        row=3,
        column=0,
        rowspan=8,
        columnspan=3,
        sticky="nsew",
        padx=1,
        pady=1
    )

    presentation_timer_var = (
        _ensure_presentation_timer_var(app)
    )

    # Fixed centre panel for the mirrored timer.
    widgets["timer_panel"] = tk.Frame(
        tab,
        bg=DISPLAY_GREY,
        bd=0,
        highlightthickness=0
    )
    widgets["timer_panel"].grid(
        row=3,
        column=3,
        rowspan=8,
        columnspan=6,
        sticky="nsew",
        padx=1,
        pady=1
    )
    widgets["timer_panel"].grid_propagate(False)

    mirror_timer_font = tkfont.Font(
        root=window,
        family="Arial",
        size=40,
        weight="bold"
    )

    widgets["timer"] = tk.Label(
        widgets["timer_panel"],
        textvariable=presentation_timer_var,
        font=mirror_timer_font,
        bg=DISPLAY_GREY,
        fg="black",
        anchor="center",
        bd=0,
        highlightthickness=0
    )
    widgets["timer"].place(
        x=0,
        y=0,
        relwidth=1.0,
        relheight=1.0
    )

    widgets["black_score"] = tk.Label(
        tab,
        textvariable=app.black_score_var,
        bg="black",
        fg="white",
        anchor="center",
        width=1
    )
    widgets["black_score"].grid(
        row=3,
        column=9,
        rowspan=8,
        columnspan=3,
        sticky="nsew",
        padx=1,
        pady=1
    )

    # Referee timeout overlay.
    widgets["ref"] = tk.Label(
        tab,
        textvariable=app.referee_timeout_timer_var,
        bg="red",
        fg="white",
        anchor="center"
    )
    widgets["ref"].grid(
        row=10,
        column=3,
        columnspan=6,
        sticky="nsew",
        pady=1
    )
    widgets["ref"].grid_remove()
    
    # Prevent mirrored-display text from changing panel widths.
    for key in (
        "white_colour",
        "black_colour",
        "white_name",
        "game",
        "black_name",
        "half",
        "white_score",
        "black_score",
        "ref",
    ):
        widgets[key].configure(width=1)

    bundle = {"window": window, "widgets": widgets, "penalty_labels": penalty_labels}
    if not hasattr(app, "display_mirror_bundles"):
        app.display_mirror_bundles = []
    app.display_mirror_bundles.append(bundle)

    last_mirror_timer_sample = None

    def refresh():
        nonlocal last_mirror_timer_sample

        try:
            if not window.winfo_exists():
                return
            use_tournament_list = True

            try:
                if hasattr(
                    app,
                    "use_tournament_list_var"
                ):
                    use_tournament_list = bool(
                        app.use_tournament_list_var.get()
                    )

            except tk.TclError:
                use_tournament_list = True

            show_names = (
                use_tournament_list
                and bool(
                    app.show_display_team_names_var.get()
                )
            )

            if not use_tournament_list:
                white_name = ""
                black_name = ""

            elif show_names:
                try:
                    white_name = (
                        app.white_team_name_widget.cget(
                            "text"
                        )
                        or ""
                    )
                    black_name = (
                        app.black_team_name_widget.cget(
                            "text"
                        )
                        or ""
                    )

                except (
                    AttributeError,
                    tk.TclError
                ):
                    white_name = ""
                    black_name = ""

            else:
                # Preserve the existing mirror behaviour when the
                # Tournament List is enabled but Show Team Names is off.
                white_name = app.white_team_var.get()
                black_name = app.black_team_var.get()
            widgets["white_name"].config(
                text=white_name
            )
            widgets["black_name"].config(
                text=black_name
            )

            formatted_timer = (
                _format_presentation_timer_text(
                    app.timer_var.get()
                )
            )

            if (
                presentation_timer_var.get()
                != formatted_timer
            ):
                presentation_timer_var.set(
                    formatted_timer
                )

            current_timer_sample = (
                _presentation_timer_fit_sample(
                    formatted_timer
                )
            )

            if (
                current_timer_sample
                != last_mirror_timer_sample
            ):
                last_mirror_timer_sample = (
                    current_timer_sample
                )

                window.after_idle(
                    lambda: scale(force=True)
                )
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

    last_mirror_size = None

    def scale(
        event=None,
        force=False
    ):
        """Scale mirrored presentation fonts only when needed."""
        nonlocal last_mirror_size

        try:
            width = max(1, tab.winfo_width())
            height = max(1, tab.winfo_height())

            if width < 100 or height < 100:
                return

            timer_panel_width = (
                widgets["timer_panel"].winfo_width()
            )
            timer_panel_height = (
                widgets["timer_panel"].winfo_height()
            )

            if (
                timer_panel_width < 100
                or timer_panel_height < 100
            ):
                return

            current_size = (
                width,
                height,
                timer_panel_width,
                timer_panel_height
            )

            if (
                not force
                and current_size == last_mirror_size
            ):
                return

            last_mirror_size = current_size

            scale_factor = min(
                width / 1200.0,
                height / 800.0
            )
            scale_factor = max(
                0.55,
                min(2.0, scale_factor)
            )

            def scaled_size(base_size):
                return max(
                    10,
                    round(base_size * scale_factor)
                )

            widgets["half"].config(
                font=(
                    "Arial",
                    scaled_size(40),
                    "bold"
                )
            )

            for key in (
                "white_colour",
                "black_colour",
                "white_name",
                "black_name"
            ):
                widgets[key].config(
                    font=(
                        "Arial",
                        scaled_size(30),
                        "bold"
                    )
                )

            widgets["game"].config(
                font=(
                    "Arial",
                    scaled_size(22)
                )
            )

            # Fit the timer independently to its actual centre panel.
            mirror_timer_sample = (
                _presentation_timer_fit_sample(
                    presentation_timer_var.get()
                )
            )

            mirror_timer_size = (
                _largest_fitting_font_size(
                    widget=widgets["timer_panel"],
                    sample_text=mirror_timer_sample,
                    font_options=mirror_timer_font.actual(),
                    width_fraction=0.95,
                    height_fraction=0.82,
                    minimum=40,
                    maximum=420
                )
            )

            mirror_timer_font.configure(
                size=mirror_timer_size
            )

            widgets["white_score"].config(
                font=(
                    "Arial",
                    scaled_size(145),
                    "bold"
                )
            )

            widgets["black_score"].config(
                font=(
                    "Arial",
                    scaled_size(145),
                    "bold"
                )
            )

            widgets["ref"].config(
                font=(
                    "Arial",
                    scaled_size(24),
                    "bold"
                )
            )

            for label in penalty_labels:
                label.config(
                    font=(
                        "Arial",
                        max(9, scaled_size(11)),
                        "bold"
                    )
                )

        except (
            tk.TclError,
            AttributeError,
            RuntimeError
        ):
            pass

    window.bind(
        "<Configure>",
        scale
    )

    def force_mirror_rescale():
        try:
            if window.winfo_exists():
                window.update_idletasks()
                scale(force=True)

        except (
            tk.TclError,
            RuntimeError
        ):
            pass

    refresh()
    force_mirror_rescale()

    window.after_idle(
        force_mirror_rescale
    )
    window.after(
        100,
        force_mirror_rescale
    )
    window.after(
        300,
        force_mirror_rescale
    )

    return window


def apply_screen_configuration(app):
    """Apply the operator aspect and create the selected display windows."""
    monitors = _get_monitor_geometries(app)
    operator = _operator_monitor(app, monitors)
    _apply_operator_layout(app, operator)

    close_all_display_windows(app)
    external = _external_monitors(app, monitors)

    layout = app.display_layout_var.get() or "Single Standard"
    widescreen = "Widescreen" in layout
    dual = layout.startswith("Dual")
    aspect = (21, 9) if widescreen else (16, 9)

    # Single-monitor development/testing mode.
    if not external:
        create_display_window(app)

        try:
            app.master.update_idletasks()

            root_x = app.master.winfo_x()
            root_y = app.master.winfo_y()
            root_w = app.master.winfo_width()

            display_x = root_x + root_w + 20
            display_y = root_y

            screen_w = app.master.winfo_screenwidth()

            # If there is insufficient space on the right,
            # place the display to the left of the operator window.
            if display_x + 900 > screen_w:
                display_x = max(0, root_x - 920)

            app.display_window.geometry(
                f"900x600+{display_x}+{display_y}"
            )

        except (tk.TclError, AttributeError):
            pass

        return

    # Multiple-monitor tournament mode.
    create_display_window(app)
    _place_window(
        app.display_window,
        external[0],
        aspect=aspect
    )

    if dual and len(external) >= 2:
        _create_full_mirror_window(
            app,
            "Display Window 2",
            external[1],
            aspect=aspect
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
