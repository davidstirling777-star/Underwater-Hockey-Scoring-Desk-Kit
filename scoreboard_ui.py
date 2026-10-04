"""Build the main referee-facing scoreboard widgets.

This module creates controls; GameManagementApp in uwh.py owns the event
handlers, match state, and presentation updates. Keep callback names in
sync when moving a handler between modules.
"""

import tkinter as tk
from tkinter import ttk

import ui_theme


def _restore_classic_scoreboard_palette(app):
    """Keep the referee scoreboard in its original white/grey/black colours.

    ttkbootstrap is intentionally limited to the configuration tabs. The live
    scoreboard remains a classic Tk presentation surface because the team
    colours and high-visibility referee controls carry operational meaning.
    """
    widget_colours = (
        (getattr(app, "court_time_label", None),
         {"bg": "lightgrey", "fg": "black"}),
        (getattr(app, "white_label", None),
         {"bg": "white", "fg": "black"}),
        (getattr(app, "white_team_name_widget", None),
         {"bg": "white", "fg": "black"}),
        (getattr(app, "white_score", None),
         {"bg": "white", "fg": "black"}),
        (getattr(app, "black_label", None),
         {"bg": "black", "fg": "white"}),
        (getattr(app, "black_team_name_widget", None),
         {"bg": "black", "fg": "white"}),
        (getattr(app, "black_score", None),
         {"bg": "black", "fg": "white"}),
        (getattr(app, "penalty_background", None),
         {"bg": "lightgrey"}),
        (getattr(app, "timer_label", None),
         {"bg": "lightgrey", "fg": "black"}),
        (getattr(app, "white_timeout_button", None),
         {
             "bg": "white", "fg": "black",
             "activebackground": "white", "activeforeground": "black",
         }),
        (getattr(app, "white_goal_button", None),
         {
             "bg": "lightgrey", "fg": "black",
             "activebackground": "lightgrey", "activeforeground": "black",
         }),
        (getattr(app, "white_minus_button", None),
         {
             "bg": "lightgrey", "fg": "black",
             "activebackground": "lightgrey", "activeforeground": "black",
         }),
        (getattr(app, "penalties_button", None),
         {
             "bg": "orange", "fg": "black",
             "activebackground": "orange", "activeforeground": "black",
         }),
        (getattr(app, "black_goal_button", None),
         {
             "bg": "lightgrey", "fg": "black",
             "activebackground": "lightgrey", "activeforeground": "black",
         }),
        (getattr(app, "black_minus_button", None),
         {
             "bg": "lightgrey", "fg": "black",
             "activebackground": "lightgrey", "activeforeground": "black",
         }),
        (getattr(app, "black_timeout_button", None),
         {
             "bg": "black", "fg": "white",
             "activebackground": "black", "activeforeground": "white",
         }),
    )

    for widget, options in widget_colours:
        if widget is None:
            continue
        try:
            widget.configure(**options)
        except tk.TclError:
            pass

    # Referee Time-Out deliberately changes colours while active.
    button = getattr(app, "referee_timeout_button", None)
    if button is not None:
        try:
            if getattr(app, "referee_timeout_active", False):
                button.configure(
                    bg=app.referee_timeout_active_bg,
                    fg=app.referee_timeout_active_fg,
                    activebackground=app.referee_timeout_active_bg,
                    activeforeground=app.referee_timeout_active_fg,
                )
            else:
                button.configure(
                    bg=app.referee_timeout_default_bg,
                    fg=app.referee_timeout_default_fg,
                    activebackground=app.referee_timeout_default_bg,
                    activeforeground=app.referee_timeout_default_fg,
                )
        except tk.TclError:
            pass


def create_scoreboard_tab(app):
    tab = ttk.Frame(app.notebook)
    app.scoreboard_tab = tab
    app.notebook.add(tab, text=ui_theme.tab_label("Scoreboard"))

    for i in range(11):
        tab.grid_rowconfigure(i, weight=1)

    for i in range(9):
        tab.grid_columnconfigure(
            i,
            weight=1,
            uniform="scoreboard_cols"
        )

    # Keep the penalties row and Game Number row at a fixed height.
    # This stops the display shifting when penalty boxes appear or disappear.
    tab.grid_rowconfigure(2, weight=0, minsize=70)
    tab.grid_rowconfigure(3, weight=0, minsize=70)

    app.court_time_label = tk.Label(
        tab,
        textvariable=app.court_time_var,
        font=app.fonts["court_time"],
        bg="lightgrey"
    )
    app.court_time_label.grid(
        row=0,
        column=0,
        columnspan=9,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.half_label = tk.Label(
        tab,
        textvariable=app.half_label_var,
        font=app.fonts["half"],
        bg="lightcoral"
    )
    app.half_label.grid(
        row=1,
        column=0,
        columnspan=9,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Row 2: team colour names and centred penalty grid.
    app.white_label = tk.Label(
        tab,
        textvariable=app.white_team_var,
        font=app.fonts["team"],
        bg="white",
        fg="black",
        anchor="center"
    )
    app.white_label.grid(
        row=2,
        column=0,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.black_label = tk.Label(
        tab,
        textvariable=app.black_team_var,
        font=app.fonts["team"],
        bg="black",
        fg="white",
        anchor="center"
    )
    app.black_label.grid(
        row=2,
        column=6,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Permanent grey background for the centre penalty area.
    # It remains visible even when there are no penalties.
    app.penalty_background = tk.Label(
        tab,
        text="",
        bg="lightgrey"
    )
    app.penalty_background.grid(
        row=2,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.penalty_grid_frame, app.penalty_labels = (
        app.create_penalty_grid_widget(tab)
    )
    app.penalty_grid_frame.grid(
        row=2,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )
    app.penalty_grid_frame.grid_remove()

    # Row 3: team names and Game Number.
    app.white_team_name_widget = tk.Label(
        tab,
        text="",
        font=app.fonts["team"],
        bg="white",
        fg="black",
        width=14,
        anchor="center"
    )
    app.white_team_name_widget.grid(
        row=3,
        column=0,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Game number stays visible below the penalty row.
    app.game_label = tk.Label(
        tab,
        textvariable=app.game_number_var,
        font=app.fonts["game_no"],
        bg="lightgrey",
        fg="black",
        anchor="center"
    )
    app.game_label.grid(
        row=3,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.black_team_name_widget = tk.Label(
        tab,
        text="",
        font=app.fonts["team"],
        bg="black",
        fg="white",
        width=14,
        anchor="center"
    )
    app.black_team_name_widget.grid(
        row=3,
        column=6,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.white_score = tk.Label(
        tab,
        textvariable=app.white_score_var,
        font=app.fonts["score"],
        bg="white",
        fg="black",
        anchor="center"
    )
    app.white_score.grid(
        row=4,
        column=0,
        rowspan=5,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.timer_label = tk.Label(
        tab,
        textvariable=app.timer_var,
        font=app.fonts["timer"],
        bg="lightgrey",
        fg="black",
        anchor="center"
    )
    app.timer_label.grid(
        row=4,
        column=3,
        rowspan=5,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.black_score = tk.Label(
        tab,
        textvariable=app.black_score_var,
        font=app.fonts["score"],
        bg="black",
        fg="white",
        anchor="center"
    )
    app.black_score.grid(
        row=4,
        column=6,
        rowspan=5,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.referee_timeout_timer_label = tk.Label(
        tab,
        textvariable=app.referee_timeout_timer_var,
        font=app.fonts["referee_timeout_timer"],
        bg="red",
        fg="white"
    )
    app.referee_timeout_timer_label.grid(
        row=8,
        column=3,
        columnspan=3,
        padx=0,
        pady=1,
        sticky="nsew"
    )
    app.referee_timeout_timer_label.grid_remove()

    app.white_timeout_button = tk.Button(
        tab,
        text="White Team\nTime-Out",
        font=app.fonts["timeout_button"],
        bg="white",
        fg="black",
        activebackground="white",
        activeforeground="black",
        justify="center",
        wraplength=180,
        height=2,
        command=app.white_team_timeout
    )
    app.white_timeout_button.grid(
        row=9,
        column=0,
        rowspan=2,
        columnspan=1,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.white_goal_button = tk.Button(
        tab,
        text="Add Goal White",
        font=app.fonts["button"],
        bg="lightgrey",
        fg="black",
        activebackground="lightgrey",
        activeforeground="black",
        command=lambda: app.add_goal_with_confirmation(
            app.white_score_var,
            "White",
            app.white_goal_button
        )
    )
    app.white_goal_button.grid(
        row=9,
        column=1,
        columnspan=2,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.referee_timeout_button = tk.Button(
        tab,
        text="Referee Time-Out",
        font=app.fonts["button"],
        bg=app.referee_timeout_default_bg,
        fg=app.referee_timeout_default_fg,
        activebackground=app.referee_timeout_default_bg,
        activeforeground=app.referee_timeout_default_fg,
        command=app.toggle_referee_timeout
    )
    app.referee_timeout_button.grid(
        row=9,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.black_goal_button = tk.Button(
        tab,
        text="Add Goal Black",
        font=app.fonts["button"],
        bg="lightgrey",
        fg="black",
        activebackground="lightgrey",
        activeforeground="black",
        command=lambda: app.add_goal_with_confirmation(
            app.black_score_var,
            "Black",
            app.black_goal_button
        )
    )
    app.black_goal_button.grid(
        row=9,
        column=6,
        columnspan=2,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.black_timeout_button = tk.Button(
        tab,
        text="Black Team\nTime-Out",
        font=app.fonts["timeout_button"],
        bg="black",
        fg="white",
        activebackground="black",
        activeforeground="white",
        justify="center",
        wraplength=180,
        height=2,
        command=app.black_team_timeout
    )
    app.black_timeout_button.grid(
        row=9,
        column=8,
        rowspan=2,
        columnspan=1,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.white_minus_button = tk.Button(
        tab,
        text="-ve Goal White",
        font=app.fonts["button"],
        bg="lightgrey",
        fg="black",
        activebackground="lightgrey",
        activeforeground="black",
        command=lambda: app.adjust_score_with_confirm(
            app.white_score_var,
            "White"
        )
    )
    app.white_minus_button.grid(
        row=10,
        column=1,
        columnspan=2,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.penalties_button = tk.Button(
        tab,
        text="Penalties",
        font=app.fonts["button"],
        bg="orange",
        fg="black",
        activebackground="orange",
        activeforeground="black",
        command=lambda: app.show_penalties(app.penalties_button)
    )
    app.penalties_button.grid(
        row=10,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.black_minus_button = tk.Button(
        tab,
        text="-ve Goal Black",
        font=app.fonts["button"],
        bg="lightgrey",
        fg="black",
        activebackground="lightgrey",
        activeforeground="black",
        command=lambda: app.adjust_score_with_confirm(
            app.black_score_var,
            "Black"
        )
    )
    app.black_minus_button.grid(
        row=10,
        column=6,
        columnspan=2,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.update_team_timeouts_allowed()

    # Flatly styles the configuration tabs, but the live referee scoreboard
    # must retain its established high-contrast match colours.
    _restore_classic_scoreboard_palette(app)
    tab.after_idle(lambda: _restore_classic_scoreboard_palette(app))
    tab.after(150, lambda: _restore_classic_scoreboard_palette(app))

    def restore_when_selected(_event=None):
        try:
            if app.notebook.select() == str(tab):
                _restore_classic_scoreboard_palette(app)
        except tk.TclError:
            pass

    app.notebook.bind(
        "<<NotebookTabChanged>>",
        restore_when_selected,
        add="+",
    )
