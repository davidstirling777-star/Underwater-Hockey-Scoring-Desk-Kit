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
            "team_timeouts_allowed": {"default": True, "checkbox": True, "unit": "", "label": "Team time-outs allowed?"},
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
            "timeout_button": font.Font(family="Arial", size=20, weight="bold"),
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
        self.game_started = False
        self.widgets = []
        self.last_valid_values = {}
        self.team_timeouts_allowed_var = tk.BooleanVar(value=self.variables["team_timeouts_allowed"]["default"])
        self.overtime_allowed_var = tk.BooleanVar(value=self.variables["overtime_allowed"]["default"])
        self.referee_timeout_active = False
        self.referee_timeout_elapsed = 0
        self.referee_timeout_default_bg = "red"
        self.referee_timeout_default_fg = "black"
        self.referee_timeout_active_bg = "black"
        self.referee_timeout_active_fg = "red"
        self.saved_state = {}
        self.stored_penalties = []

        self.create_scoreboard_tab()
        self.create_settings_tab()
        self.load_settings()
        self.build_game_sequence()
        self.reset_timer()
        self.master.bind('<Configure>', self.scale_fonts)
        self.initial_width = self.master.winfo_width()
        self.master.update_idletasks()
        self.scale_fonts(None)
        self.create_display_window()

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
        for i in range(11):
            tab.grid_rowconfigure(i, weight=1)
        for i in range(6):
            tab.grid_columnconfigure(i, weight=1)

        self.court_time_label = tk.Label(tab, text="Court Time is", font=self.fonts["court_time"], bg="lightgrey")
        self.court_time_label.grid(row=0, column=0, columnspan=6, padx=1, pady=1, sticky="nsew")
        self.half_label = tk.Label(tab, text="", font=self.fonts["half"], bg="lightcoral")
        self.half_label.grid(row=1, column=0, columnspan=6, padx=1, pady=1, sticky="nsew")
        self.white_label = tk.Label(tab, text="White", font=self.fonts["team"], bg="white", fg="black")
        self.white_label.grid(row=2, column=0, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.white_score = tk.Label(tab, textvariable=self.white_score_var, font=self.fonts["score"], bg="white", fg="black")
        self.white_score.grid(row=3, column=0, rowspan=6, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.timer_label = tk.Label(tab, text="00:00", font=self.fonts["timer"], bg="lightgrey", fg="black")
        self.timer_label.grid(row=3, column=2, rowspan=6, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.black_label = tk.Label(tab, text="Black", font=self.fonts["team"], bg="black", fg="white")
        self.black_label.grid(row=2, column=4, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.black_score = tk.Label(tab, textvariable=self.black_score_var, font=self.fonts["score"], bg="black", fg="white")
        self.black_score.grid(row=3, column=4, rowspan=6, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.white_timeout_button = tk.Button(
            tab, text="White Team\nTime-Out", font=self.fonts["timeout_button"], bg="white", fg="black",
            activebackground="white", activeforeground="black",
            justify="center", wraplength=180, height=2, command=self.white_team_timeout
        )
        self.white_timeout_button.grid(row=9, column=0, rowspan=2, padx=1, pady=1, sticky="nsew")

        self.white_goal_button = tk.Button(
            tab, text="Add Goal White", font=self.fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: self.add_goal_with_confirmation(self.white_score_var, "White")
        )
        self.white_goal_button.grid(row=9, column=1, padx=1, pady=1, sticky="nsew")

        self.white_minus_button = tk.Button(
            tab, text="-ve Goal White", font=self.fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: self.adjust_score_with_confirm(self.white_score_var, "White")
        )
        self.white_minus_button.grid(row=10, column=1, padx=1, pady=1, sticky="nsew")

        self.referee_timeout_button = tk.Button(
            tab, text="Referee Time-Out", font=self.fonts["button"],
            bg=self.referee_timeout_default_bg, fg=self.referee_timeout_default_fg,
            activebackground=self.referee_timeout_default_bg, activeforeground=self.referee_timeout_default_fg,
            command=self.toggle_referee_timeout
        )
        self.referee_timeout_button.grid(row=9, column=2, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.penalties_button = tk.Button(
            tab, text="Penalties", font=self.fonts["button"], bg="orange", fg="black",
            activebackground="orange", activeforeground="black",
            command=self.show_penalties
        )
        self.penalties_button.grid(row=10, column=2, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.game_label = tk.Label(tab, text="Game 121", font=self.fonts["game_no"], bg="light grey")
        self.game_label.grid(row=2, column=2, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.black_goal_button = tk.Button(
            tab, text="Add Goal Black", font=self.fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: self.add_goal_with_confirmation(self.black_score_var, "Black")
        )
        self.black_goal_button.grid(row=9, column=4, padx=1, pady=1, sticky="nsew")

        self.black_minus_button = tk.Button(
            tab, text="-ve Goal Black", font=self.fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: self.adjust_score_with_confirm(self.black_score_var, "Black")
        )
        self.black_minus_button.grid(row=10, column=4, padx=1, pady=1, sticky="nsew")

        self.black_timeout_button = tk.Button(
            tab, text="Black Team\nTime-Out", font=self.fonts["timeout_button"], bg="black", fg="white",
            activebackground="black", activeforeground="white",
            justify="center", wraplength=180, height=2, command=self.black_team_timeout
        )
        self.black_timeout_button.grid(row=9, column=5, rowspan=2, padx=1, pady=1, sticky="nsew")

        self.update_team_timeouts_allowed()

    def show_penalties(self):
        import tkinter as tk
        from tkinter import ttk, messagebox

        penalty_window = tk.Toplevel(self.master)
        penalty_window.title("Penalties")
        penalty_window.geometry("250x400")

        button_frame = ttk.Frame(penalty_window, padding="10")
        button_frame.pack(side="top", fill="x")
        selected_team = tk.StringVar()

        def select_team(team):
            selected_team.set(team)
            button_white.config(relief=tk.SUNKEN if team == "White" else tk.RAISED)
            button_black.config(relief=tk.SUNKEN if team == "Black" else tk.RAISED)

        button_white = ttk.Button(button_frame, text="White", command=lambda: select_team("White"))
        button_white.pack(side="left", padx=5, expand=True)
        button_black = ttk.Button(button_frame, text="Black", command=lambda: select_team("Black"))
        button_black.pack(side="left", padx=5, expand=True)

        numbers = list(range(1, 16))
        dropdown_options = ["Pick Cap Number"] + numbers
        dropdown_variable = tk.StringVar(value=dropdown_options[0])
        dropdown = ttk.Combobox(penalty_window, textvariable=dropdown_variable, values=dropdown_options, state="readonly", height=16)
        dropdown.pack(pady=10)

        radio_frame = ttk.Frame(penalty_window)
        radio_frame.pack(side="top", anchor="w", pady=10, fill="both")
        radio_variable = tk.StringVar()
        radio_button_1 = tk.Radiobutton(radio_frame, text="1 minute", variable=radio_variable, value="1 minute", indicatoron=True)
        radio_button_2 = tk.Radiobutton(radio_frame, text="2 minutes", variable=radio_variable, value="2 minutes", indicatoron=True)
        radio_button_3 = tk.Radiobutton(radio_frame, text="5 minutes", variable=radio_variable, value="5 minutes", indicatoron=True)
        radio_button_4 = tk.Radiobutton(radio_frame, text="Rest of the match", variable=radio_variable, value="Rest of the match", indicatoron=True)
        radio_button_1.pack(anchor="w")
        radio_button_2.pack(anchor="w")
        radio_button_3.pack(anchor="w")
        radio_button_4.pack(anchor="w")

        summary_frame = ttk.Frame(penalty_window)
        summary_frame.pack(side="top", fill="both", expand=True)
        summary_label = ttk.Label(summary_frame, text="Stored Penalties (max 6):")
        summary_label.pack(anchor="w")
        penalty_listbox = tk.Listbox(summary_frame, height=6)
        penalty_listbox.pack(fill="both", expand=True)

        def refresh_penalty_listbox():
            penalty_listbox.delete(0, tk.END)
            for p in getattr(self, 'stored_penalties', []):
                penalty_listbox.insert(tk.END, f"{p['team']} #{p['cap']} {p['duration']}")

        refresh_penalty_listbox()

        def start_penalty():
            team = selected_team.get()
            cap = dropdown_variable.get()
            duration = radio_variable.get()
            if team not in ["White", "Black"]:
                messagebox.showerror("Error", "Choose White or Black team.")
                return
            if cap == "Pick Cap Number":
                messagebox.showerror("Error", "Choose a cap number.")
                return
            if duration == "":
                messagebox.showerror("Error", "Choose a penalty duration.")
                return
            if len(self.stored_penalties) >= 6:
                messagebox.showerror("Error", "Maximum 6 penalties can be stored.")
                return
            self.stored_penalties.append({"team": team, "cap": cap, "duration": duration})
            refresh_penalty_listbox()
            selected_team.set("")
            dropdown_variable.set(dropdown_options[0])
            radio_variable.set("")

        start_button_frame = ttk.Frame(penalty_window)
        start_button_frame.pack(side="bottom", fill="x", pady=10)
        start_button = ttk.Button(start_button_frame, text="Start", command=start_penalty)
        start_button.pack(expand=True, fill="x")

        penalty_window.transient(self.master)
        penalty_window.grab_set()

    def toggle_referee_timeout(self):
        if not self.referee_timeout_active:
            self.referee_timeout_active = True
            self.referee_timeout_button.config(
                bg=self.referee_timeout_active_bg,
                fg=self.referee_timeout_active_fg,
                activebackground=self.referee_timeout_active_bg,
                activeforeground=self.referee_timeout_active_fg
            )
            self.saved_state = {
                "timer_seconds": self.timer_seconds,
                "timer_running": self.timer_running,
                "timer_job": self.timer_job,
                "current_index": self.current_index,
                "half_label_text": self.half_label.cget("text"),
                "half_label_bg": self.half_label.cget("bg"),
                "court_time_paused": self.court_time_paused,
                "court_time_job": self.court_time_job,
            }
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            self.timer_running = False
            if self.court_time_job:
                self.master.after_cancel(self.court_time_job)
                self.court_time_job = None
            self.court_time_paused = True
            self.referee_timeout_elapsed = 0
            self.half_label.config(text="Referee Time-Out")
            self.half_label.config(bg="red")
            self.referee_timeout_countup()
        else:
            self.referee_timeout_active = False
            self.referee_timeout_button.config(
                bg=self.referee_timeout_default_bg,
                fg=self.referee_timeout_default_fg,
                activebackground=self.referee_timeout_default_bg,
                activeforeground=self.referee_timeout_default_fg
            )
            self.timer_seconds = self.saved_state["timer_seconds"]
            self.timer_running = self.saved_state["timer_running"]
            self.current_index = self.saved_state["current_index"]
            self.half_label.config(text=self.saved_state["half_label_text"])
            self.half_label.config(bg=self.saved_state["half_label_bg"])
            self.court_time_paused = self.saved_state.get("court_time_paused", False)
            self.update_timer_display()
            if self.timer_running:
                self.timer_job = self.master.after(1000, self.countdown_timer)
            if not self.court_time_paused:
                self.court_time_job = self.master.after(1000, self.update_court_time)

    def referee_timeout_countup(self):
        if not self.referee_timeout_active:
            return
        self.referee_timeout_elapsed += 1
        mins, secs = divmod(self.referee_timeout_elapsed, 60)
        self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")
        self.timer_job = self.master.after(1000, self.referee_timeout_countup)

    def adjust_score_with_confirm(self, score_var, team_name):
        if not messagebox.askyesno(
            "Subtract Goal",
            f"Are you sure you want to remove goal from {team_name}?"
        ):
            return
        cur_period = self.full_sequence[self.current_index]
        is_break = (cur_period['type'] == 'break'
            or cur_period['name'] in ["White Team Time-Out", "Black Team Time-Out"])
        if is_break:
            if not messagebox.askyesno(
                "Adjust Goal During Break?",
                f"You are about to adjust a goal for {team_name} during a break or half time. Are you sure?"
            ):
                return
        if score_var.get() > 0:
            score_var.set(score_var.get() - 1)
        if cur_period['name'] == 'Sudden Death':
            return

    def add_goal_with_confirmation(self, score_var, team_name):
        cur_period = self.full_sequence[self.current_index]
        is_break = (cur_period['type'] == 'break'
            or cur_period['name'] in ["White Team Time-Out", "Black Team Time-Out"])
        if is_break:
            if not messagebox.askyesno(
                "Add Goal During Break?",
                f"You are about to add a goal for {team_name} during a break or half time. Are you sure?"
            ):
                return
        score_var.set(score_var.get() + 1)

        if cur_period['name'] == 'Between Game Break':
            if self.white_score_var.get() == self.black_score_var.get():
                for idx in range(self.current_index + 1, len(self.full_sequence)):
                    next_period = self.full_sequence[idx]
                    if next_period['name'] == 'Overtime Game Break':
                        self.current_index = idx
                        self.start_current_period()
                        return
                    if next_period['name'] == 'Sudden Death Game Break':
                        self.current_index = idx
                        self.start_current_period()
                        return
        elif cur_period['name'] == 'Sudden Death Game Break':
            if self.white_score_var.get() == self.black_score_var.get():
                for idx in range(self.current_index + 1, len(self.full_sequence)):
                    next_period = self.full_sequence[idx]
                    if next_period['name'] == 'Sudden Death':
                        self.current_index = idx
                        self.start_current_period()
                        return

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
            self.stop_sudden_death_timer()
            self.next_period()

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
                label_text = var_info.get("label", "Team Time-Outs allowed?")
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

    def scale_fonts(self, event):
        cur_width = self.master.winfo_width()
        base_width = 1200
        scale = cur_width / base_width
        scale = max(0.5, min(2.0, scale))
        base_sizes = {
            "court_time": 36,
            "half": 36,
            "team": 30,
            "score": 200,
            "timer": 90,
            "game_no": 12,
            "button": 20,
            "timeout_button": 20,
        }
        reduced_button_scale = 0.7
        for key in self.fonts:
            if key == "timeout_button":
                new_size = int(base_sizes[key] * scale * reduced_button_scale)
            else:
                new_size = int(base_sizes[key] * scale)
            self.fonts[key].config(size=new_size)

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

    def update_timer_display(self):
        if self.referee_timeout_active:
            mins, secs = divmod(self.referee_timeout_elapsed, 60)
            self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")
            return
        cur_period = self.full_sequence[self.current_index] if self.full_sequence and self.current_index < len(self.full_sequence) else None
        if cur_period and cur_period['name'] == 'Sudden Death':
            mins, secs = divmod(self.sudden_death_seconds, 60)
            self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")
        else:
            mins, secs = divmod(self.timer_seconds, 60)
            self.timer_label.config(text=f"{int(mins):02d}:{int(secs):02d}")

    # ---- ADDED FUNCTION ----
    def adjust_between_game_break_for_crib_time(self):
        # Calculate the current court time as datetime
        current_court_time = self.court_time_dt + datetime.timedelta(seconds=self.court_time_seconds)
        local_time = datetime.datetime.now()
        seconds_behind = int((local_time - current_court_time).total_seconds())
        if seconds_behind <= 0:
            return  # Already aligned or ahead
        crib_time_var = self.variables['crib_time']
        crib_time = int(float(crib_time_var.get("value", crib_time_var["default"])))
        # Go through all future Between Game Break periods
        for idx in range(self.current_index, len(self.full_sequence)):
            period = self.full_sequence[idx]
            if period['name'] == 'Between Game Break' and seconds_behind > 0:
                reduce_by = min(crib_time, seconds_behind, period['duration'])
                period['duration'] = max(0, period['duration'] - reduce_by)
                seconds_behind -= reduce_by
                if seconds_behind <= 0:
                    break

    def start_current_period(self):
        if self.current_index >= len(self.full_sequence):
            self.current_index = self.find_period_index('Between Game Break')
        cur_period = self.full_sequence[self.current_index]

        # ---- ADDED LOGIC ----
        if cur_period['name'] == 'Between Game Break':
            self.adjust_between_game_break_for_crib_time()

        self.half_label.config(text=cur_period['name'])
        self.update_half_label_background(cur_period['name'])

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
        if period_name == 'Second Half':
            if self.white_score_var.get() != self.black_score_var.get():
                self.current_index = self.find_period_index('Between Game Break')
                self.start_current_period()
                return
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

    def countdown_timer(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.update_timer_display()
        if not self.timer_running:
            return
        if self.timer_seconds > 0:
            cur_period = self.full_sequence[self.current_index] if self.full_sequence and self.current_index < len(self.full_sequence) else None
            if cur_period and cur_period['name'] == 'Between Game Break' and self.timer_seconds == 30:
                self.white_score_var.set(0)
                self.black_score_var.set(0)
                self.stored_penalties.clear()
            self.timer_seconds -= 1
            self.timer_job = self.master.after(1000, self.countdown_timer)
        else:
            self.next_period()

    def reset_timeouts_for_half(self):
        period = self.full_sequence[self.current_index]
        if period['type'] in ['regular']:
            if self.white_timeouts_this_half < 1:
                self.white_timeout_button.config(state=tk.NORMAL)
            else:
                self.white_timeout_button.config(state=tk.DISABLED)
            if self.black_timeouts_this_half < 1:
                self.black_timeout_button.config(state=tk.NORMAL)
            else:
                self.black_timeout_button.config(state=tk.DISABLED)
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
        self.half_label.config(text="White Team Time-Out")
        self.update_half_label_background("White Team Time-Out")
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
        self.half_label.config(text="Black Team Time-Out")
        self.update_half_label_background("Black Team Time-Out")
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
        popup.title("Time-Out Limit")
        popup.geometry("350x100")
        label = tk.Label(popup, text="One time-out period per team per half", font=self.fonts["button"])
        label.pack(pady=20)
        btn = tk.Button(popup, text="OK", font=self.fonts["button"], command=popup.destroy)
        btn.pack(pady=5)

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
            "white_team_time-out",
            "black_team_time-out",
            "referee_time-out"
        }
        internal_name = period_name.lower().replace(" ", "_")
        if internal_name in red_periods:
            self.half_label.config(bg="red")
        else:
            self.half_label.config(bg="lightblue")

    def create_display_window(self):
        self.display_window = tk.Toplevel(self.master)
        self.display_window.title("Display Window")
        self.display_window.geometry('1200x800')

        tab = ttk.Frame(self.display_window)
        tab.pack(fill="both", expand=True, padx=10, pady=10)

        for i in range(11):
            tab.grid_rowconfigure(i, weight=1)
        for i in range(6):
            tab.grid_columnconfigure(i, weight=1)

        self.display_court_time_label = tk.Label(tab, text="Court Time is", font=self.fonts["court_time"], bg="lightgrey")
        self.display_court_time_label.grid(row=0, column=0, columnspan=6, padx=1, pady=1, sticky="nsew")
        self.display_half_label = tk.Label(tab, text="", font=self.fonts["half"], bg="lightcoral")
        self.display_half_label.grid(row=1, column=0, columnspan=6, padx=1, pady=1, sticky="nsew")
        self.display_white_label = tk.Label(tab, text="White", font=self.fonts["team"], bg="white", fg="black")
        self.display_white_label.grid(row=2, column=0, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.display_white_score = tk.Label(tab, textvariable=self.white_score_var, font=self.fonts["score"], bg="white", fg="black")
        self.display_white_score.grid(row=3, column=0, rowspan=8, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.display_timer_label = tk.Label(tab, text="00:00", font=self.fonts["timer"], bg="lightgrey", fg="black")
        self.display_timer_label.grid(row=3, column=2, rowspan=8, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.display_black_label = tk.Label(tab, text="Black", font=self.fonts["team"], bg="black", fg="white")
        self.display_black_label.grid(row=2, column=4, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.display_black_score = tk.Label(tab, textvariable=self.black_score_var, font=self.fonts["score"], bg="black", fg="white")
        self.display_black_score.grid(row=3, column=4, rowspan=8, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.display_game_label = tk.Label(tab, text="Game 121", font=self.fonts["game_no"], bg="light grey")
        self.display_game_label.grid(row=2, column=2, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.sync_display_widgets()

    def sync_display_widgets(self):
        def update_display():
            self.display_court_time_label.config(text=self.court_time_label.cget("text"))
            self.display_half_label.config(text=self.half_label.cget("text"), bg=self.half_label.cget("bg"))
            self.display_timer_label.config(text=self.timer_label.cget("text"))
            self.display_game_label.config(text=self.game_label.cget("text"))
            self.display_white_label.config(text=self.white_label.cget("text"))
            self.display_black_label.config(text=self.black_label.cget("text"))
            self.display_window.after(200, update_display)
        update_display()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameManagementApp(root)
    root.mainloop()
