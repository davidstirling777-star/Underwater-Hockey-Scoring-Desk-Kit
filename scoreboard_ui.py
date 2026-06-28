import tkinter as tk
from tkinter import ttk


def create_scoreboard_tab(app):
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Scoreboard")

    for i in range(11):
        tab.grid_rowconfigure(i, weight=1)

    for i in range(9):
        tab.grid_columnconfigure(
            i,
            weight=1,
            uniform="scoreboard_cols"
        )

    # Keep the top two centre rows visually stable
    tab.grid_rowconfigure(2, minsize=58)
    tab.grid_rowconfigure(3, minsize=58)

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

    # Team colour row
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

    # Fixed centre container for penalties so the row does not jump
    app.penalty_area_frame = tk.Frame(
        tab,
        bg="lightgrey",
        bd=0,
        highlightthickness=0
    )
    app.penalty_area_frame.grid(
        row=2,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )
    app.penalty_area_frame.grid_rowconfigure(0, weight=1)
    app.penalty_area_frame.grid_columnconfigure(0, weight=1)
    app.penalty_area_frame.grid_propagate(False)

    app.penalty_grid_frame, app.penalty_labels = app.create_penalty_grid_widget(
        app.penalty_area_frame
    )
    app.penalty_grid_frame.grid(
        row=0,
        column=0,
        sticky="nsew"
    )
    app.penalty_grid_frame.grid_remove()

    # Team names row
    app.white_team_name_widget = tk.Label(
        tab,
        text="",
        font=app.fonts["team"],
        bg="white",
        fg="black",
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

    # Move Game Number DOWN to the row below penalties
    app.game_label = tk.Label(
        tab,
        textvariable=app.game_number_var,
        font=app.fonts["game_no"],
        bg="lightgrey",
        fg="black"
    )
    app.game_label.grid(
        row=3,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    # Scores
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

    # Timer
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
