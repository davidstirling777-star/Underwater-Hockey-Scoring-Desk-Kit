import tkinter as tk
from tkinter import ttk


def create_scoreboard_tab(app):
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Scoreboard")

    for row in range(11):
        tab.grid_rowconfigure(row, weight=1)

    # Left score area = columns 0–2
    # Larger timer area = columns 3–5
    # Right score area = columns 6–8
    #
    # The middle area receives more proportional width than either score area.
    for column in range(9):
        if column in (3, 4, 5):
            tab.grid_columnconfigure(
                column,
                weight=3,
                uniform="timer_columns"
            )
        elif column in (0, 1, 2):
            tab.grid_columnconfigure(
                column,
                weight=2,
                uniform="left_score_columns"
            )
        else:
            tab.grid_columnconfigure(
                column,
                weight=2,
                uniform="right_score_columns"
            )

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

    app.white_label = tk.Label(
        tab,
        textvariable=app.white_team_var,
        font=app.fonts["team"],
        bg="white",
        fg="black"
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
        fg="white"
    )
    app.black_label.grid(
        row=2,
        column=6,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    app.game_label = tk.Label(
        tab,
        textvariable=app.game_number_var,
        font=app.fonts["game_no"],
        bg="light grey"
    )
    app.game_label.grid(
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

    app.timer_spacer = tk.Label(
        tab,
        text="",
        bg="lightgrey"
    )
    app.timer_spacer.grid(
        row=3,
        column=3,
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
        width=2,
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

    app.black_score = tk.Label(
        tab,
        textvariable=app.black_score_var,
        font=app.fonts["score"],
        bg="black",
        fg="white",
        width=2,
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

    app.white_goal_button = tk.Button(
        tab,
        text="Add Goal White",
        font=app.fonts["button"],
        bg="light grey",
        fg="black",
        activebackground="light grey",
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

    app.black_goal_button = tk.Button(
        tab,
        text="Add Goal Black",
        font=app.fonts["button"],
        bg="light grey",
        fg="black",
        activebackground="light grey",
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

    app.white_minus_button = tk.Button(
        tab,
        text="-ve Goal White",
        font=app.fonts["button"],
        bg="light grey",
        fg="black",
        activebackground="light grey",
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

    app.black_minus_button = tk.Button(
        tab,
        text="-ve Goal Black",
        font=app.fonts["button"],
        bg="light grey",
        fg="black",
        activebackground="light grey",
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

    app.update_team_timeouts_allowed()
