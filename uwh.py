import tkinter as tk
from tkinter import ttk, messagebox, font
import datetime

class GameManagementApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Underwater Hockey Game Management App")
        self.master.geometry('1200x800')

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.settings_file = "game_settings.json"
        self.variables = {
            "start_first_game_at_this_time": {"default": "12:00", "checkbox": False, "unit": "hh:mm"},
            "half_period": {"default": 15, "checkbox": False, "unit": "minutes"},
            "half_time_break": {"default": 3, "checkbox": False, "unit": "minutes"},
            "overtime_game_break": {"default": 3, "checkbox": True, "unit": "minutes"},  # CHANGED
            "overtime_half_period": {"default": 5, "checkbox": True, "unit": "minutes"},
            "overtime_half_time_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "overtime_second_half": {"default": 5, "checkbox": True, "unit": "minutes"},
            "sudden_death_game_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "between_game_break": {"default": 5, "checkbox": False, "unit": "minutes"},
            "timeout_period": {"default": 1, "checkbox": True, "unit": "minutes"},
            "crib_time": {"default": 60, "checkbox": True, "unit": "seconds"}
        }
        self.periods = []
        self.overtime_periods = []
        self.sudden_death_periods = []
        self.widgets = []
        self.last_valid_values = {}

        self.fonts = {
            "court_time": font.Font(family="Arial", size=36),
            "half": font.Font(family="Arial", size=36, weight="bold"),
            "team": font.Font(family="Arial", size=30, weight="bold"),
            "score": font.Font(family="Arial", size=200, weight="bold"),
            "timer": font.Font(family="Arial", size=90, weight="bold"),
            "game_no": font.Font(family="Arial", size=18)
        }
        self.white_score_var = tk.IntVar(value=0)
        self.black_score_var = tk.IntVar(value=0)

        self.timer_running = False
        self.timer_seconds = 0
        self.current_period_index = 0
        self.timer_job = None
        self.in_sudden_death = False
        self.sudden_death_goal_scored = False
        self.just_added_break_goal = False

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

    def create_scoreboard_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Scoreboard")
        for i, weight in enumerate([1, 2, 5, 1]):
            tab.grid_rowconfigure(i, weight=weight)
        for i in range(3):
            tab.grid_columnconfigure(i, weight=1)

        self.court_time_label = tk.Label(
            tab, text="Court Time is", font=self.fonts["court_time"]
        )
        self.court_time_label.grid(row=0, column=0, columnspan=3, pady=1, sticky="nsew")
        self.half_label = tk.Label(
            tab, text="", font=self.fonts["half"], bg="lightblue"
        )
        self.half_label.grid(row=1, column=0, columnspan=3, pady=1, sticky="nsew")

        scoreboard_frame = tk.Frame(tab, bg="grey")
        scoreboard_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", padx=1, pady=1)
        for i, weight in enumerate([1, 5, 1]):
            scoreboard_frame.grid_rowconfigure(i, weight=weight)
        for i in range(3):
            scoreboard_frame.grid_columnconfigure(i, weight=1)

        self.white_label = tk.Label(scoreboard_frame, text="White", font=self.fonts["team"], bg="white", fg="black")
        self.white_label.grid(row=0, column=0, sticky="new", padx=5, pady=2)
        self.white_score = tk.Label(scoreboard_frame, textvariable=self.white_score_var, font=self.fonts["score"], bg="white", fg="black")
        self.white_score.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 2))

        self.timer_label = tk.Label(scoreboard_frame, text="00:00", font=self.fonts["timer"], bg="lightgrey", fg="darkblue")
        self.timer_label.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)

        self.black_label = tk.Label(scoreboard_frame, text="Black", font=self.fonts["team"], bg="black", fg="white")
        self.black_label.grid(row=0, column=2, sticky="new", padx=5, pady=2)
        self.black_score = tk.Label(scoreboard_frame, textvariable=self.black_score_var, font=self.fonts["score"], bg="black", fg="white")
        self.black_score.grid(row=1, column=2, sticky="nsew", padx=5, pady=(0, 2))

        game_info_frame = tk.Frame(tab)
        game_info_frame.grid(row=3, column=0, columnspan=3, pady=10, padx=10, sticky="ew")
        for i in range(3):
            game_info_frame.grid_columnconfigure(i, weight=1)

        score_button_frame_white = ttk.Frame(game_info_frame)
        score_button_frame_white.grid(row=0, column=0, sticky="ew")
        score_button_frame_white.grid_columnconfigure(0, weight=1)
        ttk.Button(score_button_frame_white, text="Add Goal", command=lambda: self.add_goal_with_confirmation(self.white_score_var, "White")).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(score_button_frame_white, text="-ve Goal", command=lambda: self.adjust_score_with_confirm(self.white_score_var, "White")).grid(row=1, column=0, padx=2, pady=2)

        self.game_no_label = tk.Label(game_info_frame, text="This is game No 121.", font=self.fonts["game_no"])
        self.game_no_label.grid(row=0, column=1, pady=10, sticky="ew")

        score_button_frame_black = ttk.Frame(game_info_frame)
        score_button_frame_black.grid(row=0, column=2, sticky="ew")
        score_button_frame_black.grid_columnconfigure(0, weight=1)
        ttk.Button(score_button_frame_black, text="Add Goal", command=lambda: self.add_goal_with_confirmation(self.black_score_var, "Black")).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(score_button_frame_black, text="-ve Goal", command=lambda: self.adjust_score_with_confirm(self.black_score_var, "Black")).grid(row=1, column=0, padx=2, pady=2)

    def create_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Game Variables")
        frame = ttk.Frame(tab, padding=(10, 10, 10, 10))
        frame.pack(fill=tk.BOTH, expand=True)
        for i in range(5):
            frame.grid_columnconfigure(i, weight=0 if i < 4 else 1)

        style = ttk.Style()
        default_font = font.nametofont("TkDefaultFont")
        new_size = default_font.cget("size") + 2
        style.configure("Settings.TLabel", font=(default_font.cget("family"), new_size, "bold"))
        headers = ["Use?", "Variable", "Value", "Units"]
        for i, h in enumerate(headers):
            ttk.Label(frame, text=h, style="Settings.TLabel").grid(row=0, column=i, sticky="w", padx=5, pady=5)

        style.configure("Settings.TLabel", font=(default_font.cget("family"), new_size))
        for i, (var_name, var_info) in enumerate(self.variables.items(), 1):
            check_var = tk.BooleanVar(value=True) if var_info["checkbox"] else None
            if check_var:
                cb = ttk.Checkbutton(frame, variable=check_var)
                cb.grid(row=i, column=0, sticky="w", pady=5)
                check_var.trace_add("write", lambda *args, name=var_name: self._on_settings_variable_change())
            label_text = f"{var_name.replace('_', ' ').title()}:"
            ttk.Label(frame, text=label_text, style="Settings.TLabel").grid(row=i, column=1, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=10)
            entry.insert(0, str(var_info["default"]))
            entry.grid(row=i, column=2, sticky="w", padx=5, pady=5)
            ttk.Label(frame, text=var_info["unit"], style="Settings.TLabel").grid(row=i, column=3, sticky="w", padx=5, pady=5)
            self.widgets.append({"name": var_name, "entry": entry, "checkbox": check_var})
            self.last_valid_values[var_name] = entry.get()
            entry.bind("<FocusOut>", lambda e, name=var_name: self._on_settings_variable_change())
            entry.bind("<Return>", lambda e, name=var_name: self._on_settings_variable_change())

        button_frame = ttk.Frame(tab)
        button_frame.pack(pady=10)
        self.start_timer_button = ttk.Button(button_frame, text="Start Timer", command=self.start_pause_timer)
        self.start_timer_button.grid(row=0, column=0, padx=10)
        self.reset_timer_button = ttk.Button(button_frame, text="Reset Timer", command=self.reset_timer)
        self.reset_timer_button.grid(row=0, column=1, padx=10)

    def _on_settings_variable_change(self, *args):
        self.load_settings()
        self.setup_periods()
        self.reset_timer()

    def load_settings(self):
        for widget in self.widgets:
            entry = widget["entry"]
            value = entry.get()
            var_name = widget["name"]
            self.variables[var_name]["value"] = value
            if widget["checkbox"] is not None:
                self.variables[var_name]["used"] = widget["checkbox"].get()
            else:
                self.variables[var_name]["used"] = True

    def setup_periods(self):
        self.periods = []
        self.overtime_periods = []
        self.sudden_death_periods = []
        v = self.variables

        def int_or_default(name):
            try:
                return int(float(v[name].get("value", v[name]["default"])))
            except Exception:
                return v[name]["default"]

        def minutes(name):
            return int_or_default(name) * 60

        # Add "Game Starts in:" as the first period (fixed for start timer)
        start_first_game = v["start_first_game_at_this_time"].get("value", v["start_first_game_at_this_time"]["default"])
        if isinstance(start_first_game, str) and ":" in start_first_game:
            try:
                now = datetime.datetime.now()
                hh, mm = map(int, start_first_game.split(":"))
                start_time = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if start_time < now:
                    start_time += datetime.timedelta(days=1)
                seconds_until = int((start_time - now).total_seconds())
            except Exception:
                seconds_until = 0
        else:
            seconds_until = minutes("start_first_game_at_this_time")
        self.periods.append({
            "name": "Game Starts in:",
            "duration": seconds_until,
            "setting_name": "start_first_game_at_this_time"
        })

        self.periods.append({"name": "First Half", "duration": minutes("half_period"), "setting_name": "half_period"})
        self.periods.append({"name": "Half Time", "duration": minutes("half_time_break"), "setting_name": "half_time_break"})
        self.periods.append({"name": "Second Half", "duration": minutes("half_period"), "setting_name": "half_period"})

        if v["overtime_game_break"].get("used", True):
            self.overtime_periods.append({"name": "Overtime Game Break", "duration": minutes("overtime_game_break"), "setting_name": "overtime_game_break"})
        if v["overtime_half_period"].get("used", True):
            self.overtime_periods.append({"name": "Overtime First Half", "duration": minutes("overtime_half_period"), "setting_name": "overtime_half_period"})
        if v["overtime_half_time_break"].get("used", True):
            self.overtime_periods.append({"name": "Overtime Half Time", "duration": minutes("overtime_half_time_break"), "setting_name": "overtime_half_time_break"})
        if v["overtime_second_half"].get("used", True):
            self.overtime_periods.append({"name": "Overtime Second Half", "duration": minutes("overtime_second_half"), "setting_name": "overtime_second_half"})
        if v["sudden_death_game_break"].get("used", True):
            self.sudden_death_periods.append({"name": "Sudden Death Game Break", "duration": minutes("sudden_death_game_break"), "setting_name": "sudden_death_game_break"})
            self.sudden_death_periods.append({"name": "Sudden Death", "duration": 60*60, "setting_name": "sudden_death"})

        self.periods.append({"name": "Between Game Break", "duration": minutes("between_game_break"), "setting_name": "between_game_break"})

    def start_pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
        else:
            # Cancel any existing timer job before starting
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            self.timer_running = True
            self.countdown_timer()

    def countdown_timer(self):
        self.update_timer_display()
        if not self.timer_running:
            return
        if self.timer_seconds > 0:
            # Check for auto-reset at 30 seconds during Between Game Break
            if (self.timer_seconds == 30 and 
                self.current_period_index < len(self.periods) and
                self.periods[self.current_period_index].get("setting_name", "") == "between_game_break"):
                # Auto-reset scores to 0 at 30 seconds remaining
                self.white_score_var.set(0)
                self.black_score_var.set(0)
            
            self.timer_seconds -= 1
            # Cancel any existing timer job before scheduling new one
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
            self.timer_job = self.master.after(1000, self.countdown_timer)
        else:
            self.next_period()

    def reset_timer(self):
        self.white_score_var.set(0)
        self.black_score_var.set(0)
        self.current_period_index = 0
        self.timer_running = False
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        if self.periods:
            self.timer_seconds = self.periods[0]["duration"]
            self.half_label.config(text=self.periods[0]["name"])
            self.update_half_label_background(self.periods[0]["name"])
        else:
            self.timer_seconds = 0
            self.half_label.config(text="")
        self.update_timer_display()

    def update_timer_display(self):
        mins, secs = divmod(self.timer_seconds, 60)
        self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")

    def scale_fonts(self, event):
        pass

    def update_court_time(self):
        now = datetime.datetime.now()
        time_string = now.strftime('%I:%M:%S %p').lstrip('0')
        self.court_time_label.config(text=f"Court Time is {time_string}")
        self.master.after(1000, self.update_court_time)

    def update_half_label_background(self, period_name):
        red_periods = {
            "half_time_break",
            "overtime_game_break",
            "overtime_half_time_break",
            "between_game_break",
            "start_first_game_at_this_time",
        }
        internal_name = None
        for period in self.periods + self.overtime_periods + self.sudden_death_periods:
            if period["name"] == period_name:
                internal_name = period.get("setting_name", "")
                break
        if internal_name in red_periods:
            self.half_label.config(bg="red")
        else:
            self.half_label.config(bg="lightblue")

    def is_overtime_enabled(self):
        """Check if overtime periods are enabled via checkboxes"""
        v = self.variables
        return (v["overtime_game_break"].get("used", True) or 
                v["overtime_half_period"].get("used", True) or
                v["overtime_half_time_break"].get("used", True) or
                v["overtime_second_half"].get("used", True))

    def is_sudden_death_enabled(self):
        """Check if sudden death periods are enabled via checkboxes"""
        v = self.variables
        return v["sudden_death_game_break"].get("used", True)

    def is_break_or_half_time(self):
        break_names = {
            "half_time_break",
            "overtime_game_break",
            "overtime_half_time_break",
            "between_game_break",
        }
        cur_period = None
        if self.current_period_index < len(self.periods):
            cur_period = self.periods[self.current_period_index]
        elif self.in_sudden_death and self.current_period_index < len(self.sudden_death_periods):
            cur_period = self.sudden_death_periods[self.current_period_index]
        elif not self.in_sudden_death and self.current_period_index < len(self.overtime_periods):
            cur_period = self.overtime_periods[self.current_period_index]
        if cur_period:
            return cur_period.get("setting_name", "") in break_names
        return False

    def add_goal_with_confirmation(self, score_var, team_name):
        if self.is_break_or_half_time():
            if not messagebox.askyesno("Add Goal During Break?", f"You are about to add a goal for {team_name} during a break or half time. Are you sure?"):
                return
            self.just_added_break_goal = True
        else:
            self.just_added_break_goal = False

        if self.in_sudden_death and not self.sudden_death_goal_scored:
            score_var.set(score_var.get() + 1)
            self.sudden_death_goal_scored = True
            self.timer_running = False
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            self.goto_between_game_break()
            return

        score_var.set(score_var.get() + 1)
        if self.just_added_break_goal and self.white_score_var.get() == self.black_score_var.get():
            self.handle_tiebreak_after_break()
        self.just_added_break_goal = False

    def adjust_score_with_confirm(self, score_var, team_name):
        if score_var.get() > 0:
            if messagebox.askyesno("Subtract Goal", f"Are you sure you want to subtract a goal from {team_name}?"):
                score_var.set(score_var.get() - 1)

    def handle_tiebreak_after_break(self):
        # Cancel any existing timer job first
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
            
        cur_setting = self.periods[self.current_period_index].get("setting_name", "")
        if cur_setting == "between_game_break":
            if self.overtime_periods and self.is_overtime_enabled():
                self.periods = self.overtime_periods + self.periods[self.current_period_index+1:]
                self.current_period_index = 0
                self.timer_seconds = self.periods[0]["duration"]
                self.half_label.config(text=self.periods[0]["name"])
                self.update_half_label_background(self.periods[0]["name"])
                self.timer_running = False  # Ensure state is correct before starting
                self.start_pause_timer()
            elif self.sudden_death_periods and self.is_sudden_death_enabled():
                self.periods = self.sudden_death_periods + self.periods[self.current_period_index+1:]
                self.current_period_index = 0
                self.timer_seconds = self.periods[0]["duration"]
                self.half_label.config(text=self.periods[0]["name"])
                self.update_half_label_background(self.periods[0]["name"])
                self.in_sudden_death = True
                self.sudden_death_goal_scored = False
                self.timer_running = False  # Ensure state is correct before starting
                self.start_pause_timer()
            else:
                # No overtime/sudden death enabled or available, loop back to First Half
                self.setup_periods()
                self.current_period_index = 1  # First Half
                self.timer_seconds = self.periods[1]["duration"]
                self.half_label.config(text=self.periods[1]["name"])
                self.update_half_label_background(self.periods[1]["name"])
                self.timer_running = False  # Ensure state is correct before starting
                self.start_pause_timer()
        elif cur_setting in {"half_time_break", "overtime_game_break", "overtime_half_time_break"}:
            if self.overtime_periods and self.is_overtime_enabled() and cur_setting != "overtime_half_time_break":
                self.periods = self.overtime_periods + self.periods[self.current_period_index+1:]
                self.current_period_index = 0
                self.timer_seconds = self.periods[0]["duration"]
                self.half_label.config(text=self.periods[0]["name"])
                self.update_half_label_background(self.periods[0]["name"])
                self.timer_running = False  # Ensure state is correct before starting
                self.start_pause_timer()
            elif self.sudden_death_periods and self.is_sudden_death_enabled() and cur_setting == "overtime_half_time_break":
                self.periods = self.sudden_death_periods + self.periods[self.current_period_index+1:]
                self.current_period_index = 0
                self.timer_seconds = self.periods[0]["duration"]
                self.half_label.config(text=self.periods[0]["name"])
                self.update_half_label_background(self.periods[0]["name"])
                self.in_sudden_death = True
                self.sudden_death_goal_scored = False
                self.timer_running = False  # Ensure state is correct before starting
                self.start_pause_timer()

    def goto_between_game_break(self):
        # Cancel any existing timer job first
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
            
        # Reset to main periods to find the "Between Game Break" period
        # This ensures we can find it regardless of whether we're in overtime or sudden death
        self.setup_periods()
        self.in_sudden_death = False
        
        for i, period in enumerate(self.periods):
            if period.get("setting_name", "") == "between_game_break":
                self.current_period_index = i
                self.timer_seconds = period["duration"]
                self.half_label.config(text=period["name"])
                self.update_half_label_background(period["name"])
                self.update_timer_display()
                self.sudden_death_goal_scored = False
                self.timer_running = False  # Ensure state is correct before starting
                self.start_pause_timer()
                return
        self.timer_seconds = 0
        self.half_label.config(text="Game Over")
        self.update_half_label_background("Game Over")
        self.update_timer_display()
        if self.start_timer_button:
            self.start_timer_button.config(text="Game Over", state="disabled")
        if self.reset_timer_button:
            self.reset_timer_button.config(state=tk.NORMAL)
        self.timer_running = False

    def next_period(self):
        # Cancel any existing timer job first
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        
        self.current_period_index += 1
        if self.current_period_index >= len(self.periods):
            # Check if scores are tied and overtime/sudden death should be triggered
            if self.white_score_var.get() == self.black_score_var.get():
                if self.overtime_periods and self.is_overtime_enabled():
                    self.periods = self.overtime_periods
                    self.current_period_index = 0
                    self.timer_seconds = self.periods[0]["duration"]
                    self.half_label.config(text=self.periods[0]["name"])
                    self.update_half_label_background(self.periods[0]["name"])
                    self.timer_running = False  # Ensure state is correct before starting
                    self.start_pause_timer()
                    return
                elif self.sudden_death_periods and self.is_sudden_death_enabled():
                    self.periods = self.sudden_death_periods
                    self.current_period_index = 0
                    self.timer_seconds = self.periods[0]["duration"]
                    self.half_label.config(text=self.periods[0]["name"])
                    self.update_half_label_background(self.periods[0]["name"])
                    self.in_sudden_death = True
                    self.sudden_death_goal_scored = False
                    self.timer_running = False  # Ensure state is correct before starting
                    self.start_pause_timer()
                    return
            # No overtime/sudden death, or scores not tied - start new game
            self.setup_periods()
            self.current_period_index = 0
            self.timer_seconds = self.periods[0]["duration"]
            self.half_label.config(text=self.periods[0]["name"])
            self.update_half_label_background(self.periods[0]["name"])
            self.timer_running = False  # Ensure state is correct before starting
            self.start_pause_timer()
            return
        cur_period = self.periods[self.current_period_index]
        self.timer_seconds = cur_period["duration"]
        self.half_label.config(text=cur_period["name"])
        self.update_half_label_background(cur_period["name"])
        self.update_timer_display()
        self.timer_running = True
        self.countdown_timer()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameManagementApp(root)
    root.mainloop()
