import tkinter as tk
from tkinter import ttk


def create_display_window(app):
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

    for row in range(11):
        tab.grid_rowconfigure(row, weight=1)

    for column in range(9):
        tab.grid_columnconfigure(
            column,
            weight=1,
            uniform="display_scoreboard_cols"
        )

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

    app.display_white_label = tk.Label(
        tab,
        textvariable=app.white_team_var,
        font=app.display_fonts["team"],
        bg="white",
        fg="black"
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
        fg="white"
    )
    app.display_black_label.grid(
        row=2,
        column=6,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.display_game_label = tk.Label(
        tab,
        textvariable=app.game_number_var,
        font=app.display_fonts["game_no"],
        bg="light grey"
    )
    app.display_game_label.grid(
        row=2,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    (
        app.display_penalty_grid_frame,
        app.display_penalty_labels
    ) = app.create_penalty_grid_widget(
        tab,
        is_display=True
    )

    app.display_penalty_grid_frame.grid(
        row=2,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )
    app.display_penalty_grid_frame.grid_remove()

    app.display_white_score = tk.Label(
        tab,
        textvariable=app.white_score_var,
        font=app.display_fonts["score"],
        bg="white",
        fg="black"
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
        fg="white"
    )
    app.display_black_score.grid(
        row=3,
        column=6,
        rowspan=8,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.display_timer_label = tk.Label(
        tab,
        textvariable=app.timer_var,
        font=app.display_fonts["timer"],
        bg="lightgrey",
        fg="black"
    )
    app.display_timer_label.grid(
        row=3,
        column=3,
        rowspan=8,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.display_referee_timeout_timer_label = tk.Label(
        tab,
        textvariable=app.referee_timeout_timer_var,
        font=app.display_fonts["referee_timeout_timer"],
        bg="red",
        fg="white"
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

    app.display_initial_width = app.display_window.winfo_width() or 1200

    app.display_window.update_idletasks()
    app.scale_display_fonts(None)
    app.sync_display_widgets()
