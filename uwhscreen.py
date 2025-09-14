import tkinter as tk
from tkinter import font as tkfont


class ScoreboardApp:
    """
    A class to create a scoreboard application using tkinter.
    """
    def __init__(self, master):
        self.master = master
        self.master.title("Scoreboard")

        # Maximize the window
        # This works on Windows and some Linux environments
        self.master.state('normal')

        # Configure grid for dynamic resizing
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=2)
        self.master.grid_rowconfigure(2, weight=5)
        self.master.grid_rowconfigure(3, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)
        self.master.grid_columnconfigure(2, weight=1)

        # --- Widgets ---

        # Court Time
        self.court_time_label = tk.Label(
            self.master,
            text="Court Time is 12:27:57 PM",
            font=("Arial", 24)
        )
        self.court_time_label.grid(
            row=0,
            column=0,
            columnspan=3,
            pady=10,
            sticky="nsew"
        )

        # Half Information
        self.half_label = tk.Label(
            self.master,
            text="1st Half",
            font=("Arial", 36, "bold"),
            bg="lightblue"
        )
        self.half_label.grid(
            row=1,
            column=0,
            columnspan=3,
            pady=5,
            sticky="nsew"
        )

        # Main Scoreboard Frame
        self.scoreboard_frame = tk.Frame(self.master, bg="grey")
        self.scoreboard_frame.grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="nsew",
            padx=10,
            pady=10
        )

        # Configure scoreboard frame grid for dynamic resizing
        self.scoreboard_frame.grid_rowconfigure(0, weight=1)
        self.scoreboard_frame.grid_columnconfigure(0, weight=1)
        self.scoreboard_frame.grid_columnconfigure(1, weight=1)
        self.scoreboard_frame.grid_columnconfigure(2, weight=1)

        # White Team Score
        self.white_label = tk.Label(
            self.scoreboard_frame,
            text="White",
            font=("Arial", 30, "bold"),
            bg="white",
            fg="black"
        )
        self.white_label.grid(row=0, column=0, sticky="new", padx=5, pady=5)
        self.white_score = tk.Label(
            self.scoreboard_frame,
            text="0",
            font=("Arial", 120, "bold"),
            bg="white",
            fg="black"
        )
        self.white_score.grid(row=0, column=0, sticky="nsew", padx=5, pady=(0, 5))

        # Game Timer
        self.timer_label = tk.Label(
            self.scoreboard_frame,
            text="09:44",
            font=("Arial", 120, "bold"),
            bg="lightgrey",
            fg="darkblue"
        )
        self.timer_label.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Black Team Score
        self.black_label = tk.Label(
            self.scoreboard_frame,
            text="Black",
            font=("Arial", 30, "bold"),
            bg="black",
            fg="white"
        )
        self.black_label.grid(row=0, column=2, sticky="new", padx=5, pady=5)
        self.black_score = tk.Label(
            self.scoreboard_frame,
            text="0",
            font=("Arial", 120, "bold"),
            bg="black",
            fg="white"
        )
        self.black_score.grid(row=0, column=2, sticky="nsew", padx=5, pady=(0, 5))

        # Game Number
        self.game_no_label = tk.Label(
            self.master,
            text="This is game No 121.",
            font=("Arial", 18),
        )
        self.game_no_label.grid(
            row=3,
            column=0,
            columnspan=3,
            pady=10,
            padx=10,
            sticky="ew"
        )


# Create the main window and run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = ScoreboardApp(root)
    root.mainloop()


