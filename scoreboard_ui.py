
import tkinter as tk
from tkinter import ttk

def create_scoreboard_tab(app):
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Scoreboard")

    for i in range(11):
        tab.grid_rowconfigure(i, weight=1)

    for i in range(9):
        tab.grid_columnconfigure(
            i,
            weight=1,
            uniform="scoreboard_cols"
        )

    self.court_time_label = tk.Label(
        tab,
        textvariable=self.court_time_var,
        font=self.fonts["court_time"],
        bg="lightgrey"
    )
    self.court_time_label.grid(
        row=0,
        column=0,
        columnspan=9,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.half_label = tk.Label(
        tab,
        textvariable=self.half_label_var,
        font=self.fonts["half"],
        bg="lightcoral"
    )
    self.half_label.grid(
        row=1,
        column=0,
        columnspan=9,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.white_label = tk.Label(
        tab,
        textvariable=self.white_team_var,
        font=self.fonts["team"],
        bg="white",
        fg="black"
    )
    self.white_label.grid(
        row=2,
        column=0,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.black_label = tk.Label(
        tab,
        textvariable=self.black_team_var,
        font=self.fonts["team"],
        bg="black",
        fg="white"
    )
    self.black_label.grid(
        row=2,
        column=6,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.game_label = tk.Label(
        tab,
        textvariable=self.game_number_var,
        font=self.fonts["game_no"],
        bg="light grey"
    )
    self.game_label.grid(
        row=2,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.penalty_grid_frame, self.penalty_labels = (
        self.create_penalty_grid_widget(tab)
    )
    self.penalty_grid_frame.grid(
        row=2,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )
    self.penalty_grid_frame.grid_remove()

    self.white_team_name_widget = tk.Label(
        tab,
        text="",
        font=self.fonts["team"],
        bg="white",
        fg="black",
        width=14,
        anchor="center"
    )
    self.white_team_name_widget.grid(
        row=3,
        column=0,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.black_team_name_widget = tk.Label(
        tab,
        text="",
        font=self.fonts["team"],
        bg="black",
        fg="white",
        width=14,
        anchor="center"
    )
    self.black_team_name_widget.grid(
        row=3,
        column=6,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.timer_spacer = tk.Label(
        tab,
        text="",
        bg="lightgrey"
    )
    self.timer_spacer.grid(
        row=3,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.white_score = tk.Label(
        tab,
        textvariable=self.white_score_var,
        font=self.fonts["score"],
        bg="white",
        fg="black"
    )
    self.white_score.grid(
        row=4,
        column=0,
        rowspan=5,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.black_score = tk.Label(
        tab,
        textvariable=self.black_score_var,
        font=self.fonts["score"],
        bg="black",
        fg="white"
    )
    self.black_score.grid(
        row=4,
        column=6,
        rowspan=5,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.timer_label = tk.Label(
        tab,
        textvariable=self.timer_var,
        font=self.fonts["timer"],
        bg="lightgrey",
        fg="black"
    )
    self.timer_label.grid(
        row=4,
        column=3,
        rowspan=5,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.referee_timeout_timer_label = tk.Label(
        tab,
        textvariable=self.referee_timeout_timer_var,
        font=self.fonts["referee_timeout_timer"],
        bg="red",
        fg="white"
    )
    self.referee_timeout_timer_label.grid(
        row=8,
        column=3,
        rowspan=1,
        columnspan=3,
        padx=0,
        pady=1,
        sticky="nsew"
    )
    self.referee_timeout_timer_label.grid_remove()

    self.white_timeout_button = tk.Button(
        tab,
        text="White Team\nTime-Out",
        font=self.fonts["timeout_button"],
        bg="white",
        fg="black",
        activebackground="white",
        activeforeground="black",
        justify="center",
        wraplength=180,
        height=2,
        command=self.white_team_timeout
    )
    self.white_timeout_button.grid(
        row=9,
        column=0,
        rowspan=2,
        columnspan=1,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.black_timeout_button = tk.Button(
        tab,
        text="Black Team\nTime-Out",
        font=self.fonts["timeout_button"],
        bg="black",
        fg="white",
        activebackground="black",
        activeforeground="white",
        justify="center",
        wraplength=180,
        height=2,
        command=self.black_team_timeout
    )
    self.black_timeout_button.grid(
        row=9,
        column=8,
        rowspan=2,
        columnspan=1,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.white_goal_button = tk.Button(
        tab,
        text="Add Goal White",
        font=self.fonts["button"],
        bg="light grey",
        fg="black",
        activebackground="light grey",
        activeforeground="black",
        command=lambda: self.add_goal_with_confirmation(
            self.white_score_var,
            "White",
            self.white_goal_button
        )
    )
    self.white_goal_button.grid(
        row=9,
        column=1,
        columnspan=2,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.black_goal_button = tk.Button(
        tab,
        text="Add Goal Black",
        font=self.fonts["button"],
        bg="light grey",
        fg="black",
        activebackground="light grey",
        activeforeground="black",
        command=lambda: self.add_goal_with_confirmation(
            self.black_score_var,
            "Black",
            self.black_goal_button
        )
    )
    self.black_goal_button.grid(
        row=9,
        column=6,
        columnspan=2,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.white_minus_button = tk.Button(
        tab,
        text="-ve Goal White",
        font=self.fonts["button"],
        bg="light grey",
        fg="black",
        activebackground="light grey",
        activeforeground="black",
        command=lambda: self.adjust_score_with_confirm(
            self.white_score_var,
            "White"
        )
    )
    self.white_minus_button.grid(
        row=10,
        column=1,
        columnspan=2,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.black_minus_button = tk.Button(
        tab,
        text="-ve Goal Black",
        font=self.fonts["button"],
        bg="light grey",
        fg="black",
        activebackground="light grey",
        activeforeground="black",
        command=lambda: self.adjust_score_with_confirm(
            self.black_score_var,
            "Black"
        )
    )
    self.black_minus_button.grid(
        row=10,
        column=6,
        columnspan=2,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.referee_timeout_button = tk.Button(
        tab,
        text="Referee Time-Out",
        font=self.fonts["button"],
        bg=self.referee_timeout_default_bg,
        fg=self.referee_timeout_default_fg,
        activebackground=self.referee_timeout_default_bg,
        activeforeground=self.referee_timeout_default_fg,
        command=self.toggle_referee_timeout
    )
    self.referee_timeout_button.grid(
        row=9,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.penalties_button = tk.Button(
        tab,
        text="Penalties",
        font=self.fonts["button"],
        bg="orange",
        fg="black",
        activebackground="orange",
        activeforeground="black",
        command=lambda: self.show_penalties(self.penalties_button)
    )
    self.penalties_button.grid(
        row=10,
        column=3,
        columnspan=3,
        padx=1,
        pady=1,
        sticky="nsew"
    )

    self.update_team_timeouts_allowed()
