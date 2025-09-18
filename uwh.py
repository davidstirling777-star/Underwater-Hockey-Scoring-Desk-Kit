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

        self.variables = {
            "team_timeouts_allowed": {"default": False, "checkbox": True, "unit": "", "label": "Team time outs allowed?"},
            "start_first_game_at_this_time": {"default": 1, "checkbox": False, "unit": "hh:mm"},
            "half_period": {"default": 1, "checkbox": False, "unit": "minutes"},
            "half_time_break": {"default": 1, "checkbox": False, "unit": "minutes"},
            "overtime_allowed": {"default": False, "checkbox": True, "unit": "", "label": "Overtime allowed?"},
            "overtime_game_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "overtime_half_period": {"default": 1, "checkbox": True, "unit": "minutes"},
            "overtime_half_time_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "overtime_second_half": {"default": 1, "checkbox": True, "unit": "minutes"},
            "sudden_death_game_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "between_game_break": {"default": 1, "checkbox": False, "unit": "minutes"},
            "timeout_period": {"default": 1, "checkbox": True, "unit": "minutes"},
            "crib_time": {"default": 1, "checkbox": True, "unit": "seconds"}
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
            "game_no": font.Font(family="Arial", size=12),
            "button": font.Font(family="Arial", size=20, weight="bold"),
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

        self.reset_timer_button = None

        self.court_time_dt = None
        self.court_time_seconds = 0
        self.court_time_job = None
        self.court_time_paused = False

        self.in_timeout = False
        self.pending_timeout = None
        self.white_timeouts_this_half = 0
        self.black_timeouts_this_half = 0
        self.current_half = 0
        self.active_timeout_team = None

        self.sudden_death_timer_job = None
        self.sudden_death_seconds = 0

        self.team_timeouts_allowed_var = tk.BooleanVar(value=self.variables["team_timeouts_allowed"]["default"])
        self.overtime_allowed_var = tk.BooleanVar(value=self.variables["overtime_allowed"]["default"])

        self.create_scoreboard_tab()
        self.create_settings_tab()
        self.load_settings()
        self.setup_periods()
        self.reset_timer()

        self.master.bind('<Configure>', self.scale_fonts)
        self.initial_width = self.master.winfo_width()
        self.master.update_idletasks()
        self.scale_fonts(None)

    def create_scoreboard_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Scoreboard")
        for i, weight in enumerate([1, 2, 5, 1]):
            tab.grid_rowconfigure(i, weight=weight)
        for i in range(5):
            tab.grid_columnconfigure(i, weight=1)

        self.court_time_label = tk.Label(tab, text="Court Time is", font=self.fonts["court_time"])
        self.court_time_label.grid(row=0, column=0, columnspan=5, pady=1, sticky="nsew")
        self.half_label = tk.Label(tab, text="", font=self.fonts["half"], bg="lightblue")
        self.half_label.grid(row=1, column=0, columnspan=5, pady=1, sticky="nsew")

        scoreboard_frame = tk.Frame(tab, bg="grey")
        scoreboard_frame.grid(row=2, column=0, columnspan=5, sticky="nsew", padx=1, pady=1)
        for i in range(5):
            scoreboard_frame.grid_columnconfigure(i, weight=1)
        for i in range(5):
            scoreboard_frame.grid_rowconfigure(i, weight=1)

        self.white_label = tk.Label(scoreboard_frame, text="White", font=self.fonts["team"], bg="white", fg="black")
        self.white_label.grid(row=0, column=1, sticky="new", padx=5, pady=2)
        self.white_score = tk.Label(scoreboard_frame, textvariable=self.white_score_var, font=self.fonts["score"], bg="white", fg="black")
        self.white_score.grid(row=1, column=1, sticky="nsew", padx=5, pady=(0, 2))
        self.white_goal_button = tk.Button(scoreboard_frame, text="Add Goal", command=lambda: self.add_goal_with_confirmation(self.white_score_var, "White"), font=self.fonts["button"])
        self.white_goal_button.grid(row=2, column=1, sticky="ew", padx=2, pady=2)
        self.white_minus_button = tk.Button(scoreboard_frame, text="-ve Goal", command=lambda: self.adjust_score_with_confirm(self.white_score_var, "White"), font=self.fonts["button"])
        self.white_minus_button.grid(row=3, column=1, sticky="ew", padx=2, pady=2)

        self.white_timeout_button = tk.Button(
            scoreboard_frame,
            text="White Team\nTime Out",
            font=self.fonts["button"],
            bg="white",
            fg="black",
            justify="center",
            wraplength=180,
            height=2,
            command=self.white_team_timeout
        )
        self.white_timeout_button.grid(row=1, column=0, rowspan=3, sticky="ew", padx=2, pady=2, ipadx=10, ipady=10)

        self.timer_label = tk.Label(scoreboard_frame, text="00:00", font=self.fonts["timer"], bg="lightgrey", fg="darkblue")
        self.timer_label.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)

        self.black_label = tk.Label(scoreboard_frame, text="Black", font=self.fonts["team"], bg="black", fg="white")
        self.black_label.grid(row=0, column=3, sticky="new", padx=5, pady=2)
        self.black_score = tk.Label(scoreboard_frame, textvariable=self.black_score_var, font=self.fonts["score"], bg="black", fg="white")
        self.black_score.grid(row=1, column=3, sticky="nsew", padx=5, pady=(0, 2))
        self.black_goal_button = tk.Button(scoreboard_frame, text="Add Goal", command=lambda: self.add_goal_with_confirmation(self.black_score_var, "Black"), font=self.fonts["button"])
        self.black_goal_button.grid(row=2, column=3, sticky="ew", padx=2, pady=2)
        self.black_minus_button = tk.Button(scoreboard_frame, text="-ve Goal", command=lambda: self.adjust_score_with_confirm(self.black_score_var, "Black"), font=self.fonts["button"])
        self.black_minus_button.grid(row=3, column=3, sticky="ew", padx=2, pady=2)

        self.black_timeout_button = tk.Button(
            scoreboard_frame,
            text="Black Team\nTime Out",
            font=self.fonts["button"],
            bg="black",
            fg="white",
            justify="center",
            wraplength=180,
            height=2,
            command=self.black_team_timeout
        )
        self.black_timeout_button.grid(row=1, column=4, rowspan=3, sticky="ew", padx=2, pady=2, ipadx=10, ipady=10)

        game_info_frame = tk.Frame(tab)
        game_info_frame.grid(row=3, column=0, columnspan=5, pady=10, padx=10, sticky="ew")
        for i in range(5):
            game_info_frame.grid_columnconfigure(i, weight=1)
        self.game_no_label = tk.Label(game_info_frame, text="This is game No 121.", font=self.fonts["game_no"])
        self.game_no_label.grid(row=0, column=2, pady=5, sticky="ew")

        self.update_team_timeouts_allowed()

    def update_team_timeouts_allowed(self):
        allowed = self.team_timeouts_allowed_var.get()
        state = tk.NORMAL if allowed else tk.DISABLED
        self.white_timeout_button.config(state=state)
        self.black_timeout_button.config(state=state)

    def update_overtime_variables_state(self):
        overtime_enabled = self.overtime_allowed_var.get()
        for widget in self.widgets:
            name = widget.get("name", "")
            if name in ["overtime_game_break", "overtime_half_period", "overtime_half_time_break"]:
                label = widget.get("label_widget")
                entry = widget.get("entry")
                if overtime_enabled:
                    if label:
                        label.config(fg="black")
                    if entry:
                        entry.config(state="normal")
                else:
                    if label:
                        label.config(fg="grey")
                    if entry:
                        entry.config(state="disabled")

    def create_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Game Variables")
        frame = ttk.Frame(tab, padding=(10, 10, 10, 10))
        frame.pack(fill=tk.BOTH, expand=True)
        for i in range(5):
            frame.grid_columnconfigure(i, weight=0 if i < 4 else 1)

        default_font = font.nametofont("TkDefaultFont")
        new_size = default_font.cget("size") + 2
        headers = ["Use?", "Variable", "Value", "Units"]
        for i, h in enumerate(headers):
            tk.Label(frame, text=h, font=(default_font.cget("family"), new_size, "bold")).grid(row=0, column=i, sticky="w", padx=5, pady=5)

        row_idx = 1
        for var_name, var_info in self.variables.items():
            if var_name == "team_timeouts_allowed":
                check_var = self.team_timeouts_allowed_var
                cb = ttk.Checkbutton(frame, variable=check_var)
                cb.grid(row=row_idx, column=0, sticky="w", pady=5)
                label_text = var_info.get("label", "Team time outs allowed?")
                label_widget = tk.Label(frame, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=5)
                check_var.trace_add("write", lambda *args: self.update_team_timeouts_allowed())
                self.widgets.append({"name": var_name, "entry": None, "checkbox": check_var, "label_widget": label_widget})
                row_idx += 1
                continue
            if var_name == "overtime_allowed":
                check_var = self.overtime_allowed_var
                cb = ttk.Checkbutton(frame, variable=check_var)
                cb.grid(row=row_idx, column=0, sticky="w", pady=5)
                label_text = var_info.get("label", "Overtime allowed?")
                label_widget = tk.Label(frame, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=5)
                check_var.trace_add("write", lambda *args: self.update_overtime_variables_state())
                self.widgets.append({"name": var_name, "entry": None, "checkbox": check_var, "label_widget": label_widget})
                row_idx += 1
                continue
            check_var = tk.BooleanVar(value=True) if var_info["checkbox"] else None
            if check_var:
                cb = ttk.Checkbutton(frame, variable=check_var)
                cb.grid(row=row_idx, column=0, sticky="w", pady=5)
                check_var.trace_add("write", lambda *args, name=var_name: self._on_settings_variable_change())
            label_text = f"{var_name.replace('_', ' ').title()}:"
            label_widget = tk.Label(frame, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
            label_widget.grid(row=row_idx, column=1, sticky="w", pady=5)
            entry = ttk.Entry(frame, width=10)
            entry.insert(0, str(var_info["default"]))
            entry.grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
            tk.Label(frame, text=var_info["unit"], font=(default_font.cget("family"), new_size, "bold")).grid(row=row_idx, column=3, sticky="w", padx=5, pady=5)
            self.widgets.append({"name": var_name, "entry": entry, "checkbox": check_var, "label_widget": label_widget})
            self.last_valid_values[var_name] = entry.get()
            entry.bind("<FocusOut>", lambda e, name=var_name: self._on_settings_variable_change())
            entry.bind("<Return>", lambda e, name=var_name: self._on_settings_variable_change())
            row_idx += 1

        button_frame = ttk.Frame(tab)
        button_frame.pack(pady=10)
        self.reset_timer_button = ttk.Button(button_frame, text="Reset Timer", command=self.reset_timer)
        self.reset_timer_button.grid(row=0, column=0, padx=10)

        self.update_overtime_variables_state()

    # --- Game and Timer Logic ---

    def get_current_half(self):
        if self.in_sudden_death:
            return 99
        if self.periods == self.overtime_periods:
            if self.current_period_index < len(self.periods):
                name = self.periods[self.current_period_index]["name"].lower()
                if "first half" in name:
                    return 3
                elif "second half" in name:
                    return 4
        if self.current_period_index < len(self.periods):
            name = self.periods[self.current_period_index]["name"].lower()
            if "first half" in name:
                return 1
            elif "second half" in name:
                return 2
        return self.current_half if self.current_half else 1

    def reset_timeouts_for_half(self):
        self.white_timeouts_this_half = 0
        self.black_timeouts_this_half = 0

    def check_and_update_half(self):
        half = self.get_current_half()
        if half != self.current_half:
            self.current_half = half
            self.reset_timeouts_for_half()

    def white_team_timeout(self):
        if not self.team_timeouts_allowed_var.get():
            return
        self.check_and_update_half()
        if self.white_timeouts_this_half >= 1:
            self.show_timeout_popup("White")
            return
        if self.in_timeout:
            if self.active_timeout_team == "black" and self.pending_timeout is None:
                self.pending_timeout = "white"
            return
        self.white_timeouts_this_half += 1
        self.in_timeout = True
        self.active_timeout_team = "white"
        self.court_time_paused = True
        self.save_timer_state()
        timeout_seconds = int(float(self.variables["timeout_period"].get("value", self.variables["timeout_period"]["default"]))) * 60
        self.timer_seconds = timeout_seconds
        self.timer_running = True
        self.half_label.config(text="White Team Timeout")
        self.update_half_label_background("White Team Timeout")
        self.update_timer_display()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_job = self.master.after(1000, self.timeout_countdown)

    def black_team_timeout(self):
        if not self.team_timeouts_allowed_var.get():
            return
        self.check_and_update_half()
        if self.black_timeouts_this_half >= 1:
            self.show_timeout_popup("Black")
            return
        if self.in_timeout:
            if self.active_timeout_team == "white" and self.pending_timeout is None:
                self.pending_timeout = "black"
            return
        self.black_timeouts_this_half += 1
        self.in_timeout = True
        self.active_timeout_team = "black"
        self.court_time_paused = True
        self.save_timer_state()
        timeout_seconds = int(float(self.variables["timeout_period"].get("value", self.variables["timeout_period"]["default"]))) * 60
        self.timer_seconds = timeout_seconds
        self.timer_running = True
        self.half_label.config(text="Black Team Timeout")
        self.update_half_label_background("Black Team Timeout")
        self.update_timer_display()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_job = self.master.after(1000, self.timeout_countdown)

    def save_timer_state(self):
        self.saved_timer_running = self.timer_running
        self.saved_timer_seconds = self.timer_seconds
        self.saved_period_index = self.current_period_index
        self.saved_periods = self.periods
        self.saved_half_label = self.half_label.cget("text")
        self.saved_half_label_bg = self.half_label.cget("bg")
        self.saved_in_sudden_death = self.in_sudden_death
        self.saved_sudden_death_goal_scored = self.sudden_death_goal_scored

    def show_timeout_popup(self, team):
        popup = tk.Toplevel(self.master)
        popup.title("Timeout Limit")
        popup.geometry("350x100")
        label = tk.Label(popup, text="One time-out period per team per half", font=self.fonts["button"])
        label.pack(pady=20)
        btn = tk.Button(popup, text="OK", font=self.fonts["button"], command=popup.destroy)
        btn.pack(pady=5)

    def update_court_time(self):
        if self.court_time_paused or self.should_pause_court_time_for_period():
            self.court_time_job = self.master.after(1000, self.update_court_time)
            return
        current_dt = self.court_time_dt + datetime.timedelta(seconds=self.court_time_seconds)
        time_string = current_dt.strftime('%I:%M:%S %p').lstrip('0')
        self.court_time_label.config(text=f"Court Time is {time_string}")
        self.court_time_seconds += 1
        self.court_time_job = self.master.after(1000, self.update_court_time)

    def should_pause_court_time_for_period(self):
        period_name = ""
        if self.in_sudden_death and self.current_period_index < len(self.sudden_death_periods):
            period_name = self.sudden_death_periods[self.current_period_index]["name"].lower()
            return True
        elif self.periods == self.overtime_periods and self.current_period_index < len(self.periods):
            period_name = self.periods[self.current_period_index]["name"].lower()
        elif self.periods == self.sudden_death_periods and self.current_period_index < len(self.periods):
            period_name = self.periods[self.current_period_index]["name"].lower()
        elif self.current_period_index < len(self.periods):
            period_name = self.periods[self.current_period_index]["name"].lower()
        if any(sub in period_name for sub in ["overtime game break", "overtime first half", "overtime half time", "overtime second half", "sudden death game break", "sudden death"]):
            return True
        return False

    def timeout_countdown(self):
        self.update_timer_display()
        if not self.timer_running:
            return
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
            self.timer_job = self.master.after(1000, self.timeout_countdown)
        else:
            self.end_timeout()

    def end_timeout(self):
        self.in_timeout = False
        self.active_timeout_team = None
        self.court_time_paused = False
        self.timer_running = self.saved_timer_running
        self.timer_seconds = self.saved_timer_seconds
        self.current_period_index = self.saved_period_index
        self.periods = self.saved_periods
        self.half_label.config(text=self.saved_half_label)
        self.half_label.config(bg=self.saved_half_label_bg)
        self.in_sudden_death = self.saved_in_sudden_death
        self.sudden_death_goal_scored = self.saved_sudden_death_goal_scored
        self.update_timer_display()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        if self.pending_timeout == "white":
            self.pending_timeout = None
            self.white_team_timeout()
        elif self.pending_timeout == "black":
            self.pending_timeout = None
            self.black_team_timeout()
        elif self.timer_running:
            self.countdown_timer()

    def _on_settings_variable_change(self, *args):
        self.load_settings()
        self.setup_periods()

    def load_settings(self):
        for widget in self.widgets:
            entry = widget["entry"]
            var_name = widget["name"]
            if entry is not None:
                value = entry.get()
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
            self.sudden_death_periods.append({"name": "Sudden Death", "duration": None, "setting_name": "sudden_death"})

        self.periods.append({"name": "Between Game Break", "duration": minutes("between_game_break"), "setting_name": "between_game_break"})

    def countdown_timer(self):
        self.update_timer_display()
        if not self.timer_running:
            return
        if self.in_sudden_death and self.current_period_index < len(self.sudden_death_periods):
            period = self.sudden_death_periods[self.current_period_index]
            if period.get("setting_name") == "sudden_death":
                self.start_sudden_death_timer()
                return
        if self.timer_seconds > 0:
            if (self.timer_seconds == 30 and 
                self.current_period_index < len(self.periods) and
                self.periods[self.current_period_index].get("setting_name", "") == "between_game_break"):
                self.white_score_var.set(0)
                self.black_score_var.set(0)
            
            self.timer_seconds -= 1
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
            self.timer_job = self.master.after(1000, self.countdown_timer)
        else:
            self.next_period()

    def reset_timer(self):
        self.white_score_var.set(0)
        self.black_score_var.set(0)
        self.current_period_index = 0
        self.timer_running = True
        self.in_sudden_death = False
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        if self.sudden_death_timer_job:
            self.master.after_cancel(self.sudden_death_timer_job)
            self.sudden_death_timer_job = None
        self.sudden_death_seconds = 0
        if self.periods:
            self.timer_seconds = self.periods[0]["duration"]
            self.half_label.config(text=self.periods[0]["name"])
            self.update_half_label_background(self.periods[0]["name"])
        else:
            self.timer_seconds = 0
            self.half_label.config(text="")
        self.update_timer_display()
        self.court_time_dt = datetime.datetime.now()
        self.court_time_seconds = 0
        if self.court_time_job:
            self.master.after_cancel(self.court_time_job)
        self.court_time_paused = False
        self.update_court_time()
        self.countdown_timer()

    def update_timer_display(self):
        if self.in_sudden_death and self.current_period_index < len(self.sudden_death_periods):
            period = self.sudden_death_periods[self.current_period_index]
            if period.get("setting_name") == "sudden_death":
                mins, secs = divmod(self.sudden_death_seconds, 60)
                self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")
                return
        mins, secs = divmod(self.timer_seconds, 60)
        self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")

    def start_sudden_death_timer(self):
        self.update_timer_display()
        self.sudden_death_seconds += 1
        self.sudden_death_timer_job = self.master.after(1000, self.start_sudden_death_timer)

    def stop_sudden_death_timer(self):
        if self.sudden_death_timer_job:
            self.master.after_cancel(self.sudden_death_timer_job)
            self.sudden_death_timer_job = None

    def scale_fonts(self, event):
        pass

    def update_half_label_background(self, period_name):
        red_periods = {
            "half_time_break",
            "overtime_game_break",
            "overtime_half_time_break",
            "between_game_break",
            "start_first_game_at_this_time",
            "sudden_death_game_break",
            "white_team_timeout",
            "black_team_timeout"
        }
        internal_name = None
        for period in self.periods + self.overtime_periods + self.sudden_death_periods:
            if period["name"] == period_name:
                internal_name = period.get("setting_name", "")
                break
        if period_name in ["White Team Timeout", "Black Team Timeout"]:
            internal_name = period_name.lower().replace(" ", "_")
        if internal_name in red_periods:
            self.half_label.config(bg="red")
        else:
            self.half_label.config(bg="lightblue")

    def is_overtime_enabled(self):
        return self.overtime_allowed_var.get()

    def is_sudden_death_enabled(self):
        v = self.variables
        return v["sudden_death_game_break"].get("used", True)

    def is_break_or_half_time(self):
        break_names = {
            "half_time_break",
            "overtime_game_break",
            "overtime_half_time_break",
            "between_game_break",
            "sudden_death_game_break",
            "white_team_timeout",
            "black_team_timeout"
        }
        cur_period = None
        if self.current_period_index < len(self.periods):
            cur_period = self.periods[self.current_period_index]
        elif self.in_sudden_death and self.current_period_index < len(self.sudden_death_periods):
            cur_period = self.sudden_death_periods[self.current_period_index]
        elif not self.in_sudden_death and self.current_period_index < len(self.overtime_periods):
            cur_period = self.overtime_periods[self.current_period_index]
        if self.half_label.cget("text") in ["White Team Timeout", "Black Team Timeout"]:
            return True
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

        score_var.set(score_var.get() + 1)
        self.handle_tiebreak_and_overtime_logic()
        self.just_added_break_goal = False

    def adjust_score_with_confirm(self, score_var, team_name):
        if score_var.get() > 0:
            if messagebox.askyesno("Subtract Goal", f"Are you sure you want to subtract a goal from {team_name}?"):
                score_var.set(score_var.get() - 1)
                self.handle_tiebreak_and_overtime_logic()

    def handle_tiebreak_and_overtime_logic(self):
        if self.in_sudden_death and not self.sudden_death_goal_scored and (self.white_score_var.get() != self.black_score_var.get()):
            self.sudden_death_goal_scored = True
            self.timer_running = False
            self.stop_sudden_death_timer()
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            self.goto_between_game_break()
            return

        if self.periods and self.current_period_index < len(self.periods):
            cur_setting = self.periods[self.current_period_index].get("setting_name", "")
            if cur_setting == "between_game_break":
                if self.white_score_var.get() == self.black_score_var.get():
                    if self.is_overtime_enabled() and self.overtime_periods:
                        self.periods = self.overtime_periods + self.periods[self.current_period_index+1:]
                        self.current_period_index = 0
                        self.timer_seconds = self.periods[0]["duration"]
                        self.half_label.config(text=self.periods[0]["name"])
                        self.update_half_label_background(self.periods[0]["name"])
                        self.timer_running = True
                        self.countdown_timer()
                        return
                    elif self.is_sudden_death_enabled() and self.sudden_death_periods:
                        self.periods = self.sudden_death_periods + self.periods[self.current_period_index+1:]
                        self.current_period_index = 0
                        self.timer_seconds = self.sudden_death_periods[0]["duration"]
                        self.half_label.config(text=self.sudden_death_periods[0]["name"])
                        self.update_half_label_background(self.sudden_death_periods[0]["name"])
                        self.in_sudden_death = True
                        self.sudden_death_goal_scored = False
                        self.timer_running = True
                        self.countdown_timer()
                        return

        if self.periods and self.current_period_index > 2:
            cur_setting = self.periods[self.current_period_index].get("setting_name", "")
            if cur_setting == "second_half" and self.timer_seconds == 0:
                if self.white_score_var.get() == self.black_score_var.get():
                    if self.is_overtime_enabled() and self.overtime_periods:
                        self.periods = self.overtime_periods + self.periods[self.current_period_index+1:]
                        self.current_period_index = 0
                        self.timer_seconds = self.periods[0]["duration"]
                        self.half_label.config(text=self.periods[0]["name"])
                        self.update_half_label_background(self.periods[0]["name"])
                        self.timer_running = True
                        self.countdown_timer()
                        return
                    elif self.is_sudden_death_enabled() and self.sudden_death_periods:
                        self.periods = self.sudden_death_periods + self.periods[self.current_period_index+1:]
                        self.current_period_index = 0
                        self.timer_seconds = self.sudden_death_periods[0]["duration"]
                        self.half_label.config(text=self.sudden_death_periods[0]["name"])
                        self.update_half_label_background(self.sudden_death_periods[0]["name"])
                        self.in_sudden_death = True
                        self.sudden_death_goal_scored = False
                        self.timer_running = True
                        self.countdown_timer()
                        return
                self.goto_between_game_break()
                return

    def goto_between_game_break(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.stop_sudden_death_timer()
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
                self.timer_running = True
                self.countdown_timer()
                return
        self.timer_seconds = 0
        self.half_label.config(text="Game Over")
        self.update_half_label_background("Game Over")
        self.update_timer_display()
        if self.reset_timer_button:
            self.reset_timer_button.config(state=tk.NORMAL)
        self.timer_running = False

    def next_period(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        self.current_period_index += 1

        if self.periods == self.overtime_periods:
            overtime_second_half_idx = None
            for idx, p in enumerate(self.overtime_periods):
                if p.get("setting_name") == "overtime_second_half":
                    overtime_second_half_idx = idx
                    break
            if overtime_second_half_idx is not None and self.current_period_index > overtime_second_half_idx:
                if self.white_score_var.get() == self.black_score_var.get() and self.is_sudden_death_enabled():
                    self.periods = self.sudden_death_periods
                    self.current_period_index = 0
                    self.timer_seconds = self.sudden_death_periods[0]["duration"]
                    self.half_label.config(text=self.sudden_death_periods[0]["name"])
                    self.update_half_label_background(self.sudden_death_periods[0]["name"])
                    self.in_sudden_death = True
                    self.sudden_death_goal_scored = False
                    self.timer_running = True
                    self.countdown_timer()
                    return
                else:
                    self.goto_between_game_break()
                    return

        if self.periods == self.sudden_death_periods:
            if self.current_period_index < len(self.sudden_death_periods):
                period = self.sudden_death_periods[self.current_period_index]
                if period.get("setting_name") == "sudden_death":
                    self.sudden_death_seconds = 0
                    self.half_label.config(text=period["name"])
                    self.update_half_label_background(period["name"])
                    self.update_timer_display()
                    self.timer_running = True
                    self.start_sudden_death_timer()
                    return
            if self.current_period_index >= len(self.sudden_death_periods):
                self.goto_between_game_break()
                return

        if self.current_period_index >= len(self.periods):
            if self.white_score_var.get() == self.black_score_var.get():
                if self.is_overtime_enabled() and self.overtime_periods:
                    self.periods = self.overtime_periods
                    self.current_period_index = 0
                    self.timer_seconds = self.periods[0]["duration"]
                    self.half_label.config(text=self.periods[0]["name"])
                    self.update_half_label_background(self.periods[0]["name"])
                    self.timer_running = True
                    self.countdown_timer()
                    return
                elif self.is_sudden_death_enabled() and self.sudden_death_periods:
                    self.periods = self.sudden_death_periods
                    self.current_period_index = 0
                    self.timer_seconds = self.sudden_death_periods[0]["duration"]
                    self.half_label.config(text=self.sudden_death_periods[0]["name"])
                    self.update_half_label_background(self.sudden_death_periods[0]["name"])
                    self.in_sudden_death = True
                    self.sudden_death_goal_scored = False
                    self.timer_running = True
                    self.countdown_timer()
                    return
            self.goto_between_game_break()
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
