import tkinter as tk
from tkinter import ttk, messagebox, font
import datetime
import re
import time
import os
import subprocess
import json
from zigbee_siren import ZigbeeSirenController, is_mqtt_available
from sound import (check_audio_device_available, handle_no_audio_device_warning, 
                   get_sound_files, play_sound, play_sound_with_volume)

SETTINGS_FILE = "settings.json"

def is_usb_dongle_connected():
    """
    Check if a Sonoff USB Zigbee dongle is connected.
    Returns True if a USB Zigbee dongle is detected, False otherwise.
    
    Cross-platform support:
    - Linux: Checks /dev/ttyUSB* devices and lsusb output
    - Windows: Checks COM ports via registry or device manager (if available)
    """
    import platform
    
    system = platform.system()
    
    # Linux-specific checks
    if system == 'Linux':
        try:
            # Check for /dev/ttyUSB* devices first
            dev_dir = os.path.join(os.sep, 'dev')
            if os.path.exists(dev_dir):
                devices = [f for f in os.listdir(dev_dir) if f.startswith('ttyUSB')]
                if devices:
                    return True
        except (OSError, PermissionError):
            pass
        
        try:
            # Check using lsusb for Zigbee dongles
            result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Look for common Zigbee dongle identifiers
                usb_output = result.stdout.lower()
                # Check for common Zigbee dongle manufacturers/chips
                zigbee_keywords = ['itead', 'sonoff', 'cc2531', 'cc2652', 'silicon labs', 'cp210']
                return any(keyword in usb_output for keyword in zigbee_keywords)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    # Windows-specific checks (placeholder for future implementation)
    elif system == 'Windows':
        # On Windows, COM ports can be checked via serial.tools.list_ports
        # This is handled in zigbee_siren.py WindowsZigbeeSirenController
        # For now, return False to avoid false positives
        pass
    
    return False

def open_folder_in_file_manager(folder_path):
    """
    Open a folder in the system's file manager.
    
    Cross-platform support:
    - Windows: Uses explorer.exe
    - macOS: Uses open command
    - Linux: Uses xdg-open
    
    Args:
        folder_path: Absolute path to the folder to open
    """
    import platform
    
    if not os.path.exists(folder_path):
        messagebox.showerror("Error", f"Folder does not exist:\n{folder_path}")
        return
    
    system = platform.system()
    
    try:
        if system == 'Windows':
            # Windows: Use explorer
            subprocess.run(['explorer', os.path.normpath(folder_path)], check=True)
        elif system == 'Darwin':
            # macOS: Use open
            subprocess.run(['open', folder_path], check=True)
        else:
            # Linux and other Unix-like systems: Use xdg-open
            subprocess.run(['xdg-open', folder_path], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to open folder:\n{e}")
    except FileNotFoundError:
        messagebox.showerror("Error", f"File manager command not found on {system}")

def migrate_legacy_settings():
    """Migrate settings from legacy separate files to unified settings.json"""
    unified_settings = get_default_unified_settings()
    migrated = False
    
    # Migrate game_settings.json (sound settings)
    legacy_sound_file = os.path.join(os.getcwd(), "game_settings.json")
    if os.path.exists(legacy_sound_file):
        try:
            with open(legacy_sound_file, "r") as f:
                legacy_sound_settings = json.load(f)
            unified_settings["soundSettings"].update(legacy_sound_settings)
            migrated = True
            print("Migrated sound settings from game_settings.json")
        except Exception as e:
            print(f"Error migrating game_settings.json: {e}")
    
    # Migrate zigbee_config.json (zigbee settings)
    legacy_zigbee_file = os.path.join(os.getcwd(), "zigbee_config.json")
    if os.path.exists(legacy_zigbee_file):
        try:
            with open(legacy_zigbee_file, "r") as f:
                legacy_zigbee_settings = json.load(f)
            unified_settings["zigbeeSettings"].update(legacy_zigbee_settings)
            migrated = True
            print("Migrated Zigbee settings from zigbee_config.json")
        except Exception as e:
            print(f"Error migrating zigbee_config.json: {e}")
    
    if migrated:
        save_unified_settings(unified_settings)
        print("Migration completed. Legacy files preserved.")
    
    return unified_settings

def load_unified_settings():
    """Load unified settings from JSON file."""
    settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            try:
                return json.load(f)
            except Exception:
                # If settings.json exists but is corrupted, try migration
                return migrate_legacy_settings()
    else:
        # If settings.json doesn't exist, try migration first
        return migrate_legacy_settings()

def save_unified_settings(settings):
    """Save unified settings to JSON file."""
    settings_path = os.path.join(os.getcwd(), SETTINGS_FILE)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

def get_default_unified_settings():
    """Get default unified settings structure."""
    return {
        "soundSettings": {
            "pips_sound": "Default",
            "siren_sound": "Default", 
            "pips_volume": 50.0,
            "siren_volume": 50.0,
            "air_volume": 50.0,
            "water_volume": 50.0,
            "enable_sound": True
        },
        "zigbeeSettings": {
            "mqtt_broker": "localhost",
            "mqtt_port": 1883,
            "mqtt_username": "",
            "mqtt_password": "",
            "mqtt_topic": "zigbee2mqtt/+",
            "siren_button_devices": ["siren_button"],  # Now supports multiple devices as a list
            "siren_button_device": "siren_button",     # Keep for backward compatibility
            "connection_timeout": 60,
            "reconnect_delay": 5,
            "enable_logging": True
        },
        "gameSettings": {
            "time_to_start_first_game": "",
            "start_first_game_in": 1,
            "team_timeouts_allowed": True,
            "team_timeout_period": 1,
            "half_period": 1,
            "half_time_break": 1,
            "overtime_allowed": True,
            "overtime_game_break": 1,
            "overtime_half_period": 1,
            "overtime_half_time_break": 1,
            "sudden_death_game_break": 1,
            "between_game_break": 1,
            "record_scorers_cap_number": False,
            "crib_time": 3
        },
        "presetSettings": [
            {
                "text": "CMAS",
                "values": {
                    "team_timeout_period": "1",           # Team timeout 1 minute
                    "half_period": "15",                  # Half period 15 minutes
                    "half_time_break": "3",               # Half time break 3 minutes
                    "overtime_game_break": "3",           # Overtime game break 3 minutes
                    "overtime_half_period": "5",          # Overtime half period 5 minutes
                    "overtime_half_time_break": "1",      # Overtime half time break 1 minute
                    "sudden_death_game_break": "1",       # Sudden Death Game break 1 minute
                    "between_game_break": "5",            # Between Game break 5 minutes
                    "crib_time": "60"                     # Crib time default 60 seconds
                },
                "checkboxes": {
                    "team_timeouts_allowed": True,        # Team timeouts allowed checked
                    "overtime_allowed": True              # Overtime allowed checked
                }
            },
            {
                "text": "2",
                "values": {},
                "checkboxes": {}
            },
            {
                "text": "3",
                "values": {},
                "checkboxes": {}
            },
            {
                "text": "4",
                "values": {},
                "checkboxes": {}
            },
            {
                "text": "5",
                "values": {},
                "checkboxes": {}
            },
            {
                "text": "6",
                "values": {},
                "checkboxes": {}
            }
        ]
    }

def load_sound_settings():
    """Load sound settings from unified JSON file."""
    unified_settings = load_unified_settings()
    return unified_settings.get("soundSettings", {})

def save_sound_settings(settings):
    """Save sound settings to unified JSON file."""
    unified_settings = load_unified_settings()
    unified_settings["soundSettings"] = settings
    save_unified_settings(unified_settings)

def load_preset_settings():
    """Load preset settings from unified JSON file."""
    unified_settings = load_unified_settings()
    return unified_settings.get("presetSettings", get_default_unified_settings()["presetSettings"])

def save_preset_settings(presets):
    """Save preset settings to unified JSON file."""
    unified_settings = load_unified_settings()
    unified_settings["presetSettings"] = presets
    save_unified_settings(unified_settings)

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
            "start_first_game_in": {"default": 1, "checkbox": False, "unit": "minutes", "label": "First Game Starts In:"},
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
            "record_scorers_cap_number": {"default": False, "checkbox": True, "unit": "", "label": "Record Scorers Cap Number"},
            "crib_time": {"default": 1, "checkbox": True, "unit": "seconds"}
        }

        # PATCH: Initialize 'value' and 'used' fields properly for all variables
        for var_name, var_info in self.variables.items():
            if var_info["checkbox"]:
                # Variables with checkboxes: separate 'value' and 'used' fields
                if var_name in ["team_timeouts_allowed", "overtime_allowed", "record_scorers_cap_number"]:
                    # Pure boolean variables (no numeric component)
                    self.variables[var_name]["value"] = var_info["default"]  # True or False
                    self.variables[var_name]["used"] = var_info["default"]   # True or False
                else:
                    # Mixed variables (checkbox + entry): numeric value, boolean used
                    self.variables[var_name]["value"] = str(var_info["default"])  # "1" 
                    self.variables[var_name]["used"] = True  # enabled by default
            else:
                # Variables without checkboxes: only 'value' field, always used
                self.variables[var_name]["value"] = str(var_info["default"])
                self.variables[var_name]["used"] = True

        self.fonts = {
            "court_time": font.Font(family="Arial", size=36),
            "half": font.Font(family="Arial", size=36, weight="bold"),
            "team": font.Font(family="Arial", size=30, weight="bold"),
            "score": font.Font(family="Arial", size=200, weight="bold"),
            "timer": font.Font(family="Arial", size=90, weight="bold"),
            "game_no": font.Font(family="Arial", size=20),
            "button": font.Font(family="Arial", size=20, weight="bold"),
            "timeout_button": font.Font(family="Arial", size=20, weight="bold"),
            "referee_timeout_timer": font.Font(family="Arial", size=20, weight="bold"),
        }

        self.display_fonts = {
            "court_time": font.Font(family="Arial", size=36),
            "half": font.Font(family="Arial", size=36, weight="bold"),
            "team": font.Font(family="Arial", size=30, weight="bold"),
            "score": font.Font(family="Arial", size=200, weight="bold"),
            "timer": font.Font(family="Arial", size=90, weight="bold"),
            "game_no": font.Font(family="Arial", size=20),
            "referee_timeout_timer": font.Font(family="Arial", size=24),
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
        self.referee_timeout_timer_var = tk.StringVar(value="Ref Time-Out")
        
        # Tournament List tracking
        self.current_game_index = 0  # Index in self.game_numbers list
        
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
        self.record_scorers_cap_number_var = tk.BooleanVar(value=self.variables["record_scorers_cap_number"]["default"])
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

        # Initialize volume variables for sounds - load from settings
        sound_settings = load_sound_settings()
        self.pips_volume = tk.DoubleVar(value=sound_settings.get("pips_volume", 50.0))
        self.siren_volume = tk.DoubleVar(value=sound_settings.get("siren_volume", 50.0))
        self.air_volume = tk.DoubleVar(value=sound_settings.get("air_volume", 50.0))
        self.water_volume = tk.DoubleVar(value=sound_settings.get("water_volume", 50.0))
        self.enable_sound = tk.BooleanVar(value=sound_settings.get("enable_sound", True))
        
        # Initialize sound selection variables with auto-selection of first audio file if no saved setting
        sound_files = get_sound_files()
        available_audio_files = sound_files if sound_files != ["No sound files found"] else []
        
        pips_default = sound_settings.get("pips_sound", "Default")
        siren_default = sound_settings.get("siren_sound", "Default")
        
        # If no saved setting and audio files are available, pick the first one
        if pips_default == "Default" and available_audio_files:
            pips_default = available_audio_files[0]
        if siren_default == "Default" and available_audio_files:
            siren_default = available_audio_files[0]
            
        self.pips_var = tk.StringVar(value=pips_default)
        self.siren_var = tk.StringVar(value=siren_default)
        
        # Track audio device warning to prevent loops
        self.audio_device_warning_shown = False

        # Initialize Zigbee siren controller
        self.zigbee_controller = ZigbeeSirenController(siren_callback=self.trigger_wireless_siren)
        self.zigbee_status_var = tk.StringVar(value="Disconnected")
        self.zigbee_controller.set_connection_status_callback(self.update_zigbee_status)
        
        # Connection watchdog variables
        self.connection_watchdog_active = False
        self.connection_watchdog_attempts = 0
        self.connection_watchdog_max_attempts = 3
        self.connection_watchdog_job = None
        self.user_initiated_action = False

        self.create_scoreboard_tab()
        self.create_settings_tab()
        self.create_sounds_tab()
        self.create_zigbee_siren_tab()
        
        # Select Game Variables tab by default
        self.notebook.select(1)
        
        # Initialize USB dongle status after creating the Zigbee tab
        self.update_usb_dongle_status()
        
        # Start connection watchdog instead of direct auto-connect
        self.start_connection_watchdog()
        
        self.load_game_settings()  # Load game settings from unified file
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

    def log_game_event(self, event_type, team=None, cap_number=None, duration=None, break_status=None):
        """
        Log a game event to UWH_Game_Data.txt.
        Creates the file if it doesn't exist, otherwise appends.
        Each event is written as a pipe-separated line with fields:
        local_datetime|court_time|event_type|team|cap_number|duration|break_status
        
        Args:
            event_type: Type of event (e.g., "First Half Start", "Goal", "Penalty Start")
            team: Team name for goals and penalties (White/Black)
            cap_number: Cap number for penalties
            duration: Duration for penalties (e.g., "2 minutes")
            break_status: Break/timeout status (e.g., "Team Time-Out", "Referee Time-Out", "Break")
        """
        # Get current date/time
        now = datetime.datetime.now()
        local_time = now.strftime("%Y-%m-%d %H:%M:%S")
        
        # Get court time (hh:mm:ss format)
        if self.court_time_seconds is not None:
            hours, remainder = divmod(self.court_time_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            court_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            court_time = "00:00:00"
        
        # Build the event data fields in order
        fields = [
            local_time,
            court_time,
            event_type,
            team if team else "",
            cap_number if cap_number else "",
            duration if duration else "",
            break_status if break_status else ""
        ]
        
        # Create pipe-separated line
        event_line = "|".join(str(field) for field in fields)
        
        txt_file = os.path.join(os.getcwd(), "UWH_Game_Data.txt")
        
        try:
            # Open in append mode, create if doesn't exist
            with open(txt_file, 'a') as f:
                f.write(event_line + "\n")
        except Exception as e:
            print(f"Error logging game event: {e}")

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

        # Team name widgets - NEW: Added in row 3 to show CSV team names
        self.white_team_name_widget = tk.Label(tab, text="", font=self.fonts["team"], bg="white", fg="black")
        self.white_team_name_widget.grid(row=3, column=0, columnspan=3, padx=1, pady=1, sticky="nsew")
        
        self.black_team_name_widget = tk.Label(tab, text="", font=self.fonts["team"], bg="black", fg="white")
        self.black_team_name_widget.grid(row=3, column=6, columnspan=3, padx=1, pady=1, sticky="nsew")

        # Score widgets - MODIFIED: Moved to row 4 and reduced rowspan from 6 to 5
        self.white_score = tk.Label(tab, textvariable=self.white_score_var, font=self.fonts["score"], bg="white", fg="black")
        self.white_score.grid(row=4, column=0, rowspan=5, columnspan=3, padx=1, pady=1, sticky="nsew")
        self.black_score = tk.Label(tab, textvariable=self.black_score_var, font=self.fonts["score"], bg="black", fg="white")
        self.black_score.grid(row=4, column=6, rowspan=5, columnspan=3, padx=1, pady=1, sticky="nsew")

        # Timer widget - MODIFIED: Moved to row 4 and reduced rowspan from 6 to 5
        self.timer_label = tk.Label(tab, textvariable=self.timer_var, font=self.fonts["timer"], bg="lightgrey", fg="black")
        self.timer_label.grid(row=4, column=3, rowspan=5, columnspan=3, padx=1, pady=1, sticky="nsew")

        # Referee timeout timer label - positioned below the main timer
        self.referee_timeout_timer_label = tk.Label(
            tab, textvariable=self.referee_timeout_timer_var, 
            font=self.fonts["referee_timeout_timer"], 
            bg="red", fg="white"
        )
        self.referee_timeout_timer_label.grid(row=8, column=3, rowspan=1, columnspan=3, padx=0, pady=1, sticky="nsew")
        self.referee_timeout_timer_label.grid_remove()  # Hide initially

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
            # Show current game number label always
            if not self.game_label.winfo_ismapped():
                self.game_label.grid(row=2, column=3, columnspan=3, padx=1, pady=1, sticky="nsew")
            # Event-driven: Update the StringVar with current game number
            self.update_game_number_display()

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
            # Event-driven: Update the StringVar with current game number
            self.update_game_number_display()

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
            if self.penalty_labels[i][0].cget('text') != label_text:
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
            if self.penalty_labels[i][1].cget('text') != label_text:
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
            if self.display_penalty_labels[i][0].cget('text') != label_text:
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
            if self.display_penalty_labels[i][1].cget('text') != label_text:
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
            "game_no": 20,
            "button": 20,
            "timeout_button": 20,
            "referee_timeout_timer": 24,
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
            "game_no": 20,
            "referee_timeout_timer": 24,
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
            # PATCH: Handle boolean values by falling back to default
            if isinstance(val, bool):
                val = self.variables[varname]["default"]
            val = str(val).replace(',', '.')
            return float(val) * 60
        except Exception:
            val = str(self.variables[varname]["default"]).replace(',', '.')
            return float(val) * 60

    def build_game_sequence(self):
        seq = []
        # Always start with "First Game Starts In:" period
        now = datetime.datetime.now()
        time_val = self.variables.get("time_to_start_first_game", {}).get("value", "")
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
                # Use the time directly without subtracting Between Game Break
                game_starts_in_minutes = max(0, minutes_to_start)
        # First period: "First Game Starts In:" - only runs once at app start
        if game_starts_in_minutes is not None:
            seq.append({'name': 'First Game Starts In:', 'type': 'break', 'duration': game_starts_in_minutes * 60})
        else:
            # When time_to_start_first_game is blank, use start_first_game_in with minimum 30 seconds
            seq.append({'name': 'First Game Starts In:', 'type': 'break', 'duration': max(30, self.get_minutes('start_first_game_in'))})
        # First Game Starts In: transitions directly to First Half (no Between Game Break)

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
        # Add Between Game Break at the end for looping back to next game
        seq.append({'name': 'Between Game Break', 'type': 'break', 'duration': self.get_minutes('between_game_break')})
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
        tab.grid_rowconfigure(0, weight=3)  # Widget 1 gets most of the space
        tab.grid_rowconfigure(1, weight=1)  # Widget 2 (Presets) gets less space - reduced from 2 to 1 (50% height)
        tab.grid_rowconfigure(2, weight=1)  # Widget 4 (Tournament List) - NEW WIDGET
        tab.grid_rowconfigure(3, weight=1)  # Widget 3 (Game Sequence Explanation) - height reduced for snug text 
        tab.grid_columnconfigure(0, weight=2)  # Widget 1 on left
        tab.grid_columnconfigure(1, weight=1)  # Widget 2 and 3 on right

        default_font = font.nametofont("TkDefaultFont")
        new_size = default_font.cget("size") + 2
        headers = ["Use?", "Variable", "Value", "Units"]
        
        # Configure custom style for Preset buttons and checkboxes
        style = ttk.Style()
        style.configure('Preset.TButton', 
                       padding=(4, 2),
                       font=(default_font.cget("family"), default_font.cget("size") + 1))
        
        # Configure larger checkboxes for better visibility
        style.configure('Large.TCheckbutton',
                       focuscolor='none',
                       font=(default_font.cget("family"), default_font.cget("size") + 2))

        # Widget 1 (Game Variables) - Left side, spans all rows
        widget1 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget1.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=8, pady=8)
        for i in range(4):
            widget1.grid_columnconfigure(i, weight=1)
        for i in range(17):
            widget1.grid_rowconfigure(i, weight=1)
        for i, h in enumerate(headers):
            tk.Label(widget1, text=h, font=(default_font.cget("family"), new_size, "bold")).grid(row=0, column=i, sticky="w", padx=5, pady=4)
        row_idx = 1
        self.widgets = []
        # Ensure "time_to_start_first_game" is first, then "start_first_game_in" above team_timeouts_allowed
        entry_order = list(self.variables.keys())
        for special_name in ["time_to_start_first_game", "start_first_game_in", "record_scorers_cap_number"]:
            if special_name in entry_order:
                entry_order.remove(special_name)
        # Insert record_scorers_cap_number before crib_time
        crib_time_index = entry_order.index("crib_time") if "crib_time" in entry_order else len(entry_order)
        entry_order = (["time_to_start_first_game", "start_first_game_in"] + 
                       entry_order[:crib_time_index] + 
                       ["record_scorers_cap_number"] + 
                       entry_order[crib_time_index:])
        for var_name in entry_order:
            var_info = self.variables[var_name]
            # PATCH: Don't overwrite numeric defaults for checkbox variables that also have entries
            # Only set default to True for pure checkbox variables (no numeric component)
            if var_info["checkbox"] and var_name in ["team_timeouts_allowed", "overtime_allowed", "record_scorers_cap_number"]:
                var_info["default"] = var_info.get("default", True)
            if var_name == "team_timeouts_allowed":
                check_var = self.team_timeouts_allowed_var
                cb = ttk.Checkbutton(widget1, variable=check_var, style='Large.TCheckbutton')
                cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))
                label_text = var_info.get("label", "Team Time-Outs allowed?")
                label_widget = tk.Label(widget1, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)
                check_var.trace_add("write", lambda *args: self._on_team_timeouts_change())
                self.widgets.append({"name": var_name, "entry": None, "checkbox": check_var, "label_widget": label_widget})
                row_idx += 1
                continue
            if var_name == "overtime_allowed":
                check_var = self.overtime_allowed_var
                cb = ttk.Checkbutton(widget1, variable=check_var, style='Large.TCheckbutton')
                cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))
                label_text = var_info.get("label", "Overtime allowed?")
                label_widget = tk.Label(widget1, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)
                check_var.trace_add("write", lambda *args: self._on_overtime_change())
                self.widgets.append({"name": var_name, "entry": None, "checkbox": check_var, "label_widget": label_widget})
                row_idx += 1
                continue
            if var_name == "record_scorers_cap_number":
                check_var = self.record_scorers_cap_number_var
                cb = ttk.Checkbutton(widget1, variable=check_var, style='Large.TCheckbutton')
                cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))
                label_text = var_info.get("label", "Record Scorers Cap Number")
                label_widget = tk.Label(widget1, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)
                check_var.trace_add("write", lambda *args: self._on_single_variable_change("record_scorers_cap_number"))
                self.widgets.append({"name": var_name, "entry": None, "checkbox": check_var, "label_widget": label_widget})
                row_idx += 1
                continue
            check_var = tk.BooleanVar(value=True) if var_info["checkbox"] else None
            if check_var:
                cb = ttk.Checkbutton(widget1, variable=check_var, style='Large.TCheckbutton')
                cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))
                check_var.trace_add("write", lambda *args, name=var_name: self._on_single_variable_change(name))
            label_text = var_info.get("label", f"{var_name.replace('_', ' ').title()}:")
            label_widget = tk.Label(widget1, text=label_text, font=(default_font.cget("family"), new_size, "bold"))
            label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)
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
                    self._on_single_variable_change("time_to_start_first_game")
                entry.bind("<FocusOut>", validate_hhmm_on_focusout)
                entry.bind("<Return>", validate_hhmm_on_focusout)
            else:
                entry.insert(0, "1")
                # Special validation for numeric-only variables - only accepts numbers
                if var_name in ["crib_time", "sudden_death_game_break"]:
                    def validate_numeric_on_focusout(event, field_name=var_name):
                        val = event.widget.get().strip()
                        if val == "":
                            return
                        # Accept valid numbers (int or float with . or ,)
                        try:
                            # Replace comma with dot for European decimal notation
                            val_normalized = val.replace(',', '.')
                            val_float = float(val_normalized)  # Test if it's a valid number
                            
                            # Special validation for crib_time: check against between_game_break
                            if field_name == "crib_time":
                                # Get current between_game_break value
                                between_game_break_minutes = None
                                for widget in self.widgets:
                                    if widget["name"] == "between_game_break":
                                        try:
                                            bgb_val = widget["entry"].get().strip().replace(',', '.')
                                            between_game_break_minutes = float(bgb_val)
                                        except (ValueError, AttributeError):
                                            pass
                                        break
                                
                                # If we have a between_game_break value, validate the condition
                                if between_game_break_minutes is not None:
                                    crib_time_seconds = val_float
                                    if (between_game_break_minutes * 60) - crib_time_seconds <= 31:
                                        messagebox.showerror("Input Error", "Crib time too large. Between Game Break minus Crib time must be > 31 seconds.")
                                        event.widget.delete(0, tk.END)
                                        event.widget.insert(0, self.last_valid_values[field_name])
                                        event.widget.focus_set()
                                        event.widget.selection_range(0, tk.END)
                                        return
                            
                            # Update last valid value if validation passes
                            self.last_valid_values[field_name] = val
                            self._on_single_variable_change(field_name)
                        except ValueError:
                            # Show error and restore last valid value
                            messagebox.showerror("Input Error", f"Please enter a valid number for {field_name.replace('_', ' ').title()}.")
                            event.widget.delete(0, tk.END)
                            event.widget.insert(0, self.last_valid_values[field_name])
                            event.widget.focus_set()
                            event.widget.selection_range(0, tk.END)
                    
                    entry.bind("<FocusOut>", validate_numeric_on_focusout)
                    entry.bind("<Return>", validate_numeric_on_focusout)
                else:
                    entry.bind("<FocusOut>", lambda e, name=var_name: self._on_single_variable_change(name))
                    entry.bind("<Return>", lambda e, name=var_name: self._on_single_variable_change(name))
            entry.grid(row=row_idx, column=2, sticky="w", padx=5, pady=4)
            tk.Label(widget1, text=var_info["unit"], font=(default_font.cget("family"), new_size, "bold")).grid(row=row_idx, column=3, sticky="w", padx=5, pady=4)
            self.widgets.append({"name": var_name, "entry": entry, "checkbox": check_var, "label_widget": label_widget})
            self.last_valid_values[var_name] = entry.get()
            if var_name == "team_timeout_period":
                self.team_timeout_period_entry = entry
                self.team_timeout_period_label = label_widget
            row_idx += 1
            # Insert combined explanation label after Crib Time row
            if var_name == "crib_time":
                combined_explanation = tk.Label(
                    widget1,
                    text="• Crib Time is a period (in seconds) that is subtracted from the \"Between Game Break\" time at the start of each game to try to realign Court Time with Local Computer Time.\n• Value boxes accept decimal time e.g. 1.5 or 1,5 = 1 min, 30 sec",
                    font=(default_font.cget("family"), default_font.cget("size") - 1),
                    anchor="w", justify="left", wraplength=600
                )
                combined_explanation.grid(row=row_idx, column=0, columnspan=4, pady=3, sticky="nsew")
                row_idx += 1
                # Add reset warning as third bullet point (red and bold)
                reset_warning_bullet = tk.Label(
                    widget1,
                    text="• If you change any value in here, push the 'Reset Timer' Button!",
                    font=(default_font.cget("family"), default_font.cget("size") - 1, "bold"),
                    fg="red",
                    anchor="w", justify="left", wraplength=600
                )
                reset_warning_bullet.grid(row=row_idx, column=0, columnspan=4, pady=3, sticky="nsew")
                row_idx += 1            
        # Reset Timer button
        self.reset_timer_button = ttk.Button(widget1, text="Reset Timer", command=self.reset_timer)
        self.reset_timer_button.grid(row=row_idx, column=0, columnspan=4, pady=8)

        # Widget 2 ("Presets") - Top right, reduced size
        widget2 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget2.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)  # MODIFIED: Reduced padding from 8 to 4 (50% reduction)

        for col in range(3):
            widget2.grid_columnconfigure(col, weight=1)
        # Reduced height configuration for Widget 2
        widget2.grid_rowconfigure(0, weight=0)  # Header
        widget2.grid_rowconfigure(1, weight=1)  # Button row 1
        widget2.grid_rowconfigure(2, weight=1)  # Button row 2
        widget2.grid_rowconfigure(3, weight=0)  # Spacer
        widget2.grid_rowconfigure(4, weight=0)  # Instructional text 1
        widget2.grid_rowconfigure(5, weight=0)  # Instructional text 2
        header_label = tk.Label(widget2, text="Presets", font=(default_font.cget("family"), new_size, "bold"))
        header_label.grid(row=0, column=0, columnspan=3, padx=4, pady=(12,4), sticky="nsew")

#add in default values for CMAS rules as per section 14.2 INTERNATIONAL RULES FOR UNDERWATER HOCKEY
#RULES OF PLAY, Version 13.0, February 2025
        self.widget2_buttons = []
        # Load presets from JSON settings
        preset_data = load_preset_settings()
        self.button_data = preset_data.copy()  # Make a copy to avoid modifying the original
        
        for i in range(6):
            btn_row = 1 if i < 3 else 2
            btn_col = i % 3
            btn = ttk.Button(widget2, text=self.button_data[i]["text"], width=14, style='Preset.TButton')
            btn.grid(row=btn_row, column=btn_col, padx=8, pady=4, sticky="n")
            btn.bind("<ButtonPress-1>", self._make_press_handler(i))
            btn.bind("<ButtonRelease-1>", self._make_release_handler(i))
            self.widget2_buttons.append(btn)

        # Reduced spacer row (row 3) - smaller height for compactness
        spacer = tk.Label(widget2, text="", font=(default_font.cget("family"), new_size))
        spacer.grid(row=3, column=0, columnspan=3, sticky="ew")
        # Add row 4: instructional text
        instruction1 = tk.Label(
            widget2,
            text="Click the buttons above to load preset times and allowed Game Periods",
            anchor="w", justify="left", font=(default_font.cget("family"), new_size)
        )
        instruction1.grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=(2,1))
        # Add row 5: instructional text
        instruction2 = tk.Label(
            widget2,
            text="Press and hold the button for >4 seconds to alter the stored preset values",
            anchor="w", justify="left", font=(default_font.cget("family"), new_size)
        )
        instruction2.grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=(1,4))

        # Widget 4 (Tournament List) - NEW: Between Presets and Game Sequence
        widget4 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget4.grid(row=2, column=1, sticky="nsew", padx=8, pady=8)
        
        widget4.grid_columnconfigure(0, weight=1)
        widget4.grid_columnconfigure(1, weight=1)
        widget4.grid_rowconfigure(0, weight=0)  # Header
        widget4.grid_rowconfigure(1, weight=0)  # CSV dropdown label
        widget4.grid_rowconfigure(2, weight=0)  # CSV dropdown
        widget4.grid_rowconfigure(3, weight=0)  # Open Folder button - NEW
        widget4.grid_rowconfigure(4, weight=0)  # Game number label  
        widget4.grid_rowconfigure(5, weight=0)  # Game number dropdown
        widget4.grid_rowconfigure(6, weight=0)  # Comment label
        widget4.grid_rowconfigure(7, weight=1)  # Spacer
        
        # Add header
        tournament_header = tk.Label(widget4, text="Tournament List", font=(default_font.cget("family"), new_size, "bold"))
        tournament_header.grid(row=0, column=0, columnspan=2, padx=8, pady=(12,8), sticky="ew")
        
        # CSV file selection
        tk.Label(widget4, text="CSV File:", font=(default_font.cget("family"), default_font.cget("size")), anchor="w").grid(row=1, column=0, sticky="w", padx=8, pady=2)
        
        # Get CSV files in current directory
        csv_files = self.get_csv_files()
        self.csv_var = tk.StringVar(value=csv_files[0] if csv_files else "No CSV files found")
        csv_dropdown = ttk.Combobox(widget4, textvariable=self.csv_var, values=csv_files, state="readonly", width=20)
        csv_dropdown.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=2)
        csv_dropdown.bind("<<ComboboxSelected>>", self.on_csv_file_changed)
        
        # Open Folder button
        open_folder_btn = tk.Button(widget4, text="Open Folder", 
                                    font=(default_font.cget("family"), default_font.cget("size")),
                                    command=self.open_csv_folder, width=12)
        open_folder_btn.grid(row=3, column=0, columnspan=2, padx=8, pady=(2,8))
        
        # Starting game number selection
        tk.Label(widget4, text="Starting Game #:", font=(default_font.cget("family"), default_font.cget("size")), anchor="w").grid(row=4, column=0, sticky="w", padx=8, pady=(8,2))
        
        self.game_numbers = []
        self.starting_game_var = tk.StringVar(value="")
        self.starting_game_dropdown = ttk.Combobox(widget4, textvariable=self.starting_game_var, values=self.game_numbers, state="readonly", width=10)
        self.starting_game_dropdown.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=2)
        
        # Add callback to update game number display when user selects different game
        self.starting_game_dropdown.bind('<<ComboboxSelected>>', self.on_game_selection_changed)
        
        # Initialize game numbers if CSV file is available
        self.on_csv_file_changed()
        
        # ADDED: Comment label about saving CSV files
        csv_comment = tk.Label(widget4, text="Save a CSV file of games into the same folder as this program is in.\nExpected CSV headers: date,#,White,Score,Black,Score,Referees,Penalties\n(where # is the Game Number)", 
                              font=(default_font.cget("family"), default_font.cget("size") - 1),
                              anchor="w", justify="left", wraplength=600)
        csv_comment.grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=(4,8))

        # Widget 3 (Game Sequence Explanation) - Bottom right - height reduced for snug text
        widget3 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget3.grid(row=3, column=1, sticky="nsew", padx=8, pady=8)
        
        widget3.grid_columnconfigure(0, weight=1)
        widget3.grid_rowconfigure(0, weight=0)  # Header
        widget3.grid_rowconfigure(1, weight=1)  # Content
        
        # Add header
        explanation_header = tk.Label(widget3, text="Game Sequence", font=(default_font.cget("family"), new_size, "bold"))
        explanation_header.grid(row=0, column=0, padx=4, pady=(8,2), sticky="ew")
        
        # Add explanatory text - reduced font size and padding for more snug appearance
        # Updated to reflect the new game sequence naming
        explanation_text = (
            "Game Sequence Flow:\n"
            "1. First Game Starts In: (runs once at app start)\n"
            "2. First Half → Half Time → Second Half\n"
            "3. If scores tied: Overtime Game Break → Overtime First Half → Overtime Half Time → Overtime Second Half (if enabled)\n"
            "4. If still tied: Sudden Death Game Break → Sudden Death (if enabled)\n"
            "5. Between Game Break (loop back to step 2)\n\n"
            "Important Notes:\n"
            "• 'First Game Starts In:' transitions directly to First Half\n"
            "• Crib time is subtracted from Between Game Break"
        )
        
        # Reduced font size for more compact appearance
        explanation_label = tk.Label(
            widget3, 
            text=explanation_text,
            font=(default_font.cget("family"), default_font.cget("size") - 1),
            justify="left",
            anchor="nw"
        )
        explanation_label.grid(row=1, column=0, padx=4, pady=(2,4), sticky="nsew")

        self.update_overtime_variables_state()

    def get_csv_files(self):
        """
        Scan the current directory for CSV files.
        Returns a list of CSV files found.
        """
        csv_files = []
        try:
            current_dir = os.getcwd()
            for filename in os.listdir(current_dir):
                if filename.lower().endswith('.csv'):
                    csv_files.append(filename)
        except Exception as e:
            print(f"Error scanning for CSV files: {e}")
        
        return sorted(csv_files) if csv_files else ["No CSV files found"]
    
    def parse_csv_game_numbers(self, csv_filename):
        """
        Parse CSV file and extract game numbers from the '#' column.
        Expected header: date,#,White,Score,Black,Score,Referees,Penalties
        """
        game_numbers = []
        if csv_filename == "No CSV files found" or not csv_filename:
            return game_numbers
            
        try:
            csv_path = os.path.join(os.getcwd(), csv_filename)
            if not os.path.exists(csv_path):
                return game_numbers
                
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < 2:  # Need header + at least one data row
                    return game_numbers
                    
                # Check header format
                header = lines[0].strip().lower()
                expected_cols = ['date', '#', 'white', 'score', 'black', 'score', 'referees']
                header_cols = [col.strip() for col in header.split(',')]
                
                # Find the '#' column index (flexible header matching)
                game_num_col_idx = -1
                for i, col in enumerate(header_cols):
                    if col in ['#', 'game', 'game#', 'game_number']:
                        game_num_col_idx = i
                        break
                
                if game_num_col_idx == -1:
                    print(f"Warning: Could not find game number column in CSV {csv_filename}")
                    return game_numbers
                
                # Parse data rows
                for line in lines[1:]:
                    line = line.strip()
                    if line:
                        cols = [col.strip() for col in line.split(',')]
                        if len(cols) > game_num_col_idx:
                            try:
                                game_num = int(cols[game_num_col_idx])
                                game_numbers.append(str(game_num))
                            except ValueError:
                                continue
                                
        except Exception as e:
            print(f"Error parsing CSV file {csv_filename}: {e}")
        
        return sorted(set(game_numbers), key=int) if game_numbers else []
    
    def parse_csv_team_names(self, csv_filename, game_number):
        """
        Parse CSV file and extract team names for a specific game number.
        Expected header: date,#,White,Score,Black,Score,Referees,Penalties
        Returns: (white_team_name, black_team_name) or (None, None) if not found
        """
        if csv_filename == "No CSV files found" or not csv_filename or not game_number:
            return (None, None)
            
        try:
            csv_path = os.path.join(os.getcwd(), csv_filename)
            if not os.path.exists(csv_path):
                return (None, None)
                
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < 2:  # Need header + at least one data row
                    return (None, None)
                    
                # Check header format
                header = lines[0].strip().lower()
                header_cols = [col.strip() for col in header.split(',')]
                
                # Find column indices
                game_num_col_idx = -1
                white_team_col_idx = -1
                black_team_col_idx = -1
                
                for i, col in enumerate(header_cols):
                    if col in ['#', 'game', 'game#', 'game_number']:
                        game_num_col_idx = i
                    elif col in ['white']:
                        white_team_col_idx = i
                    elif col in ['black']:
                        black_team_col_idx = i
                
                # Must have all required columns
                if game_num_col_idx == -1 or white_team_col_idx == -1 or black_team_col_idx == -1:
                    return (None, None)
                
                # Parse data rows to find the specific game
                for line in lines[1:]:
                    line = line.strip()
                    if line:
                        cols = [col.strip() for col in line.split(',')]
                        if len(cols) > max(game_num_col_idx, white_team_col_idx, black_team_col_idx):
                            try:
                                if str(int(cols[game_num_col_idx])) == str(game_number):
                                    white_team = cols[white_team_col_idx] if white_team_col_idx < len(cols) else None
                                    black_team = cols[black_team_col_idx] if black_team_col_idx < len(cols) else None
                                    return (white_team, black_team)
                            except (ValueError, IndexError):
                                continue
                                
        except Exception as e:
            print(f"Error parsing team names from CSV file {csv_filename}: {e}")
        
        return (None, None)
    
    def write_game_results_to_csv(self, game_number, white_score, black_score, penalties_list):
        """
        Write game results to CSV file.
        Updates existing row if game number exists, otherwise appends new row.
        Expected header: date,#,White,Score,Black,Score,Referees,Penalties,Comments
        
        Args:
            game_number: The game number to write results for
            white_score: White team's score
            black_score: Black team's score  
            penalties_list: List of penalty dicts with 'team', 'cap', 'duration' keys
        """
        csv_file = self.csv_var.get() if hasattr(self, 'csv_var') else None
        if not csv_file or csv_file == "No CSV files found":
            print("No CSV file selected, skipping game results write")
            return
            
        try:
            import csv
            csv_path = os.path.join(os.getcwd(), csv_file)
            
            # Format penalties as comma-separated W-#cap-duration, B-#cap-duration
            penalty_strings = []
            for penalty in penalties_list:
                team_prefix = "W" if penalty["team"] == "White" else "B"
                cap = penalty["cap"]
                duration = penalty["duration"]
                # Convert duration to short form: "2 minutes" -> "2", "Rest of Game" -> "Rest"
                if "Rest" in duration:
                    duration_str = "Rest"
                else:
                    # Extract just the number from duration like "2 minutes"
                    duration_str = duration.split()[0] if duration.split() else duration
                penalty_strings.append(f"{team_prefix}-#{cap}-{duration_str}")
            penalties_formatted = ",".join(penalty_strings)
            
            # Read existing CSV
            rows = []
            header_row = None
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if header_row is None:
                            header_row = row
                        else:
                            rows.append(row)
            
            # If no header exists, create one
            if header_row is None:
                header_row = ['date', '#', 'White', 'Score', 'Black', 'Score', 'Referees', 'Penalties', 'Comments']
            
            # Normalize header to lowercase for matching
            header_lower = [col.strip().lower() for col in header_row]
            
            # Find column indices (case-insensitive)
            game_num_idx = -1
            white_idx = -1
            white_score_idx = -1
            black_idx = -1
            black_score_idx = -1
            penalties_idx = -1
            comments_idx = -1
            
            for i, col in enumerate(header_lower):
                if col in ['#', 'game', 'game#', 'game_number']:
                    game_num_idx = i
                elif col == 'white':
                    white_idx = i
                elif col == 'black':
                    black_idx = i
                elif col in ['penalties', 'penalty']:
                    penalties_idx = i
                elif col in ['comments', 'comment']:
                    comments_idx = i
            
            # Find score columns (they come after team name columns)
            if white_idx != -1 and white_idx + 1 < len(header_lower) and header_lower[white_idx + 1] == 'score':
                white_score_idx = white_idx + 1
            if black_idx != -1 and black_idx + 1 < len(header_lower) and header_lower[black_idx + 1] == 'score':
                black_score_idx = black_idx + 1
            
            # If penalties column doesn't exist, add it
            if penalties_idx == -1:
                header_row.append('Penalties')
                penalties_idx = len(header_row) - 1
                if comments_idx == -1:
                    header_row.append('Comments')
                    comments_idx = len(header_row) - 1
            
            # Find if game number already exists
            game_row_index = -1
            for i, row in enumerate(rows):
                if len(row) > game_num_idx:
                    try:
                        if str(int(row[game_num_idx])) == str(game_number):
                            game_row_index = i
                            break
                    except (ValueError, IndexError):
                        continue
            
            if game_row_index != -1:
                # Update existing row
                row = rows[game_row_index]
                
                # Ensure we have enough columns
                while len(row) < len(header_row):
                    row.append("")
                
                # Update scores
                if white_score_idx != -1:
                    row[white_score_idx] = str(white_score)
                if black_score_idx != -1:
                    row[black_score_idx] = str(black_score)
                    
                # Update penalties
                if penalties_idx != -1:
                    row[penalties_idx] = penalties_formatted
                
                rows[game_row_index] = row
            else:
                # Append new row
                # Get team names from CSV if available
                white_team, black_team = self.parse_csv_team_names(csv_file, game_number)
                if not white_team:
                    white_team = "Team A"
                if not black_team:
                    black_team = "Team B"
                
                # Create new row with current date
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                new_row = [''] * len(header_row)
                
                # Fill in the values we know
                if game_num_idx != -1:
                    new_row[game_num_idx] = str(game_number)
                if white_idx != -1:
                    new_row[white_idx] = white_team
                if white_score_idx != -1:
                    new_row[white_score_idx] = str(white_score)
                if black_idx != -1:
                    new_row[black_idx] = black_team
                if black_score_idx != -1:
                    new_row[black_score_idx] = str(black_score)
                if penalties_idx != -1:
                    new_row[penalties_idx] = penalties_formatted
                    
                # Set date in first column
                new_row[0] = current_date
                
                rows.append(new_row)
            
            # Write back to CSV
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header_row)
                writer.writerows(rows)
            
            print(f"Game results written to {csv_file}: Game #{game_number}, W:{white_score} B:{black_score}, Penalties:{penalties_formatted}")
            
        except Exception as e:
            print(f"Error writing game results to CSV: {e}")
            import traceback
            traceback.print_exc()
    
    def on_csv_file_changed(self, event=None):
        """Handle CSV file selection change - update game numbers dropdown."""
        csv_file = self.csv_var.get()
        self.game_numbers = self.parse_csv_game_numbers(csv_file)
        
        if hasattr(self, 'starting_game_dropdown'):
            self.starting_game_dropdown['values'] = self.game_numbers
            if self.game_numbers:
                self.starting_game_var.set(self.game_numbers[0])
                self.current_game_index = 0
            else:
                self.starting_game_var.set("")
                self.current_game_index = 0
        
        # Update game number display after CSV change
        self.update_game_number_display()

    def get_current_game_number(self):
        """Get the current game number from Tournament List selection."""
        try:
            selected_game = self.starting_game_var.get()
            if selected_game and selected_game in self.game_numbers:
                return selected_game
            elif self.game_numbers and len(self.game_numbers) > self.current_game_index:
                return self.game_numbers[self.current_game_index]
            else:
                return "121"  # fallback to default
        except Exception:
            return "121"  # fallback to default

    def update_game_number_display(self):
        """Update the game number display based on current Tournament List selection."""
        current_game = self.get_current_game_number()
        self.game_number_var.set(f"Game #{current_game}")
        # Also update team names when game number changes
        self.update_team_names_display()

    def update_team_names_display(self):
        """Update the team name widgets with data from CSV file."""
        try:
            current_game = self.get_current_game_number()
            csv_file = self.csv_var.get() if hasattr(self, 'csv_var') else None
            
            # Get team names from CSV
            white_team, black_team = self.parse_csv_team_names(csv_file, current_game)
            
            # Update the team name widgets if they exist
            if hasattr(self, 'white_team_name_widget'):
                if white_team:
                    self.white_team_name_widget.config(text=white_team)
                else:
                    self.white_team_name_widget.config(text="")
                    
            if hasattr(self, 'black_team_name_widget'):
                if black_team:
                    self.black_team_name_widget.config(text=black_team)
                else:
                    self.black_team_name_widget.config(text="")
                    
        except Exception as e:
            print(f"Error updating team names display: {e}")
            # Set empty text on error
            if hasattr(self, 'white_team_name_widget'):
                self.white_team_name_widget.config(text="")
            if hasattr(self, 'black_team_name_widget'):
                self.black_team_name_widget.config(text="")

    def advance_to_next_game(self):
        """Advance to the next game in the Tournament List."""
        if not self.game_numbers:
            return
        
        # Find current game index
        current_game = self.starting_game_var.get()
        if current_game in self.game_numbers:
            self.current_game_index = self.game_numbers.index(current_game)
        
        # Advance to next game (wrap around to start if at end)
        self.current_game_index = (self.current_game_index + 1) % len(self.game_numbers)
        next_game = self.game_numbers[self.current_game_index]
        
        # Update the dropdown selection
        self.starting_game_var.set(next_game)
        
        # Update the display
        self.update_game_number_display()

    def on_game_selection_changed(self, event=None):
        """Handle manual game selection change from dropdown."""
        self.update_game_number_display()

    def open_csv_folder(self):
        """Open the folder containing CSV files in the system file manager."""
        csv_file = self.csv_var.get() if hasattr(self, 'csv_var') else None
        
        if not csv_file or csv_file == "No CSV files found":
            messagebox.showinfo("Info", "No CSV file selected")
            return
        
        # Get the directory containing the CSV file
        csv_folder = os.getcwd()
        open_folder_in_file_manager(csv_folder)

    def create_sounds_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Sounds")
        
        # Configure main grid layout for the sounds tab
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        
        # Create the main sounds widget frame - using LabelFrame like demo
        sounds_widget = tk.LabelFrame(tab, text="Sounds", borderwidth=2, relief="solid")
        sounds_widget.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        
        # Configure grid layout for sounds widget - 10 rows and 6 columns (like demo)
        for r in range(10):
            sounds_widget.grid_rowconfigure(r, weight=1)
        for c in range(6):
            sounds_widget.grid_columnconfigure(c, weight=1)
        sounds_widget.grid_columnconfigure(3, weight=0)  # Column 3 has fixed width
        
        # Get dynamic list of sound files
        sound_files = get_sound_files()
        pips_options = ["Default"] + sound_files if sound_files != ["No sound files found"] else sound_files
        siren_options = ["Default"] + sound_files if sound_files != ["No sound files found"] else sound_files
        
        # Row 0, column 0: Save Settings button
        save_btn = tk.Button(sounds_widget, text="Save Settings", font=("Arial", 11), command=self.save_sound_settings_method)
        save_btn.grid(row=0, column=0)

        # Row 1, column 0: Enable Sound checkbox
        enable_sound_cb = tk.Checkbutton(sounds_widget, text="Enable Sound?", font=("Arial", 11), variable=self.enable_sound)
        enable_sound_cb.grid(row=1, column=0, sticky="w")

        # Row 0, column 4, columnspan=2: "Volume"
        tk.Label(sounds_widget, text="Volume", font=("Arial", 12)).grid(row=0, column=4, columnspan=2, sticky="nsew")

        # Row 1, column 4: "Air"
        tk.Label(sounds_widget, text="Air", font=("Arial", 12)).grid(row=1, column=4, sticky="nsew")

        # Row 1, column 5: "Water"
        tk.Label(sounds_widget, text="Water", font=("Arial", 12)).grid(row=1, column=5, sticky="nsew")

        # Row 2, column 0: "Pips"
        tk.Label(sounds_widget, text="Pips", font=("Arial", 12)).grid(row=2, column=0, sticky="nsew")

        # Row 2, column 1, columnspan=2: Pips dropdown (sticky="ew", padx=(0, 10))
        pips_dropdown = ttk.Combobox(sounds_widget, textvariable=self.pips_var, values=pips_options, state="readonly")
        pips_dropdown.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, 10))
        
        # Add validation callback for pips selection - only on user interaction
        def validate_pips_selection(*args):
            # Only validate if user is actively interacting with the combobox
            if hasattr(self, '_user_interacting_with_pips') and self._user_interacting_with_pips:
                selected = self.pips_var.get()
                if selected != "Default" and selected != "No sound files found":
                    if not check_audio_device_available(self.enable_sound):
                        self.audio_device_warning_shown = handle_no_audio_device_warning(
                            self.pips_var, "pips", self.enable_sound, self.audio_device_warning_shown)
                # Reset interaction flag
                self._user_interacting_with_pips = False
        
        self.pips_var.trace_add("write", validate_pips_selection)
        
        # Add event binding to detect user interaction
        def on_pips_user_interaction(event=None):
            self._user_interacting_with_pips = True
        
        pips_dropdown.bind("<<ComboboxSelected>>", on_pips_user_interaction)
        # Also bind to focusin and button clicks to detect any user interaction
        pips_dropdown.bind("<Button-1>", on_pips_user_interaction)
        pips_dropdown.bind("<FocusIn>", on_pips_user_interaction)

        # Row 2, column 3: Play button for pips demo sound
        def test_pips_sound():
            try:
                play_sound_with_volume(self.pips_var.get(), "pips", 
                    self.enable_sound, self.pips_volume, self.siren_volume, 
                    self.air_volume, self.water_volume)
            except Exception as e:
                print(f"Error testing pips sound: {e}")
        
        pips_play_btn = tk.Button(sounds_widget, text="Play", font=("Arial", 11), width=5,
                                  command=test_pips_sound)
        pips_play_btn.grid(row=2, column=3)

        # Row 3, column 0: "Pips Vol"
        tk.Label(sounds_widget, text="Pips Vol", font=("Arial", 11)).grid(row=3, column=0, sticky="ew")

        # Row 3, column 1, columnspan=2: Pips slider (sticky="ew"), no value text
        pips_vol_slider = tk.Scale(
            sounds_widget, from_=0, to=100, orient="horizontal", variable=self.pips_volume,
            font=("Arial", 10), showvalue=False
        )
        pips_vol_slider.grid(row=3, column=1, columnspan=2, sticky="ew")
        
        # Add interaction detection for pips volume slider
        def on_pips_slider_interaction(event=None):
            # Check audio device when user interacts with volume slider
            if not check_audio_device_available(self.enable_sound):
                self.audio_device_warning_shown = handle_no_audio_device_warning(
                    self.pips_var, "pips volume", self.enable_sound, self.audio_device_warning_shown)
        
        pips_vol_slider.bind("<Button-1>", on_pips_slider_interaction)
        pips_vol_slider.bind("<B1-Motion>", on_pips_slider_interaction)

        # Row 5, column 0: "Siren"
        tk.Label(sounds_widget, text="Siren", font=("Arial", 12)).grid(row=5, column=0, sticky="nsew")

        # Row 5, column 1, columnspan=2: Siren dropdown (sticky="ew", padx=(0, 10))
        siren_dropdown = ttk.Combobox(sounds_widget, textvariable=self.siren_var, values=siren_options, state="readonly")
        siren_dropdown.grid(row=5, column=1, columnspan=2, sticky="ew", padx=(0, 10))
        
        # Add validation callback for siren selection - only on user interaction
        def validate_siren_selection(*args):
            # Only validate if user is actively interacting with the combobox
            if hasattr(self, '_user_interacting_with_siren') and self._user_interacting_with_siren:
                selected = self.siren_var.get()
                if selected != "Default" and selected != "No sound files found":
                    if not check_audio_device_available(self.enable_sound):
                        self.audio_device_warning_shown = handle_no_audio_device_warning(
                            self.siren_var, "siren", self.enable_sound, self.audio_device_warning_shown)
                # Reset interaction flag
                self._user_interacting_with_siren = False
        
        self.siren_var.trace_add("write", validate_siren_selection)
        
        # Add event binding to detect user interaction
        def on_siren_user_interaction(event=None):
            self._user_interacting_with_siren = True
        
        siren_dropdown.bind("<<ComboboxSelected>>", on_siren_user_interaction)
        # Also bind to focusin and button clicks to detect any user interaction
        siren_dropdown.bind("<Button-1>", on_siren_user_interaction)
        siren_dropdown.bind("<FocusIn>", on_siren_user_interaction)

        # Row 5, column 3: Play button for siren demo sound
        def test_siren_sound():
            try:
                play_sound_with_volume(self.siren_var.get(), "siren",
                    self.enable_sound, self.pips_volume, self.siren_volume,
                    self.air_volume, self.water_volume)
            except Exception as e:
                print(f"Error testing siren sound: {e}")
        
        siren_play_btn = tk.Button(sounds_widget, text="Play", font=("Arial", 11), width=5,
                                   command=test_siren_sound)
        siren_play_btn.grid(row=5, column=3)

        # Row 6, column 0: "Siren Vol"
        tk.Label(sounds_widget, text="Siren Vol", font=("Arial", 11)).grid(row=6, column=0, sticky="ew")

        # Row 6, column 1, columnspan=2: Siren slider (sticky="ew"), no value text
        siren_vol_slider = tk.Scale(
            sounds_widget, from_=0, to=100, orient="horizontal", variable=self.siren_volume,
            font=("Arial", 10), showvalue=False
        )
        siren_vol_slider.grid(row=6, column=1, columnspan=2, sticky="ew")
        
        # Add interaction detection for siren volume slider
        def on_siren_slider_interaction(event=None):
            # Check audio device when user interacts with volume slider
            if not check_audio_device_available(self.enable_sound):
                self.audio_device_warning_shown = handle_no_audio_device_warning(
                    self.siren_var, "siren volume", self.enable_sound, self.audio_device_warning_shown)
        
        siren_vol_slider.bind("<Button-1>", on_siren_slider_interaction)
        siren_vol_slider.bind("<B1-Motion>", on_siren_slider_interaction)

        # Air slider: row=2, column=4, rowspan=5, sticky="ns" (no text)
        air_vol_slider = tk.Scale(
            sounds_widget, from_=100, to=0, orient="vertical", variable=self.air_volume,
            font=("Arial", 10), showvalue=False
        )
        air_vol_slider.grid(row=2, column=4, rowspan=5, sticky="ns")
        
        # Add interaction detection for air volume slider
        def on_air_slider_interaction(event=None):
            # Check audio device when user interacts with volume slider
            if not check_audio_device_available(self.enable_sound):
                self.audio_device_warning_shown = handle_no_audio_device_warning(
                    tk.StringVar(value="Default"), "air volume", self.enable_sound, self.audio_device_warning_shown)
        
        air_vol_slider.bind("<Button-1>", on_air_slider_interaction)
        air_vol_slider.bind("<B1-Motion>", on_air_slider_interaction)

        # Water slider: row=2, column=5, rowspan=5, sticky="ns" (no text)
        water_vol_slider = tk.Scale(
            sounds_widget, from_=100, to=0, orient="vertical", variable=self.water_volume,
            font=("Arial", 10), showvalue=False
        )
        water_vol_slider.grid(row=2, column=5, rowspan=5, sticky="ns")
        
        # Add interaction detection for water volume slider
        def on_water_slider_interaction(event=None):
            # Check audio device when user interacts with volume slider
            if not check_audio_device_available(self.enable_sound):
                self.audio_device_warning_shown = handle_no_audio_device_warning(
                    tk.StringVar(value="Default"), "water volume", self.enable_sound, self.audio_device_warning_shown)
        
        water_vol_slider.bind("<Button-1>", on_water_slider_interaction)
        water_vol_slider.bind("<B1-Motion>", on_water_slider_interaction)

    def create_zigbee_siren_tab(self):
        """Create the Zigbee Siren configuration tab."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Zigbee Siren")
        
        # Configure main grid layout
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        main_frame = tk.LabelFrame(tab, text="Zigbee2MQTT Wireless Siren Control", 
                                  borderwidth=2, relief="solid")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        
        # Configure grid layout
        for r in range(12):
            main_frame.grid_rowconfigure(r, weight=1)
        for c in range(4):
            main_frame.grid_columnconfigure(c, weight=1)
        
        # Connection Status Section
        status_frame = tk.LabelFrame(main_frame, text="Connection Status", 
                                   borderwidth=1, relief="solid")
        status_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        
        # Status display
        tk.Label(status_frame, text="Status:", font=("Arial", 11, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=2)
        self.zigbee_status_label = tk.Label(status_frame, textvariable=self.zigbee_status_var, 
                                          font=("Arial", 11), fg="red")
        self.zigbee_status_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # MQTT availability check
        mqtt_status = "Available" if is_mqtt_available() else "Not Available (install paho-mqtt)"
        tk.Label(status_frame, text="MQTT Library:", font=("Arial", 11, "bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=2)
        mqtt_color = "green" if is_mqtt_available() else "red"
        tk.Label(status_frame, text=mqtt_status, font=("Arial", 11), fg=mqtt_color).grid(
            row=1, column=1, sticky="w", padx=5, pady=2)
        
        # USB Dongle status check
        tk.Label(status_frame, text="USB Dongle:", font=("Arial", 11, "bold")).grid(
            row=2, column=0, sticky="w", padx=5, pady=2)
        self.usb_dongle_status_label = tk.Label(status_frame, text="Checking...", 
                                              font=("Arial", 11), fg="orange")
        self.usb_dongle_status_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Retest USB Dongle button
        self.retest_usb_btn = tk.Button(status_frame, text="Retest USB Dongle", 
                                      font=("Arial", 9), command=self.update_usb_dongle_status)
        self.retest_usb_btn.grid(row=2, column=2, sticky="w", padx=5, pady=2)
        
        # Connection Control Buttons
        control_frame = tk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        self.toggle_connection_btn = tk.Button(control_frame, text="Connect", font=("Arial", 11),
                                             command=self.toggle_zigbee_connection)
        self.toggle_connection_btn.pack(side="left", padx=5)
        
        self.test_btn = tk.Button(control_frame, text="Test Connection", font=("Arial", 11),
                                command=self.test_zigbee_connection)
        self.test_btn.pack(side="left", padx=5)
        
        # Configuration Section
        config_frame = tk.LabelFrame(main_frame, text="MQTT Configuration", 
                                   borderwidth=1, relief="solid")
        config_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        
        # Configuration widgets
        self.config_widgets = {}
        config = self.zigbee_controller.config
        
        # MQTT Broker
        row = 0
        tk.Label(config_frame, text="MQTT Broker:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=5, pady=2)
        self.config_widgets["mqtt_broker"] = tk.Entry(config_frame, font=("Arial", 10))
        self.config_widgets["mqtt_broker"].insert(0, config["mqtt_broker"])
        self.config_widgets["mqtt_broker"].grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        
        # MQTT Port
        tk.Label(config_frame, text="Port:", font=("Arial", 10)).grid(
            row=row, column=2, sticky="w", padx=5, pady=2)
        self.config_widgets["mqtt_port"] = tk.Entry(config_frame, font=("Arial", 10), width=8)
        self.config_widgets["mqtt_port"].insert(0, str(config["mqtt_port"]))
        self.config_widgets["mqtt_port"].grid(row=row, column=3, sticky="w", padx=5, pady=2)
        
        # Username/Password
        row += 1
        tk.Label(config_frame, text="Username:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=5, pady=2)
        self.config_widgets["mqtt_username"] = tk.Entry(config_frame, font=("Arial", 10))
        self.config_widgets["mqtt_username"].insert(0, config["mqtt_username"])
        self.config_widgets["mqtt_username"].grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        
        tk.Label(config_frame, text="Password:", font=("Arial", 10)).grid(
            row=row, column=2, sticky="w", padx=5, pady=2)
        self.config_widgets["mqtt_password"] = tk.Entry(config_frame, font=("Arial", 10), show="*")
        self.config_widgets["mqtt_password"].insert(0, config["mqtt_password"])
        self.config_widgets["mqtt_password"].grid(row=row, column=3, sticky="ew", padx=5, pady=2)
        
        # Topic and Device
        row += 1
        tk.Label(config_frame, text="MQTT Topic:", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=5, pady=2)
        self.config_widgets["mqtt_topic"] = tk.Entry(config_frame, font=("Arial", 10))
        self.config_widgets["mqtt_topic"].insert(0, config["mqtt_topic"])
        self.config_widgets["mqtt_topic"].grid(row=row, column=1, columnspan=3, sticky="ew", padx=5, pady=2)
        
        row += 1
        tk.Label(config_frame, text="Button Device Names (comma-separated):", font=("Arial", 10)).grid(
            row=row, column=0, sticky="w", padx=5, pady=2)
        
        # Handle both new list format and old single device format
        device_value = ""
        if "siren_button_devices" in config and isinstance(config["siren_button_devices"], list):
            device_value = ", ".join(config["siren_button_devices"])
        elif "siren_button_device" in config:
            device_value = config["siren_button_device"]
        
        self.config_widgets["siren_button_devices"] = tk.Entry(config_frame, font=("Arial", 10))
        self.config_widgets["siren_button_devices"].insert(0, device_value)
        self.config_widgets["siren_button_devices"].grid(row=row, column=1, columnspan=3, sticky="ew", padx=5, pady=2)
        
        # Configure column weights
        config_frame.grid_columnconfigure(1, weight=1)
        
        # Save Configuration Button
        save_config_btn = tk.Button(main_frame, text="Save Configuration", font=("Arial", 11),
                                  command=self.save_zigbee_config)
        save_config_btn.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Manual Siren Test Button
        test_siren_btn = tk.Button(main_frame, text="Test Siren via MQTT", font=("Arial", 11),
                                 command=self.test_wireless_siren)
        test_siren_btn.grid(row=3, column=2, columnspan=2, pady=5)
        
        # Information Section
        info_frame = tk.LabelFrame(main_frame, text="Setup Information", 
                                 borderwidth=1, relief="solid")
        info_frame.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        
        info_text = """Zigbee2MQTT Wireless Siren Setup:

1. Install Zigbee2MQTT on your system
2. Install MQTT library: pip install paho-mqtt  
3. Configure your Zigbee button devices in Zigbee2MQTT
4. Set the device names above (comma-separated for multiple buttons)
5. Configure MQTT broker connection details
6. Click Connect (if not already connected) to start wireless siren connection

The 'Test Siren via MQTT' will use the same sound file and volume settings as configured in the Sounds tab."""
        
        info_label = tk.Label(info_frame, text=info_text, font=("Arial", 9), 
                            justify="left", anchor="nw", wraplength=0)
        info_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Log Section
        log_frame = tk.LabelFrame(main_frame, text="Activity Log", 
                                borderwidth=1, relief="solid")
        log_frame.grid(row=5, column=0, columnspan=4, sticky="ew", padx=5, pady=5)
        
        # Create scrollable log area
        log_scroll_frame = tk.Frame(log_frame)
        log_scroll_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        log_scroll_frame.grid_columnconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_scroll_frame, height=6, font=("Courier", 9), 
                              wrap=tk.WORD, state=tk.DISABLED)
        log_scrollbar = tk.Scrollbar(log_scroll_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="ew")
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Clear log button
        clear_log_btn = tk.Button(log_frame, text="Clear Log", font=("Arial", 9),
                                command=self.clear_zigbee_log)
        clear_log_btn.grid(row=1, column=0, pady=2)
        
        # Add initial log entry
        self.add_to_zigbee_log("Zigbee Siren tab initialized")
        if not is_mqtt_available():
            self.add_to_zigbee_log("WARNING: paho-mqtt library not installed. Install with: pip install paho-mqtt")

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
            # Do not apply preset to "time_to_start_first_game" or "start_first_game_in"
            if var_name in ["time_to_start_first_game", "start_first_game_in"]:
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
        
        # Validate crib_time after applying preset
        crib_time_seconds = None
        between_game_break_minutes = None
        for widget in self.widgets:
            if widget["name"] == "crib_time" and widget["entry"] is not None:
                try:
                    crib_time_seconds = float(widget["entry"].get().strip().replace(',', '.'))
                except (ValueError, AttributeError):
                    pass
            elif widget["name"] == "between_game_break":
                try:
                    between_game_break_minutes = float(widget["entry"].get().strip().replace(',', '.'))
                except (ValueError, AttributeError):
                    pass
        
        # Check the validation condition
        if crib_time_seconds is not None and between_game_break_minutes is not None:
            if (between_game_break_minutes * 60) - crib_time_seconds <= 31:
                # Restore the last valid crib_time value
                for widget in self.widgets:
                    if widget["name"] == "crib_time" and widget["entry"] is not None:
                        widget["entry"].delete(0, tk.END)
                        widget["entry"].insert(0, self.last_valid_values.get("crib_time", "60"))
                messagebox.showerror("Input Error", "Crib time too large. Between Game Break minus Crib time must be > 31 seconds.")
                return
        
        self.load_settings()
        # Fix: Rebuild game sequence after applying preset settings so Reset button uses new values
        self.build_game_sequence()


    def _open_button_dialog(self, idx):
        dlg = tk.Toplevel(self.master)
        dlg.title(f"Button {idx+1} Settings")
        dlg.geometry("400x700")
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
            
            # Skip "Time to Start First Game" and "First Game Starts In:" from preset dialog
            if var_name in ["time_to_start_first_game", "start_first_game_in"]:
                continue
            
            # Special handling for sudden_death_game_break: show both checkbox and entry
            if var_name == "sudden_death_game_break":
                # Show checkbox with relabeled text
                tk.Label(dlg, text="Sudden Death Allowed?").grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
                # Use default value from self.variables instead of current UI value
                default_checkbox_val = self.variables[var_name].get("used", True)
                val = self.button_data[idx]["checkboxes"].get(var_name, default_checkbox_val)
                check_var = tk.BooleanVar(value=val)
                cb = ttk.Checkbutton(dlg, variable=check_var)
                cb.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
                checks[var_name] = check_var
                row_num += 1
                # Add value entry immediately below checkbox
                tk.Label(dlg, text="Sudden Death Game Break:").grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
                sudden_death_val = self.button_data[idx]["values"].get("sudden_death_game_break", "1")
                sudden_death_entry_var = tk.StringVar(value=sudden_death_val)
                sudden_death_entry = ttk.Entry(dlg, textvariable=sudden_death_entry_var, width=10)
                sudden_death_entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
                entries["sudden_death_game_break"] = sudden_death_entry_var
                row_num += 1
                continue
            
            tk.Label(dlg, text=label.cget("text")).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
            if widget["checkbox"] is not None:
                # For button 1, preset checkboxes as True for required options
                if idx == 0 and var_name in ["team_timeouts_allowed", "overtime_allowed"]:
                    val = True
                else:
                    # Use default value from self.variables instead of current UI value
                    default_checkbox_val = self.variables[var_name].get("used", True)
                    val = self.button_data[idx]["checkboxes"].get(var_name, default_checkbox_val)
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
                    }.get(var_name, str(self.variables[var_name]["default"])))
                else:
                    # Use default value from self.variables instead of current UI value
                    default_entry_val = str(self.variables[var_name]["default"])
                    val = self.button_data[idx]["values"].get(var_name, default_entry_val)
                entry_var = tk.StringVar(value=val)
                entry = ttk.Entry(dlg, textvariable=entry_var, width=10)
                entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
                entries[var_name] = entry_var
            row_num += 1

        # --- PATCH: Add Crib Time entry below Crib Time: checkbox and above Save button ---
        tk.Label(dlg, text="Crib Time (seconds):").grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
        crib_time_val = self.button_data[idx]["values"].get("crib_time", "60")
        crib_time_entry_var = tk.StringVar(value=crib_time_val)
        crib_time_entry = ttk.Entry(dlg, textvariable=crib_time_entry_var, width=10)
        crib_time_entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
        entries["crib_time"] = crib_time_entry_var
        row_num += 1

        def save_and_close():
            for v in entries:
                # PATCH: Remove "time_to_start_first_game" and "start_first_game_in" from dialog value save
                if v in ["time_to_start_first_game", "start_first_game_in"]:
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
            # Save presets to JSON file
            save_preset_settings(self.button_data)
            dlg.destroy()
        save_btn = ttk.Button(dlg, text="Save", command=save_and_close)
        save_btn.grid(row=row_num, column=0, columnspan=2, pady=16)
        dlg.transient(self.master)
        dlg.wait_visibility()
        dlg.grab_set()

    def _on_settings_variable_change(self, *args):
        self.load_settings()
        self.build_game_sequence()
        # Save game settings when variables change
        self.save_game_settings()
    
    def _on_single_variable_change(self, var_name):
        """Handle change to a single variable without updating all widgets."""
        # Only update the specific variable in self.variables
        for widget in self.widgets:
            if widget["name"] == var_name:
                entry = widget["entry"]
                var_info = self.variables[var_name]
                
                # Update the specific variable
                if entry is not None and widget["checkbox"] is not None:
                    # Variable with both checkbox and entry
                    value = entry.get().replace(',', '.')
                    try:
                        float(value)
                        self.variables[var_name]["value"] = value
                    except ValueError:
                        self.variables[var_name]["value"] = str(var_info["default"])
                    self.variables[var_name]["used"] = widget["checkbox"].get()
                elif entry is not None:
                    # Entry-only variable
                    value = entry.get().replace(',', '.')
                    self.variables[var_name]["value"] = value
                    self.variables[var_name]["used"] = True
                elif widget["checkbox"] is not None:
                    # Checkbox-only variable
                    self.variables[var_name]["used"] = widget["checkbox"].get()
                break
        
        # Synchronize the two time fields bidirectionally
        if var_name == "time_to_start_first_game":
            # Update start_first_game_in when time_to_start_first_game changes
            self._update_start_first_game_in()
        elif var_name == "start_first_game_in":
            # Update time_to_start_first_game when start_first_game_in changes
            self._update_time_to_start_first_game()
        
        # Only rebuild game sequence if the variable affects the sequence structure
        # Variables that don't affect game sequence: record_scorers_cap_number, team_timeouts_allowed, crib_time
        if var_name not in ["record_scorers_cap_number", "team_timeouts_allowed", "crib_time"]:
            self.build_game_sequence()
        
        # Always save settings when a variable changes
        self.save_game_settings()
    
    def _update_start_first_game_in(self):
        """Update only the start_first_game_in calculated field."""
        time_entry_val = None
        start_first_game_in_widget = None
        
        for widget in self.widgets:
            if widget["name"] == "time_to_start_first_game":
                time_entry_val = widget["entry"].get().strip()
            elif widget["name"] == "start_first_game_in":
                start_first_game_in_widget = widget["entry"]
        
        # Calculate start_first_game_in value if time is valid
        minutes_to_start = None
        now = datetime.datetime.now()
        if time_entry_val:
            try:
                time_match = re.match(r"^([01][0-9]|2[0-3]):[0-5][0-9]$", time_entry_val)
                if time_match:
                    hh, mm = map(int, time_entry_val.split(":"))
                    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                    if target < now:
                        target = target + datetime.timedelta(days=1)
                    delta = target - now
                    minutes_to_start = int(delta.total_seconds() // 60)
            except Exception:
                minutes_to_start = None
        
        if minutes_to_start is not None and start_first_game_in_widget is not None:
            value = max(0, minutes_to_start)
            start_first_game_in_widget.delete(0, tk.END)
            start_first_game_in_widget.insert(0, str(value))
            self.variables["start_first_game_in"]["value"] = str(value)
    
    def _update_time_to_start_first_game(self):
        """Update time_to_start_first_game based on start_first_game_in."""
        start_first_game_in_val = None
        time_widget = None
        
        for widget in self.widgets:
            if widget["name"] == "start_first_game_in":
                start_first_game_in_val = widget["entry"].get().strip()
            elif widget["name"] == "time_to_start_first_game":
                time_widget = widget["entry"]
        
        # Calculate time_to_start_first_game if start_first_game_in is valid
        if start_first_game_in_val and time_widget is not None:
            try:
                # Parse start_first_game_in as minutes
                start_minutes = float(start_first_game_in_val.replace(",", "."))
                
                # Calculate target time
                now = datetime.datetime.now()
                target = now + datetime.timedelta(minutes=int(start_minutes))
                
                # Format as HH:MM
                time_str = f"{target.hour:02d}:{target.minute:02d}"
                
                # Update the widget
                time_widget.delete(0, tk.END)
                time_widget.insert(0, time_str)
                self.variables["time_to_start_first_game"]["value"] = time_str
            except Exception:
                pass  # If parsing fails, don't update

    def load_settings(self):
        # Calculate "Start First Game In" from "Time to Start First Game"
        time_entry_val = None
        start_first_game_in_widget = None
        for widget in self.widgets:
            if widget["name"] == "time_to_start_first_game":
                time_entry_val = widget["entry"].get().strip()
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
        if minutes_to_start is not None and start_first_game_in_widget is not None:
            value = max(0, minutes_to_start)
            start_first_game_in_widget.delete(0, tk.END)
            start_first_game_in_widget.insert(0, str(value))
            self.variables["start_first_game_in"]["value"] = str(value)
        # Set all other values normally
        for widget in self.widgets:
            entry = widget["entry"]
            var_name = widget["name"]
            var_info = self.variables[var_name]
            
            # PATCH: For variables with both checkbox and entry widgets
            if entry is not None and widget["checkbox"] is not None:
                # Entry always sets 'value' as float-convertible string
                value = entry.get().replace(',', '.')
                try:
                    # Validate it's numeric
                    float(value)
                    self.variables[var_name]["value"] = value
                except ValueError:
                    # Fallback to default if invalid
                    self.variables[var_name]["value"] = str(var_info["default"])
                # Checkbox always sets 'used' as boolean
                self.variables[var_name]["used"] = widget["checkbox"].get()
            elif entry is not None:
                # Entry-only variables (no checkbox)
                value = entry.get().replace(',', '.')
                self.variables[var_name]["value"] = value
                self.variables[var_name]["used"] = True
            elif widget["checkbox"] is not None:
                # Checkbox-only variables (no entry)
                self.variables[var_name]["used"] = widget["checkbox"].get()
            else:
                # Neither entry nor checkbox (shouldn't happen)
                self.variables[var_name]["used"] = True

    def save_sound_settings_method(self):
        """Save current sound settings to JSON file."""
        settings = {
            "pips_sound": self.pips_var.get(),
            "siren_sound": self.siren_var.get(),
            "pips_volume": self.pips_volume.get(),
            "siren_volume": self.siren_volume.get(),
            "air_volume": self.air_volume.get(),
            "water_volume": self.water_volume.get(),
            "enable_sound": self.enable_sound.get()
        }
        save_sound_settings(settings)
        # Show a message to confirm settings were saved
        messagebox.showinfo("Settings Saved", "Sound settings have been saved.")

    def load_game_settings(self):
        """Load game settings from unified JSON file."""
        unified_settings = load_unified_settings()
        game_settings = unified_settings.get("gameSettings", {})
        
        # Load settings into variables
        for var_name, var_info in self.variables.items():
            if var_name in game_settings:
                value = game_settings[var_name]
                
                # Check if this variable has both checkbox and entry
                has_checkbox = var_info.get("checkbox", False)
                has_entry = False
                for widget in self.widgets:
                    if widget["name"] == var_name and widget["entry"] is not None:
                        has_entry = True
                        break
                
                if has_checkbox and has_entry:
                    # For variables with both checkbox and entry (like sudden_death_game_break, crib_time)
                    if isinstance(value, bool):
                        # Legacy format - convert to numeric value and enable
                        self.variables[var_name]["value"] = str(var_info["default"])
                        self.variables[var_name]["used"] = value
                    else:
                        # New format - value is numeric, assume enabled
                        self.variables[var_name]["value"] = str(value)
                        self.variables[var_name]["used"] = True
                elif has_checkbox:
                    # Pure checkbox variables (like team_timeouts_allowed, overtime_allowed)
                    self.variables[var_name]["used"] = value
                else:
                    # Entry-only variables
                    self.variables[var_name]["value"] = str(value)
                
                # Update widgets if they exist
                for widget in self.widgets:
                    if widget["name"] == var_name:
                        if widget["entry"] is not None:
                            widget["entry"].delete(0, tk.END)
                            if has_checkbox and has_entry:
                                # Use the numeric value for mixed variables
                                widget["entry"].insert(0, self.variables[var_name]["value"])
                            else:
                                widget["entry"].insert(0, str(value))
                        if widget["checkbox"] is not None:
                            if has_checkbox and has_entry:
                                # Use the "used" flag for mixed variables
                                widget["checkbox"].set(self.variables[var_name]["used"])
                            else:
                                widget["checkbox"].set(value if isinstance(value, bool) else True)
                        break

    def save_game_settings(self):
        """Save current game settings to unified JSON file."""
        unified_settings = load_unified_settings()
        game_settings = {}
        
        # Collect current game settings from variables (updated by load_settings)
        for var_name, var_info in self.variables.items():
            if var_info.get("checkbox", False):
                # Check if this is a pure checkbox variable or has both checkbox and entry
                has_entry = False
                for widget in self.widgets:
                    if widget["name"] == var_name and widget["entry"] is not None:
                        has_entry = True
                        break
                
                if has_entry:
                    # For variables with both checkbox and entry (like sudden_death_game_break, crib_time)
                    # Save the numeric value from the entry, not the boolean
                    value = var_info.get("value", var_info["default"])
                    if var_name != "time_to_start_first_game":
                        try:
                            game_settings[var_name] = float(value) if '.' in str(value) else int(value)
                        except (ValueError, TypeError):
                            game_settings[var_name] = var_info["default"]
                    else:
                        game_settings[var_name] = value
                else:
                    # For pure checkbox variables (like team_timeouts_allowed, overtime_allowed)
                    # Save the "used" boolean value
                    game_settings[var_name] = var_info.get("used", var_info["default"])
            else:
                # For other variables, use the current value
                value = var_info.get("value", var_info["default"])
                if var_name != "time_to_start_first_game":
                    try:
                        game_settings[var_name] = float(value) if '.' in str(value) else int(value)
                    except (ValueError, TypeError):
                        game_settings[var_name] = value
                else:
                    game_settings[var_name] = value
        
        unified_settings["gameSettings"] = game_settings
        save_unified_settings(unified_settings)

    # Zigbee Siren Methods
    def toggle_zigbee_connection(self):
        """Toggle Zigbee connection (connect if disconnected, disconnect if connected)."""
        if self.zigbee_controller.connected:
            self.stop_zigbee_connection()
        else:
            self.start_zigbee_connection()

    def start_zigbee_connection(self):
        """Start the Zigbee siren connection."""
        # Mark as user-initiated action to prevent watchdog interference
        self.user_initiated_action = True
        self.stop_connection_watchdog()
        
        try:
            if self.zigbee_controller.start():
                self.toggle_connection_btn.config(text="Disconnect", state="normal")
                self.add_to_zigbee_log("Starting Zigbee connection...")
            else:
                self.add_to_zigbee_log("Failed to start Zigbee connection")
                messagebox.showerror("Connection Error", 
                                   "Failed to start Zigbee connection. Check MQTT library installation.")
        except Exception as e:
            self.add_to_zigbee_log(f"Error starting connection: {e}")
            messagebox.showerror("Connection Error", f"Error starting connection: {e}")
        finally:
            # Reset user action flag after a brief delay
            self.master.after(1000, lambda: setattr(self, 'user_initiated_action', False))

    def stop_zigbee_connection(self):
        """Stop the Zigbee siren connection."""
        # Mark as user-initiated action to prevent watchdog interference
        self.user_initiated_action = True
        self.stop_connection_watchdog()
        
        try:
            self.zigbee_controller.stop()
            self.toggle_connection_btn.config(text="Connect", state="normal")
            self.add_to_zigbee_log("Zigbee connection stopped")
        except Exception as e:
            self.add_to_zigbee_log(f"Error stopping connection: {e}")
        finally:
            # Reset user action flag after a brief delay
            self.master.after(1000, lambda: setattr(self, 'user_initiated_action', False))

    def test_zigbee_connection(self):
        """Test the MQTT connection."""
        self.add_to_zigbee_log("Testing MQTT connection...")
        try:
            if self.zigbee_controller.test_connection():
                self.add_to_zigbee_log("Connection test successful")
                messagebox.showinfo("Connection Test", "MQTT connection test successful!")
            else:
                self.add_to_zigbee_log("Connection test failed")
                messagebox.showerror("Connection Test", "MQTT connection test failed. Check configuration.")
        except Exception as e:
            self.add_to_zigbee_log(f"Connection test error: {e}")
            messagebox.showerror("Connection Test", f"Connection test error: {e}")
    
    def start_connection_watchdog(self):
        """Start the connection watchdog to monitor and retry Zigbee connections."""
        if self.connection_watchdog_active:
            return  # Already running
        
        self.connection_watchdog_active = True
        self.connection_watchdog_attempts = 0
        self.user_initiated_action = False
        self.add_to_zigbee_log("Starting connection watchdog...")
        
        # Start the first connection attempt
        self.schedule_connection_check()
    
    def stop_connection_watchdog(self):
        """Stop the connection watchdog."""
        if self.connection_watchdog_job:
            self.master.after_cancel(self.connection_watchdog_job)
            self.connection_watchdog_job = None
        
        self.connection_watchdog_active = False
        self.connection_watchdog_attempts = 0
        
        if hasattr(self, 'zigbee_status_var'):
            self.add_to_zigbee_log("Connection watchdog stopped")
    
    def schedule_connection_check(self):
        """Schedule the next connection check after 10 seconds."""
        if not self.connection_watchdog_active:
            return
        
        # Cancel any existing scheduled check
        if self.connection_watchdog_job:
            self.master.after_cancel(self.connection_watchdog_job)
        
        # Schedule the next check in 10 seconds (10000 ms)
        self.connection_watchdog_job = self.master.after(10000, self.check_connection_status)
    
    def check_connection_status(self):
        """Check connection status and attempt reconnection if needed."""
        if not self.connection_watchdog_active or self.user_initiated_action:
            return
        
        # Check if already connected
        if self.zigbee_controller.connected:
            self.add_to_zigbee_log("Watchdog: Connection established successfully")
            self.stop_connection_watchdog()
            return
        
        # Not connected, attempt reconnection
        self.connection_watchdog_attempts += 1
        
        if self.connection_watchdog_attempts <= self.connection_watchdog_max_attempts:
            self.add_to_zigbee_log(f"Watchdog: Connection attempt {self.connection_watchdog_attempts}/{self.connection_watchdog_max_attempts}")
            
            try:
                if self.zigbee_controller.start():
                    # Connection attempt started, wait for callback
                    self.schedule_connection_check()
                else:
                    # Immediate failure, schedule next attempt
                    self.schedule_connection_check()
            except Exception as e:
                self.add_to_zigbee_log(f"Watchdog connection error: {e}")
                self.schedule_connection_check()
        else:
            # Max attempts reached
            self.add_to_zigbee_log(f"Watchdog: Max connection attempts ({self.connection_watchdog_max_attempts}) reached. Giving up.")
            self.toggle_connection_btn.config(text="Connect", state="normal")
            self.stop_connection_watchdog()

    def save_zigbee_config(self):
        """Save Zigbee configuration."""
        try:
            config = {}
            for key, widget in self.config_widgets.items():
                value = widget.get()
                if key == "mqtt_port":
                    config[key] = int(value) if value.isdigit() else 1883
                elif key == "siren_button_devices":
                    # Convert comma-separated string to list
                    device_names = [name.strip() for name in value.split(",") if name.strip()]
                    config["siren_button_devices"] = device_names
                    # Also set legacy single device for backward compatibility
                    config["siren_button_device"] = device_names[0] if device_names else "siren_button"
                else:
                    config[key] = value
            
            # Keep other settings from current config
            current_config = self.zigbee_controller.config.copy()
            current_config.update(config)
            
            # Save to both the Zigbee controller and unified settings
            self.zigbee_controller.save_config(current_config)
            
            # Also save to unified settings file
            unified_settings = load_unified_settings()
            unified_settings["zigbeeSettings"] = current_config
            save_unified_settings(unified_settings)
            
            self.add_to_zigbee_log("Configuration saved")
            messagebox.showinfo("Configuration", "Zigbee configuration saved successfully!")
        except Exception as e:
            self.add_to_zigbee_log(f"Error saving config: {e}")
            messagebox.showerror("Configuration Error", f"Error saving configuration: {e}")

    def test_wireless_siren(self):
        """Test the wireless siren manually."""
        self.add_to_zigbee_log("Manual siren test triggered")
        self.trigger_wireless_siren()

    def trigger_wireless_siren(self):
        """Trigger the wireless siren using current sound settings."""
        try:
            # Use the same sound file and volume as the regular siren
            siren_file = self.siren_var.get()
            self.add_to_zigbee_log(f"Triggering wireless siren: {siren_file}")
            
            # Use the existing sound playing method with volume control
            play_sound_with_volume(siren_file, "siren", self.enable_sound, self.pips_volume, 
                                   self.siren_volume, self.air_volume, self.water_volume)
            
        except Exception as e:
            self.add_to_zigbee_log(f"Error triggering siren: {e}")

    def update_zigbee_status(self, connected: bool, message: str):
        """Update Zigbee connection status in UI."""
        try:
            if connected:
                status_text = f"Connected - {message}"
                self.zigbee_status_label.config(fg="green")
                self.toggle_connection_btn.config(text="Disconnect", state="normal")
                
                # If watchdog is active and we're connected, stop watchdog
                if self.connection_watchdog_active and not self.user_initiated_action:
                    self.add_to_zigbee_log("Watchdog: Connection established, stopping watchdog")
                    self.stop_connection_watchdog()
                    
            else:
                status_text = f"Disconnected - {message}"
                self.zigbee_status_label.config(fg="red")
                # Only change button text if watchdog is not running or has exceeded max attempts
                if not self.connection_watchdog_active or self.connection_watchdog_attempts >= self.connection_watchdog_max_attempts:
                    self.toggle_connection_btn.config(text="Connect", state="normal")
                else:
                    # Watchdog is still trying, keep showing "Disconnect" temporarily
                    self.toggle_connection_btn.config(text="Disconnect", state="normal")
            
            self.zigbee_status_var.set(status_text)
            self.add_to_zigbee_log(f"Status: {status_text}")
        except Exception as e:
            print(f"Error updating Zigbee status: {e}")

    def update_usb_dongle_status(self):
        """Update USB dongle connection status in UI."""
        try:
            if is_usb_dongle_connected():
                self.usb_dongle_status_label.config(text="Connected", fg="green")
                self.add_to_zigbee_log("USB Dongle: Connected")
            else:
                self.usb_dongle_status_label.config(text="Disconnected", fg="red")
                self.add_to_zigbee_log("USB Dongle: Disconnected")
        except Exception as e:
            self.usb_dongle_status_label.config(text="Error", fg="red")
            self.add_to_zigbee_log(f"USB Dongle check error: {e}")
            print(f"Error updating USB dongle status: {e}")

    def add_to_zigbee_log(self, message: str):
        """Add a message to the Zigbee log."""
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error adding to Zigbee log: {e}")

    def clear_zigbee_log(self):
        """Clear the Zigbee log."""
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.add_to_zigbee_log("Log cleared")
        except Exception as e:
            print(f"Error clearing Zigbee log: {e}")

    def is_overtime_enabled(self):
        return self.overtime_allowed_var.get()

    def is_sudden_death_enabled(self):
        v = self.variables
        return v["sudden_death_game_break"].get("used", True)

    def update_team_timeouts_allowed(self):
        allowed = self.team_timeouts_allowed_var.get()

        # Update white timeout button
        if hasattr(self, 'white_timeout_button') and self.white_timeout_button is not None:
            try:
                if allowed:
                    self.white_timeout_button.config(state=tk.NORMAL, bg="white", fg="black")
                else:
                    self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            except Exception:
                pass
        
        # Update black timeout button
        if hasattr(self, 'black_timeout_button') and self.black_timeout_button is not None:
            try:
                if allowed:
                    self.black_timeout_button.config(state=tk.NORMAL, bg="black", fg="white")
                else:
                    self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            except Exception:
                pass

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
    
    def _on_team_timeouts_change(self):
        """Handle team_timeouts_allowed checkbox change."""
        # Update the variable
        self.variables["team_timeouts_allowed"]["used"] = self.team_timeouts_allowed_var.get()
        # Update UI state
        self.update_team_timeouts_allowed()
        # team_timeouts_allowed doesn't affect game sequence structure, only UI state
        # So we don't need to rebuild the sequence
        self.save_game_settings()
    
    def _on_overtime_change(self):
        """Handle overtime_allowed checkbox change."""
        # Update the variable
        self.variables["overtime_allowed"]["used"] = self.overtime_allowed_var.get()
        # Update UI state
        self.update_overtime_variables_state()
        # Rebuild sequence and save
        self.build_game_sequence()
        self.save_game_settings()

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

        # Referee timeout timer label for display window
        self.display_referee_timeout_timer_label = tk.Label(
            tab, textvariable=self.referee_timeout_timer_var, 
            font=self.display_fonts["referee_timeout_timer"], 
            bg="red", fg="white"
        )
        self.display_referee_timeout_timer_label.grid(row=10, column=3, rowspan=1, columnspan=3, padx=0, pady=1, sticky="nsew")
        self.display_referee_timeout_timer_label.grid_remove()  # Hide initially

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
            self.master.after(200, sync_backgrounds)  # Reduced frequency for background sync only
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
        # Rebuild game sequence to reflect any settings changes (e.g., cleared "Time to Start First Game")
        self.build_game_sequence()
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
            # Reset Between Game Break to configured duration before applying crib time adjustment
            cur_period['duration'] = self.get_minutes('between_game_break')
            
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
                # Only reduce by crib_time maximum, never by more
                reduce_by = min(delta, crib_time)
                if reduce_by > 0 and cur_period['duration'] is not None:
                    # Ensure minimum duration is preserved (>31 seconds as per validation)
                    new_duration = cur_period['duration'] - reduce_by
                    cur_period['duration'] = max(32, new_duration)

        if cur_period['name'] in ['First Half', 'Second Half', 'Between Game Break']:
            self.white_timeouts_this_half = 0
            self.black_timeouts_this_half = 0

        # Event-driven: Update the StringVar instead of calling .config()
        self.half_label_var.set(cur_period['name'])
        self.update_half_label_background(cur_period['name'])

        TIMEOUTS_DISABLED_PERIODS = [
            "First Game Starts In:",
            "Half Time",
            "Overtime Game Break",
            "Sudden Death Game Break",
            "Overtime First Half",
            "Overtime Half Time",
            "Overtime Second Half",
            "Sudden Death",
        ]
        # Always enable penalties during Referee Time-Out, even if entered from First Game Starts In:
        if cur_period['name'] == "Referee Time-Out":
            self.penalties_button.config(state=tk.NORMAL)
            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
        elif cur_period['name'] in TIMEOUTS_DISABLED_PERIODS:
            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            if cur_period['name'] in ["First Game Starts In:", "Between Game Break", "Half Time", "Overtime Game Break", "Sudden Death Game Break"]:
                self.penalties_button.config(state=tk.DISABLED)
            else:
                self.penalties_button.config(state=tk.NORMAL)
        elif cur_period['name'] == "Between Game Break":
            # Team timeout buttons should be greyed out (disabled) during Between Game Break
            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.penalties_button.config(state=tk.DISABLED)
        else:
            # Only enable timeout buttons if team timeouts are allowed
            if self.team_timeouts_allowed_var.get():
                self.white_timeout_button.config(state=tk.NORMAL, bg="white", fg="black")
                self.black_timeout_button.config(state=tk.NORMAL, bg="black", fg="white")
            else:
                self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
                self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.penalties_button.config(state=tk.NORMAL)

        PAUSE_PERIODS = [
            "First Game Starts In:",
            "Between Game Break",
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
            # Log Sudden Death start
            self.log_game_event("Sudden Death Start")
        else:
            self.timer_seconds = cur_period['duration'] if cur_period['duration'] is not None else 0
            self.update_timer_display()
            self.timer_running = True
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
            self.timer_job = self.master.after(1000, self.countdown_timer)
            
            # Log period start events for halves and overtime halves
            if cur_period['name'] == 'First Half':
                self.log_game_event("First Half Start")
            elif cur_period['name'] == 'Second Half':
                self.log_game_event("Second Half Start")
            elif cur_period['name'] == 'Overtime First Half':
                self.log_game_event("Overtime First Half Start")
            elif cur_period['name'] == 'Overtime Second Half':
                self.log_game_event("Overtime Second Half Start")

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
        
        # Log period end events before transitioning
        if period_name == 'First Half':
            self.log_game_event("First Half End")
        elif period_name == 'Second Half':
            self.log_game_event("Second Half End")
        elif period_name == 'Overtime First Half':
            self.log_game_event("Overtime First Half End")
        elif period_name == 'Overtime Second Half':
            self.log_game_event("Overtime Second Half End")
        elif period_name == 'Sudden Death':
            self.log_game_event("Sudden Death End")
        
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
        # After Between Game Break at the end of sequence, loop back to First Half
        if self.current_index >= len(self.full_sequence):
            # Find First Half to loop back to regular game
            first_half_idx = self.find_period_index('First Half')
            self.current_index = first_half_idx
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
                    # Write game results to CSV/TXT BEFORE resetting scores
                    current_game = self.get_current_game_number()
                    white_score = self.white_score_var.get()
                    black_score = self.black_score_var.get()
                    # Copy stored_penalties before clearing
                    penalties_to_write = list(self.stored_penalties)
                    
                    # Log game end event to TXT file
                    self.log_game_event("Game End")
                    
                    # Write results to CSV file
                    self.write_game_results_to_csv(current_game, white_score, black_score, penalties_to_write)
                    
                    # Now reset game state
                    self.white_score_var.set(0)
                    self.black_score_var.set(0)
                    self.stored_penalties.clear()
                    self.clear_all_penalties()
                    # Advance to next game in Tournament List
                    self.advance_to_next_game()
                    # Update team names in scoreboard tab for the next game
                    self.update_team_names_display()
                if self.timer_seconds <= 30:
                    self.sudden_death_restore_active = False
                    self.sudden_death_restore_time = None
            
            # Sound logic for break periods
            if cur_period and cur_period['type'] == 'break':
                break_periods = ['First Game Starts In:', 'Between Game Break', 'Half Time', 'Sudden Death Game Break', 
                               'Overtime Game Break', 'Overtime Half Time']
                if cur_period['name'] in break_periods:
                    if self.timer_seconds == 30:
                        # Play one pip at 30s remaining
                        try:
                            play_sound_with_volume(self.pips_var.get(), "pips", self.enable_sound, 
                                                   self.pips_volume, self.siren_volume, 
                                                   self.air_volume, self.water_volume)
                        except Exception as e:
                            print(f"Error playing pip sound at 30s: {e}")
                    elif 1 <= self.timer_seconds <= 10:
                        # Play one pip per second from 10s to 1s remaining
                        try:
                            play_sound_with_volume(self.pips_var.get(), "pips", self.enable_sound,
                                                   self.pips_volume, self.siren_volume,
                                                   self.air_volume, self.water_volume)
                        except Exception as e:
                            print(f"Error playing pip sound at {self.timer_seconds}s: {e}")
            
            self.timer_seconds -= 1
            self.timer_job = self.master.after(1000, self.countdown_timer)
        else:
            # Timer reached 0
            cur_period = self.full_sequence[self.current_index] if self.full_sequence and self.current_index < len(self.full_sequence) else None
            if cur_period:
                # Sound logic for when timer hits 0
                if cur_period['type'] == 'break':
                    break_periods = ['First Game Starts In:', 'Between Game Break', 'Half Time', 'Sudden Death Game Break', 
                                   'Overtime Game Break', 'Overtime Half Time']
                    if cur_period['name'] in break_periods:
                        # Play siren at 0s for break periods
                        try:
                            play_sound_with_volume(self.siren_var.get(), "siren", self.enable_sound,
                                                   self.pips_volume, self.siren_volume,
                                                   self.air_volume, self.water_volume)
                        except Exception as e:
                            print(f"Error playing siren at end of break period: {e}")
                elif cur_period['type'] in ['regular', 'overtime']:
                    half_periods = ['First Half', 'Second Half', 'Overtime First Half', 'Overtime Second Half']
                    if cur_period['name'] in half_periods:
                        # Play siren at end of each half
                        try:
                            play_sound_with_volume(self.siren_var.get(), "siren", self.enable_sound,
                                                   self.pips_volume, self.siren_volume,
                                                   self.air_volume, self.water_volume)
                        except Exception as e:
                            print(f"Error playing siren at end of half: {e}")
            
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
            "first_game_starts_in:",
            "game_starts_in:",
            "half_time",
            "half_time_break",
            "overtime_game_break",
            "overtime_half_time",
            "overtime_half_time_break",
            "between_game_break",
            "between_game_break_starts_in:",
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
        
        # Log the penalty start
        self.log_game_event("Penalty Start", team=team, cap_number=str(cap), duration=duration)
        
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
            # Check if penalty just expired (reached 0)
            if penalty["seconds_remaining"] == 0:
                # Immediately remove the expired penalty
                self.remove_penalty(penalty)  # This will update the display
            else:
                # Still time remaining, update display and schedule next countdown
                self.update_penalty_display()
                self.schedule_penalty_countdown(penalty)
        else:
            # Should not normally reach here, but handle it just in case
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

    def show_cap_number_dialog(self):
        """
        Show a dialog to select a cap number (1-15) or Unknown.
        Returns the selected cap number as a string, or None if canceled.
        """
        cap_number_dialog = tk.Toplevel(self.master)
        cap_number_dialog.title("Select Cap Number")
        cap_number_dialog.geometry("400x300")
        cap_number_dialog.transient(self.master)
        cap_number_dialog.grab_set()
        
        selected_cap = {"value": None}
        
        # Title label
        title_label = tk.Label(cap_number_dialog, text="Select Scorer's Cap Number:", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=10)
        
        # Frame for the button matrix
        matrix_frame = tk.Frame(cap_number_dialog)
        matrix_frame.pack(pady=10)
        
        def select_cap(cap):
            selected_cap["value"] = str(cap)
            # Highlight the selected button and keep it highlighted
            def apply_highlight():
                for widget in matrix_frame.winfo_children():
                    if hasattr(widget, 'cap_value') and widget.cap_value == cap:
                        widget.config(relief=tk.SUNKEN, bg="lightblue")
                    elif isinstance(widget, tk.Button) and hasattr(widget, 'original_bg'):
                        widget.config(relief=tk.RAISED, bg=widget.original_bg)
                for widget in bottom_frame.winfo_children():
                    if isinstance(widget, tk.Button) and hasattr(widget, 'original_bg'):
                        widget.config(relief=tk.RAISED, bg=widget.original_bg)
            # Apply immediately and schedule again to override button's default behavior
            apply_highlight()
            cap_number_dialog.after(1, apply_highlight)
        
        def select_unknown():
            selected_cap["value"] = "Unknown"
            # Highlight Unknown button and keep it highlighted
            def apply_highlight():
                for widget in matrix_frame.winfo_children():
                    if isinstance(widget, tk.Button) and hasattr(widget, 'original_bg'):
                        widget.config(relief=tk.RAISED, bg=widget.original_bg)
                for widget in bottom_frame.winfo_children():
                    if hasattr(widget, 'is_unknown'):
                        widget.config(relief=tk.SUNKEN, bg="lightblue")
                    elif isinstance(widget, tk.Button) and hasattr(widget, 'original_bg'):
                        widget.config(relief=tk.RAISED, bg=widget.original_bg)
            # Apply immediately and schedule again to override button's default behavior
            apply_highlight()
            cap_number_dialog.after(1, apply_highlight)
        
        def select_penalty_goal():
            selected_cap["value"] = "Penalty Goal"
            # Highlight Penalty Goal button and keep it highlighted
            def apply_highlight():
                for widget in matrix_frame.winfo_children():
                    if isinstance(widget, tk.Button) and hasattr(widget, 'original_bg'):
                        widget.config(relief=tk.RAISED, bg=widget.original_bg)
                for widget in bottom_frame.winfo_children():
                    if hasattr(widget, 'is_penalty_goal'):
                        widget.config(relief=tk.SUNKEN, bg="lightblue")
                    elif isinstance(widget, tk.Button) and hasattr(widget, 'original_bg'):
                        widget.config(relief=tk.RAISED, bg=widget.original_bg)
            # Apply immediately and schedule again to override button's default behavior
            apply_highlight()
            cap_number_dialog.after(1, apply_highlight)
        
        def on_ok():
            if selected_cap["value"] is not None:
                cap_number_dialog.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select a cap number or Unknown.")
        
        # Create 5x3 matrix of buttons (1-15)
        button_width = 5
        button_height = 2
        for row in range(3):
            for col in range(5):
                cap_num = row * 5 + col + 1
                btn = tk.Button(matrix_frame, text=str(cap_num), width=button_width, height=button_height,
                               command=lambda c=cap_num: select_cap(c))
                btn.cap_value = cap_num
                btn.original_bg = btn.cget('bg')  # Store original background color
                btn.grid(row=row, column=col, padx=2, pady=2)
        
        # Bottom frame for Unknown and OK buttons
        bottom_frame = tk.Frame(cap_number_dialog)
        bottom_frame.pack(pady=10)
        
        # Unknown button (columnspan 2, half the original width)
        unknown_btn = tk.Button(bottom_frame, text="Unknown", width=button_width * 2 + 3, height=button_height,
                               command=select_unknown)
        unknown_btn.is_unknown = True
        unknown_btn.original_bg = unknown_btn.cget('bg')  # Store original background color
        unknown_btn.grid(row=0, column=0, columnspan=2, padx=2, pady=2)
        
        # Penalty Goal button (columnspan 2)
        penalty_goal_btn = tk.Button(bottom_frame, text="Penalty Goal", width=button_width * 2 + 3, height=button_height,
                                    command=select_penalty_goal)
        penalty_goal_btn.is_penalty_goal = True
        penalty_goal_btn.original_bg = penalty_goal_btn.cget('bg')  # Store original background color
        penalty_goal_btn.grid(row=0, column=2, columnspan=2, padx=2, pady=2)
        
        # OK button (in column 4)
        ok_btn = tk.Button(bottom_frame, text="OK", width=button_width, height=button_height,
                          command=on_ok)
        ok_btn.original_bg = ok_btn.cget('bg')  # Store original background color
        ok_btn.grid(row=0, column=4, padx=2, pady=2)
        
        # Wait for the dialog to close
        self.master.wait_window(cap_number_dialog)
        
        return selected_cap["value"]

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
            self.half_label_var.set("Ref Time-Out")
            self.half_label.config(bg="red")
            # Show the referee timeout timer label
            self.referee_timeout_timer_label.grid()
            if hasattr(self, "display_referee_timeout_timer_label"):
                self.display_referee_timeout_timer_label.grid()
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
            # Hide the referee timeout timer label
            self.referee_timeout_timer_label.grid_remove()
            if hasattr(self, "display_referee_timeout_timer_label"):
                self.display_referee_timeout_timer_label.grid_remove()
            self.timer_seconds = self.saved_state["timer_seconds"]
            self.timer_running = self.saved_state["timer_running"]
            self.current_index = self.saved_state["current_index"]
            # Event-driven: Update the StringVar instead of calling .config()
            self.half_label_var.set(self.saved_state["half_label_text"])
            self.half_label.config(bg=self.saved_state["half_label_bg"])
            self.court_time_paused = self.saved_state.get("court_time_paused", False)
            # Only resume penalty timers if we're not in a break period
            cur_period = self.full_sequence[self.current_index]
            PAUSE_PERIODS = [
                "First Game Starts In:",
                "Between Game Break",
                "Half Time",
                "Overtime Game Break",
                "Overtime Half Time",
                "Sudden Death Game Break",
                "White Team Time-Out",
                "Black Team Time-Out",
                "Referee Time-Out"
            ]
            if cur_period['name'] not in PAUSE_PERIODS:
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
            # (reusing cur_period from line 3773)
            if cur_period['name'] in ["Between Game Break Starts in:", "Between Game Break"]:
                self.penalties_button.config(state=tk.DISABLED)
            else:
                self.penalties_button.config(state=tk.NORMAL)

    def referee_timeout_countup(self):
        if not self.referee_timeout_active:
            return
        mins, secs = divmod(self.referee_timeout_elapsed, 60)
        # Update the referee timeout timer label
        self.referee_timeout_timer_var.set(f"Ref Time-Out: {int(mins):02d}:{int(secs):02d}")
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
        is_team_timeout = getattr(self, 'in_timeout', False)
        is_referee_timeout = getattr(self, 'referee_timeout_active', False)
        is_break = cur_period['type'] == 'break'
        if is_break or is_team_timeout or is_referee_timeout:
            # Customize the warning message based on the situation
            if is_team_timeout:
                warning_msg = f"You are about to adjust a goal for {team_name} during a Team Time-Out. Are you sure?"
            elif is_referee_timeout:
                warning_msg = f"You are about to adjust a goal for {team_name} during a Referee Time-Out. Are you sure?"
            else:
                warning_msg = f"You are about to adjust a goal for {team_name} during a break or half time. Are you sure?"
            
            if not messagebox.askyesno(
                "Adjust Goal During Break?",
                warning_msg
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
        is_team_timeout = getattr(self, 'in_timeout', False)
        is_referee_timeout = getattr(self, 'referee_timeout_active', False)
        is_break = cur_period['type'] == 'break'
        
        # Determine if we should show a warning and what message to use
        show_warning = is_break or is_team_timeout or is_referee_timeout
        
        if show_warning:
            # Customize the warning message based on the situation
            if is_team_timeout:
                warning_msg = f"You are about to add a goal for {team_name} during a Team Time-Out. Are you sure?"
            elif is_referee_timeout:
                warning_msg = f"You are about to add a goal for {team_name} during a Referee Time-Out. Are you sure?"
            else:
                warning_msg = f"You are about to add a goal for {team_name} during a break or half time. Are you sure?"
            
            if not messagebox.askyesno(
                "Add Goal During Break?",
                warning_msg
            ):
                return
        
        # Get cap number if recording is enabled
        cap_number = None
        if self.record_scorers_cap_number_var.get():
            cap_number = self.show_cap_number_dialog()
            if cap_number is None:
                # User canceled the dialog, don't add the goal
                return
        
        score_var.set(score_var.get() + 1)
        
        # Log the goal with cap number and break/timeout status
        break_status = None
        if is_team_timeout:
            break_status = "Team Time-Out"
        elif is_referee_timeout:
            break_status = "Referee Time-Out"
        elif is_break:
            break_status = "Break"
        
        self.log_game_event("Goal", team=team_name, cap_number=cap_number, break_status=break_status)

#Saves the current Sudden Death timer value (self.sudden_death_seconds) for possible restoration (for example, if the goal is later subtracted).
#Flags that a goal has been scored in Sudden Death (prevents this block from running again).
#Progresses the game to the next period (typically Between Game Break or End of Game).
        if cur_period['name'] == 'Sudden Death' and not getattr(self, 'sudden_death_goal_scored', False):
            self.sudden_death_restore_time = self.sudden_death_seconds
            self.sudden_death_restore_active = True
            self.sudden_death_goal_scored = True
            self.timer_running = False
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

if __name__ == "__main__":
    root = tk.Tk()
    app = GameManagementApp(root)
    
    def on_closing():
        """Handle application shutdown."""
        try:
            # Stop connection watchdog
            app.stop_connection_watchdog()
            # Stop Zigbee controller
            app.zigbee_controller.stop()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
