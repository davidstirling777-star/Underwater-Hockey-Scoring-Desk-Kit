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

        # All variables default to 1 (all entry fields will show "1")
        self.variables = {
            "team_timeouts_allowed": {"default": True, "checkbox": True, "unit": "", "label": "Team time outs allowed?"},
            "start_first_game_at_this_time": {"default": 1, "checkbox": False, "unit": "hh:mm"},
            "half_period": {"default": 1, "checkbox": False, "unit": "minutes"},
            "half_time_break": {"default": 1, "checkbox": False, "unit": "minutes"},
            "overtime_allowed": {"default": True, "checkbox": True, "unit": "", "label": "Overtime allowed?"},
            "overtime_game_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "overtime_half_period": {"default": 1, "checkbox": True, "unit": "minutes"},
            "overtime_half_time_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "sudden_death_game_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "between_game_break": {"default": 1, "checkbox": False, "unit": "minutes"},
            "timeout_period": {"default": 1, "checkbox": True, "unit": "minutes"},
            "crib_time": {"default": 1, "checkbox": True, "unit": "seconds"}
        }

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
        self.court_time_dt = None
        self.court_time_seconds = 0
        self.court_time_job = None
        self.court_time_paused = False
        self.timer_job = None

        self.reset_timer_button = None

        self.in_timeout = False
        self.pending_timeout = None
        self.white_timeouts_this_half = 0
        self.black_timeouts_this_half = 0
        self.current_half = 0
        self.active_timeout_team = None

        self.sudden_death_timer_job = None
        self.sudden_death_seconds = 0
        self.sudden_death_goal_scored = False

        self.full_sequence = []
        self.current_index = 0
        self.game_started = False  # Track if game has started

        self.widgets = []
        self.last_valid_values = {}

        self.team_timeouts_allowed_var = tk.BooleanVar(value=self.variables["team_timeouts_allowed"]["default"])
        self.overtime_allowed_var = tk.BooleanVar(value=self.variables["overtime_allowed"]["default"])

        self.create_scoreboard_tab()
        self.create_settings_tab()
        self.load_settings()
        self.build_game_sequence()
        self.reset_timer()

        self.master.bind('<Configure>', self.scale_fonts)
        self.initial_width = self.master.winfo_width()
        self.master.update_idletasks()
        self.scale_fonts(None)

    def get_minutes(self, varname):
        try:
            return int(float(self.variables[varname].get("value", self.variables[varname]["default"]))) * 60
        except Exception:
            return int(self.variables[varname]["default"]) * 60

    def build_game_sequence(self):
        seq = []
        if not self.game_started:
            seq.append({'name': 'Game Starts in:', 'type': 'break', 'duration': self.get_minutes('start_first_game_at_this_time')})
            self.game_started = True
        seq.append({'name': 'Between Game Break', 'type': 'break', 'duration': self.get_minutes('between_game_break')})
        seq.append({'name': 'First Half', 'type': 'regular', 'duration': self.get_minutes('half_period')})
        seq.append({'name': 'Half Time', 'type': 'break', 'duration': self.get_minutes('half_time_break')})
        seq.append({'name': 'Second Half', 'type': 'regular', 'duration': self.get_minutes('half_period')})
        if self.is_overtime_enabled():
            seq.append({'name': 'Overtime Game Break', 'type': 'break', 'duration': self.get_minutes('overtime_game_break')})
            seq.append({'name': 'Overtime First Half', 'type': 'overtime', 'duration': self.get_minutes('overtime_half_period')})
            seq.append({'name': 'Overtime Half Time', 'type': 'break', 'duration': self.get_minutes('overtime_half_time_break')})
            seq.append({'name': 'Overtime Second Half', 'type': 'overtime', 'duration': self.get_minutes('overtime_half_period')})
        if self.is_sudden_death_enabled():
            seq.append({'name': 'Sudden Death Game Break', 'type': 'break', 'duration': self.get_minutes('sudden_death_game_break')})
            seq.append({'name': 'Sudden Death', 'type': 'sudden_death', 'duration': None})
        self.full_sequence = seq
        self.current_index = 0

    def find_period_index(self, name):
        for idx, period in enumerate(self.full_sequence):
            if period['name'] == name:
                return idx
        return len(self.full_sequence) - 1

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
            if var_info["checkbox"]:
                var_info["default"] = True
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
            entry.insert(0, "1")
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

    def _on_settings_variable_change(self, *args):
        self.load_settings()
        self.build_game_sequence()
        self.reset_timer()

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

    def is_overtime_enabled(self):
        return self.overtime_allowed_var.get()

    def is_sudden_death_enabled(self):
        v = self.variables
        return v["sudden_death_game_break"].get("used", True)

    def reset_timeouts_for_half(self):
        self.white_timeouts_this_half = 0
        self.black_timeouts_this_half = 0
        period = self.full_sequence[self.current_index]
        if period['type'] in ['regular']:
            self.white_timeout_button.config(state=tk.NORMAL)
            self.black_timeout_button.config(state=tk.NORMAL)
        else:
            self.white_timeout_button.config(state=tk.DISABLED)
            self.black_timeout_button.config(state=tk.DISABLED)

    def white_team_timeout(self):
        period = self.full_sequence[self.current_index]
        if period['type'] != 'regular' or not self.team_timeouts_allowed_var.get():
            self.white_timeout_button.config(state=tk.DISABLED)
            return
        if self.white_timeouts_this_half >= 1:
            self.show_timeout_popup("White")
            return
        self.white_timeouts_this_half += 1
        self.white_timeout_button.config(state=tk.DISABLED)
        self.in_timeout = True
        self.active_timeout_team = "white"
        self.court_time_paused = True
        self.save_timer_state()
        timeout_seconds = self.get_minutes('timeout_period')
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
        period = self.full_sequence[self.current_index]
        if period['type'] != 'regular' or not self.team_timeouts_allowed_var.get():
            self.black_timeout_button.config(state=tk.DISABLED)
            return
        if self.black_timeouts_this_half >= 1:
            self.show_timeout_popup("Black")
            return
        self.black_timeouts_this_half += 1
        self.black_timeout_button.config(state=tk.DISABLED)
        self.in_timeout = True
        self.active_timeout_team = "black"
        self.court_time_paused = True
        self.save_timer_state()
        timeout_seconds = self.get_minutes('timeout_period')
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
        self.saved_index = self.current_index
        self.saved_half_label = self.half_label.cget("text")
        self.saved_half_label_bg = self.half_label.cget("bg")
        self.saved_sudden_death_goal_scored = getattr(self, "sudden_death_goal_scored", False)

    def show_timeout_popup(self, team):
        popup = tk.Toplevel(self.master)
        popup.title("Timeout Limit")
        popup.geometry("350x100")
        label = tk.Label(popup, text="One time-out period per team per half", font=self.fonts["button"])
        label.pack(pady=20)
        btn = tk.Button(popup, text="OK", font=self.fonts["button"], command=popup.destroy)
        btn.pack(pady=5)
        self.team_timeouts_allowed_var.set(False)

    def update_court_time(self):
        if self.court_time_paused:
            self.court_time_job = self.master.after(1000, self.update_court_time)
            return
        if self.court_time_dt is None:
            self.court_time_dt = datetime.datetime.now()
        current_dt = self.court_time_dt + datetime.timedelta(seconds=self.court_time_seconds)
        time_string = current_dt.strftime('%I:%M:%S %p').lstrip('0')
        self.court_time_label.config(text=f"Court Time is {time_string}")
        self.court_time_seconds += 1
        self.court_time_job = self.master.after(1000, self.update_court_time)

    def timeout_countdown(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.update_timer_display()
        if not self.timer_running:
            return
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.timer_job = self.master.after(1000, self.timeout_countdown)
        else:
            self.end_timeout()

    def end_timeout(self):
        self.in_timeout = False
        self.active_timeout_team = None
        self.court_time_paused = False
        self.timer_running = self.saved_timer_running
        self.timer_seconds = self.saved_timer_seconds
        self.current_index = self.saved_index
        self.half_label.config(text=self.saved_half_label)
        self.half_label.config(bg=self.saved_half_label_bg)
        self.update_timer_display()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        if self.timer_running:
            self.timer_job = self.master.after(1000, self.countdown_timer)

    def update_half_label_background(self, period_name):
        red_periods = {
            "game_starts_in:",
            "half_time",
            "half_time_break",
            "overtime_game_break",
            "overtime_half_time",
            "overtime_half_time_break",
            "between_game_break",
            "start_first_game_at_this_time",
            "sudden_death_game_break",
            "white_team_timeout",
            "black_team_timeout"
        }
        internal_name = period_name.lower().replace(" ", "_")
        if internal_name in red_periods:
            self.half_label.config(bg="red")
        else:
            self.half_label.config(bg="lightblue")

    def countdown_timer(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.update_timer_display()
        if not self.timer_running:
            return
        if self.timer_seconds > 0:
            self.timer_seconds -= 1

            cur_period = self.full_sequence[self.current_index] if self.full_sequence and self.current_index < len(self.full_sequence) else None
            if cur_period and cur_period['name'] == 'Between Game Break' and self.timer_seconds == 30:
                self.white_score_var.set(0)
                self.black_score_var.set(0)

            self.timer_job = self.master.after(1000, self.countdown_timer)
        else:
            self.next_period()

    def reset_timer(self):
        self.white_score_var.set(0)
        self.black_score_var.set(0)
        self.current_index = 0
        self.timer_running = True
        self.sudden_death_goal_scored = False
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.sudden_death_timer_job = None
        self.sudden_death_seconds = 0
        if self.full_sequence:
            self.timer_seconds = self.full_sequence[0]["duration"]
            self.half_label.config(text=self.full_sequence[0]["name"])
            self.update_half_label_background(self.full_sequence[0]["name"])
        else:
            self.timer_seconds = 0
            self.half_label.config(text="")
        self.update_timer_display()
        self.court_time_dt = datetime.datetime.now()
        self.court_time_seconds = 0
        self.court_time_paused = False
        self.update_court_time()
        self.start_current_period()

    def start_current_period(self):
        if self.current_index >= len(self.full_sequence):
            self.current_index = self.find_period_index('Between Game Break')
        cur_period = self.full_sequence[self.current_index]
        self.half_label.config(text=cur_period['name'])
        self.update_half_label_background(cur_period['name'])

        # Pause court time during overtime and sudden death periods
        paused_periods = [
            'Overtime Game Break',
            'Overtime First Half',
            'Overtime Half Time',
            'Overtime Second Half',
            'Sudden Death Game Break',
            'Sudden Death'
        ]
        if cur_period['name'] in paused_periods:
            self.court_time_paused = True
        else:
            self.court_time_paused = False

        if cur_period['name'] == 'Sudden Death':
            self.timer_running = True
            self.sudden_death_seconds = 0
            self.update_timer_display()
            self.start_sudden_death_timer()
            self.reset_timeouts_for_half()
        else:
            self.timer_seconds = cur_period['duration'] if cur_period['duration'] is not None else 0
            self.update_timer_display()
            self.timer_running = True
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            self.timer_job = self.master.after(1000, self.countdown_timer)
            self.reset_timeouts_for_half()

    def next_period(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        if self.current_index >= len(self.full_sequence):
            self.current_index = self.find_period_index('Between Game Break')
            self.start_current_period()
            return

        cur_period = self.full_sequence[self.current_index]
        period_name = cur_period['name']

        if period_name == 'Overtime Second Half':
            if self.white_score_var.get() != self.black_score_var.get():
                self.current_index = self.find_period_index('Between Game Break')
                self.start_current_period()
                return

        if period_name == 'Sudden Death' and self.sudden_death_goal_scored:
            self.current_index = self.find_period_index('Between Game Break')
            self.start_current_period()
            return

        self.current_index += 1

        if self.current_index < len(self.full_sequence):
            next_period = self.full_sequence[self.current_index]
            if next_period['name'] == 'Between Game Break':
                self.current_index = self.find_period_index('First Half')
                self.start_current_period()
                return

        if self.current_index >= len(self.full_sequence):
            self.current_index = self.find_period_index('Between Game Break')
            self.start_current_period()
            return

        self.start_current_period()

    def start_sudden_death_timer(self):
        if not self.timer_running:
            return
        self.sudden_death_seconds += 1
        self.update_timer_display()
        self.sudden_death_timer_job = self.master.after(1000, self.start_sudden_death_timer)

    def stop_sudden_death_timer(self):
        if self.sudden_death_timer_job:
            self.master.after_cancel(self.sudden_death_timer_job)
            self.sudden_death_timer_job = None

    def goto_between_game_break(self):
        idx = self.find_period_index('Between Game Break')
        self.current_index = idx
        self.start_current_period()

    def update_timer_display(self):
        cur_period = self.full_sequence[self.current_index] if self.full_sequence and self.current_index < len(self.full_sequence) else None
        if cur_period and cur_period['name'] == 'Sudden Death':
            mins, secs = divmod(self.sudden_death_seconds, 60)
            self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")
        else:
            mins, secs = divmod(self.timer_seconds, 60)
            self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")

    def scale_fonts(self, event):
        pass

    def add_goal_with_confirmation(self, score_var, team_name):
        cur_period = self.full_sequence[self.current_index]
        is_break = (cur_period['type'] == 'break'
            or cur_period['name'] in ["White Team Timeout", "Black Team Timeout"])

        # Only show confirmation and add goal if user agrees
        if is_break:
            if not messagebox.askyesno(
                "Add Goal During Break?",
                f"You are about to add a goal for {team_name} during a break or half time. Are you sure?"
            ):
                return

        score_var.set(score_var.get() + 1)

        # Overtime Game Break or Sudden Death Game Break logic: handle post-goal transitions
        if cur_period['name'] in ['Overtime Game Break', 'Sudden Death Game Break']:
            if self.white_score_var.get() != self.black_score_var.get():
                self.current_index = self.find_period_index('Between Game Break')
                self.start_current_period()
                return
            elif self.white_score_var.get() == self.black_score_var.get():
                for idx in range(self.current_index + 1, len(self.full_sequence)):
                    next_period = self.full_sequence[idx]
                    if next_period['name'] in ['Overtime First Half', 'Sudden Death']:
                        self.current_index = idx
                        self.start_current_period()
                        return

        if cur_period['name'] == 'Sudden Death' and not getattr(self, 'sudden_death_goal_scored', False):
            self.sudden_death_goal_scored = True
            self.timer_running = False
            self.stop_sudden_death_timer()
            self.goto_between_game_break()

    def adjust_score_with_confirm(self, score_var, team_name):
        if score_var.get() > 0:
            if messagebox.askyesno("Remove Goal", f"Are you sure you want to remove a goal from {team_name}?"):
                score_var.set(score_var.get() - 1)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameManagementApp(root)
    root.mainloop()
