import tkinter as tk
from tkinter import ttk, messagebox, font
import datetime
import json
import os
import re


class MultiTabApp:
    """
    A single-window application with multiple tabs for scoreboard
    and game variable settings.
    """
    def __init__(self, master):
        self.master = master
        self.master.title("Game Management App")

        self.master.state('normal')
        self.master.geometry('1200x800')

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.after_id = None
        self.timer_job = None
        self.timer_running = False
        self.timer_seconds = 0
        self.current_period_index = 0
        self.settings_file = "game_settings.json"

        self.font_court_time = font.Font(family="Arial", size=36)
        self.font_half = font.Font(family="Arial", size=36, weight="bold")
        self.font_team = font.Font(family="Arial", size=30, weight="bold")
        self.font_score = font.Font(family="Arial", size=200, weight="bold")
        self.font_timer = font.Font(family="Arial", size=90, weight="bold")
        self.font_game_no = font.Font(family="Arial", size=18)

        self.white_score_var = tk.IntVar(value=0)
        self.black_score_var = tk.IntVar(value=0)

        self.variables = {
            "start_first_game_at_this_time": {"default": "12:00", "checkbox": False, "unit": "hh:mm"},
            "half_period": {"default": 15, "checkbox": False, "unit": "minutes"},
            "half_time_break": {"default": 3, "checkbox": False, "unit": "minutes"},
            "overtime_game_break_before_start": {"default": 3, "checkbox": True, "unit": "minutes"},
            "overtime_half_period": {"default": 5, "checkbox": True, "unit": "minutes"},
            "overtime_half_time_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "overtime_second_half": {"default": 5, "checkbox": True, "unit": "minutes"},
            "sudden_death_game_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "between_game_duration": {"default": 5, "checkbox": False, "unit": "minutes"},
            "timeout_period": {"default": 1, "checkbox": True, "unit": "minutes"},
            "crib_time": {"default": 60, "checkbox": True, "unit": "seconds"}
        }

        self.periods = []
        self.widgets = []

        self.start_timer_button = None
        self.reset_timer_button = None

        self.create_scoreboard_tab()
        self.create_settings_tab()
        self.load_settings()
        self.setup_periods()
        self.reset_timer()

        self.master.bind('<Configure>', self.scale_fonts)
        self.initial_width = self.master.winfo_width()
        self.master.update_idletasks()
        
        self.scale_fonts(None)
        self.update_court_time()

        # Auto-start the timer after a slight delay
        self.master.after(100, self.toggle_timer)


    def scale_fonts(self, event):
        """Debounce the font scaling to prevent flickering."""
        if self.after_id:
            self.master.after_cancel(self.after_id)
        self.after_id = self.master.after(50, self._delayed_scale_fonts)

    def _delayed_scale_fonts(self):
        """Performs the actual font scaling after a brief delay."""
        new_width = self.master.winfo_width()
        base_width = 1200
        if new_width == self.initial_width:
            return
        self.initial_width = new_width
        scaling_factor = new_width / base_width

        self.font_court_time.configure(size=max(12, int(36 * scaling_factor * 0.7)))
        self.font_half.configure(size=max(18, int(36 * scaling_factor * 0.8)))
        self.font_team.configure(size=max(16, int(30 * scaling_factor * 0.8)))
        self.font_score.configure(size=max(60, int(200 * scaling_factor * 0.9)))
        self.font_timer.configure(size=max(60, int(90 * scaling_factor * 0.9)))
        self.font_game_no.configure(size=max(12, int(18 * scaling_factor * 0.7)))

    def update_court_time(self):
        """Updates the court time label every second."""
        now = datetime.datetime.now()
        time_string = now.strftime('%I:%M:%S %p').lstrip('0')
        self.court_time_label.config(text=f"Court Time is {time_string}")
        self.master.after(1000, self.update_court_time)

    def create_scoreboard_tab(self):
        """Creates and configures the Scoreboard tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Scoreboard")

        tab.grid_rowconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=2)
        tab.grid_rowconfigure(2, weight=5)
        tab.grid_rowconfigure(3, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_columnconfigure(2, weight=1)

        self.court_time_label = tk.Label(
            tab,
            text="Court Time is",
            font=self.font_court_time
        )
        self.court_time_label.grid(row=0, column=0, columnspan=3, pady=1, sticky="nsew")

        self.half_label = tk.Label(
            tab,
            text="",
            font=self.font_half,
            bg="lightblue"
        )
        self.half_label.grid(row=1, column=0, columnspan=3, pady=1, sticky="nsew")

        scoreboard_frame = tk.Frame(tab, bg="grey")
        scoreboard_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=1, pady=1)

        scoreboard_frame.grid_rowconfigure(0, weight=1)
        scoreboard_frame.grid_rowconfigure(1, weight=5)
        scoreboard_frame.grid_rowconfigure(2, weight=1)
        scoreboard_frame.grid_columnconfigure(0, weight=1)
        scoreboard_frame.grid_columnconfigure(1, weight=1)
        scoreboard_frame.grid_columnconfigure(2, weight=1)

        self.white_label = tk.Label(
            scoreboard_frame,
            text="White",
            font=self.font_team,
            bg="white",
            fg="black"
        )
        self.white_label.grid(row=0, column=0, sticky="new", padx=5, pady=2)
        self.white_score = tk.Label(
            scoreboard_frame,
            textvariable=self.white_score_var,
            font=self.font_score,
            bg="white",
            fg="black"
        )
        self.white_score.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 2))

        self.timer_label = tk.Label(
            scoreboard_frame,
            text="00:00",
            font=self.font_timer,
            bg="lightgrey",
            fg="darkblue"
        )
        self.timer_label.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)

        self.black_label = tk.Label(
            scoreboard_frame,
            text="Black",
            font=self.font_team,
            bg="black",
            fg="white"
        )
        self.black_label.grid(row=0, column=2, sticky="new", padx=5, pady=2)
        self.black_score = tk.Label(
            scoreboard_frame,
            textvariable=self.black_score_var,
            font=self.font_score,
            bg="black",
            fg="white"
        )
        self.black_score.grid(row=1, column=2, sticky="nsew", padx=5, pady=(0, 2))

        game_info_frame = tk.Frame(tab)
        game_info_frame.grid(row=3, column=0, columnspan=3, pady=10, padx=10, sticky="ew")
        game_info_frame.grid_columnconfigure(0, weight=1)
        game_info_frame.grid_columnconfigure(1, weight=1)
        game_info_frame.grid_columnconfigure(2, weight=1)

        score_button_frame_white = ttk.Frame(game_info_frame)
        score_button_frame_white.grid(row=0, column=0, sticky="ew")
        score_button_frame_white.grid_columnconfigure(0, weight=1)
        
        white_add_goal_button = ttk.Button(
            score_button_frame_white,
            text="Add Goal",
            command=lambda: self.adjust_score(self.white_score_var, 1)
        )
        white_add_goal_button.grid(row=0, column=0, padx=2, pady=2)
        
        white_neg_goal_button = ttk.Button(
            score_button_frame_white,
            text="-ve Goal",
            command=lambda: self.adjust_score_with_confirm(self.white_score_var, "White")
        )
        white_neg_goal_button.grid(row=1, column=0, padx=2, pady=2)

        self.game_no_label = tk.Label(
            game_info_frame,
            text="This is game No 121.",
            font=self.font_game_no,
        )
        self.game_no_label.grid(row=0, column=1, pady=10, sticky="ew")
        
        score_button_frame_black = ttk.Frame(game_info_frame)
        score_button_frame_black.grid(row=0, column=2, sticky="ew")
        score_button_frame_black.grid_columnconfigure(0, weight=1)
        
        black_add_goal_button = ttk.Button(
            score_button_frame_black,
            text="Add Goal",
            command=lambda: self.adjust_score(self.black_score_var, 1)
        )
        black_add_goal_button.grid(row=0, column=0, padx=2, pady=2)
        
        black_neg_goal_button = ttk.Button(
            score_button_frame_black,
            text="-ve Goal",
            command=lambda: self.adjust_score_with_confirm(self.black_score_var, "Black")
        )
        black_neg_goal_button.grid(row=1, column=0, padx=2, pady=2)

    def create_settings_tab(self):
        """Creates and configures the Game Variable Settings tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Game Variables")

        frame = ttk.Frame(tab, padding=(10, 10, 10, 10))
        frame.pack(fill=tk.BOTH, expand=True)

        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=0)
        frame.grid_columnconfigure(2, weight=0)
        frame.grid_columnconfigure(3, weight=0)
        frame.grid_columnconfigure(4, weight=1)

        style = ttk.Style()
        default_font = font.nametofont("TkDefaultFont")
        new_size = default_font.cget("size") + 2
        style.configure("Settings.TLabel", font=(default_font.cget("family"), new_size, "bold"))

        header_names = ["Use?", "Variable", "Value", "Units"]
        for i, name in enumerate(header_names):
            header_label = ttk.Label(frame, text=name, style="Settings.TLabel")
            header_label.grid(row=0, column=i, sticky="w", padx=5, pady=5)

        style.configure("Settings.TLabel", font=(default_font.cget("family"), new_size))

        for i, (var_name, var_info) in enumerate(self.variables.items(), start=1):
            
            if var_info["checkbox"]:
                check_var = tk.BooleanVar(value=True)
                checkbox = ttk.Checkbutton(frame, variable=check_var)
                checkbox.grid(row=i, column=0, sticky="w", pady=5)
            else:
                check_var = None

            label_text = f"{var_name.replace('_', ' ').title()}:"
            label = ttk.Label(frame, text=label_text, style="Settings.TLabel")
            label.grid(row=i, column=1, sticky="w", pady=5)

            entry = ttk.Entry(frame, width=10)
            entry.insert(0, str(var_info["default"]))
            entry.grid(row=i, column=2, sticky="w", padx=5, pady=5)

            units_label = ttk.Label(frame, text=var_info["unit"], style="Settings.TLabel")
            units_label.grid(row=i, column=3, sticky="w", padx=5, pady=5)

            self.widgets.append({"name": var_name, "entry": entry, "checkbox": check_var})

    def load_settings(self):
        """Loads settings from a JSON file if it exists."""
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                settings = json.load(f)
                for widget_info in self.widgets:
                    name = widget_info["name"]
                    if name in settings:
                        setting_value = settings[name]
                        if isinstance(setting_value, int) or isinstance(setting_value, str):
                            widget_info["entry"].delete(0, tk.END)
                            widget_info["entry"].insert(0, str(setting_value))
                        elif isinstance(setting_value, dict):
                            widget_info["entry"].delete(0, tk.END)
                            widget_info["entry"].insert(0, str(setting_value["value"]))
                            if widget_info["checkbox"]:
                                widget_info["checkbox"].set(setting_value["used"])

    def _convert_hh_mm_to_seconds(self, hh_mm_str):
        """Converts an 'hh:mm' string to seconds."""
        pattern = r"^(\d{1,2}):(\d{2})$"
        match = re.match(pattern, hh_mm_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return (hours * 3600) + (minutes * 60)
        return None

    def setup_periods(self):
        """Sets up the game periods based on the values in the settings tab."""
        self.periods = []
        settings = self.get_variable_settings()
        
        if settings is None:
            return

        def add_period(name, setting_name):
            setting = settings.get(setting_name, {})
            is_used = setting.get("used", not self.variables[setting_name]["checkbox"])
            if not is_used:
                return True

            duration = setting["value"]
            
            if self.variables[setting_name]["unit"] == "minutes":
                duration *= 60
            elif self.variables[setting_name]["unit"] == "hh:mm":
                start_time_seconds = self._convert_hh_mm_to_seconds(duration)
                if start_time_seconds is None:
                    messagebox.showerror("Invalid Time Format",
                                         f"Invalid time format for '{setting_name}'. Must be 'hh:mm'.")
                    return None
                
                now = datetime.datetime.now()
                current_time_seconds = (now.hour * 3600) + (now.minute * 60) + now.second

                if start_time_seconds < current_time_seconds:
                    time_diff = (start_time_seconds + 86400) - current_time_seconds
                else:
                    time_diff = start_time_seconds - current_time_seconds
                
                duration = time_diff

            self.periods.append({"name": name, "duration": duration, "unit": self.variables[setting_name]["unit"]})
            return True

        if not add_period("Game Starts in", "start_first_game_at_this_time"): return
        if not add_period("First Half", "half_period"): return
        if not add_period("Half Time", "half_time_break"): return
        if not add_period("Second Half", "half_period"): return
        
        if settings.get("overtime_game_break_before_start", {}).get("used", False):
            if not add_period("Overtime Game Break", "overtime_game_break_before_start"): return
            if not add_period("Overtime First Half", "overtime_half_period"): return
            if not add_period("Overtime Half Time", "overtime_half_time_break"): return
            if not add_period("Overtime Second Half", "overtime_second_half"): return
            if not add_period("Sudden Death Game Break", "sudden_death_game_break"): return
            
        if not add_period("Between Game Duration", "between_game_duration"): return
        
    def get_variable_settings(self):
        """Retrieves and validates the settings from the entries."""
        settings = {}
        for widget_info in self.widgets:
            name = widget_info["name"]
            try:
                if self.variables[name]["unit"] == "hh:mm":
                    value = widget_info["entry"].get()
                else:
                    value = int(widget_info["entry"].get())
                
                used = widget_info["checkbox"].get() if widget_info["checkbox"] else True
                settings[name] = {"value": value, "used": used}
            except ValueError:
                messagebox.showerror("Invalid Input", f"Please enter a valid number for '{name}'.")
                return None
        return settings

    def reset_timer(self):
        """Resets the timer to the beginning of the game sequence."""
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
        self.timer_running = False
        self.current_period_index = 0
        self.setup_periods()
        if self.start_timer_button:
            self.start_timer_button.config(text="Start/Pause")
            self.start_timer_button.config(state="normal")
        self.update_timer_state()

    def toggle_timer(self):
        """Toggles the timer between running and paused."""
        if not self.timer_running:
            if self.current_period_index >= len(self.periods):
                return
            self.timer_running = True
            if self.start_timer_button:
                self.start_timer_button.config(text="Pause")
            self.update_timer()
        else:
            self.timer_running = False
            if self.start_timer_button:
                self.start_timer_button.config(text="Start")
            if self.timer_job:
                self.master.after_cancel(self.timer_job)

    def update_timer(self):
        """Updates the timer countdown every second."""
        if not self.timer_running:
            return

        if self.timer_seconds <= 0:
            self.end_of_period_handler()
            return
        
        self.timer_seconds -= 1
        self.update_timer_display()
        self.timer_job = self.master.after(1000, self.update_timer)
        
    def end_of_period_handler(self):
        """Handles the transition to the next period."""
        self.current_period_index += 1
        self.update_timer_state()

    def update_timer_state(self):
        """Sets the timer for the current period and updates labels."""
        if self.current_period_index < len(self.periods):
            period_info = self.periods[self.current_period_index]
            self.timer_seconds = period_info["duration"]
            self.half_label.config(text=period_info["name"])
            if self.start_timer_button and self.start_timer_button["state"] == "disabled":
                self.start_timer_button.config(state="normal")
                self.start_timer_button.config(text="Start/Pause")
        else:
            self.timer_seconds = 0
            self.half_label.config(text="Game Over")
            self.timer_running = False
            if self.start_timer_button:
                self.start_timer_button.config(text="Game Over")
                self.start_timer_button.config(state="disabled")

        self.update_timer_display()

    def update_timer_display(self):
        """Formats and displays the remaining time."""
        current_period_unit = self.periods[self.current_period_index]["unit"] \
            if self.current_period_index < len(self.periods) else None

        if current_period_unit == "hh:mm":
            remaining_time = datetime.timedelta(seconds=self.timer_seconds)
            total_seconds = int(remaining_time.total_seconds())
            hours, total_seconds = divmod(total_seconds, 3600)
            minutes, seconds = divmod(total_seconds, 60)

            if hours > 0:
                time_string = f"{hours:02}:{minutes:02}:{seconds:02}"
            else:
                time_string = f"{minutes:02}:{seconds:02}"
        else:
            mins, secs = divmod(self.timer_seconds, 60)
            time_string = f"{mins:02}:{secs:02}"
            
        self.timer_label.config(text=time_string)

    def adjust_score(self, score_var, change):
        """Adjusts the given score variable by the specified amount."""
        score_var.set(score_var.get() + change)

    def adjust_score_with_confirm(self, score_var, team_name):
        """Shows a confirmation pop-up before removing a goal."""
        if score_var.get() > 0:
            message = f"Are you sure you want to remove a goal from {team_name}?"
            response = messagebox.askyesno("Confirm Score Change", message)
            if response:
                self.adjust_score(score_var, -1)
        else:
            messagebox.showinfo("Cannot Decrease Score", "Score cannot be negative.")


if __name__ == "__main__":
    root = tk.Tk()
    app = MultiTabApp(root)
    root.mainloop()
