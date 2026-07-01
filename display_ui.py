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

    for column in range(9):
        tab.grid_columnconfigure(
            column,
            weight=1,
            uniform="scoreboard_cols"
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
        anchor="center"
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
        anchor="center"
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

    app.display_window.bind(
        "<Configure>",
        app.scale_display_fonts
    )

    # Calculate dimensions only after widgets have been laid out.
    app.display_window.update_idletasks()

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
