import tkinter as tk
from tkinter import ttk, messagebox, font
import datetime
import re
import time
import os
import subprocess

class GameManagementApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Underwater Hockey Game Management App")
        self.master.geometry('1200x800')

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both',)

        # --- Variable and font setup ---
        self.variables = {
            "time_to_start_first_game": {"default": "", "checkbox": False, "unit": "hh:mm", "label": "Time to Start First Game:"},
            "start_first_game_in": {"default": 1, "checkbox": False, "unit": "minutes", "label": "Start First Game in:"},
            "team_timeouts_allowed": {"default": True, "checkbox": True, "unit": "", "label": "Team time-outs allowed?"},
            "team_timeout_period": {"default": 1, "checkbox": False, "unit": "minutes"},
            "half_period": {"default": 1, "checkbox": False, "unit": "minutes"},
            "half_time_break": {"default": 1, "checkbox": False, "unit": "minutes"},
            "overtime_allowed": {"default": True, "checkbox": True, "unit": "", "label": "Overtime allowed?"},
            "overtime_game_break": {"default": 1, "checkbox": False, "unit": "minutes"},
            "overtime_half_period": {"default": 1, "checkbox": False, "unit": "minutes"},
            "overtime_half_time_break": {"default": 1, "checkbox": False, "unit": "minutes"},
            "sudden_death_game_break": {"default": 1, "checkbox": True, "unit": "minutes"},
            "between_game_break": {"default": 1, "checkbox": False, "unit": "minutes"},
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

        self.display_fonts = {
            "court_time": font.Font(family="Arial", size=36),
            "half": font.Font(family="Arial", size=36, weight="bold"),
            "team": font.Font(family="Arial", size=30, weight="bold"),
            "score": font.Font(family="Arial", size=200, weight="bold"),
            "timer": font.Font(family="Arial", size=90, weight="bold"),
            "game_no": font.Font(family="Arial", size=12),
        }

        # Event-driven Tkinter variables for all display widgets
        self.white_score_var = tk.IntVar(value=0)
        self.black_score_var = tk.IntVar(value=0)
        self.timer_var = tk.StringVar(value="00:00")
        self.court_time_var = tk.StringVar(value="Court Time is 00:00:00")
        self.half_label_var = tk.StringVar(value="")
        self.game_number_var = tk.StringVar(value="Game 121")
        self.white_team_var = tk.StringVar(value="White")
        self.black_team_var = tk.StringVar(value="Black")
        
        self.timer_running = True
        self.timer_seconds = 0

        # Court time system
        self.court_time_seconds = None  # Will be synchronized to local time at startup/reset
        self.court_time_job = None
        self.court_time_paused = False

        self.timer_job = None
        self.reset_timer_button = None
        self.in_timeout = False
        self.pending_timeout = None
        self.white_timeouts_this_half = 0
        self.black_timeouts_this_half = 0
        self.active_timeout_team = None
        self.sudden_death_timer_job = None
        self.sudden_death_seconds = 0
        self.sudden_death_goal_scored = False
        self.full_sequence = []
        self.current_index = 0
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
        
        # Penalty timer system
        self.active_penalties = []
        self.penalty_timers_paused = False
        self.penalty_timer_jobs = []

        self.create_scoreboard_tab()
        self.create_settings_tab()
        self.load_settings()
        self.build_game_sequence()
        self.master.bind('<Configure>', self.scale_fonts)
        self.initial_width = self.master.winfo_width()
        self.master.update_idletasks()
        self.scale_fonts(None)

        # --- Sudden Death restoration variables ---
        self.sudden_death_restore_time = None
        self.sudden_death_restore_active = False

        # --- Display window and penalty grid must be created before display updates ---
        self.create_display_window()
        self.start_penalty_display_updates()
        self.sync_penalty_display_to_external()
        self.reset_timer()  # <-- moved here, after display window creation

    def create_scoreboard_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Scoreboard")
        for i in range(11):
            tab.grid_rowconfigure(i, weight=1)
        for i in range(9):
            tab.grid_columnconfigure(i, weight=1)

        self.court_time_label = tk.Label(tab, textvariable=self.court_time_var, font=self.fonts["court_time"], bg="lightgrey")
        self.court_time_label.grid(row=0, column=0, columnspan=9, padx=1, pady=1, sticky="nsew")

        self.half_label = tk.Label(tab, textvariable=self.half_label_var, font=self.fonts["half"], bg="lightcoral")
        self.half_label.grid(row=1, column=0, columnspan=9, padx=1, pady=1, sticky="nsew")

        self.white_label = tk.Label(tab, textvariable=self.white_team_var, font=self.fonts["team"], bg="white", fg="black")
        self.white_label.grid(row=2, column=0, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.black_label = tk.Label(tab, textvariable=self.black_team_var, font=self.fonts["team"], bg="black", fg="white")
        self.black_label.grid(row=2, column=6, columnspan=3, padx=1, pady=1, sticky="nsew")

        self.game_label = tk.Label(tab, textvariable=self.game_number_var, font=self.fonts["game_no"], bg="light grey")
        self.game_label.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.penalty_grid_frame, self.penalty_labels = self.create_penalty_grid_widget(tab)
        self.penalty_grid_frame.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.penalty_grid_frame.grid_remove()  # hide initially

        self.white_score = tk.Label(tab, textvariable=self.white_score_var, font=self.fonts["score"], bg="white", fg="black")
        self.white_score.grid(row=3, column=0, rowspan=6, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.black_score = tk.Label(tab, textvariable=self.black_score_var, font=self.fonts["score"], bg="black", fg="white")
        self.black_score.grid(row=3, column=6, rowspan=6, columnspan=3, padx=1, pady=1, sticky="nsew")

        self.timer_label = tk.Label(tab, textvariable=self.timer_var, font=self.fonts["timer"], bg="lightgrey", fg="black")
        self.timer_label.grid(row=3, column=3, rowspan=6, columnspan=3, padx=1, pady=1, sticky="nsew")

        self.white_timeout_button = tk.Button(
            tab, text="White Team\nTime-Out", font=self.fonts["timeout_button"], bg="white", fg="black",
            activebackground="white", activeforeground="black",
            justify="center", wraplength=180, height=2, command=self.white_team_timeout
        )
        self.white_timeout_button.grid(row=9, column=0, rowspan=2, columnspan=1, padx=1, pady=1, sticky="nsew")
        self.black_timeout_button = tk.Button(
            tab, text="Black Team\nTime-Out", font=self.fonts["timeout_button"], bg="black", fg="white",
            activebackground="black", activeforeground="white",
            justify="center", wraplength=180, height=2, command=self.black_team_timeout
        )
        self.black_timeout_button.grid(row=9, column=8, rowspan=2, columnspan=1, padx=1, pady=1, sticky="nsew")

        self.white_goal_button = tk.Button(
            tab, text="Add Goal White", font=self.fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: self.add_goal_with_confirmation(self.white_score_var, "White")
        )
        self.white_goal_button.grid(row=9, column=1, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.black_goal_button = tk.Button(
            tab, text="Add Goal Black", font=self.fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: self.add_goal_with_confirmation(self.black_score_var, "Black")
        )
        self.black_goal_button.grid(row=9, column=6, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.white_minus_button = tk.Button(
            tab, text="-ve Goal White", font=self.fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: self.adjust_score_with_confirm(self.white_score_var, "White")
        )
        self.white_minus_button.grid(row=10, column=1, columnspan=2, padx=1, pady=1, sticky="nsew")
        self.black_minus_button = tk.Button(
            tab, text="-ve Goal Black", font=self.fonts["button"], bg="light grey", fg="black",
            activebackground="light grey", activeforeground="black",
            command=lambda: self.adjust_score_with_confirm(self.black_score_var, "Black")
        )
        self.black_minus_button.grid(row=10, column=6, columnspan=2, padx=1, pady=1, sticky="nsew")

        self.referee_timeout_button = tk.Button(
            tab, text="Referee Time-Out", font=self.fonts["button"],
            bg=self.referee_timeout_default_bg, fg=self.referee_timeout_default_fg,
            activebackground=self.referee_timeout_default_bg, activeforeground=self.referee_timeout_default_fg,
            command=self.toggle_referee_timeout
        )
        self.referee_timeout_button.grid(row=9, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.penalties_button = tk.Button(
            tab, text="Penalties", font=self.fonts["button"], bg="orange", fg="black",
            activebackground="orange", activeforeground="black",
            command=self.show_penalties
        )
        self.penalties_button.grid(row=10, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")

        self.update_team_timeouts_allowed()

    def get_sound_files(self):
        """
        Scan the current directory for supported sound files (.wav, .mp3).
        Returns a list of sound files found.
        """
        sound_files = []
        supported_extensions = ['.wav', '.mp3']
        
        try:
            current_dir = os.getcwd()
            for filename in os.listdir(current_dir):
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    sound_files.append(filename)
        except Exception as e:
            print(f"Error scanning for sound files: {e}")
        
        return sorted(sound_files) if sound_files else ["No sound files found"]
    
    def play_sound(self, filename):
        """
        Play a sound file using the appropriate system command.
        Uses aplay for WAV files and omxplayer for MP3 files (Raspberry Pi compatible).
        """
        if filename == "No sound files found" or filename == "Default":
            messagebox.showinfo("Sound Test", f"Cannot play '{filename}' - not a valid sound file")
            return
            
        try:
            file_path = os.path.join(os.getcwd(), filename)
            if not os.path.exists(file_path):
                messagebox.showerror("Sound Error", f"Sound file '{filename}' not found")
                return
                
            # Determine command based on file extension
            if filename.lower().endswith('.wav'):
                # Use aplay for WAV files (works well on Raspberry Pi with DigiAMP+ HAT)
                subprocess.run(['aplay', file_path], check=True, capture_output=True)
            elif filename.lower().endswith('.mp3'):
                # Use omxplayer for MP3 files (Raspberry Pi optimized)
                subprocess.run(['omxplayer', '--no-osd', file_path], check=True, capture_output=True)
            else:
                messagebox.showerror("Sound Error", f"Unsupported file format: {filename}")
                return
                
            # Show success feedback
            messagebox.showinfo("Sound Test", f"Successfully played: {filename}")
            
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Sound Error", f"Failed to play {filename}. Command failed: {e}")
        except FileNotFoundError:
            # Fallback for development environments without aplay/omxplayer
            messagebox.showwarning("Sound Warning", f"Audio player not found. Would play: {filename}")
        except Exception as e:
            messagebox.showerror("Sound Error", f"Unexpected error playing {filename}: {e}")

    def update_penalty_display(self):
        """
        Robustly ensures that the penalty grid is only shown if there are penalties left to serve,
        and that 'Game 121' label is shown otherwise.
        Applies to both main and display windows.
        """
        main_has_penalties = bool(self.active_penalties or self.stored_penalties)
        # Main window: show penalty grid if any penalties; otherwise show 'Game 121'
        if main_has_penalties:
            if self.game_label.winfo_ismapped():
                self.game_label.grid_remove()
            if not self.penalty_grid_frame.winfo_ismapped():
                self.penalty_grid_frame.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
            self.update_penalty_grid()
        else:
            # Hide penalty grid
            try:
                self.penalty_grid_frame.grid_remove()
            except Exception:
                pass
            # Show Game 121 label always
            if not self.game_label.winfo_ismapped():
                self.game_label.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
            # Event-driven: Update the StringVar instead of calling .config()
            self.game_number_var.set("Game 121")

        # Display window: same logic
        display_has_penalties = bool(self.active_penalties or self.stored_penalties)
        if display_has_penalties:
            if self.display_game_label.winfo_ismapped():
                self.display_game_label.grid_remove()
            if not self.display_penalty_grid_frame.winfo_ismapped():
                self.display_penalty_grid_frame.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
            self.update_display_penalty_grid()
        else:
            try:
                self.display_penalty_grid_frame.grid_remove()
            except Exception:
                pass
            if not self.display_game_label.winfo_ismapped():
                self.display_game_label.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
            # Event-driven: StringVar automatically updates display widget

    def _penalty_sort_key(self, p):
        """Helper method to sort penalties by time remaining."""
        return p["seconds_remaining"] if not p["is_rest_of_match"] else 999999

    def update_penalty_grid(self):
        white_penalties = sorted(
            [p for p in self.active_penalties if p["team"] == "White"],
            key=self._penalty_sort_key
        )[:3]
        black_penalties = sorted(
            [p for p in self.active_penalties if p["team"] == "Black"],
            key=self._penalty_sort_key
        )[:3]
        for i in range(3):
            if i < len(white_penalties):
                p = white_penalties[i]
                cap_str = f"#{p['cap']}"
                if p["is_rest_of_match"]:
                    time_str = "rest"
                else:
                    mins, secs = divmod(p["seconds_remaining"], 60)
                    time_str = f"{mins}:{secs:02d}"
                label_text = f"{cap_str}  {time_str}"
            else:
                label_text = ""
            self.penalty_labels[i][0].config(text=label_text)
            if i < len(black_penalties):
                p = black_penalties[i]
                cap_str = f"#{p['cap']}"
                if p["is_rest_of_match"]:
                    time_str = "rest"
                else:
                    mins, secs = divmod(p["seconds_remaining"], 60)
                    time_str = f"{mins}:{secs:02d}"
                label_text = f"{cap_str}  {time_str}"
            else:
                label_text = ""
            self.penalty_labels[i][1].config(text=label_text)

    def update_display_penalty_grid(self):
        white_penalties = sorted(
            [p for p in self.active_penalties if p["team"] == "White"],
            key=self._penalty_sort_key
        )[:3]
        black_penalties = sorted(
            [p for p in self.active_penalties if p["team"] == "Black"],
            key=self._penalty_sort_key
        )[:3]
        for i in range(3):
            if i < len(white_penalties):
                p = white_penalties[i]
                cap_str = f"#{p['cap']}"
                if p["is_rest_of_match"]:
                    time_str = "rest"
                else:
                    mins, secs = divmod(p["seconds_remaining"], 60)
                    time_str = f"{mins}:{secs:02d}"
                label_text = f"{cap_str}  {time_str}"
            else:
                label_text = ""
            self.display_penalty_labels[i][0].config(text=label_text)
            if i < len(black_penalties):
                p = black_penalties[i]
                cap_str = f"#{p['cap']}"
                if p["is_rest_of_match"]:
                    time_str = "rest"
                else:
                    mins, secs = divmod(p["seconds_remaining"], 60)
                    time_str = f"{mins}:{secs:02d}"
                label_text = f"{cap_str}  {time_str}"
            else:
                label_text = ""
            self.display_penalty_labels[i][1].config(text=label_text)

    def start_penalty_display_updates(self):
        self.update_penalty_display()
        self.master.after(1000, self.start_penalty_display_updates)

    def sync_penalty_display_to_external(self):
        # Event-driven: No need to sync text since both widgets use the same StringVar
        # Only background colors need to be synchronized
        self.display_window.after(1000, self.sync_penalty_display_to_external)

    def create_penalty_grid_widget(self, parent, is_display=False):
        # Add internal padding for slightly smaller appearance than the game label
        frame = tk.Frame(parent, padx=10, pady=4)
        for col in range(2):
            frame.grid_columnconfigure(col, weight=1)
        for row in range(3):
            frame.grid_rowconfigure(row, weight=1)
        labels = [[None for _ in range(2)] for _ in range(3)]
        for row in range(3):
            lbl_white = tk.Label(frame, text="", font=("Arial", 9), width=8,
                                 anchor="center", relief="ridge", fg="black", bg="white", justify="center")
            lbl_white.grid(row=row, column=0, padx=1, pady=1, sticky="nsew")
            labels[row][0] = lbl_white
            lbl_black = tk.Label(frame, text="", font=("Arial", 9), width=8,
                                 anchor="center", relief="ridge", fg="white", bg="black", justify="center")
            lbl_black.grid(row=row, column=1, padx=1, pady=1, sticky="nsew")
            labels[row][1] = lbl_black
        return frame, labels

    def scale_fonts(self, event=None):
        try:
            cur_width = self.master.winfo_width()
            if cur_width <= 0:
                cur_width = self.initial_width if hasattr(self, 'initial_width') else 1200
        except Exception:
            cur_width = 1200
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
        for key, fnt in self.fonts.items():
            if key == "timeout_button":
                new_size = int(base_sizes[key] * scale * reduced_button_scale)
            else:
                new_size = int(base_sizes[key] * scale)
            try:
                fnt.config(size=new_size)
            except Exception:
                pass

    def scale_display_fonts(self, event=None):
        try:
            cur_width = self.display_window.winfo_width()
            if cur_width <= 0:
                cur_width = self.display_initial_width if hasattr(self, 'display_initial_width') else 1200
        except Exception:
            cur_width = 1200
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
        }
        for key, fnt in self.display_fonts.items():
            new_size = int(base_sizes[key] * scale)
            try:
                fnt.config(size=new_size)
            except Exception:
                pass

    def get_minutes(self, varname):
        try:
            val = self.variables[varname].get("value", self.variables[varname]["default"])
            val = str(val).replace(',', '.')
            return float(val) * 60
        except Exception:
            val = str(self.variables[varname]["default"]).replace(',', '.')
            return float(val) * 6

    def build_game_sequence(self):
        seq = []
        # Always start with "Game Starts in:"
        now = datetime.datetime.now()
        time_val = self.variables.get("time_to_start_first_game", {}).get("value", "")
        bgb_val = self.variables.get("between_game_break", {}).get("value", "1").replace(",", ".")
        try:
            bgb_minutes = float(bgb_val)
        except Exception:
            bgb_minutes = 1.0
        game_starts_in_minutes = None
        if time_val:
            match = re.fullmatch(r"(?:[0-9]|1[0-9]|2[0-3]):[0-5][0-9]", time_val.strip())
            if match:
                hh, mm = map(int, time_val.strip().split(":"))
                target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if target < now:
                    target = target + datetime.timedelta(days=1)
                delta = target - now
                minutes_to_start = int(delta.total_seconds() // 60)
                # Subtract the Between Game Break
                game_starts_in_minutes = max(0, minutes_to_start - int(bgb_minutes))
        if game_starts_in_minutes is not None:
            seq.append({'name': 'Game Starts in:', 'type': 'break', 'duration': game_starts_in_minutes * 60})
        else:
            seq.append({'name': 'Game Starts in:', 'type': 'break', 'duration': self.get_minutes('start_first_game_in')})
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
        
    def create_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Game Variables")
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_columnconfigure(0, weight=2)
        tab.grid_columnconfigure(1, weight=1)

        default_font = font.nametofont("TkDefaultFont")
        new_size = default_font.cget("size") + 2
        headers = ["Use?", "Variable", "Value", "Units"]

        # Widget 1
        widget1 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget1.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        for i in range(4):
            widget1.grid_columnconfigure(i, weight=1)
        for i in range(17):
            widget1.grid_rowconfigure(i, weight=1)
        for i, h in enumerate(headers):
            tk.Label(widget1, text=h, font=(default_font.cget("family"), new_size, "bold")).grid(row=0, column=i, sticky="w", padx=5, pady=5)
        row_idx = 1
        self.widgets = []
        # Ensure "time_to_start_first_game" is first, then "start_first_game_in" above team_timeouts_allowed
        entry_order = list(self.variables.keys())
        for special_name in ["time_to_start_first_game", "start_first_game_in"]:
            if special_name in entry_order:
                entry_order.remove(special_name)
        entry_order = ["time_to_start_first_game", "start_first_game_in"] + entry_order
        for var_name in entry_order:
            var_info = self.variables[var_name]
            if var_info["checkbox"]:
                var_info["default"] = True
            if var_name == "team_timeouts_allowed":
                check_var = self.team_timeouts_allowed_var
                cb = ttk.Checkbutton(widget1, variable=check_var)
                cb.grid(row=row_idx, column=0, sticky="w", pady=5)
                label_text = var_info.get("label", "Team Time-Outs allowed?")
                label_widget = tk.Label(widget1, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=5)
                check_var.trace_add("write", lambda *args: self.update_team_timeouts_allowed())
                self.widgets.append({"name": var_name, "entry": None, "checkbox": check_var, "label_widget": label_widget})
                row_idx += 1
                continue
            if var_name == "overtime_allowed":
                check_var = self.overtime_allowed_var
                cb = ttk.Checkbutton(widget1, variable=check_var)
                cb.grid(row=row_idx, column=0, sticky="w", pady=5)
                label_text = var_info.get("label", "Overtime allowed?")
                label_widget = tk.Label(widget1, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=5)
                check_var.trace_add("write", lambda *args: self.update_overtime_variables_state())
                self.widgets.append({"name": var_name, "entry": None, "checkbox": check_var, "label_widget": label_widget})
                row_idx += 1
                continue
            check_var = tk.BooleanVar(value=True) if var_info["checkbox"] else None
            if check_var:
                cb = ttk.Checkbutton(widget1, variable=check_var)
                cb.grid(row=row_idx, column=0, sticky="w", pady=5)
                check_var.trace_add("write", lambda *args, name=var_name: self._on_settings_variable_change())
            label_text = var_info.get("label", f"{var_name.replace('_', ' ').title()}:")
            label_widget = tk.Label(widget1, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
            label_widget.grid(row=row_idx, column=1, sticky="w", pady=5)
            # Set up value box for time_to_start_first_game and validate as hh:mm
            entry = ttk.Entry(widget1, width=10)
            if var_name == "time_to_start_first_game":
                entry.insert(0, "")
                # Only validate on focusout/return, allow any input while typing
                def validate_hhmm_on_focusout(event):
                    val = event.widget.get().strip()
                    if val == "":
                        return
                    # Accept HH:MM (single or double digit hour)
                    if not re.fullmatch(r"(?:[0-9]|1[0-9]|2[0-3]):[0-5][0-9]", val):
                        messagebox.showerror("Input Error", "Please enter time in HH:MM 24-hour format (e.g., 19:36 or 9:36).")
                        event.widget.focus_set()
                        event.widget.selection_range(0, tk.END)
                        return
                    self._on_settings_variable_change()
                entry.bind("<FocusOut>", validate_hhmm_on_focusout)
                entry.bind("<Return>", validate_hhmm_on_focusout)
            else:
                entry.insert(0, "1")
                entry.bind("<FocusOut>", lambda e, name=var_name: self._on_settings_variable_change())
                entry.bind("<Return>", lambda e, name=var_name: self._on_settings_variable_change())
            entry.grid(row=row_idx, column=2, sticky="w", padx=5, pady=5)
            tk.Label(widget1, text=var_info["unit"], font=(default_font.cget("family"), new_size, "bold")).grid(row=row_idx, column=3, sticky="w", padx=5, pady=5)
            self.widgets.append({"name": var_name, "entry": entry, "checkbox": check_var, "label_widget": label_widget})
            self.last_valid_values[var_name] = entry.get()
            if var_name == "team_timeout_period":
                self.team_timeout_period_entry = entry
                self.team_timeout_period_label = label_widget
            row_idx += 1
            # Insert info label after Crib Time row
            if var_name == "crib_time":
                info_label = tk.Label(
                    widget1,
                    text="Value boxes accept decimal time e.g. 1.5 or 1,5 = 1 min, 30 sec",
                    font=(default_font.cget("family"), new_size, "italic"),
                    fg="blue", anchor="center", justify="center"
                )
                info_label.grid(row=row_idx, column=0, columnspan=4, pady=(2,8), sticky="nsew")
                row_idx += 1            
        # --- PATCH: Add warning label above Reset Timer button ---
        self.reset_warning_label = tk.Label(
            widget1,
            text="If you change anything in here, push the reset button!",
            font=(default_font.cget("family"), new_size, "bold"),
            fg="red"
        )
        self.reset_warning_label.grid(row=15, column=0, columnspan=4, pady=(8,0))
        self.reset_timer_button = ttk.Button(widget1, text="Reset Timer", command=self.reset_timer)
        self.reset_timer_button.grid(row=16, column=0, columnspan=4, pady=8)

        # Widget 2 ("Presets")
        widget2 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget2.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)


        for col in range(3):
            widget2.grid_columnconfigure(col, weight=1)
        # Make widget2 about 50% of previous height: only expand button rows
        widget2.grid_rowconfigure(0, weight=0)  # Header
        widget2.grid_rowconfigure(1, weight=0)  # Button row 1
        widget2.grid_rowconfigure(2, weight=0)  # Button row 2
        widget2.grid_rowconfigure(3, weight=0)  # Spacer
        widget2.grid_rowconfigure(4, weight=0)  # Instructional text 1
        widget2.grid_rowconfigure(5, weight=0)  # Instructional text 2
        header_label = tk.Label(widget2, text="Presets", font=(default_font.cget("family"), new_size, "bold"))
        header_label.grid(row=0, column=0, columnspan=3, padx=4, pady=(12,4), sticky="nsew")

#add in default values for CMAS rules as per section 14.2 INTERNATIONAL RULES FOR UNDERWATER HOCKEY
#RULES OF PLAY, Version 13.0, February 2025
        self.widget2_buttons = []
        self.button_data = [{} for _ in range(6)]
        for i in range(6):
            btn_row = 1 if i < 3 else 2
            btn_col = i % 3
            if i == 0:
                self.button_data[i]["text"] = "CMAS"
                self.button_data[i]["values"] = {
                    "team_timeout_period": "1",           # Team timeout 1 minute
                    "half_period": "15",                  # Half period 15 minutes
                    "half_time_break": "3",               # Half time break 3 minutes
                    "overtime_game_break": "3",           # Overtime game break 3 minutes
                    "overtime_half_period": "5",          # Overtime half period 5 minutes
                    "overtime_half_time_break": "1",      # Overtime half time break 1 minute
                    "sudden_death_game_break": "1",       # Sudden Death Game break 1 minute
                    "between_game_break": "5",            # Between Game break 5 minutes
                    "crib_time": "60"                     # Crib time default 60 seconds
                }
                self.button_data[i]["checkboxes"] = {
                    "team_timeouts_allowed": True,        # Team timeouts allowed checked
                    "overtime_allowed": True              # Overtime allowed checked
                }
            else:
                self.button_data[i]["text"] = str(i + 1)
                self.button_data[i]["values"] = {}
                self.button_data[i]["checkboxes"] = {}
            btn = ttk.Button(widget2, text=self.button_data[i]["text"], width=16)
            btn.grid(row=btn_row, column=btn_col, padx=8, pady=12, sticky="nsew")
            btn.bind("<ButtonPress-1>", self._make_press_handler(i))
            btn.bind("<ButtonRelease-1>", self._make_release_handler(i))
            self.widget2_buttons.append(btn)

        # Optional spacer row (row 3)
        spacer = tk.Label(widget2, text="", font=(default_font.cget("family"), new_size))
        spacer.grid(row=3, column=0, columnspan=3, sticky="nsew")
        # Add row 4: instructional text
        instruction1 = tk.Label(
            widget2,
            text="Click the buttons above to load preset times and allowed Game Periods",
            anchor="w", justify="left", font=(default_font.cget("family"), new_size)
        )
        instruction1.grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=(4,2))
        # Add row 5: instructional text
        instruction2 = tk.Label(
            widget2,
            text="Press and hold the button for >4 seconds to alter the stored preset values",
            anchor="w", justify="left", font=(default_font.cget("family"), new_size)
        )
        instruction2.grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=(2,8))

        # Widget 3 ("Sounds")
        widget3 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget3.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
        widget3.grid_columnconfigure(0, weight=0)  # Label column
        widget3.grid_columnconfigure(1, weight=1)  # Dropdown column
        widget3.grid_columnconfigure(2, weight=0)  # Play button column
        widget3.grid_rowconfigure(0, weight=1)
        widget3.grid_rowconfigure(1, weight=1)
        widget3.grid_rowconfigure(2, weight=1)
        
        sounds_label = tk.Label(widget3, text="Sounds", font=(default_font.cget("family"), new_size, "bold"))
        sounds_label.grid(row=0, column=0, columnspan=3, padx=4, pady=(0,8), sticky="nsew")
        
        # Get dynamic list of sound files
        sound_files = self.get_sound_files()
        pips_options = ["Default"] + sound_files if sound_files != ["No sound files found"] else sound_files
        siren_options = ["Default"] + sound_files if sound_files != ["No sound files found"] else sound_files
        
        # Pips row
        tk.Label(widget3, text="Pips:", font=(default_font.cget("family"), new_size)).grid(row=1, column=0, sticky="e", padx=(8,4), pady=4)
        self.pips_var = tk.StringVar(value="Default")
        pips_dropdown = ttk.Combobox(widget3, textvariable=self.pips_var, values=pips_options, state="readonly")
        pips_dropdown.grid(row=1, column=1, sticky="ew", padx=4, pady=4)
        pips_play_button = tk.Button(
            widget3, text="Play", font=(default_font.cget("family"), new_size), 
            command=lambda: self.play_sound(self.pips_var.get())
        )
        pips_play_button.grid(row=1, column=2, sticky="w", padx=(4,8), pady=4)
        
        # Siren row
        tk.Label(widget3, text="Siren:", font=(default_font.cget("family"), new_size)).grid(row=2, column=0, sticky="e", padx=(8,4), pady=4)
        self.siren_var = tk.StringVar(value="Default")
        siren_dropdown = ttk.Combobox(widget3, textvariable=self.siren_var, values=siren_options, state="readonly")
        siren_dropdown.grid(row=2, column=1, sticky="ew", padx=4, pady=4)
        siren_play_button = tk.Button(
            widget3, text="Play", font=(default_font.cget("family"), new_size),
            command=lambda: self.play_sound(self.siren_var.get())
        )
        siren_play_button.grid(row=2, column=2, sticky="w", padx=(4,8), pady=4)
        
        self.update_overtime_variables_state()

    def _make_press_handler(self, idx):
        return lambda e: self._start_button_hold(e, idx)

    def _make_release_handler(self, idx):
        return lambda e: self._button_release(e, idx)

    def set_widget2_button_text(self, idx, new_text):
        if 0 <= idx < len(self.widget2_buttons):
            self.widget2_buttons[idx].config(text=new_text)

    def _start_button_hold(self, event, idx):
        self._button_hold_start_time = time.time()
        self._button_hold_index = idx
        self._button_hold_timer = self.master.after(3000, lambda: self._open_button_dialog(idx))

    def _button_release(self, event, idx):
        if hasattr(self, '_button_hold_timer') and self._button_hold_timer is not None:
            self.master.after_cancel(self._button_hold_timer)
            self._button_hold_timer = None
        if hasattr(self, '_button_hold_start_time') and self._button_hold_start_time is not None and (time.time() - self._button_hold_start_time < 2.9):
            self._apply_button_data(idx)
        self._button_hold_start_time = None
        self._button_hold_index = None

    def _apply_button_data(self, idx):
        # Apply saved values and checkboxes for all widgets
        for widget in self.widgets:
            var_name = widget["name"]
            # Do not apply preset to "start_first_game_in"
            if var_name == "start_first_game_in":
                continue
            if widget["checkbox"] is not None:
                val = self.button_data[idx]["checkboxes"].get(var_name, widget["checkbox"].get())
                widget["checkbox"].set(val)
            else:
                val = self.button_data[idx]["values"].get(var_name, widget["entry"].get())
                widget["entry"].delete(0, tk.END)
                widget["entry"].insert(0, val)
        # Also populate Crib Time value in main variables from preset
        crib_time_val = self.button_data[idx]["values"].get("crib_time", None)
        if crib_time_val is not None:
            for widget in self.widgets:
                if widget["name"] == "crib_time" and widget["entry"] is not None:
                    widget["entry"].delete(0, tk.END)
                    widget["entry"].insert(0, crib_time_val)
        self.load_settings()

    def _open_button_dialog(self, idx):
        dlg = tk.Toplevel(self.master)
        dlg.title(f"Button {idx+1} Settings")
        dlg.geometry("400x700")
        # --- Add validation for numbers/decimals ---
        def validate_number(P):
            if P == "":
                return True
            try:
                float(P.replace(',', '.'))
                return True
            except ValueError:
                return False
        vcmd = (dlg.register(validate_number), '%P')
        entries = {}
        checks = {}
        row_num = 0
        max_btn_text_len = 16
        tk.Label(dlg, text="Button Display Text:").grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
        btn_text_var = tk.StringVar(value=self.button_data[idx].get("text", str(idx+1)))
        text_entry = ttk.Entry(dlg, textvariable=btn_text_var, width=max_btn_text_len)
        text_entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
        row_num += 1

        for widget in self.widgets:
            var_name = widget["name"]
            label = widget["label_widget"]
            tk.Label(dlg, text=label.cget("text")).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
            if widget["checkbox"] is not None:
                # For button 1, preset checkboxes as True for required options
                if idx == 0 and var_name in ["team_timeouts_allowed", "overtime_allowed"]:
                    val = True
                else:
                    val = self.button_data[idx]["checkboxes"].get(var_name, widget["checkbox"].get())
                check_var = tk.BooleanVar(value=val)
                cb = ttk.Checkbutton(dlg, variable=check_var)
                cb.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
                checks[var_name] = check_var
            else:
                # For button 1, preset values for required options
                if idx == 0 and var_name in [
                    "team_timeout_period", "half_period", "half_time_break",
                    "overtime_game_break", "overtime_half_period", "overtime_half_time_break",
                    "sudden_death_game_break", "between_game_break", "crib_time"
                ]:
                    val = self.button_data[idx]["values"].get(var_name, {
                        "team_timeout_period": "1",
                        "half_period": "15",
                        "half_time_break": "3",
                        "overtime_game_break": "3",
                        "overtime_half_period": "5",
                        "overtime_half_time_break": "1",
                        "sudden_death_game_break": "1",
                        "between_game_break": "5",
                        "crib_time": "60"
                    }.get(var_name, widget["entry"].get()))
                else:
                    val = self.button_data[idx]["values"].get(var_name, widget["entry"].get())
                entry_var = tk.StringVar(value=val)
                entry = ttk.Entry(dlg, textvariable=entry_var, width=10, validate="key", validatecommand=vcmd)
                entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
                entries[var_name] = entry_var
            row_num += 1

        # --- PATCH: Add Crib Time entry below Crib Time: checkbox and above Save button ---
        tk.Label(dlg, text="Crib Time (seconds):").grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
        crib_time_val = self.button_data[idx]["values"].get("crib_time", "60")
        crib_time_entry_var = tk.StringVar(value=crib_time_val)
        crib_time_entry = ttk.Entry(dlg, textvariable=crib_time_entry_var, width=10, validate="key", validatecommand=vcmd)
        crib_time_entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
        entries["crib_time"] = crib_time_entry_var
        row_num += 1

        def save_and_close():
            for v in entries:
                # PATCH: Remove "start_first_game_in" from dialog value save
                if v == "start_first_game_in":
                    continue
                try:
                    val = entries[v].get().replace(',', '.')
                    float(val)
                    self.button_data[idx]["values"][v] = val
                except ValueError:
                    continue
            for v in checks:
                self.button_data[idx]["checkboxes"][v] = checks[v].get()
            self.button_data[idx]["text"] = btn_text_var.get()[:max_btn_text_len]
            self.set_widget2_button_text(idx, self.button_data[idx]["text"])
            dlg.destroy()
        save_btn = ttk.Button(dlg, text="Save", command=save_and_close)
        save_btn.grid(row=row_num, column=0, columnspan=2, pady=16)
        dlg.transient(self.master)
        dlg.wait_visibility()
        dlg.grab_set()

        def _apply_button_data(self, idx):
            for widget in self.widgets:
                var_name = widget["name"]
                if widget["checkbox"] is not None:
                    val = self.button_data[idx]["checkboxes"].get(var_name, widget["checkbox"].get())
                    widget["checkbox"].set(val)
                else:
                    val = self.button_data[idx]["values"].get(var_name, widget["entry"].get())
                    widget["entry"].delete(0, tk.END)
                    widget["entry"].insert(0, val)
            # --- PATCH: also populate the Crib Time value in main variables from preset ---
            crib_time_val = self.button_data[idx]["values"].get("crib_time", None)
            if crib_time_val is not None:
                for widget in self.widgets:
                    if widget["name"] == "crib_time" and widget["entry"] is not None:
                        widget["entry"].delete(0, tk.END)
                        widget["entry"].insert(0, crib_time_val)
            self.load_settings()

    def _on_settings_variable_change(self, *args):
        self.load_settings()
        self.build_game_sequence()

    def load_settings(self):
        # Calculate "Start First Game In" from "Time to Start First Game" minus "Between Game Break"
        time_entry_val = None
        between_game_break_val = None
        start_first_game_in_widget = None
        for widget in self.widgets:
            if widget["name"] == "time_to_start_first_game":
                time_entry_val = widget["entry"].get().strip()
            elif widget["name"] == "between_game_break":
                between_game_break_val = widget["entry"].get().replace(",", ".")
            elif widget["name"] == "start_first_game_in":
                start_first_game_in_widget = widget["entry"]
        # Calculate start_first_game_in value if time is valid
        minutes_to_start = None
        now = datetime.datetime.now()
        if time_entry_val:
            try:
                # Allow single or double digit hour, always two digit minute
                # Use strict 24-hour regex
                time_match = re.match(r"^([01][0-9]|2[0-3]):[0-5][0-9]$", time_entry_val)
                if time_match:
                    hh, mm = map(int, time_entry_val.split(":"))
                    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    # If target time already passed today, assume it's tomorrow
                    if target < now:
                        target = target + datetime.timedelta(days=1)
                    delta = target - now
                    minutes_to_start = int(delta.total_seconds() // 60)
            except Exception:
                minutes_to_start = None
        try:
            # Between game break (minutes), allow comma/dot decimal
            bgb_minutes = float(between_game_break_val) if between_game_break_val else 0.0
        except Exception:
            bgb_minutes = 0.0
        if minutes_to_start is not None and start_first_game_in_widget is not None:
            value = max(0, minutes_to_start - int(bgb_minutes))
            start_first_game_in_widget.delete(0, tk.END)
            start_first_game_in_widget.insert(0, str(value))
            self.variables["start_first_game_in"]["value"] = str(value)
        # Set all other values normally
        for widget in self.widgets:
            entry = widget["entry"]
            var_name = widget["name"]
            if entry is not None:
                value = entry.get().replace(',', '.')
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

        def set_button_state(btn, allowed, disabled_bg="#d3d3d3", disabled_fg="#888"):
            if btn is not None:
                try:
                    if allowed:
                        btn.config(state=tk.NORMAL)
                        btn.config(bg=btn.cget("bg"), fg=btn.cget("fg"))
                    else:
                        btn.config(state=tk.DISABLED)
                        btn.config(bg=disabled_bg, fg=disabled_fg)
                except Exception:
                    pass

        set_button_state(getattr(self, 'white_timeout_button', None), allowed)
        set_button_state(getattr(self, 'black_timeout_button', None), allowed)

        if hasattr(self, "team_timeout_period_entry") and self.team_timeout_period_entry is not None:
            try:
                entry_state = "normal" if allowed else "disabled"
                self.team_timeout_period_entry.config(state=entry_state)
            except Exception:
                pass
        if hasattr(self, "team_timeout_period_label") and self.team_timeout_period_label is not None:
            try:
                label_fg = "black" if allowed else "grey"
                self.team_timeout_period_label.config(fg=label_fg)
            except Exception:
                pass

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

    def create_display_window(self):
        self.display_window = tk.Toplevel(self.master)
        self.display_window.title("Display Window")
        self.display_window.geometry('1200x800')

        tab = ttk.Frame(self.display_window)
        tab.pack(fill="both", expand=True,)

        for i in range(11):
            tab.grid_rowconfigure(i, weight=1)
        for i in range(9):
            tab.grid_columnconfigure(i, weight=1)

        self.display_court_time_label = tk.Label(tab, textvariable=self.court_time_var, font=self.display_fonts["court_time"], bg="lightgrey")
        self.display_court_time_label.grid(row=0, column=0, columnspan=9, padx=1, pady=1, sticky="nsew")

        self.display_half_label = tk.Label(tab, textvariable=self.half_label_var, font=self.display_fonts["half"], bg="lightcoral")
        self.display_half_label.grid(row=1, column=0, columnspan=9, padx=1, pady=1, sticky="nsew")

        self.display_white_label = tk.Label(tab, textvariable=self.white_team_var, font=self.display_fonts["team"], bg="white", fg="black")
        self.display_white_label.grid(row=2, column=0, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.display_black_label = tk.Label(tab, textvariable=self.black_team_var, font=self.display_fonts["team"], bg="black", fg="white")
        self.display_black_label.grid(row=2, column=6, columnspan=3, padx=1, pady=1, sticky="nsew")

        self.display_game_label = tk.Label(tab, textvariable=self.game_number_var, font=self.display_fonts["game_no"], bg="light grey")
        self.display_game_label.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.display_penalty_grid_frame, self.display_penalty_labels = self.create_penalty_grid_widget(tab, is_display=True)
        self.display_penalty_grid_frame.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.display_penalty_grid_frame.grid_remove()  # hide initially

        self.display_white_score = tk.Label(tab, textvariable=self.white_score_var, font=self.display_fonts["score"], bg="white", fg="black")
        self.display_white_score.grid(row=3, column=0, rowspan=8, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.display_black_score = tk.Label(tab, textvariable=self.black_score_var, font=self.display_fonts["score"], bg="black", fg="white")
        self.display_black_score.grid(row=3, column=6, rowspan=8, columnspan=3, padx=1, pady=1, sticky="nsew")

        self.display_timer_label = tk.Label(tab, textvariable=self.timer_var, font=self.display_fonts["timer"], bg="lightgrey", fg="black")
        self.display_timer_label.grid(row=3, column=3, rowspan=8, columnspan=3, padx=1, pady=1, sticky="nsew")

        self.display_window.bind('<Configure>', self.scale_display_fonts)
        self.display_initial_width = self.display_window.winfo_width() or 1200
        self.display_window.update_idletasks()
        self.scale_display_fonts(None)
        self.sync_display_widgets()

    def sync_display_widgets(self):
        # Event-driven approach: No polling needed since all widgets use textvariable
        # Background colors still need to be synchronized for the half label
        def sync_backgrounds():
            # Only sync background colors that can't be handled by textvariable
            self.display_half_label.config(bg=self.half_label.cget("bg"))
            self.master.after(100, sync_backgrounds)  # Reduced frequency for background sync only
        sync_backgrounds()

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
            # Event-driven: Update the StringVar instead of calling .config()
            self.half_label_var.set(self.full_sequence[0]["name"])
            self.update_half_label_background(self.full_sequence[0]["name"])
        else:
            self.timer_seconds = 0
            # Event-driven: Update the StringVar instead of calling .config()
            self.half_label_var.set("")
        self.update_timer_display()

        now = datetime.datetime.now()
        self.court_time_seconds = now.hour * 3600 + now.minute * 60 + now.second
        self.court_time_paused = False
        self.update_court_time()
        self.start_current_period()
    def update_court_time(self):
        if self.court_time_job is not None:
            self.master.after_cancel(self.court_time_job)
            self.court_time_job = None

        if self.court_time_seconds is None:
            now = datetime.datetime.now()
            self.court_time_seconds = now.hour * 3600 + now.minute * 60 + now.second

        if self.court_time_paused:
            self.court_time_job = self.master.after(1000, self.update_court_time)
            return

        self.court_time_seconds += 1

        hours, remainder = divmod(self.court_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_string = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        # Event-driven: Update the StringVar instead of calling .config()
        self.court_time_var.set(f"Court Time is {time_string}")
        self.court_time_job = self.master.after(1000, self.update_court_time)

    def update_timer_display(self):
        if self.referee_timeout_active:
            mins, secs = divmod(self.referee_timeout_elapsed, 60)
            # Event-driven: Update the StringVar instead of calling .config()
            self.timer_var.set(f"{int(mins):02d}:{int(secs):02d}")
            return
        cur_period = self.full_sequence[self.current_index] if self.full_sequence and self.current_index < len(self.full_sequence) else None
        if cur_period and cur_period['name'] == 'Sudden Death':
            mins, secs = divmod(self.sudden_death_seconds, 60)
            # Event-driven: Update the StringVar instead of calling .config()
            self.timer_var.set(f"{int(mins):02d}:{int(secs):02d}")
        else:
            mins, secs = divmod(self.timer_seconds, 60)
            # Event-driven: Update the StringVar instead of calling .config()
            self.timer_var.set(f"{int(mins):02d}:{int(secs):02d}")

    def adjust_between_game_break_for_crib_time(self):
        current_court_time = datetime.datetime.now() - datetime.timedelta(seconds=self.court_time_seconds)
        local_time = datetime.datetime.now()
        seconds_behind = int((local_time - current_court_time).total_seconds())
        if seconds_behind <= 0:
            return
        crib_time_var = self.variables['crib_time']
        crib_time = int(float(crib_time_var.get("value", crib_time_var["default"])))
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

        # Shorten Between Game Break if court time is behind local time (paused for ref timeout etc)
        if cur_period['name'] == "Between Game Break":
            now = datetime.datetime.now()
            local_seconds = now.hour * 3600 + now.minute * 60 + now.second
            court_seconds = self.court_time_seconds
            if local_seconds > court_seconds:
                delta = local_seconds - court_seconds
                crib_time = 0
                try:
                    crib_var = self.variables['crib_time']
                    crib_time = int(float(crib_var.get("value", crib_var["default"])))
                except Exception:
                    crib_time = 0
                reduce_by = min(delta, crib_time)
                if reduce_by > 0 and cur_period['duration'] is not None:
                    cur_period['duration'] = max(0, cur_period['duration'] - reduce_by)

        if cur_period['name'] in ['First Half', 'Second Half', 'Between Game Break']:
            self.white_timeouts_this_half = 0
            self.black_timeouts_this_half = 0

        # Event-driven: Update the StringVar instead of calling .config()
        self.half_label_var.set(cur_period['name'])
        self.update_half_label_background(cur_period['name'])

        TIMEOUTS_DISABLED_PERIODS = [
            "Game Starts in:",
            "Half Time",
            "Overtime Game Break",
            "Sudden Death Game Break",
            "Overtime First Half",
            "Overtime Half Time",
            "Overtime Second Half",
            "Sudden Death",
        ]
        # Always enable penalties during Referee Time-Out, even if entered from Game Starts in
        if cur_period['name'] == "Referee Time-Out":
            self.penalties_button.config(state=tk.NORMAL)
            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
        elif cur_period['name'] in TIMEOUTS_DISABLED_PERIODS:
            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            if cur_period['name'] in ["Game Starts in:", "Between Game Break", "Half Time", "Overtime Game Break", "Sudden Death Game Break"]:
                self.penalties_button.config(state=tk.DISABLED)
            else:
                self.penalties_button.config(state=tk.NORMAL)
        elif cur_period['name'] == "Between Game Break":
            # Team timeout buttons should be greyed out (disabled) during Between Game Break
            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.penalties_button.config(state=tk.DISABLED)
        else:
            self.white_timeout_button.config(state=tk.NORMAL, bg="white", fg="black")
            self.black_timeout_button.config(state=tk.NORMAL, bg="black", fg="white")
            self.penalties_button.config(state=tk.NORMAL)

        PAUSE_PERIODS = [
            "Half Time",
            "Overtime Game Break",
            "Overtime Half Time",
            "Sudden Death Game Break",
            "White Team Time-Out",
            "Black Team Time-Out",
            "Referee Time-Out"
        ]
        if cur_period['name'] in PAUSE_PERIODS:
            self.pause_all_penalty_timers()
        else:
            self.resume_all_penalty_timers()

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
            self.sudden_death_seconds = -1
            self.update_timer_display()
            self.start_sudden_death_timer()
        else:
            self.timer_seconds = cur_period['duration'] if cur_period['duration'] is not None else 0
            self.update_timer_display()
            self.timer_running = True
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            self.timer_job = self.master.after(1000, self.countdown_timer)

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
        if self.sudden_death_seconds < 0:
            self.sudden_death_seconds = 0
        else:
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
            if cur_period and cur_period['name'] == 'Between Game Break':
                if self.timer_seconds == 30:
                    self.white_score_var.set(0)
                    self.black_score_var.set(0)
                    self.stored_penalties.clear()
                    self.clear_all_penalties()
                if self.timer_seconds <= 30:
                    self.sudden_death_restore_active = False
                    self.sudden_death_restore_time = None
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
        # Immediately grey out (disable) the button when pressed
        self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
        if period['type'] != 'regular' or not self.team_timeouts_allowed_var.get():
            return
        if self.in_timeout:
            if self.pending_timeout is None and self.active_timeout_team != "white":
                self.pending_timeout = "white"
                status = f"{self.active_timeout_team.capitalize()} Team Time-Out (White Pending)"
                # Event-driven: Update the StringVar instead of calling .config()
                self.half_label_var.set(status)
            return
        if self.white_timeouts_this_half >= 1:
            self.show_timeout_popup("White")
            return
        self.white_timeouts_this_half += 1
        self.in_timeout = True
        self.active_timeout_team = "white"
        self.court_time_paused = True
        self.save_timer_state()
        self.pause_all_penalty_timers()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_running = False
        timeout_seconds = self.get_minutes('team_timeout_period')
        self.timer_seconds = timeout_seconds
        # Event-driven: Update the StringVar instead of calling .config()
        self.half_label_var.set("White Team Time-Out")
        self.update_half_label_background("White Team Time-Out")
        self.update_timer_display()
        self.timer_job = self.master.after(1000, self.timeout_countdown)

    def black_team_timeout(self):
        period = self.full_sequence[self.current_index]
        # Immediately grey out (disable) the button when pressed
        self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
        if period['type'] != 'regular' or not self.team_timeouts_allowed_var.get():
            return
        if self.in_timeout:
            if self.pending_timeout is None and self.active_timeout_team != "black":
                self.pending_timeout = "black"
                status = f"{self.active_timeout_team.capitalize()} Team Time-Out (Black Pending)"
                # Event-driven: Update the StringVar instead of calling .config()
                self.half_label_var.set(status)
            return
        if self.black_timeouts_this_half >= 1:
            self.show_timeout_popup("Black")
            return
        self.black_timeouts_this_half += 1
        self.in_timeout = True
        self.active_timeout_team = "black"
        self.court_time_paused = True
        self.save_timer_state()
        self.pause_all_penalty_timers()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_running = False
        timeout_seconds = self.get_minutes('team_timeout_period')
        self.timer_seconds = timeout_seconds
        # Event-driven: Update the StringVar instead of calling .config()
        self.half_label_var.set("Black Team Time-Out")
        self.update_half_label_background("Black Team Time-Out")
        self.update_timer_display()
        self.timer_job = self.master.after(1000, self.timeout_countdown)

    def timeout_countdown(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.update_timer_display()
        if not self.in_timeout:
            return
        if self.timer_seconds > 0:
            self.timer_seconds -= 1
            self.timer_job = self.master.after(1000, self.timeout_countdown)
        else:
            self.end_timeout()

    def end_timeout(self):
        self.in_timeout = False
        prev_active_team = self.active_timeout_team  # Store who just finished
        self.active_timeout_team = None
        self.court_time_paused = False
        self.resume_all_penalty_timers()
        self.timer_running = self.saved_timer_running
        self.timer_seconds = self.saved_timer_seconds
        self.current_index = self.saved_index
        # Event-driven: Update the StringVar instead of calling .config()
        self.half_label_var.set(self.saved_half_label)
        self.half_label.config(bg=self.saved_half_label_bg)
        self.update_timer_display()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        # If a pending timeout exists, start it now
        if self.pending_timeout is not None:
            if self.pending_timeout == "white" and self.white_timeouts_this_half < 1:
                self.pending_timeout = None
                self.white_team_timeout()
            elif self.pending_timeout == "black" and self.black_timeouts_this_half < 1:
                self.pending_timeout = None
                self.black_team_timeout()
            else:
                self.pending_timeout = None
        elif self.timer_running:
            self.timer_job = self.master.after(1000, self.countdown_timer)

    def save_timer_state(self):
        self.saved_timer_running = self.timer_running
        self.saved_timer_seconds = self.timer_seconds
        self.saved_index = self.current_index
        # Event-driven: Get text from StringVar instead of widget
        self.saved_half_label = self.half_label_var.get()
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
            "referee_time-out",
            "white_team_time-out",
            "black_team_time-out",
            "white_team_time-out",
            "black_team_time-out",
            "white_team_time-out",
            "black_team_time-out"
        }
        internal_name = period_name.lower().replace(" ", "_")
        if "time_out" in internal_name or internal_name in red_periods:
            self.half_label.config(bg="red")
        else:
            self.half_label.config(bg="lightblue")

    def convert_duration_to_seconds(self, duration):
        if duration == "1 minute":
            return 60
        elif duration == "2 minutes":
            return 120
        elif duration == "5 minutes":
            return 300
        elif duration == "Rest of the match":
            return -1
        return 0

    def start_penalty_timer(self, team, cap, duration):
        seconds = self.convert_duration_to_seconds(duration)
        if seconds == 0:
            return False
        penalty = {
            "team": team,
            "cap": cap,
            "duration": duration,
            "seconds_remaining": seconds,
            "timer_job": None,
            "is_rest_of_match": seconds == -1
        }
        self.active_penalties.append(penalty)
        self.stored_penalties.append({"team": team, "cap": cap, "duration": duration})
        self.update_penalty_display()
        if not penalty["is_rest_of_match"]:
            self.schedule_penalty_countdown(penalty)
        return True

    def schedule_penalty_countdown(self, penalty):
        if not self.penalty_timers_paused and penalty["seconds_remaining"] > 0:
            penalty["timer_job"] = self.master.after(1000, lambda: self.penalty_countdown(penalty))

    def penalty_countdown(self, penalty):
        """
        Handles countdown for an individual penalty. When the timer runs down to zero,
        removes the penalty and updates the penalty display robustly.
        """
        if penalty not in self.active_penalties:
            # Don't need to call update_penalty_display here, remove_penalty does it
            return
        if penalty.get("timer_job"):
            try:
                self.master.after_cancel(penalty["timer_job"])
            except Exception:
                pass
            penalty["timer_job"] = None
        if self.penalty_timers_paused or penalty.get("is_rest_of_match"):
            return
        if penalty["seconds_remaining"] > 0:
            penalty["seconds_remaining"] -= 1
            self.update_penalty_display()
            self.schedule_penalty_countdown(penalty)
        else:
            self.remove_penalty(penalty)  # This will update the display

    def remove_penalty(self, penalty):
        if penalty in self.active_penalties:
            if penalty["timer_job"]:
                self.master.after_cancel(penalty["timer_job"])
                penalty["timer_job"] = None
            self.active_penalties.remove(penalty)
            for stored in self.stored_penalties[:]:
                if (stored["team"] == penalty["team"] and 
                    stored["cap"] == penalty["cap"] and 
                    stored["duration"] == penalty["duration"]):
                    self.stored_penalties.remove(stored)
                    break
            # Ensure widget display updates after ALL removals
            self.update_penalty_display()

    def clear_all_penalties(self):
        for penalty in self.active_penalties[:]:
            self.remove_penalty(penalty)
        self.update_penalty_display()

    def pause_all_penalty_timers(self):
        self.penalty_timers_paused = True
        for penalty in self.active_penalties:
            if penalty["timer_job"]:
                self.master.after_cancel(penalty["timer_job"])
                penalty["timer_job"] = None
        self.update_penalty_display()

    def resume_all_penalty_timers(self):
        self.penalty_timers_paused = False
        for penalty in self.active_penalties:
            if not penalty["is_rest_of_match"] and penalty["seconds_remaining"] > 0:
                self.schedule_penalty_countdown(penalty)
        self.update_penalty_display()

    def show_penalties(self):
        penalty_window = tk.Toplevel(self.master)
        penalty_window.title("Penalties")
        penalty_window.geometry("250x450")

        button_frame = ttk.Frame(penalty_window, padding="10")
        button_frame.pack(side="top", fill="x")
        selected_team = tk.StringVar()

        button_white = tk.Button(button_frame, text="White", width=10, command=lambda: select_team("White"))
        button_white.pack(side="left", padx=5, expand=True)
        button_black = tk.Button(button_frame, text="Black", width=10, command=lambda: select_team("Black"))
        button_black.pack(side="left", padx=5, expand=True)

        def select_team(team):
            selected_team.set(team)
            button_white.config(relief=tk.SUNKEN if team == "White" else tk.RAISED)
            button_black.config(relief=tk.SUNKEN if team == "Black" else tk.RAISED)

        select_team(selected_team.get())

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
        penalty_listbox = tk.Listbox(summary_frame, height=6, exportselection=0)
        penalty_listbox.pack(fill="both", expand=True)

        def refresh_penalty_listbox():
            selection = penalty_listbox.curselection()
            selected_index = selection[0] if selection else None

            penalty_listbox.delete(0, tk.END)
            for penalty in getattr(self, 'active_penalties', []):
                if penalty["is_rest_of_match"]:
                    time_str = "REST OF MATCH"
                else:
                    mins, secs = divmod(penalty["seconds_remaining"], 60)
                    time_str = f"{int(mins):02d}:{int(secs):02d}"
                penalty_listbox.insert(tk.END, f"{penalty['team']} #{penalty['cap']} {time_str}")

            for p in getattr(self, 'stored_penalties', []):
                if not any(ap["team"] == p["team"] and ap["cap"] == p["cap"] and ap["duration"] == p["duration"]
                        for ap in getattr(self, 'active_penalties', [])):
                    penalty_listbox.insert(tk.END, f"{p['team']} #{p['cap']} {p['duration']}")

            if selected_index is not None and penalty_listbox.size() > selected_index:
                penalty_listbox.selection_set(selected_index)
                penalty_listbox.activate(selected_index)
            elif penalty_listbox.size() > 0:
                penalty_listbox.selection_clear(0, tk.END)

        refresh_penalty_listbox()

        def periodic_refresh():
            if penalty_window.winfo_exists():
                refresh_penalty_listbox()
                penalty_window.after(1000, periodic_refresh)
        penalty_window.after(1000, periodic_refresh)

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

            if self.start_penalty_timer(team, cap, duration):
                refresh_penalty_listbox()
                selected_team.set("")
                select_team("")
                dropdown_variable.set(dropdown_options[0])
                radio_variable.set("")
            else:
                messagebox.showerror("Error", "Failed to start penalty timer.")

        def remove_penalty():
            selection = penalty_listbox.curselection()
            if not selection:
                messagebox.showerror("Error", "Please select a penalty to remove.")
                return

            idx = selection[0]
            active_count = len(getattr(self, 'active_penalties', []))

            if idx < active_count:
                penalty_to_remove = self.active_penalties[idx]
                self.remove_penalty(penalty_to_remove)
                refresh_penalty_listbox()
            else:
                stored_idx = idx - active_count
                if 0 <= stored_idx < len(self.stored_penalties):
                    self.stored_penalties.pop(stored_idx)
                    refresh_penalty_listbox()

        start_button_frame = ttk.Frame(penalty_window)
        start_button_frame.pack(side="bottom", fill="x", pady=10)

        button_container = ttk.Frame(start_button_frame)
        button_container.pack(expand=True, fill="x")
    
        start_button = ttk.Button(button_container, text="Start Penalty", command=start_penalty)
        start_button.pack(side="left", expand=True, fill="x", padx=(0, 5))

        remove_button = ttk.Button(button_container, text="Remove Selected", command=remove_penalty)
        remove_button.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # --- PATCH: Close button directly under Start Penalty/Remove Selected buttons ---
        close_button = ttk.Button(start_button_frame, text="Close", command=penalty_window.destroy)
        close_button.pack(side="bottom", fill="x", padx=10, pady=(0,10))

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
                # Event-driven: Get text from StringVar instead of widget
                "half_label_text": self.half_label_var.get(),
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
            self.pause_all_penalty_timers()
            self.referee_timeout_elapsed = 0
            # Event-driven: Update the StringVar instead of calling .config()
            self.half_label_var.set("Referee Time-Out")
            self.half_label.config(bg="red")
            self.referee_timeout_countup()
            # --- PATCH: Explicitly enable penalties button during referee timeout ---
            if hasattr(self, "penalties_button"):
                self.penalties_button.config(state=tk.NORMAL)
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
            # Event-driven: Update the StringVar instead of calling .config()
            self.half_label_var.set(self.saved_state["half_label_text"])
            self.half_label.config(bg=self.saved_state["half_label_bg"])
            self.court_time_paused = self.saved_state.get("court_time_paused", False)
            self.resume_all_penalty_timers()
            self.update_timer_display()
            # --- PATCH: Resume Team Time-Out timer if it was interrupted ---
            if self.in_timeout:
                # Resume the timeout countdown
                if self.timer_job:
                    self.master.after_cancel(self.timer_job)
                    self.timer_job = None
                self.timer_job = self.master.after(1000, self.timeout_countdown)
            elif self.timer_running:
                self.timer_job = self.master.after(1000, self.countdown_timer)
            if not self.court_time_paused:
                self.court_time_job = self.master.after(1000, self.update_court_time)
            # --- PATCH: Restore penalties button state after referee timeout ends ---
            cur_period = self.full_sequence[self.current_index]
            if cur_period['name'] in ["Game Starts in:", "Between Game Break"]:
                self.penalties_button.config(state=tk.DISABLED)
            else:
                self.penalties_button.config(state=tk.NORMAL)

    def referee_timeout_countup(self):
        if not self.referee_timeout_active:
            return
        mins, secs = divmod(self.referee_timeout_elapsed, 60)
        # Event-driven: Update the StringVar instead of calling .config()
        self.timer_var.set(f"{int(mins):02d}:{int(secs):02d}")
        self.referee_timeout_elapsed += 1
        self.timer_job = self.master.after(1000, self.referee_timeout_countup)

    def restore_sudden_death_after_goal_removal(self):
        self.sudden_death_goal_scored = False
        self.current_index = self.find_period_index('Sudden Death')
        self.sudden_death_seconds = self.sudden_death_restore_time
        self.sudden_death_restore_active = False
        self.sudden_death_restore_time = None
        self.start_current_period()

    def adjust_score_with_confirm(self, score_var, team_name):
        if score_var.get() == 0:
            return
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
            if (cur_period['name'] == 'Between Game Break'
                and getattr(self, 'sudden_death_restore_active', False)
                and self.sudden_death_restore_time is not None
                and self.timer_seconds > 30):
                score_var.set(score_var.get() - 1)
                self.restore_sudden_death_after_goal_removal()
                return
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

#Saves the current Sudden Death timer value (self.sudden_death_seconds) for possible restoration (for example, if the goal is later subtracted).
#Flags that a goal has been scored in Sudden Death (prevents this block from running again).
#Progresses the game to the next period (typically Between Game Break or End of Game).
        if cur_period['name'] == 'Sudden Death' and not getattr(self, 'sudden_death_goal_scored', False):
            self.sudden_death_restore_time = self.sudden_death_seconds
            self.sudden_death_restore_active = True
            self.sudden_death_goal_scored = True
            self.stop_sudden_death_timer()
            self.next_period()
            return

        # If goal added during Between Game Break and scores are now EVEN
        if cur_period['name'] == 'Between Game Break':
            if self.white_score_var.get() == self.black_score_var.get():
                if self.is_overtime_enabled():
                    self.current_index = self.find_period_index('Overtime Game Break')
                    self.start_current_period()
                    return
                elif self.is_sudden_death_enabled():
                    self.current_index = self.find_period_index('Sudden Death Game Break')
                    self.start_current_period()
                    return

        # If goal added during Overtime Game Break and scores are now UNEVEN, skip Overtime
        if cur_period['name'] == 'Overtime Game Break':
            if self.white_score_var.get() != self.black_score_var.get():
                # Skip Overtime, go straight to Between Game Break
                self.current_index = self.find_period_index('Between Game Break')
                self.start_current_period()
                return

        # Logic for Sudden Death Game Break after Overtime
        if cur_period['name'] == 'Sudden Death Game Break':
            prev_period = self.full_sequence[self.current_index - 1] if self.current_index > 0 else None
            # If scores are now unequal, progress to Between Game Break
            if self.white_score_var.get() != self.black_score_var.get():
                self.current_index = self.find_period_index('Between Game Break')
                self.start_current_period()
                return
                    
        if cur_period['name'] == 'Sudden Death' and not getattr(self, 'sudden_death_goal_scored', False):
            self.sudden_death_goal_scored = True
            self.stop_sudden_death_timer()
            self.next_period()

if __name__ == "__main__":
    root = tk.Tk()
    app = GameManagementApp(root)
    root.mainloop()
