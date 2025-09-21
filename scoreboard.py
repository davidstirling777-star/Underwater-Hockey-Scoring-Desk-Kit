import tkinter as tk
from tkinter import ttk

class ScoreboardTab:
    def __init__(self, notebook, fonts, white_score_var, black_score_var, app_callbacks):
        """
        notebook: the ttk.Notebook instance to add the tab to
        fonts: dict of fonts used throughout the UI
        white_score_var, black_score_var: tk.IntVar instances for scores
        app_callbacks: dict of callback functions, e.g. {
            'add_goal_with_confirmation': fn,
            'adjust_score_with_confirm': fn,
            'white_team_timeout': fn,
            'black_team_timeout': fn,
            'toggle_referee_timeout': fn,
            'show_penalties': fn,
            'update_team_timeouts_allowed': fn,
        }
        """
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Scoreboard")
        for i in range(11):
            tab.grid_rowconfigure(i, weight=1)
        for i in range(6):
            tab.grid_columnconfigure(i, weight=1)

        self.court_time_label = tk.Label(tab, text="Court Time is", font=fonts["court_time"], bg="lightgrey")
        self.court_time_label.grid(row=0, column=0, columnspan=6, padx=1, pady=1, sticky="nsew")
        self.half_label = tk.Label(tab, text="", font=fonts["half"], bg="lightcoral")
        self.half_label.grid(row=1, column=0, columnspan=6, padx=1, pady=1, sticky="nsew")
        self.white_label = tk.Label(tab, text="White", font=fonts["team"], bg="white", fg="black")
        self.white_label.grid(row=2, column=0, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.white_score = tk.Label(tab, textvariable=white_score_var, font=fonts["score"], bg="white", fg="black")
        self.white_score.grid(row=3, column=0, rowspan=6, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.timer_label = tk.Label(tab, text="00:00", font=fonts["timer"], bg="lightgrey", fg="black")
        self.timer_label.grid(row=3, column=2, rowspan=6, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.black_label = tk.Label(tab, text="Black", font=fonts["team"], bg="black", fg="white")
        self.black_label.grid(row=2, column=4, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.black_score = tk.Label(tab, textvariable=black_score_var, font=fonts["score"], bg="black", fg="white")
        self.black_score.grid(row=3, column=4, rowspan=6, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.white_timeout_button = tk.Button(
            tab, text="White Team\nTime-Out", font=fonts["timeout_button"], bg="white", fg="black",
            activebackground="white", activeforeground="black",
            justify="center", wraplength=180, height=2, command=app_callbacks['white_team_timeout']
        )
        self.white_timeout_button.grid(row=9, column=0, rowspan=2, padx=1, pady=1, sticky="nsew")

        self.white_goal_button = tk.Button(
            tab, text="Add Goal White", font=fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: app_callbacks['add_goal_with_confirmation'](white_score_var, "White")
        )
        self.white_goal_button.grid(row=9, column=1, padx=1, pady=1, sticky="nsew")

        self.white_minus_button = tk.Button(
            tab, text="-ve Goal White", font=fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: app_callbacks['adjust_score_with_confirm'](white_score_var, "White")
        )
        self.white_minus_button.grid(row=10, column=1, padx=1, pady=1, sticky="nsew")

        self.referee_timeout_button = tk.Button(
            tab, text="Referee Time-Out", font=fonts["button"],
            bg="red", fg="black",
            activebackground="red", activeforeground="black",
            command=app_callbacks['toggle_referee_timeout']
        )
        self.referee_timeout_button.grid(row=9, column=2, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.penalties_button = tk.Button(
            tab, text="Penalties", font=fonts["button"], bg="orange", fg="black",
            activebackground="orange", activeforeground="black",
            command=app_callbacks['show_penalties']
        )
        self.penalties_button.grid(row=10, column=2, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.game_label = tk.Label(tab, text="Game 121", font=fonts["game_no"], bg="light grey")
        self.game_label.grid(row=2, column=2, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.black_goal_button = tk.Button(
            tab, text="Add Goal Black", font=fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: app_callbacks['add_goal_with_confirmation'](black_score_var, "Black")
        )
        self.black_goal_button.grid(row=9, column=4, padx=1, pady=1, sticky="nsew")

        self.black_minus_button = tk.Button(
            tab, text="-ve Goal Black", font=fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: app_callbacks['adjust_score_with_confirm'](black_score_var, "Black")
        )
        self.black_minus_button.grid(row=10, column=4, padx=1, pady=1, sticky="nsew")

        self.black_timeout_button = tk.Button(
            tab, text="Black Team\nTime-Out", font=fonts["timeout_button"], bg="black", fg="white",
            activebackground="black", activeforeground="white",
            justify="center", wraplength=180, height=2, command=app_callbacks['black_team_timeout']
        )
        self.black_timeout_button.grid(row=9, column=5, rowspan=2, padx=1, pady=1, sticky="nsew")

        app_callbacks['update_team_timeouts_allowed']()

    # You can add more methods here for scoreboard-specific logic or UI updates
