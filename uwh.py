
import csv_export
import hardware_detection
import startup_selftest
import game_logging
import display_manager
import game_flow
import csv_helpers
import csv_ui
import zigbee_ui
import zigbee_hardware_ui
import os
import sys
import shutil

def get_executable_directory():
    """Returns the absolute path to the root folder where the .exe sits."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# Establish the base directory (Root folder containing the EXE)
BASE_DIR = get_executable_directory()

# --- EMERGENCY RUNTIME DEBUG LOGGING ---
# Captures console prints from background threads and drops them into a text file
if getattr(sys, 'frozen', False):
    log_file_path = os.path.join(BASE_DIR, "debug_log.txt")
    # Open file in append mode; buffering=1 forces it to write to disk instantly
    log_file = open(log_file_path, "a", encoding="utf-8", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file
    print("\n--- APP LAUNCHED: SERIAL DEBUGGER INITIALISED ---")
# ----------------------------------------


# Final, writable paths where the files SHOULD live for the user
SETTINGS_PATH = os.path.join(BASE_DIR, 'settings.json')
DRAW_PATH = os.path.join(BASE_DIR, 'Tournament_Draw.csv')
LICENSE_PATH = os.path.join(BASE_DIR, 'LICENSE')
INO_PATH = os.path.join(BASE_DIR, 'arduino_siren_button.ino')
README_PATH = os.path.join(BASE_DIR, 'README.md')
ZIGBEE_PATH = os.path.join(BASE_DIR, 'ZIGBEE_SETUP.md')

# --- SELF-EXTRACTING ROUTINE FOR PYINSTALLER 6 ---
# If running compiled, ensure files exist in the root folder. If missing, copy them from _internal.
if getattr(sys, 'frozen', False):
    internal_dir = os.path.join(BASE_DIR, '_internal')
    
    # List of files we want to push out to the root directory
    files_to_extract = [
        ('settings.json', SETTINGS_PATH),
        ('Tournament_Draw.csv', DRAW_PATH),
        ('LICENSE', LICENSE_PATH),
        ('arduino_siren_button.ino', INO_PATH),
        ('README.md', README_PATH),
        ('ZIGBEE_SETUP.md', ZIGBEE_PATH)
    ]
    
    for filename, target_path in files_to_extract:
        # Only copy if the file doesn't already exist in the root directory
        # This ensures user modifications to settings.json are NEVER overwritten
        if not os.path.exists(target_path):
            source_path = os.path.join(internal_dir, filename)
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)

    # Tell Python to check the '_internal' folder for your helper modules
    sys.path.insert(0, internal_dir)

# NOW you can safely import your custom helper modules
import sound
import zigbee_siren
import serial_siren_listener
import tkinter as tk
from tkinter import ttk, messagebox, font
import datetime
import re
import time
import threading
import os
import subprocess
import json
import webbrowser

# ------------------------------------------------------------------
# Global settings
# ------------------------------------------------------------------

DEBUG_MODE = False

from zigbee_siren import ZigbeeSirenController, is_mqtt_available
from sound import (check_audio_device_available, handle_no_audio_device_warning, 
                   get_sound_files, play_sound, play_sound_with_volume, preload_sounds)
from game_engine import GameEngine

SETTINGS_FILE = "settings.json"

def is_usb_dongle_connected():
    return hardware_detection.is_usb_dongle_connected(
        load_unified_settings,
        DEBUG_MODE
    )

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
            # Windows: Use explorer with Popen (doesn't wait for exit status)
            # Explorer.exe often returns non-zero exit codes even on success
            subprocess.Popen(['explorer', os.path.normpath(folder_path)])
        elif system == 'Darwin':
            # macOS: Use open (don't check exit status)
            subprocess.Popen(['open', folder_path])
        else:
            # Linux and other Unix-like systems: Use xdg-open (don't check exit status)
            subprocess.Popen(['xdg-open', folder_path])
    except FileNotFoundError:
        messagebox.showerror("Error", f"File manager command not found on {system}")
    except OSError as e:
        messagebox.showerror("Error", f"Failed to open folder:\n{e}")

def load_hardware_detection_cache():
    return hardware_detection.load_hardware_detection_cache(
        load_unified_settings
    )

def save_hardware_detection_cache(arduino_port, zigbee_port):
    return hardware_detection.save_hardware_detection_cache(
        arduino_port,
        zigbee_port,
        load_unified_settings,
        save_unified_settings,
        DEBUG_MODE
    )

def auto_detect_com_ports():
    return hardware_detection.auto_detect_com_ports(
        load_unified_settings,
        save_unified_settings,
        DEBUG_MODE
    )

def migrate_legacy_settings():
    """Migrate settings from legacy separate files to unified settings.json"""
    unified_settings = get_default_unified_settings()
    migrated = False
    
    # Migrate game_settings.json (sound settings)
    # CHANGED: Use BASE_DIR instead of os.getcwd() to guarantee looking next to the .exe
    legacy_sound_file = os.path.join(BASE_DIR, "game_settings.json")
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
    # CHANGED: Use BASE_DIR instead of os.getcwd()
    legacy_zigbee_file = os.path.join(BASE_DIR, "zigbee_config.json")
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
    # CHANGED: Use the absolute SETTINGS_PATH defined at the top of the file
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
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
    # CHANGED: Use the absolute SETTINGS_PATH defined at the top of the file
    with open(SETTINGS_PATH, "w") as f:
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

    def _on_display_window_close(self):
        """Handle Display Window being closed by the window X button."""
        try:
            if hasattr(self, "display_window") and self.display_window is not None:
                if self.display_window.winfo_exists():
                    self.display_window.destroy()
        except tk.TclError:
            pass
    
        self.display_window = None
    
        try:
            if hasattr(self, "show_display_screen_var"):
                self.show_display_screen_var.set(False)
        except tk.TclError:
            pass

    def toggle_display_screen(self):
        """Open or close the main Display Window from the Game Variables checkbox."""
        if self.show_display_screen_var.get():
            try:
                if (
                    hasattr(self, "display_window")
                    and self.display_window is not None
                    and self.display_window.winfo_exists()
                ):
                    self.display_window.lift()
                    self.display_window.focus_force()
                    return
            except tk.TclError:
                self.display_window = None
    
            self.create_display_window()
            self.update_penalty_display()
    
        else:
            try:
                if (
                    hasattr(self, "display_window")
                    and self.display_window is not None
                    and self.display_window.winfo_exists()
                ):
                    self.display_window.destroy()
            except tk.TclError:
                pass
    
            self.display_window = None

    def handle_hardware_siren_event(self, event_name="ON"):

        if event_name == "OFF":
            try:
                if hasattr(self, "arduino_siren_channel") and self.arduino_siren_channel:
                    self.arduino_siren_channel.stop()
                    self.arduino_siren_channel = None
            except Exception:
                pass

            try:
                self.zigbee_controller.handle_hardware_siren_event("OFF")
            except Exception:
                pass

            return

        try:
            import sound

            track = self.siren_var.get()
            volume = self.siren_volume.get()

            normalized_volume = max(0.0, min(100.0, volume)) / 100.0

            if hasattr(sound, "_preloaded_sounds") and track in sound._preloaded_sounds:
                sound_obj = sound._preloaded_sounds[track]
                sound_obj.set_volume(normalized_volume)

                # Stop previous Arduino loop if one somehow exists
                if hasattr(self, "arduino_siren_channel") and self.arduino_siren_channel:
                    self.arduino_siren_channel.stop()

                # Let pygame choose the channel, same general path as normal playback
                self.arduino_siren_channel = sound_obj.play(loops=-1)

        except Exception as e:
            if DEBUG_MODE:
                print(f"Hardware siren local audio failed: {e}")

        try:
            self.zigbee_controller.handle_hardware_siren_event("ON")
        except Exception:
            pass
    
    def __init__(self, master):
        self.master = master
        self.master.title("Underwater Hockey Game Management App")
        self.master.geometry('1200x800')
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both',)

        # --- Variable and font setup ---
        self.variables = {
            "time_to_start_first_game": {"default": "", "checkbox": False, "unit": "HH:mm", "label": "Time to Start First Game:"},
            "start_first_game_in": {"default": 1, "checkbox": False, "unit": "minutes", "label": "First Game Starts In:"},
            "team_timeouts_allowed": {"default": True, "checkbox": True, "unit": "", "label": "Team time-outs allowed?"},
            "team_timeout_period": {"default": 1, "checkbox": False, "unit": "minutes", "label": "Team Time-Out Period:"},
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

        self.engine = GameEngine()
        
        # Event-driven Tkinter variables for all display widgets
        self.white_score_var = tk.IntVar(value=0)
        self.black_score_var = tk.IntVar(value=0)
        self.timer_var = tk.StringVar(value="00:00")
        self.court_time_var = tk.StringVar(value="Court Time is 00:00:00")
        self.half_label_var = tk.StringVar(value="")
        self.game_number_var = tk.StringVar(value="Game 1")
        self.white_team_var = tk.StringVar(value="White")
        self.black_team_var = tk.StringVar(value="Black")
        self.referee_timeout_timer_var = tk.StringVar(value="Ref Time-Out")
        
        # Tournament List tracking
        self.current_game_index = 0  # Index in self.game_numbers list
        
        self.engine.start_timer()
        self.engine.set_timer_seconds(0)

        # Court time system
        self.court_time_seconds = None  # Will be synchronized to local time at startup/reset
        self.court_time_job = None
        self.court_time_paused = False

        self.timer_job = None
        self.reset_timer_button = None
        self.in_timeout = False
        self.pending_timeout = None
        self.sudden_death_timer_job = None
        self.engine.sudden_death_seconds = 0
        self.widgets = []
        self.last_valid_values = {}
        self.team_timeouts_allowed_var = tk.BooleanVar(value=self.variables["team_timeouts_allowed"]["default"])
        self.overtime_allowed_var = tk.BooleanVar(value=self.variables["overtime_allowed"]["default"])
        self.record_scorers_cap_number_var = tk.BooleanVar(value=self.variables["record_scorers_cap_number"]["default"])
        self.show_display_screen_var = tk.BooleanVar(value=True)
        self.referee_timeout_active = False
        self.referee_timeout_elapsed = 0
        self.referee_timeout_default_bg = "red"
        self.referee_timeout_default_fg = "black"
        self.referee_timeout_active_bg = "black"
        self.referee_timeout_active_fg = "red"
        
        # Penalty timer system
        self.penalty_timers_paused = False
        self.penalty_timer_jobs = []
        
        # Store last position of penalties dialog (None means use default positioning)
        self.penalty_dialog_last_position = None

        # Initialize volume variables for sounds - load from settings
        sound_settings = load_sound_settings()
        self.pips_volume = tk.DoubleVar(value=sound_settings.get("pips_volume", 50.0))
        self.siren_volume = tk.DoubleVar(value=sound_settings.get("siren_volume", 50.0))
        self.air_volume = tk.DoubleVar(value=sound_settings.get("air_volume", 50.0))
        self.water_volume = tk.DoubleVar(value=sound_settings.get("water_volume", 50.0))
        self.enable_sound = tk.BooleanVar(value=sound_settings.get("enable_sound", True))
        self.siren_duration = tk.DoubleVar(value=sound_settings.get("siren_duration", 1.5))
        
        # Initialize sound selection variables with auto-selection of first audio file if no saved setting
        sound_files = get_sound_files()
        available_audio_files = sound_files if sound_files != ["No sound files found"] else []
        
        pips_default = sound_settings.get("pips_sound", "Default")
        siren_default = sound_settings.get("siren_sound", "Default")
        
        # If no saved setting and audio files are available, pick the first one
        if pips_default == "Default" and available_audio_files:
            pips_default = available_audio_files[0]
        if siren_default == "Default" and available_audio_files:
            # Try to default to siren-police.mp3 if available, otherwise use first available
            if "siren-police.mp3" in available_audio_files:
                siren_default = "siren-police.mp3"
            else:
                siren_default = available_audio_files[0]
            
        self.pips_var = tk.StringVar(value=pips_default)
        self.siren_var = tk.StringVar(value=siren_default)
        
        # Preload all sound files into memory for instant playback
        preload_sounds()
        
        # Track audio device warning to prevent loops
        self.audio_device_warning_shown = False

        # ========== MQTT CONNECTION STABILITY CHECK ==========
        # Pause initialization until MQTT network is completely stable
        # This prevents race conditions with audio and hardware detection
        print("\nSTARTUP: Waiting for MQTT network stability check...")
        
        # Create a splash screen to show initialization progress
        splash = tk.Toplevel(master)
        splash.transient(master)
        splash.attributes("-topmost", True)
        splash.lift()
        splash.focus_force()
        splash.grab_set()
        splash.title("Initializing UWH Scoring Desk")
        splash_width = 520
        splash_height = 700
        
        splash.resizable(False, False)
        
        # Position splash screen
        splash.update_idletasks()
        x = (splash.winfo_screenwidth() - splash_width) // 2
        y = splash.winfo_screenheight() // 5
        
        splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

        splash_title = tk.Label(
            splash,
            text="Underwater Hockey Scoring Desk",
            font=("Arial", 13, "bold")
        )
        splash_title.pack(pady=(12, 6))

        splash_status = tk.Label(
            splash,
            text="Startup self-test",
            font=("Arial", 10, "bold")
        )
        splash_status.pack(pady=(0, 6))

        splash_log_frame = tk.Frame(splash)
        splash_log_frame.pack(fill="both", expand=True, padx=18, pady=8)

        splash_log = tk.Text(
            splash_log_frame,
            height=13,
            width=62,
            font=("Consolas", 9),
            state="disabled",
            wrap="word"
        )
        splash_log.pack(fill="both", expand=True)

        def splash_report(message, ok=True):
            prefix = "✓" if ok else "!"
            line = f"{prefix} {message}\n"

            try:
                splash_log.config(state="normal")
                splash_log.insert("end", line)
                splash_log.see("end")
                splash_log.config(state="disabled")
                splash.update_idletasks()
                splash.update()
            except tk.TclError:
                pass

            print(f"STARTUP SELF-TEST: {message}")

        def close_splash_after_final_check():
            try:
                splash_status.config(text="Startup complete")
                splash_report("Startup complete - opening application", True)
        
                def finish_startup():
                    splash.destroy()
        
                    self.master.lift()
                    self.master.focus_force()
        
                splash.after(2000, finish_startup)
        
            except tk.TclError:
                pass

        splash_report("Game engine loaded", True)
        splash_report("Settings system available", True)

        startup_selftest.report_installation_status(
            splash_report
        )

        # Perform MQTT stability check
        mqtt_connection_stable = startup_selftest.check_mqtt_stability(
            splash_report=splash_report,
            is_mqtt_available=is_mqtt_available,
            timeout_seconds=30,
            stable_threshold=3
        )

        # AUTO-DETECT ARDUINO AND ZIGBEE PORTS
        try:
            splash_report("Starting hardware auto-detection", True)
            print("Starting hardware auto-detection...")

            try:
                import serial_siren_listener
                ports = serial_siren_listener.get_detected_ports()
                arduino_com = ports.get("arduino_port")
                zigbee_com = ports.get("zigbee_port")
            except Exception:
                arduino_com, zigbee_com = auto_detect_com_ports()

            splash_report(f"Arduino detected: {arduino_com}", bool(arduino_com))
            splash_report(f"Zigbee reserved: {zigbee_com}", bool(zigbee_com))
            print(f"Assignment Complete -> Arduino: {arduino_com} | Zigbee: {zigbee_com}")

        except Exception as e:
            splash_report(f"Hardware auto-detection failed: {e}", False)
            print(f"Error during port auto-detection: {e}")
            arduino_com, zigbee_com = "COM5", "COM6"

        self.arduino_port = arduino_com
        self.zigbee_port = zigbee_com
        self.last_hardware_detection = load_hardware_detection_cache()

        # 1. INSTANTIATE ALL GUI TRACKING VARIABLES FIRST
        self.zigbee_status_var = tk.StringVar(value="Connecting...")
        self.siren_loop_active = False
        self.arduino_siren_channel = None
        self.connection_watchdog_active = False
        self.connection_watchdog_attempts = 0
        self.connection_watchdog_max_attempts = 3
        self.connection_watchdog_job = None
        self.user_initiated_action = False
        splash_report("GUI tracking variables initialized", True)

        # 2. INITIALIZE ZIGBEE CONTROLLER NOW THAT STATUS VARS EXIST
        self.zigbee_controller = ZigbeeSirenController(
            siren_callback=self.handle_hardware_siren_event,
            gui_log_callback=self.add_to_zigbee_log
        )
        self.zigbee_controller.set_connection_status_callback(self.update_zigbee_status)
        splash_report("Zigbee controller initialized", True)

        # 3. BUILD INTERFACE ARCHITECTURE
        self.create_scoreboard_tab()
        splash_report("Scoreboard tab created", True)

        self.create_settings_tab()
        splash_report("Settings tab created", True)

        self.create_sounds_tab()
        splash_report("Sounds tab created", True)

        self.create_zigbee_siren_tab()
        splash_report("Siren control tab created", True)

        # NOW start Zigbee AFTER all widgets exist
        print("STARTUP: Initializing Zigbee connection (MQTT stability verified)")
        try:
            self.zigbee_controller.start()
            splash_report("Zigbee controller started", True)
            print("STARTUP: Zigbee controller started successfully")
        except Exception as zigbee_init_err:
            splash_report(f"Zigbee controller start failed: {zigbee_init_err}", False)
            print(f"STARTUP: Zigbee controller start failed: {zigbee_init_err}")

        self.notebook.select(1)
        self.update_usb_dongle_status()
        self.monitor_usb_dongle_presence()
        self.monitor_arduino_presence()
        self.start_connection_watchdog()
        splash_report("Connection watchdog started", True)

        self.load_game_settings()
        splash_report("Game settings loaded", True)

        self.load_settings()
        splash_report("General settings loaded", True)

        self.build_game_sequence()
        splash_report("Game sequence built", True)

        self.master.bind('<Configure>', self.scale_fonts)
        self.initial_width = self.master.winfo_width()
        self.master.update_idletasks()
        self.scale_fonts(None)
        splash_report("Display scaling initialized", True)

        # Display window configurations
        self.create_display_window()
        splash_report("External display window created", True)

        self.start_penalty_display_updates()
        self.sync_penalty_display_to_external()
        splash_report("Penalty display synchronization started", True)

        self.reset_timer()
        splash_report("Timer initialized", True)

        # 4. FINAL APPLICATION HARDWARE INITIALIZATION HOOK
        try:
            import serial_siren_listener
            serial_siren_listener.start_serial_listener(self)
            splash_report("Serial siren listener started", True)
            if DEBUG_MODE:
                print("Serial hardware listener thread successfully active.")
        except Exception as e:
            splash_report(f"Serial siren listener failed: {e}", False)
            if DEBUG_MODE:
                print(f"Failed to initialize serial button module thread: {e}")

        close_splash_after_final_check()
        # ─────────────────────────────────────────────────────────────────────
    
    def log_game_event(self, event_type, team=None, cap_number=None, duration=None, break_status=None):
        return game_logging.log_game_event(
            base_dir=BASE_DIR,
            court_time_seconds=self.court_time_seconds,
            event_type=event_type,
            team=team,
            cap_number=cap_number,
            duration=duration,
            break_status=break_status,
            debug_mode=DEBUG_MODE
        )
        
    def write_game_results_to_csv(self, game_number, white_score, black_score, penalties):
        return csv_export.write_game_results_to_csv(
            csv_file=self.csv_var.get(),
            base_dir=BASE_DIR,
            game_number=game_number,
            white_score=white_score,
            black_score=black_score,
            penalties=penalties,
            record_scorers=self.record_scorers_cap_number_var.get(),
            white_goal_scorers=self.engine.white_goal_scorers,
            black_goal_scorers=self.engine.black_goal_scorers,
            debug_mode=DEBUG_MODE
        )
    
    def create_scoreboard_tab(self):
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
        
    def update_penalty_display(self):
        """
        Robustly ensures that the penalty grid is only shown if there are penalties left to serve,
        and that 'Game 1' label is shown otherwise.
        Applies to both main and display windows.
        """
        main_has_penalties = bool(self.engine.active_penalties or self.engine.stored_penalties)
        # Main window: show penalty grid if any penalties; otherwise show 'Game 1'
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
        try:
            display_has_penalties = bool(self.engine.active_penalties or self.engine.stored_penalties)
        
            if display_has_penalties:
        
                if self.display_game_label.winfo_exists() and self.display_game_label.winfo_ismapped():
                    self.display_game_label.grid_remove()
        
                if self.display_penalty_grid_frame.winfo_exists() and \
                   not self.display_penalty_grid_frame.winfo_ismapped():
                    self.display_penalty_grid_frame.grid(
                        row=2,
                        column=3,
                        columnspan=3,
                        padx=1,
                        pady=1,
                        sticky="nsew"
                    )
        
                self.update_display_penalty_grid()
        
            else:
        
                if self.display_penalty_grid_frame.winfo_exists():
                    self.display_penalty_grid_frame.grid_remove()
        
                if self.display_game_label.winfo_exists() and \
                   not self.display_game_label.winfo_ismapped():
                    self.display_game_label.grid(
                        row=2,
                        column=3,
                        columnspan=3,
                        padx=1,
                        pady=1,
                        sticky="nsew"
                    )
        
        except (AttributeError, tk.TclError):
            pass

    def _penalty_sort_key(self, p):
        return display_manager.penalty_sort_key(p)

    def update_penalty_grid(self):
        white_penalties = sorted(
            [p for p in self.engine.active_penalties if p["team"] == "White"],
            key=self._penalty_sort_key
        )[:3]
        black_penalties = sorted(
            [p for p in self.engine.active_penalties if p["team"] == "Black"],
            key=self._penalty_sort_key
        )[:3]
        for i in range(3):
            if i < len(white_penalties):
                p = white_penalties[i]
                label_text = display_manager.format_penalty_label(p)
            else:
                label_text = ""
            if self.penalty_labels[i][0].cget('text') != label_text:
                self.penalty_labels[i][0].config(text=label_text)
            if i < len(black_penalties):
                p = black_penalties[i]
                label_text = display_manager.format_penalty_label(p)
            else:
                label_text = ""
            if self.penalty_labels[i][1].cget('text') != label_text:
                self.penalty_labels[i][1].config(text=label_text)

    def update_display_penalty_grid(self):
        white_penalties = sorted(
            [p for p in self.engine.active_penalties if p["team"] == "White"],
            key=self._penalty_sort_key
        )[:3]
        black_penalties = sorted(
            [p for p in self.engine.active_penalties if p["team"] == "Black"],
            key=self._penalty_sort_key
        )[:3]
        for i in range(3):
            if i < len(white_penalties):
                p = white_penalties[i]
                label_text = display_manager.format_penalty_label(p)
            else:
                label_text = ""
            if self.display_penalty_labels[i][0].cget('text') != label_text:
                self.display_penalty_labels[i][0].config(text=label_text)
            if i < len(black_penalties):
                p = black_penalties[i]
                label_text = display_manager.format_penalty_label(p)
            else:
                label_text = ""
            if self.display_penalty_labels[i][1].cget('text') != label_text:
                self.display_penalty_labels[i][1].config(text=label_text)

    def start_penalty_display_updates(self):
        self.update_penalty_display()
        self.master.after(1000, self.start_penalty_display_updates)

    def sync_penalty_display_to_external(self):
        return display_manager.sync_penalty_display_to_external(self)

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
                cur_width = (
                    self.initial_width
                    if hasattr(self, "initial_width")
                    else 1200
                )

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
                new_size = int(
                    base_sizes[key]
                    * scale
                    * reduced_button_scale
                )
            else:
                new_size = int(
                    base_sizes[key]
                    * scale
                )

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
        game_starts_in_seconds = None
        if time_val:
            match = re.fullmatch(r"(?:[0-9]|1[0-9]|2[0-3]):[0-5][0-9]", time_val.strip())
            if match:
                hh, mm = map(int, time_val.strip().split(":"))
                target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                if target < now:
                    target = target + datetime.timedelta(days=1)
                delta = target - now
                seconds_to_start = int(delta.total_seconds())
                # Use the time directly without subtracting Between Game Break
                game_starts_in_seconds = max(0, seconds_to_start)
        # First period: "First Game Starts In:" - only runs once at app start
        if game_starts_in_seconds is not None:
            seq.append({'name': 'First Game Starts In:', 'type': 'break', 'duration': game_starts_in_seconds})
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
        self.engine.set_sequence(seq)
        
    def create_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Game Variables")

        tab.grid_rowconfigure(0, weight=3)
        tab.grid_rowconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        tab.grid_rowconfigure(3, weight=1)
        tab.grid_columnconfigure(0, weight=2)
        tab.grid_columnconfigure(1, weight=1)

        default_font = font.nametofont("TkDefaultFont")
        new_size = default_font.cget("size") + 2
        small_size = default_font.cget("size") - 1
        headers = ["Use?", "Variable", "Value", "Units"]

        style = ttk.Style()
        style.configure(
            "Large.TCheckbutton",
            focuscolor="none",
            font=(default_font.cget("family"), default_font.cget("size") + 2)
        )

        # ------------------------------------------------------------
        # Widget 1 - Game Variables
        # ------------------------------------------------------------
        widget1 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget1.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=8, pady=8)

        for i in range(4):
            widget1.grid_columnconfigure(i, weight=1)

        for i in range(17):
            widget1.grid_rowconfigure(i, weight=1)

        for i, h in enumerate(headers):
            tk.Label(
                widget1,
                text=h,
                font=(default_font.cget("family"), new_size, "bold")
            ).grid(row=0, column=i, sticky="w", padx=5, pady=4)

        row_idx = 1
        self.widgets = []

        entry_order = list(self.variables.keys())

        for special_name in [
            "time_to_start_first_game",
            "start_first_game_in",
            "record_scorers_cap_number"
        ]:
            if special_name in entry_order:
                entry_order.remove(special_name)

        crib_time_index = (
            entry_order.index("crib_time")
            if "crib_time" in entry_order
            else len(entry_order)
        )

        entry_order = (
            ["time_to_start_first_game", "start_first_game_in"]
            + entry_order[:crib_time_index]
            + ["record_scorers_cap_number"]
            + entry_order[crib_time_index:]
        )

        for var_name in entry_order:
            var_info = self.variables[var_name]

            if (
                var_info["checkbox"]
                and var_name in [
                    "team_timeouts_allowed",
                    "overtime_allowed",
                    "record_scorers_cap_number"
                ]
            ):
                var_info["default"] = var_info.get("default", True)

            if var_name == "team_timeouts_allowed":
                check_var = self.team_timeouts_allowed_var
                cb = ttk.Checkbutton(
                    widget1,
                    variable=check_var,
                    style="Large.TCheckbutton"
                )
                cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))

                label_widget = tk.Label(
                    widget1,
                    text=var_info.get("label", "Team Time-Outs allowed?"),
                    font=(default_font.cget("family"), new_size, "bold")
                )
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)

                check_var.trace_add(
                    "write",
                    lambda *args: self._on_team_timeouts_change()
                )

                self.widgets.append({
                    "name": var_name,
                    "entry": None,
                    "checkbox": check_var,
                    "label_widget": label_widget
                })

                row_idx += 1
                continue

            if var_name == "overtime_allowed":
                check_var = self.overtime_allowed_var
                cb = ttk.Checkbutton(
                    widget1,
                    variable=check_var,
                    style="Large.TCheckbutton"
                )
                cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))

                label_widget = tk.Label(
                    widget1,
                    text=var_info.get("label", "Overtime allowed?"),
                    font=(default_font.cget("family"), new_size, "bold")
                )
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)

                check_var.trace_add(
                    "write",
                    lambda *args: self._on_overtime_change()
                )

                self.widgets.append({
                    "name": var_name,
                    "entry": None,
                    "checkbox": check_var,
                    "label_widget": label_widget
                })

                row_idx += 1
                continue

            if var_name == "record_scorers_cap_number":
                check_var = self.record_scorers_cap_number_var
                cb = ttk.Checkbutton(
                    widget1,
                    variable=check_var,
                    style="Large.TCheckbutton"
                )
                cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))

                label_widget = tk.Label(
                    widget1,
                    text=var_info.get("label", "Record Scorers Cap Number"),
                    font=(default_font.cget("family"), new_size, "bold")
                )
                label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)

                check_var.trace_add(
                    "write",
                    lambda *args: self._on_single_variable_change(
                        "record_scorers_cap_number"
                    )
                )

                self.widgets.append({
                    "name": var_name,
                    "entry": None,
                    "checkbox": check_var,
                    "label_widget": label_widget
                })

                row_idx += 1
                continue

            check_var = tk.BooleanVar(value=True) if var_info["checkbox"] else None

            if check_var:
                cb = ttk.Checkbutton(
                    widget1,
                    variable=check_var,
                    style="Large.TCheckbutton"
                )
                cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))
                check_var.trace_add(
                    "write",
                    lambda *args, name=var_name: self._on_single_variable_change(name)
                )

            label_text = var_info.get(
                "label",
                f"{var_name.replace('_', ' ').title()}:"
            )

            label_widget = tk.Label(
                widget1,
                text=label_text,
                font=(default_font.cget("family"), new_size, "bold")
            )
            label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)

            entry = ttk.Entry(widget1, width=10)

            if var_name == "time_to_start_first_game":
                entry.insert(0, "")

                def validate_hhmm_on_focusout(event):
                    val = event.widget.get().strip()

                    if val == "":
                        return

                    if not re.fullmatch(
                        r"(?:[0-9]|1[0-9]|2[0-3]):[0-5][0-9]",
                        val
                    ):
                        messagebox.showerror(
                            "Input Error",
                            "Please enter time in HH:MM 24-hour format "
                            "(e.g., 19:36 or 9:36)."
                        )
                        event.widget.focus_set()
                        event.widget.selection_range(0, tk.END)
                        return

                    self._on_single_variable_change("time_to_start_first_game")

                entry.bind("<FocusOut>", validate_hhmm_on_focusout)
                entry.bind("<Return>", validate_hhmm_on_focusout)

            else:
                entry.insert(0, "1")

                if var_name in ["crib_time", "sudden_death_game_break"]:

                    def validate_numeric_on_focusout(event, field_name=var_name):
                        val = event.widget.get().strip()

                        if val == "":
                            return

                        try:
                            val_normalized = val.replace(",", ".")
                            val_float = float(val_normalized)

                            if field_name == "crib_time":
                                between_game_break_minutes = None

                                for widget in self.widgets:
                                    if widget["name"] == "between_game_break":
                                        try:
                                            bgb_val = (
                                                widget["entry"]
                                                .get()
                                                .strip()
                                                .replace(",", ".")
                                            )
                                            between_game_break_minutes = float(bgb_val)
                                        except (ValueError, AttributeError):
                                            pass
                                        break

                                if between_game_break_minutes is not None:
                                    crib_time_seconds = val_float

                                    if (
                                        between_game_break_minutes * 60
                                    ) - crib_time_seconds <= 31:
                                        messagebox.showerror(
                                            "Input Error",
                                            "Crib time too large. Between Game "
                                            "Break minus Crib time must be > "
                                            "31 seconds."
                                        )
                                        event.widget.delete(0, tk.END)
                                        event.widget.insert(
                                            0,
                                            self.last_valid_values[field_name]
                                        )
                                        event.widget.focus_set()
                                        event.widget.selection_range(0, tk.END)
                                        return

                            self.last_valid_values[field_name] = val
                            self._on_single_variable_change(field_name)

                        except ValueError:
                            messagebox.showerror(
                                "Input Error",
                                f"Please enter a valid number for "
                                f"{field_name.replace('_', ' ').title()}."
                            )
                            event.widget.delete(0, tk.END)
                            event.widget.insert(
                                0,
                                self.last_valid_values[field_name]
                            )
                            event.widget.focus_set()
                            event.widget.selection_range(0, tk.END)

                    entry.bind("<FocusOut>", validate_numeric_on_focusout)
                    entry.bind("<Return>", validate_numeric_on_focusout)

                else:
                    entry.bind(
                        "<FocusOut>",
                        lambda e, name=var_name: self._on_single_variable_change(name)
                    )
                    entry.bind(
                        "<Return>",
                        lambda e, name=var_name: self._on_single_variable_change(name)
                    )

            entry.grid(row=row_idx, column=2, sticky="w", padx=5, pady=4)

            tk.Label(
                widget1,
                text=var_info["unit"],
                font=(default_font.cget("family"), new_size, "bold")
            ).grid(row=row_idx, column=3, sticky="w", padx=5, pady=4)

            self.widgets.append({
                "name": var_name,
                "entry": entry,
                "checkbox": check_var,
                "label_widget": label_widget
            })

            self.last_valid_values[var_name] = entry.get()

            if var_name == "team_timeout_period":
                self.team_timeout_period_entry = entry
                self.team_timeout_period_label = label_widget

            row_idx += 1

            if var_name == "crib_time":
                combined_explanation = tk.Label(
                    widget1,
                    text=(
                        "• Crib Time is a period (in seconds) that is "
                        "subtracted from the \"Between Game Break\" time at "
                        "the start of each game\n"
                        "to try to realign Court Time with Local Computer Time.\n"
                        "• Value boxes accept decimal time e.g. 1.5 or 1,5 = "
                        "1 min, 30 sec"
                    ),
                    font=(default_font.cget("family"), small_size),
                    anchor="w",
                    justify="left",
                    wraplength=600
                )
                combined_explanation.grid(
                    row=row_idx,
                    column=0,
                    columnspan=4,
                    pady=3,
                    sticky="nsew"
                )

                row_idx += 1

                reset_warning_bullet = tk.Label(
                    widget1,
                    text=(
                        "• If you change any value in here, push the "
                        "'Reset Timer' Button!"
                    ),
                    font=(default_font.cget("family"), small_size, "bold"),
                    fg="red",
                    anchor="w",
                    justify="left",
                    wraplength=600
                )
                reset_warning_bullet.grid(
                    row=row_idx,
                    column=0,
                    columnspan=4,
                    pady=3,
                    sticky="nsew"
                )

                row_idx += 1

        self.reset_timer_button = ttk.Button(
            widget1,
            text="Reset Timer",
            command=self.reset_timer
        )
        self.reset_timer_button.grid(
            row=row_idx,
            column=0,
            columnspan=4,
            pady=8
        )

        # ------------------------------------------------------------
        # Widget 2 - Presets
        # ------------------------------------------------------------
        widget2 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget2.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

        for col in range(3):
            widget2.grid_columnconfigure(col, weight=1)

        widget2.grid_rowconfigure(0, weight=0)
        widget2.grid_rowconfigure(1, weight=0, minsize=38)
        widget2.grid_rowconfigure(2, weight=0, minsize=38)
        widget2.grid_rowconfigure(3, weight=1)
        widget2.grid_rowconfigure(4, weight=0)
        widget2.grid_rowconfigure(5, weight=0)

        header_label = tk.Label(
            widget2,
            text="Presets",
            font=(default_font.cget("family"), new_size, "bold")
        )
        header_label.grid(
            row=0,
            column=0,
            columnspan=3,
            padx=4,
            pady=(8, 4),
            sticky="nsew"
        )

        self.widget2_buttons = []
        preset_data = load_preset_settings()
        self.button_data = preset_data.copy()

        for i in range(6):
            btn_row = 1 if i < 3 else 2
            btn_col = i % 3

            btn = tk.Button(
                widget2,
                text=self.button_data[i]["text"],
                font=(
                    default_font.cget("family"),
                    default_font.cget("size") + 1,
                    "bold"
                ),
                width=12,
                height=1,
                relief="raised",
                borderwidth=2
            )

            btn.grid(
                row=btn_row,
                column=btn_col,
                padx=8,
                pady=4,
                sticky="nsew"
            )

            btn.bind("<ButtonPress-1>", self._make_press_handler(i))
            btn.bind("<ButtonRelease-1>", self._make_release_handler(i))

            self.widget2_buttons.append(btn)

        instruction1 = tk.Label(
            widget2,
            text="Click the buttons above to load preset times and allowed Game Periods",
            anchor="w",
            justify="left",
            font=(default_font.cget("family"), default_font.cget("size"))
        )
        instruction1.grid(
            row=4,
            column=0,
            columnspan=3,
            sticky="w",
            padx=8,
            pady=(4, 1)
        )

        instruction2 = tk.Label(
            widget2,
            text="Press and hold the button for >4 seconds to alter the stored preset values",
            anchor="w",
            justify="left",
            font=(default_font.cget("family"), default_font.cget("size"))
        )
        instruction2.grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="w",
            padx=8,
            pady=(1, 6)
        )

        # ------------------------------------------------------------
        # Widget 4 - Tournament List
        # ------------------------------------------------------------
        widget4 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget4.grid(row=2, column=1, sticky="nsew", padx=8, pady=8)

        widget4.grid_columnconfigure(0, weight=0)
        widget4.grid_columnconfigure(1, weight=1)
        widget4.grid_columnconfigure(2, weight=0)

        widget4.grid_rowconfigure(0, weight=0)
        widget4.grid_rowconfigure(1, weight=0)
        widget4.grid_rowconfigure(2, weight=0)
        widget4.grid_rowconfigure(3, weight=0)
        widget4.grid_rowconfigure(4, weight=1)

        tournament_header = tk.Label(
            widget4,
            text="Tournament List",
            font=(default_font.cget("family"), new_size, "bold")
        )
        tournament_header.grid(
            row=0,
            column=0,
            columnspan=3,
            padx=8,
            pady=(10, 8),
            sticky="ew"
        )

        tk.Label(
            widget4,
            text="CSV File:",
            font=(default_font.cget("family"), default_font.cget("size")),
            anchor="w"
        ).grid(row=1, column=0, sticky="w", padx=8, pady=2)

        csv_files = self.get_csv_files()
        self.csv_var = tk.StringVar(
            value=csv_files[0] if csv_files else "No CSV files found"
        )

        self.csv_dropdown = ttk.Combobox(
            widget4,
            textvariable=self.csv_var,
            values=csv_files,
            state="readonly",
            width=20,
            postcommand=self.refresh_csv_dropdown
        )
        self.csv_dropdown.grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=8,
            pady=2
        )

        self.csv_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_csv_file_changed
        )

        tk.Label(
            widget4,
            text="Starting Game #:",
            font=(default_font.cget("family"), default_font.cget("size")),
            anchor="w"
        ).grid(row=2, column=0, sticky="w", padx=8, pady=(8, 2))

        self.game_numbers = []
        self.starting_game_var = tk.StringVar(value="")

        self.starting_game_dropdown = ttk.Combobox(
            widget4,
            textvariable=self.starting_game_var,
            values=self.game_numbers,
            state="readonly",
            width=6
        )
        self.starting_game_dropdown.grid(
            row=2,
            column=1,
            sticky="w",
            padx=8,
            pady=(8, 2)
        )

        open_folder_btn = tk.Button(
            widget4,
            text="Open Folder",
            font=(
                default_font.cget("family"),
                default_font.cget("size")
            ),
            command=self.open_csv_folder,
            width=12
        )
        open_folder_btn.grid(
            row=2,
            column=2,
            sticky="e",
            padx=8,
            pady=(8, 2)
        )

        self.starting_game_dropdown.bind(
            "<<ComboboxSelected>>",
            self.on_game_selection_changed
        )

        self.on_csv_file_changed()

        csv_comment = tk.Label(
            widget4,
            text=(
                "Save a CSV file of games into the same folder as this program is in.\n"
                "Expected CSV headers: date,#,White,Score,Black,Score,"
                "Referees,Penalties,Comments\n"
                "(where # is the Game Number)"
            ),
            font=(default_font.cget("family"), small_size),
            anchor="nw",
            justify="left",
            wraplength=600
        )
        csv_comment.grid(
            row=3,
            column=0,
            columnspan=3,
            sticky="nw",
            padx=8,
            pady=(8, 4)
        )

        show_display_checkbox = ttk.Checkbutton(
            widget4,
            text="Show Display Screen",
            variable=self.show_display_screen_var,
            command=self.toggle_display_screen,
            style="Large.TCheckbutton"
        )
        show_display_checkbox.grid(
            row=4,
            column=0,
            columnspan=3,
            sticky="w",
            padx=8,
            pady=(4, 8)
        )

        # ------------------------------------------------------------
        # Widget 3 - Game Sequence
        # ------------------------------------------------------------
        widget3 = ttk.Frame(tab, borderwidth=1, relief="solid")
        widget3.grid(row=3, column=1, sticky="nsew", padx=8, pady=8)

        widget3.grid_columnconfigure(0, weight=1)
        widget3.grid_rowconfigure(0, weight=0)
        widget3.grid_rowconfigure(1, weight=1)

        explanation_header = tk.Label(
            widget3,
            text="Game Sequence",
            font=(default_font.cget("family"), new_size, "bold")
        )
        explanation_header.grid(
            row=0,
            column=0,
            padx=4,
            pady=(8, 2),
            sticky="ew"
        )

        explanation_text = (
            "Game Sequence Flow:\n"
            "1. First Game Starts In: (runs once at app start)\n"
            "2. First Half → Half Time → Second Half\n"
            "3. If scores tied: Overtime Game Break → Overtime First Half "
            "→ Overtime Half Time → Overtime Second Half (if enabled)\n"
            "4. If still tied: Sudden Death Game Break → Sudden Death (if enabled)\n"
            "5. Between Game Break (loop back to step 2)\n\n"
            "Important Notes:\n"
            "• 'First Game Starts In:' transitions directly to First Half\n"
            "• Crib time is subtracted from Between Game Break"
        )

        explanation_label = tk.Label(
            widget3,
            text=explanation_text,
            font=(default_font.cget("family"), small_size),
            justify="left",
            anchor="nw"
        )
        explanation_label.grid(
            row=1,
            column=0,
            padx=4,
            pady=(2, 4),
            sticky="nsew"
        )

        self.update_overtime_variables_state()

    def get_csv_files(self):
        return csv_ui.get_csv_files(
            BASE_DIR
        )

    def refresh_csv_dropdown(self):
        return csv_ui.refresh_csv_dropdown(self)
        
    def parse_csv_game_numbers(self, csv_filename):
        return csv_helpers.parse_csv_game_numbers(
            csv_filename,
            BASE_DIR
        )

    def parse_csv_team_names(
        self,
        csv_filename,
        game_number
    ):
        return csv_helpers.parse_csv_team_names(
            csv_filename,
            game_number,
            BASE_DIR
        )

    def get_goal_events_for_game(self, game_number):
        return csv_export.get_goal_events_for_game(
            BASE_DIR,
            game_number
        )
    
    def aggregate_goal_scorers(self, goal_events):
        return csv_export.aggregate_goal_scorers(
            goal_events
        )
    
    def format_goal_scorers_comment(self, scorers):
        return csv_export.format_goal_scorers_comment(
            scorers
        )
    
    def _sort_cap_key(self, cap_number):
        return csv_export.sort_cap_key(cap_number)

    def on_csv_file_changed(self, event=None):
        return game_flow.on_csv_file_changed(
            self,
            event
        )

    def get_current_game_number(self):
        return game_flow.get_current_game_number(self)

    def update_game_number_display(self):
        return game_flow.update_game_number_display(self)

    def update_team_names_display(self):
        """Update the team name widgets with data from CSV file."""
        try:
            current_game = self.get_current_game_number()
            csv_file = self.csv_var.get() if hasattr(self, "csv_var") else None

            white_team, black_team = self.parse_csv_team_names(
                csv_file,
                current_game
            )

            if hasattr(self, "white_team_name_widget"):
                self.white_team_name_widget.config(
                    text=white_team if white_team else ""
                )

            if hasattr(self, "black_team_name_widget"):
                self.black_team_name_widget.config(
                    text=black_team if black_team else ""
                )

        except Exception as e:
            print(f"Error updating team names display: {e}")

            if hasattr(self, "white_team_name_widget"):
                self.white_team_name_widget.config(text="")

            if hasattr(self, "black_team_name_widget"):
                self.black_team_name_widget.config(text="")
                
    def advance_to_next_game(self):
        return game_flow.advance_to_next_game(self)

    def on_game_selection_changed(self, event=None):
        return game_flow.on_game_selection_changed(self, event)

    def open_csv_folder(self):
        """Open the folder containing CSV files in the system file manager."""
        # CHANGED: Use BASE_DIR instead of os.getcwd() so it always opens the folder containing the EXE and CSVs
        csv_folder = BASE_DIR
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
                # Get current settings
                sound_file = self.pips_var.get()
                pips_vol = self.pips_volume.get()
                air_vol = self.air_volume.get()
                water_vol = self.water_volume.get()
                sound_enabled = self.enable_sound.get()
                
                # Log test start
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                log_msg = f"[{timestamp}] Pips sound test started: file='{sound_file}', pips_vol={pips_vol}%, air_vol={air_vol}%, water_vol={water_vol}%, sound_enabled={sound_enabled}"
                print(log_msg)
                self.add_to_zigbee_log(f"Pips test: {sound_file} (Vol: {pips_vol}%, Air: {air_vol}%, Water: {water_vol}%)")
                
                # Check audio device availability
                audio_available = check_audio_device_available(self.enable_sound)
                device_msg = f"[{timestamp}] Audio device available: {audio_available}"
                print(device_msg)
                self.add_to_zigbee_log(f"Audio device available: {audio_available}")
                
                # Play the sound
                play_sound_with_volume(self.pips_var.get(), "pips", 
                    self.enable_sound, self.pips_volume, self.siren_volume, 
                    self.air_volume, self.water_volume, self.siren_duration)
                
                # Log successful playback initiation
                success_msg = f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Pips sound playback initiated successfully"
                print(success_msg)
                self.add_to_zigbee_log("Pips sound playback initiated successfully")
                
            except Exception as e:
                error_timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                error_msg = f"[{error_timestamp}] Error testing pips sound: {type(e).__name__}: {e}"
                print(error_msg)
                self.add_to_zigbee_log(f"ERROR testing pips: {type(e).__name__}: {e}")
        
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
        
        # Row 3, column 3: Pips volume value label
        pips_vol_label = tk.Label(sounds_widget, text=f"{self.pips_volume.get()}%", 
                                  font=("Arial", 11), width=5)
        pips_vol_label.grid(row=3, column=3, sticky="w")
        
        # Add interaction detection for pips volume slider
        def on_pips_slider_interaction(event=None):
            # Update volume label
            pips_vol_label.config(text=f"{self.pips_volume.get()}%")
            # Check audio device when user interacts with volume slider
            if not check_audio_device_available(self.enable_sound):
                self.audio_device_warning_shown = handle_no_audio_device_warning(
                    self.pips_var, "pips volume", self.enable_sound, self.audio_device_warning_shown)
        
        pips_vol_slider.bind("<Button-1>", on_pips_slider_interaction)
        pips_vol_slider.bind("<B1-Motion>", on_pips_slider_interaction)
        pips_vol_slider.bind("<ButtonRelease-1>", on_pips_slider_interaction)

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
                # Get current settings
                sound_file = self.siren_var.get()
                siren_vol = self.siren_volume.get()
                air_vol = self.air_volume.get()
                water_vol = self.water_volume.get()
                sound_enabled = self.enable_sound.get()
                
                # Log test start
                timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                log_msg = f"[{timestamp}] Siren sound test started: file='{sound_file}', siren_vol={siren_vol}%, air_vol={air_vol}%, water_vol={water_vol}%, sound_enabled={sound_enabled}"
                print(log_msg)
                self.add_to_zigbee_log(f"Siren test: {sound_file} (Vol: {siren_vol}%, Air: {air_vol}%, Water: {water_vol}%)")
                
                # Check audio device availability
                audio_available = check_audio_device_available(self.enable_sound)
                device_msg = f"[{timestamp}] Audio device available: {audio_available}"
                print(device_msg)
                self.add_to_zigbee_log(f"Audio device available: {audio_available}")
                
                # Play the sound
                play_sound_with_volume(self.siren_var.get(), "siren",
                    self.enable_sound, self.pips_volume, self.siren_volume,
                    self.air_volume, self.water_volume, self.siren_duration)
                
                # Log successful playback initiation
                success_msg = f"[{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Siren sound playback initiated successfully"
                print(success_msg)
                self.add_to_zigbee_log("Siren sound playback initiated successfully")
                
            except Exception as e:
                error_timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
                error_msg = f"[{error_timestamp}] Error testing siren sound: {type(e).__name__}: {e}"
                print(error_msg)
                self.add_to_zigbee_log(f"ERROR testing siren: {type(e).__name__}: {e}")
        
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
        
        # Row 6, column 3: Siren volume value label
        siren_vol_label = tk.Label(sounds_widget, text=f"{self.siren_volume.get()}%", 
                                   font=("Arial", 11), width=5)
        siren_vol_label.grid(row=6, column=3, sticky="w")
        
        # Add interaction detection for siren volume slider
        def on_siren_slider_interaction(event=None):
            # Update volume label
            siren_vol_label.config(text=f"{self.siren_volume.get()}%")
            # Check audio device when user interacts with volume slider
            if not check_audio_device_available(self.enable_sound):
                self.audio_device_warning_shown = handle_no_audio_device_warning(
                    self.siren_var, "siren volume", self.enable_sound, self.audio_device_warning_shown)
        
        siren_vol_slider.bind("<Button-1>", on_siren_slider_interaction)
        siren_vol_slider.bind("<B1-Motion>", on_siren_slider_interaction)
        siren_vol_slider.bind("<ButtonRelease-1>", on_siren_slider_interaction)

        # Row 7, column 0: "Number of seconds to play Siren"
        tk.Label(sounds_widget, text="Number of seconds to play Siren", font=("Arial", 11)).grid(row=7, column=0, sticky="ew")

        # Row 7, column 1, columnspan=2: Siren duration entry
        siren_duration_entry = tk.Entry(sounds_widget, textvariable=self.siren_duration, font=("Arial", 11), width=10)
        siren_duration_entry.grid(row=7, column=1, columnspan=2, sticky="w", padx=(0, 10))
        
        # Validate siren duration input - accept digits, period, and comma
        def validate_siren_duration(new_value):
            if new_value == "":
                return True
            # Replace comma with period for decimal separator
            test_value = new_value.replace(',', '.')
            try:
                float(test_value)
                return True
            except ValueError:
                return False
        
        vcmd = (sounds_widget.register(validate_siren_duration), '%P')
        siren_duration_entry.config(validate='key', validatecommand=vcmd)
        
        # Normalize comma to period on focus out
        def normalize_siren_duration(event=None):
            try:
                current_value = self.siren_duration.get()
                # This will automatically handle the conversion
            except tk.TclError:
                # If the value is invalid, reset to default
                self.siren_duration.set(1.5)
        
        siren_duration_entry.bind("<FocusOut>", normalize_siren_duration)
        siren_duration_entry.bind("<Return>", normalize_siren_duration)

        # Air slider: row=2, column=4, rowspan=5, sticky="ns" (no text)
        air_vol_slider = tk.Scale(
            sounds_widget, from_=100, to=0, orient="vertical", variable=self.air_volume,
            font=("Arial", 10), showvalue=False
        )
        air_vol_slider.grid(row=2, column=4, rowspan=5, sticky="ns")
        
        # Row 8, column 4: Air volume value label
        air_vol_label = tk.Label(sounds_widget, text=f"{self.air_volume.get()}%", 
                                 font=("Arial", 11))
        air_vol_label.grid(row=8, column=4, sticky="n")
        
        # Add interaction detection for air volume slider
        def on_air_slider_interaction(event=None):
            # Update volume label
            air_vol_label.config(text=f"{self.air_volume.get()}%")
            # Check audio device when user interacts with volume slider
            if not check_audio_device_available(self.enable_sound):
                self.audio_device_warning_shown = handle_no_audio_device_warning(
                    tk.StringVar(value="Default"), "air volume", self.enable_sound, self.audio_device_warning_shown)
        
        air_vol_slider.bind("<Button-1>", on_air_slider_interaction)
        air_vol_slider.bind("<B1-Motion>", on_air_slider_interaction)
        air_vol_slider.bind("<ButtonRelease-1>", on_air_slider_interaction)

        # Water slider: row=2, column=5, rowspan=5, sticky="ns" (no text)
        water_vol_slider = tk.Scale(
            sounds_widget, from_=100, to=0, orient="vertical", variable=self.water_volume,
            font=("Arial", 10), showvalue=False
        )
        water_vol_slider.grid(row=2, column=5, rowspan=5, sticky="ns")
        
        # Row 8, column 5: Water volume value label
        water_vol_label = tk.Label(sounds_widget, text=f"{self.water_volume.get()}%", 
                                   font=("Arial", 11))
        water_vol_label.grid(row=8, column=5, sticky="n")
        
        # Add interaction detection for water volume slider
        
        def on_water_slider_interaction(event=None):
            # Update volume label
            water_vol_label.config(text=f"{self.water_volume.get()}%")
            # Check audio device when user interacts with volume slider
            if not check_audio_device_available(self.enable_sound):
                self.audio_device_warning_shown = handle_no_audio_device_warning(
                    tk.StringVar(value="Default"), "water volume", self.enable_sound, self.audio_device_warning_shown)
        
        water_vol_slider.bind("<Button-1>", on_water_slider_interaction)
        water_vol_slider.bind("<B1-Motion>", on_water_slider_interaction)
        water_vol_slider.bind("<ButtonRelease-1>", on_water_slider_interaction)

        # Row 9, column 0, columnspan=6: Windows volume warning
        warning_label = tk.Label(sounds_widget, 
                               text="These Volume controls do not work on Windows Machines, only Linux-based machines", 
                               font=("Arial", 9, "italic"), 
                               fg="gray")
        warning_label.grid(row=9, column=0, columnspan=6, sticky="ew", pady=(10, 0))

    def create_zigbee_siren_tab(self):
        return zigbee_ui.create_zigbee_siren_tab(self)
   
    def test_app_siren(self):
        """Test the app siren sound using the same path as timer sirens."""
    
        self.add_to_zigbee_log("Testing app siren sound...")
    
        try:
            play_sound_with_volume(
                self.siren_var.get(),
                "siren",
                self.enable_sound,
                self.pips_volume,
                self.siren_volume,
                self.air_volume,
                self.water_volume,
                self.siren_duration
            )
    
            self.add_to_zigbee_log("App siren sound started")
    
        except Exception as e:
            self.add_to_zigbee_log(f"App siren test failed: {e}")

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
        self._button_hold_widget = event.widget
    
        self._button_hold_timer = self.master.after(
            3000,
            lambda: self._open_button_dialog(idx, self._button_hold_widget)
        )

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


    def _open_button_dialog(self, idx, trigger_button=None):
        dialog_width = 400
        dialog_height = 700
        gap = 8
    
        dlg = tk.Toplevel(self.master)
        dlg.withdraw()  # Hide until fully built and positioned
        dlg.title(f"Button {idx + 1} Settings")
        dlg.resizable(False, False)
        dlg.transient(self.master)
    
        entries = {}
        checks = {}
        row_num = 0
        max_btn_text_len = 16
    
        tk.Label(
            dlg,
            text="Button Display Text:"
        ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
    
        btn_text_var = tk.StringVar(
            value=self.button_data[idx].get("text", str(idx + 1))
        )
    
        text_entry = ttk.Entry(
            dlg,
            textvariable=btn_text_var,
            width=max_btn_text_len
        )
        text_entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
    
        row_num += 1
    
        for widget in self.widgets:
            var_name = widget["name"]
            label = widget["label_widget"]
    
            # Skip these from preset dialog
            if var_name in ["time_to_start_first_game", "start_first_game_in"]:
                continue
    
            # Special handling for Sudden Death: checkbox plus value entry
            if var_name == "sudden_death_game_break":
                tk.Label(
                    dlg,
                    text="Sudden Death Allowed?"
                ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
    
                default_checkbox_val = self.variables[var_name].get("used", True)
                val = self.button_data[idx]["checkboxes"].get(
                    var_name,
                    default_checkbox_val
                )
    
                check_var = tk.BooleanVar(value=val)
                cb = ttk.Checkbutton(dlg, variable=check_var)
                cb.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
    
                checks[var_name] = check_var
                row_num += 1
    
                tk.Label(
                    dlg,
                    text="Sudden Death Game Break:"
                ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
    
                sudden_death_val = self.button_data[idx]["values"].get(
                    "sudden_death_game_break",
                    "1"
                )
    
                sudden_death_entry_var = tk.StringVar(value=sudden_death_val)
                sudden_death_entry = ttk.Entry(
                    dlg,
                    textvariable=sudden_death_entry_var,
                    width=10
                )
                sudden_death_entry.grid(
                    row=row_num,
                    column=1,
                    sticky="w",
                    padx=6,
                    pady=4
                )
    
                entries["sudden_death_game_break"] = sudden_death_entry_var
                row_num += 1
                continue
    
            tk.Label(
                dlg,
                text=label.cget("text")
            ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
    
            if widget["checkbox"] is not None:
                if idx == 0 and var_name in ["team_timeouts_allowed", "overtime_allowed"]:
                    val = True
                else:
                    default_checkbox_val = self.variables[var_name].get("used", True)
                    val = self.button_data[idx]["checkboxes"].get(
                        var_name,
                        default_checkbox_val
                    )
    
                check_var = tk.BooleanVar(value=val)
                cb = ttk.Checkbutton(dlg, variable=check_var)
                cb.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
    
                checks[var_name] = check_var
    
            else:
                if idx == 0 and var_name in [
                    "team_timeout_period",
                    "half_period",
                    "half_time_break",
                    "overtime_game_break",
                    "overtime_half_period",
                    "overtime_half_time_break",
                    "sudden_death_game_break",
                    "between_game_break",
                    "crib_time"
                ]:
                    val = self.button_data[idx]["values"].get(
                        var_name,
                        {
                            "team_timeout_period": "1",
                            "half_period": "15",
                            "half_time_break": "3",
                            "overtime_game_break": "3",
                            "overtime_half_period": "5",
                            "overtime_half_time_break": "1",
                            "sudden_death_game_break": "1",
                            "between_game_break": "5",
                            "crib_time": "60"
                        }.get(var_name, str(self.variables[var_name]["default"]))
                    )
                else:
                    default_entry_val = str(self.variables[var_name]["default"])
                    val = self.button_data[idx]["values"].get(
                        var_name,
                        default_entry_val
                    )
    
                entry_var = tk.StringVar(value=val)
                entry = ttk.Entry(dlg, textvariable=entry_var, width=10)
                entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
    
                entries[var_name] = entry_var
    
            row_num += 1
    
        # Crib Time entry below Crib Time checkbox and above Save button
        tk.Label(
            dlg,
            text="Crib Time (seconds):"
        ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)
    
        crib_time_val = self.button_data[idx]["values"].get("crib_time", "60")
        crib_time_entry_var = tk.StringVar(value=crib_time_val)
    
        crib_time_entry = ttk.Entry(
            dlg,
            textvariable=crib_time_entry_var,
            width=10
        )
        crib_time_entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)
    
        entries["crib_time"] = crib_time_entry_var
        row_num += 1
    
        def save_and_close():
            for v in entries:
                if v in ["time_to_start_first_game", "start_first_game_in"]:
                    continue
    
                try:
                    val = entries[v].get().replace(",", ".")
                    float(val)
                    self.button_data[idx]["values"][v] = val
                except ValueError:
                    continue
    
            for v in checks:
                self.button_data[idx]["checkboxes"][v] = checks[v].get()
    
            self.button_data[idx]["text"] = btn_text_var.get()[:max_btn_text_len]
            self.set_widget2_button_text(idx, self.button_data[idx]["text"])
    
            save_preset_settings(self.button_data)
    
            dlg.destroy()
    
        save_btn = ttk.Button(
            dlg,
            text="Save",
            command=save_and_close
        )
        save_btn.grid(row=row_num, column=0, columnspan=2, pady=16)
    
        # Position from the CURRENT live location of the held preset button.
        # The right edge of the popup sits just left of the button.
        dlg.update_idletasks()
    
        if trigger_button:
            button_x = trigger_button.winfo_rootx()
            button_y = trigger_button.winfo_rooty()
    
            popup_x = button_x - dialog_width - gap
            popup_y = button_y
        else:
            popup_x = self.master.winfo_rootx() + 100
            popup_y = self.master.winfo_rooty() + 100
    
        dlg.geometry(f"{dialog_width}x{dialog_height}+{popup_x}+{popup_y}")
    
        dlg.deiconify()
        dlg.wait_visibility()
        dlg.lift()
        dlg.focus_force()
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
        
        # Synchronize the two time fields unidirectionally
        if var_name == "time_to_start_first_game":
            # Update start_first_game_in when time_to_start_first_game changes
            self._update_start_first_game_in()
        elif var_name == "start_first_game_in":
            # Clear time_to_start_first_game when start_first_game_in changes
            # to ensure build_game_sequence uses start_first_game_in directly
            self.variables["time_to_start_first_game"]["value"] = ""
            for widget in self.widgets:
                if widget["name"] == "time_to_start_first_game":
                    widget["entry"].delete(0, tk.END)
                    break
        
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
            "enable_sound": self.enable_sound.get(),
            "siren_duration": self.siren_duration.get()
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
    def start_zigbee_connection(self):
        return zigbee_control.start_zigbee_connection(self)

    def stop_zigbee_connection(self):
        return zigbee_control.stop_zigbee_connection(self)

    def toggle_zigbee_connection(self):
        return zigbee_control.toggle_zigbee_connection(self)

    def test_zigbee_connection(self):
        return zigbee_control.test_zigbee_connection(self)

    def start_connection_watchdog(self):
        return zigbee_control.start_connection_watchdog(self)

    def stop_connection_watchdog(self):
        return zigbee_control.stop_connection_watchdog(self)

    def schedule_connection_check(self):
        return zigbee_control.schedule_connection_check(self)

    def check_connection_status(self):
        return zigbee_control.check_connection_status(self)

    def update_zigbee_status(self, connected: bool, message: str = ""):
        return zigbee_control.update_zigbee_status(self, connected, message)

    def update_usb_dongle_status(self):
        return zigbee_hardware_ui.update_usb_dongle_status(self)

    def monitor_usb_dongle_presence(self):
        return zigbee_hardware_ui.monitor_usb_dongle_presence(self)

    def monitor_arduino_presence(self):
        return zigbee_hardware_ui.monitor_arduino_presence(self)

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

    def show_hardware_diagnostics(self):
        """Display hardware detection diagnostics in a new window."""
        diag_window = tk.Toplevel(self.master)
        diag_window.title("Hardware Diagnostics")
        diag_window.geometry("500x400")
        
        # Title
        title = tk.Label(diag_window, text="Hardware Detection Diagnostics", 
                        font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        # Create scrollable text widget
        text_frame = tk.Frame(diag_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        diag_text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                           font=("Courier", 10), height=15, width=60)
        diag_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=diag_text.yview)
        
        # Gather diagnostics information
        diag_info = "HARDWARE DETECTION DIAGNOSTICS\n"
        diag_info += "=" * 50 + "\n\n"
        
        # Current Detection
        diag_info += "CURRENT SETTINGS:\n"
        diag_info += f"  Arduino Port:    {self.arduino_port}\n"
        diag_info += f"  Zigbee Port:     {self.zigbee_port}\n\n"
        
        # Last Cached Detection
        diag_info += "CACHED DETECTION (from settings.json):\n"
        if self.last_hardware_detection:
            diag_info += f"  Arduino Port:    {self.last_hardware_detection.get('arduino_port', 'N/A')}\n"
            diag_info += f"  Zigbee Port:     {self.last_hardware_detection.get('zigbee_port', 'N/A')}\n"
            diag_info += f"  Last Detected:   {self.last_hardware_detection.get('last_detected', 'N/A')}\n\n"
        else:
            diag_info += "  No cached detection found\n\n"
        
        # Connection Status
        diag_info += "CONNECTION STATUS:\n"
        try:
            import serial
            import serial.tools.list_ports
            
            ports = list(serial.tools.list_ports.comports())
            diag_info += f"  Available COM Ports: {len(ports)}\n"
            
            for port in ports:
                diag_info += f"\n    Port: {port.device}\n"
                diag_info += f"      Description: {port.description or 'N/A'}\n"
                diag_info += f"      HWID: {port.hwid or 'N/A'}\n"
        except Exception as e:
            diag_info += f"  Error scanning ports: {e}\n"
        
        diag_info += "\n\nZigbee Status:\n"
        if hasattr(self, 'zigbee_controller') and self.zigbee_controller:
            diag_info += f"  Connected: {self.zigbee_controller.connected}\n"
            diag_info += f"  MQTT Broker: {self.zigbee_controller.config.get('mqtt_broker', 'N/A')}\n"
            diag_info += f"  MQTT Port: {self.zigbee_controller.config.get('mqtt_port', 'N/A')}\n"
        
        diag_text.insert("1.0", diag_info)
        diag_text.config(state=tk.DISABLED)
        
        # Refresh button
        refresh_btn = tk.Button(diag_window, text="Refresh", 
                               command=lambda: self.show_hardware_diagnostics())
        refresh_btn.pack(pady=5)

    def re_detect_hardware(self):
        """Re-run hardware detection and update settings."""
        try:
            result = messagebox.askyesno("Re-detect Hardware",
                "This will scan for Arduino and Zigbee devices again.\n"
                "Continue?")
            if result:
                arduino_port, zigbee_port = auto_detect_com_ports()
                self.arduino_port = arduino_port
                self.zigbee_port = zigbee_port
                self.last_hardware_detection = load_hardware_detection_cache()
                
                messagebox.showinfo("Detection Complete",
                    f"Arduino: {arduino_port}\n"
                    f"Zigbee: {zigbee_port}\n\n"
                    f"Restart the application for changes to take effect.")
        except Exception as e:
            messagebox.showerror("Detection Error", f"Error during re-detection: {e}")

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
        try:
            if (
                hasattr(self, "display_window")
                and self.display_window is not None
                and self.display_window.winfo_exists()
            ):
                self.display_window.lift()
                self.display_window.focus_force()
                return
        except tk.TclError:
            self.display_window = None
    
        self.display_window = tk.Toplevel(self.master)
        self.display_window.title("Display Window")
        self.display_window.geometry('1200x800')
        self.display_window.protocol("WM_DELETE_WINDOW", self._on_display_window_close)

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
        """Safely sync display window background colors."""
        def sync_backgrounds():
            try:
                # Check if display window still exists before updating
                if self.display_window.winfo_exists():
                    self.display_half_label.config(bg=self.half_label.cget("bg"))
                    self.master.after(200, sync_backgrounds)
                # If window is closed, the loop stops automatically
            except (tk.TclError, AttributeError, RuntimeError):
                # Silently stop if widgets are destroyed
                pass
        
        sync_backgrounds()
    
    def reset_timer(self):
        self.white_score_var.set(0)
        self.black_score_var.set(0)

        self.engine.reset_to_first_period()
        self.engine.start_timer()
        self.engine.sudden_death_goal_scored = False

        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        if self.court_time_job:
            self.master.after_cancel(self.court_time_job)
            self.court_time_job = None

        if self.sudden_death_timer_job:
            self.master.after_cancel(self.sudden_death_timer_job)
            self.sudden_death_timer_job = None

        self.engine.sudden_death_seconds = 0

        # Rebuild game sequence to reflect any settings changes
        self.build_game_sequence()

        first_period = self.engine.get_first_period()

        if first_period:
            self.engine.set_timer_seconds(first_period["duration"])
            self.half_label_var.set(first_period["name"])
            self.update_half_label_background(first_period["name"])
        else:
            self.engine.set_timer_seconds(0)
            self.half_label_var.set("")

        self.update_timer_display()

        # Sync court time to local computer time at reset/startup.
        now = datetime.datetime.now()
        self.court_time_seconds = (
            now.hour * 3600 +
            now.minute * 60 +
            now.second
        )

        self.court_time_paused = False

        hours, remainder = divmod(self.court_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.court_time_var.set(
            f"Court Time is {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

        self.update_court_time()
        self.start_current_period()
            
    def update_court_time(self):
        if self.court_time_job is not None:
            self.master.after_cancel(self.court_time_job)
            self.court_time_job = None

        if self.court_time_seconds is None:
            now = datetime.datetime.now()
            self.court_time_seconds = (
                now.hour * 3600 +
                now.minute * 60 +
                now.second
            )

        if not self.court_time_paused:
            self.court_time_seconds += 1

        hours, remainder = divmod(self.court_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.court_time_var.set(
            f"Court Time is {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

        self.court_time_job = self.master.after(
            1000,
            self.update_court_time
        )

    def update_timer_display(self):
        if self.referee_timeout_active:
            self.timer_var.set(
                self.engine.format_seconds_as_mmss(
                    self.referee_timeout_elapsed
                )
            )
            return

        cur_period = self.engine.get_current_period()

        if cur_period and self.engine.is_sudden_death(cur_period["name"]):
            self.timer_var.set(
                self.engine.format_seconds_as_mmss(
                    self.engine.sudden_death_seconds
                )
            )
            return

        self.timer_var.set(
            self.engine.format_seconds_as_mmss(
                self.engine.timer_seconds
            )
        )
        
    def adjust_between_game_break_for_crib_time(self):
        current_court_time = datetime.datetime.now() - datetime.timedelta(seconds=self.court_time_seconds)
        local_time = datetime.datetime.now()
        seconds_behind = int((local_time - current_court_time).total_seconds())
        if seconds_behind <= 0:
            return
        crib_time_var = self.variables['crib_time']
        crib_time = int(float(crib_time_var.get("value", crib_time_var["default"])))
        for idx in range(self.engine.current_index, len(self.engine.full_sequence)):
            period = self.engine.full_sequence[idx]
            if period['name'] == 'Between Game Break' and seconds_behind > 0:
                reduce_by = min(crib_time, seconds_behind, period['duration'])
                period['duration'] = max(0, period['duration'] - reduce_by)
                seconds_behind -= reduce_by
                if seconds_behind <= 0:
                    break

    def start_current_period(self):
        if self.engine.current_index >= len(self.engine.full_sequence):
            self.engine.reset_to_between_game_break()
        cur_period = self.engine.get_current_period()

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

        if self.engine.is_regular_timeout_reset_period(
            cur_period["name"]
        ):
            self.engine.reset_half_timeouts()

        # Event-driven: Update the StringVar instead of calling .config()
        self.half_label_var.set(cur_period['name'])
        self.update_half_label_background(cur_period['name'])

        TIMEOUTS_DISABLED_PERIODS = (
            self.engine.timeouts_disabled_periods()
        )
        
        # Always enable penalties during Referee Time-Out, even if entered from First Game Starts In:
        if self.engine.is_referee_timeout(cur_period["name"]):
            self.penalties_button.config(state=tk.NORMAL)
            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
        elif self.engine.is_timeout_disabled_period(cur_period["name"]):
            self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
            if self.engine.is_penalty_disabled_period(cur_period["name"]):
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

        if self.engine.is_penalty_pause_period(cur_period["name"]):
            self.pause_all_penalty_timers()
        else:
            self.resume_all_penalty_timers()

        if self.engine.is_court_time_paused_period(cur_period["name"]):
            self.court_time_paused = True
        else:
            self.court_time_paused = False
        if self.engine.is_sudden_death(
            cur_period["name"]
        ):
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None

            if self.sudden_death_timer_job:
                self.master.after_cancel(self.sudden_death_timer_job)
                self.sudden_death_timer_job = None

            self.engine.start_timer()
            self.engine.sudden_death_seconds = 0
            self.update_timer_display()

            event_name = self.engine.period_start_event_name(
                cur_period["name"]
            )

            if event_name:
                self.log_game_event(event_name)

            self.sudden_death_timer_job = self.master.after(
                1000,
                lambda: game_flow.start_sudden_death_timer(self)
            )
        else:
            self.engine.set_timer_seconds(
                cur_period['duration'] if cur_period['duration'] is not None else 0
            )
            self.update_timer_display()
            self.engine.start_timer()
        
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None
        
            self.timer_job = self.master.after(1000, self.countdown_timer)
            
            event_name = self.engine.period_start_event_name(
                cur_period["name"]
            )
    
            if event_name:
                self.log_game_event(event_name)

    def next_period(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        cur_period = self.engine.get_current_period()

        if cur_period:
            event_name = self.engine.period_end_event_name(
                cur_period["name"]
            )

            if event_name:
                self.log_game_event(event_name)

        self.engine.advance_period(
            self.white_score_var.get(),
            self.black_score_var.get()
        )

        self.start_current_period()

    def start_sudden_death_timer(self):
        if not self.engine.timer_running:
            return

        self.engine.sudden_death_seconds += 1
        self.update_timer_display()

        self.sudden_death_timer_job = self.master.after(
            1000,
            lambda: game_flow.start_sudden_death_timer(self)
        )

    def goto_between_game_break(self):
        self.engine.go_to_period('Between Game Break')
        self.start_current_period()

    def countdown_timer(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        if not self.engine.timer_running:
            self.update_timer_display()
            return

        if self.engine.timer_seconds > 0:
            cur_period = self.engine.get_current_period()

            if self.engine.should_play_period_end_siren(cur_period):
                try:
                    play_sound_with_volume(
                        self.siren_var.get(),
                        "siren",
                        self.enable_sound,
                        self.pips_volume,
                        self.siren_volume,
                        self.air_volume,
                        self.water_volume,
                        self.siren_duration
                    )
                except Exception as e:
                    print(f"Error playing period-end siren: {e}")

            if self.engine.should_export_game_results(cur_period):
                game_flow.export_and_reset_game_at_break(self)

            if self.engine.should_play_break_countdown_pip(cur_period):
                try:
                    play_sound_with_volume(
                        self.pips_var.get(),
                        "pips",
                        self.enable_sound,
                        self.pips_volume,
                        self.siren_volume,
                        self.air_volume,
                        self.water_volume,
                        self.siren_duration
                    )
                except Exception as e:
                    print(
                        f"Error playing break countdown pip at "
                        f"{self.engine.timer_seconds}s: {e}"
                    )

            self.engine.decrement_timer()
            self.update_timer_display()

            self.timer_job = self.master.after(
                1000,
                self.countdown_timer
            )

        else:
            self.next_period()

    def reset_timeouts_for_half(self):
        period = self.engine.get_current_period()
        if period['type'] in ['regular']:
            if self.engine.white_timeouts_this_half < 1:
                self.white_timeout_button.config(state=tk.NORMAL)
            else:
                self.white_timeout_button.config(state=tk.DISABLED)
            if self.engine.black_timeouts_this_half < 1:
                self.black_timeout_button.config(state=tk.NORMAL)
            else:
                self.black_timeout_button.config(state=tk.DISABLED)
        else:
            self.white_timeout_button.config(state=tk.DISABLED)
            self.black_timeout_button.config(state=tk.DISABLED)

    def white_team_timeout(self, preserve_saved_state=False):
        period = self.engine.get_current_period()
        # Immediately grey out (disable) the button when pressed
        self.white_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
        if period['type'] != 'regular' or not self.team_timeouts_allowed_var.get():
            return
        if self.in_timeout:
            if self.pending_timeout is None and self.engine.active_timeout_team != "white":
                self.pending_timeout = "white"
                status = f"{self.engine.active_timeout_team.capitalize()} Team Time-Out (White Pending)"
                # Event-driven: Update the StringVar instead of calling .config()
                self.half_label_var.set(status)
            return
        if self.engine.white_timeouts_this_half >= 1:
            self.show_timeout_popup("White")
            return
        
        self.in_timeout = True
        self.engine.start_timeout("White")
        self.court_time_paused = True
        if not preserve_saved_state:
            self.save_timer_state()
        self.pause_all_penalty_timers()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.engine.stop_timer()
        timeout_seconds = self.get_minutes('team_timeout_period')
        self.engine.set_timer_seconds(timeout_seconds)
        # Event-driven: Update the StringVar instead of calling .config()
        self.half_label_var.set("White Team Time-Out")
        self.update_half_label_background("White Team Time-Out")
        self.update_timer_display()
        self.timer_job = self.master.after(1000, self.timeout_countdown)

    def black_team_timeout(self, preserve_saved_state=False):
        period = self.engine.get_current_period()
        # Immediately grey out (disable) the button when pressed
        self.black_timeout_button.config(state=tk.DISABLED, bg="#d3d3d3", fg="#888")
        if period['type'] != 'regular' or not self.team_timeouts_allowed_var.get():
            return
        if self.in_timeout:
            if self.pending_timeout is None and self.engine.active_timeout_team != "black":
                self.pending_timeout = "black"
                status = f"{self.engine.active_timeout_team.capitalize()} Team Time-Out (Black Pending)"
                # Event-driven: Update the StringVar instead of calling .config()
                self.half_label_var.set(status)
            return
        if self.engine.black_timeouts_this_half >= 1:
            self.show_timeout_popup("Black")
            return
        
        self.in_timeout = True
        self.engine.start_timeout("Black")
        self.court_time_paused = True
        if not preserve_saved_state:
            self.save_timer_state()
        self.pause_all_penalty_timers()
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None
        self.engine.stop_timer()
        timeout_seconds = self.get_minutes('team_timeout_period')
        self.engine.set_timer_seconds(timeout_seconds)
        # Event-driven: Update the StringVar instead of calling .config()
        self.half_label_var.set("Black Team Time-Out")
        self.update_half_label_background("Black Team Time-Out")
        self.update_timer_display()
        self.timer_job = self.master.after(1000, self.timeout_countdown)

    def timeout_countdown(self):
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        if not self.in_timeout:
            self.update_timer_display()
            return

        if self.engine.timer_seconds > 0:
            # Enhancement: Play pip sound at 16 seconds.
            # Plays BEFORE decrementing, while display still shows 00:16.
            # Only play if no pending timeout exists.
            if self.engine.timer_seconds == 16 and self.pending_timeout is None:
                try:
                    play_sound_with_volume(
                        self.pips_var.get(),
                        "pips",
                        self.enable_sound,
                        self.pips_volume,
                        self.siren_volume,
                        self.air_volume,
                        self.water_volume,
                        self.siren_duration
                    )
                except Exception as e:
                    print(f"Error playing pip sound at 16s timeout: {e}")

            # Enhancement: Play end-of-timeout siren at 1 second.
            # Plays BEFORE decrementing, so the siren command is sent before
            # the screen changes from 00:01 to 00:00.
            # Only play if no pending timeout exists.
            if self.engine.timer_seconds == 1 and self.pending_timeout is None:
                try:
                    play_sound_with_volume(
                        self.siren_var.get(),
                        "siren",
                        self.enable_sound,
                        self.pips_volume,
                        self.siren_volume,
                        self.air_volume,
                        self.water_volume,
                        self.siren_duration
                    )
                except Exception as e:
                    print(f"Error playing siren at 1s timeout: {e}")

            # Decrement timer AFTER playing any sounds
            self.engine.decrement_timer()
            self.update_timer_display()

            self.timer_job = self.master.after(1000, self.timeout_countdown)

        else:
            self.end_timeout()

    def end_timeout(self):
        self.in_timeout = False
        prev_active_team = self.engine.active_timeout_team
        self.engine.end_timeout()
        self.court_time_paused = False
        self.resume_all_penalty_timers()
        state = self.engine.saved_state

        self.engine.timer_running = state["timer_running"]
        self.engine.timer_seconds = state["timer_seconds"]
        self.engine.current_index = state["current_index"]

        self.half_label_var.set(state["half_label"])
        self.half_label.config(bg=state["half_label_bg"])
        self.update_timer_display()

        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        # End-of-timeout siren is now played in timeout_countdown()
        # when timer_seconds == 1, before display changes to 00:00.
        # Do not play it here or it will be late / double-trigger.

        # If a pending timeout exists, start it now
        if self.pending_timeout is not None:
            if self.pending_timeout == "white" and self.engine.white_timeouts_this_half < 1:
                self.pending_timeout = None
                self.white_team_timeout(preserve_saved_state=True)
            elif self.pending_timeout == "black" and self.engine.black_timeouts_this_half < 1:
                self.pending_timeout = None
                self.black_team_timeout(preserve_saved_state=True)
            else:
                self.pending_timeout = None

        elif self.engine.timer_running:
            self.timer_job = self.master.after(1000, self.countdown_timer)

    def save_timer_state(self):
    
        self.engine.saved_state = {
            "timer_running": self.engine.timer_running,
            "timer_seconds": self.engine.timer_seconds,
            "current_index": self.engine.current_index,
            "half_label": self.half_label_var.get(),
            "half_label_bg": self.half_label.cget("bg"),
        }

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
        self.engine.active_penalties.append(penalty)
        self.engine.stored_penalties.append({"team": team, "cap": cap, "duration": duration})
        
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
        if penalty not in self.engine.active_penalties:
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
        if penalty in self.engine.active_penalties:
            if penalty["timer_job"]:
                self.master.after_cancel(penalty["timer_job"])
                penalty["timer_job"] = None
            self.engine.active_penalties.remove(penalty)
            for stored in self.engine.stored_penalties[:]:
                if (stored["team"] == penalty["team"] and 
                    stored["cap"] == penalty["cap"] and 
                    stored["duration"] == penalty["duration"]):
                    self.engine.stored_penalties.remove(stored)
                    break
            # Ensure widget display updates after ALL removals
            self.update_penalty_display()

    def clear_all_penalties(self):
        for penalty in self.engine.active_penalties[:]:
            self.remove_penalty(penalty)
        self.update_penalty_display()

    def pause_all_penalty_timers(self):
        self.penalty_timers_paused = True
        for penalty in self.engine.active_penalties:
            if penalty["timer_job"]:
                self.master.after_cancel(penalty["timer_job"])
                penalty["timer_job"] = None
        self.update_penalty_display()

    def resume_all_penalty_timers(self):
        self.penalty_timers_paused = False
        for penalty in self.engine.active_penalties:
            if not penalty["is_rest_of_match"] and penalty["seconds_remaining"] > 0:
                self.schedule_penalty_countdown(penalty)
        self.update_penalty_display()

    def show_cap_number_dialog(self, trigger_button=None):
        """
        Show a dialog to select a cap number (1-15), Unknown, or Penalty Goal.
        Returns the selected cap number as a string, or None if canceled.
        """
    
        dialog_width = 400
        dialog_height = 300
        gap = 8
    
        cap_number_dialog = tk.Toplevel(self.master)
        cap_number_dialog.withdraw()  # Hide until correctly positioned
        cap_number_dialog.title("Select Cap Number")
        cap_number_dialog.resizable(False, False)
        cap_number_dialog.transient(self.master)
    
        selected_cap = {"value": None}
    
        title_label = tk.Label(
            cap_number_dialog,
            text="Select Scorer's Cap Number:",
            font=("Arial", 12, "bold")
        )
        title_label.pack(pady=10)
    
        matrix_frame = tk.Frame(cap_number_dialog)
        matrix_frame.pack(pady=10)
    
        bottom_frame = tk.Frame(cap_number_dialog)
        bottom_frame.pack(pady=10)
    
        def clear_button_highlights():
            for widget in matrix_frame.winfo_children():
                if isinstance(widget, tk.Button) and hasattr(widget, "original_bg"):
                    widget.config(relief=tk.RAISED, bg=widget.original_bg)
    
            for widget in bottom_frame.winfo_children():
                if isinstance(widget, tk.Button) and hasattr(widget, "original_bg"):
                    widget.config(relief=tk.RAISED, bg=widget.original_bg)
    
        def highlight_selected_button(selected_widget):
            clear_button_highlights()
            selected_widget.config(relief=tk.SUNKEN, bg="lightblue")
    
        def select_cap(cap, button):
            selected_cap["value"] = str(cap)
            highlight_selected_button(button)
    
        def select_unknown(button):
            selected_cap["value"] = "Unknown"
            highlight_selected_button(button)
    
        def select_penalty_goal(button):
            selected_cap["value"] = "Penalty Goal"
            highlight_selected_button(button)
    
        def on_ok():
            if selected_cap["value"] is None:
                messagebox.showwarning(
                    "No Selection",
                    "Please select a cap number, Unknown, or Penalty Goal."
                )
                return
    
            cap_number_dialog.destroy()
    
        button_width = 5
        button_height = 2
    
        for row in range(3):
            for col in range(5):
                cap_num = row * 5 + col + 1
    
                btn = tk.Button(
                    matrix_frame,
                    text=str(cap_num),
                    width=button_width,
                    height=button_height
                )
                btn.original_bg = btn.cget("bg")
                btn.config(command=lambda c=cap_num, b=btn: select_cap(c, b))
                btn.grid(row=row, column=col, padx=2, pady=2)
    
        unknown_btn = tk.Button(
            bottom_frame,
            text="Unknown",
            width=button_width * 2 + 3,
            height=button_height
        )
        unknown_btn.original_bg = unknown_btn.cget("bg")
        unknown_btn.config(command=lambda b=unknown_btn: select_unknown(b))
        unknown_btn.grid(row=0, column=0, columnspan=2, padx=2, pady=2)
    
        penalty_goal_btn = tk.Button(
            bottom_frame,
            text="Penalty Goal",
            width=button_width * 2 + 3,
            height=button_height
        )
        penalty_goal_btn.original_bg = penalty_goal_btn.cget("bg")
        penalty_goal_btn.config(command=lambda b=penalty_goal_btn: select_penalty_goal(b))
        penalty_goal_btn.grid(row=0, column=2, columnspan=2, padx=2, pady=2)
    
        ok_btn = tk.Button(
            bottom_frame,
            text="OK",
            width=button_width,
            height=button_height,
            command=on_ok
        )
        ok_btn.original_bg = ok_btn.cget("bg")
        ok_btn.grid(row=0, column=4, padx=2, pady=2)
    
        # Position from the CURRENT live location of the Add Goal button.
        # This works after moving the app to another monitor.
        cap_number_dialog.update_idletasks()
    
        if trigger_button:
            button_x = trigger_button.winfo_rootx()
            button_y = trigger_button.winfo_rooty()
            button_w = trigger_button.winfo_width()
    
            dialog_x = button_x + (button_w // 2) - (dialog_width // 2)
            dialog_y = button_y - dialog_height - gap
        else:
            dialog_x = self.master.winfo_rootx() + (self.master.winfo_width() // 2) - (dialog_width // 2)
            dialog_y = self.master.winfo_rooty() + (self.master.winfo_height() // 2) - (dialog_height // 2)
    
        cap_number_dialog.geometry(
            f"{dialog_width}x{dialog_height}+{dialog_x}+{dialog_y}"
        )
    
        cap_number_dialog.deiconify()
        cap_number_dialog.lift()
        cap_number_dialog.focus_force()
        cap_number_dialog.grab_set()
    
        self.master.wait_window(cap_number_dialog)
    
        return selected_cap["value"]
    
    def show_penalties(self, trigger_button=None):
        """
        Show the penalties dialog window.
    
        Args:
            trigger_button: Optional button widget that triggered this dialog.
        """
        penalty_width = 250
        penalty_height = 450
        gap = 8
    
        penalty_window = tk.Toplevel(self.master)
        penalty_window.withdraw()  # Hide until correctly positioned
        penalty_window.title("Penalties")
        penalty_window.resizable(False, False)
        penalty_window.transient(self.master)
    
        button_frame = ttk.Frame(penalty_window, padding="10")
        button_frame.pack(side="top", fill="x")
    
        selected_team = tk.StringVar(value="")
    
        def select_team(team):
            selected_team.set(team)
            button_white.config(
                relief=tk.SUNKEN if team == "White" else tk.RAISED
            )
            button_black.config(
                relief=tk.SUNKEN if team == "Black" else tk.RAISED
            )
    
        button_white = tk.Button(
            button_frame,
            text="White",
            width=10,
            command=lambda: select_team("White")
        )
        button_white.pack(side="left", padx=5, expand=True)
    
        button_black = tk.Button(
            button_frame,
            text="Black",
            width=10,
            command=lambda: select_team("Black")
        )
        button_black.pack(side="left", padx=5, expand=True)
    
        numbers = list(range(1, 16))
        dropdown_options = ["Pick Cap Number"] + numbers
        dropdown_variable = tk.StringVar(value=dropdown_options[0])
    
        dropdown = ttk.Combobox(
            penalty_window,
            textvariable=dropdown_variable,
            values=dropdown_options,
            state="readonly",
            height=16
        )
        dropdown.pack(pady=10)
    
        radio_frame = ttk.Frame(penalty_window)
        radio_frame.pack(side="top", anchor="w", pady=10, fill="both")
    
        # Blank when the popup opens
        NO_PENALTY_DURATION_SELECTED = "__none__"
        radio_variable = tk.StringVar(value=NO_PENALTY_DURATION_SELECTED)
    
        radio_button_1 = tk.Radiobutton(
            radio_frame,
            text="1 minute",
            variable=radio_variable,
            value="1 minute",
            tristatevalue="__tristate__"
        )
        
        radio_button_2 = tk.Radiobutton(
            radio_frame,
            text="2 minutes",
            variable=radio_variable,
            value="2 minutes",
            tristatevalue="__tristate__"
        )
        
        radio_button_3 = tk.Radiobutton(
            radio_frame,
            text="5 minutes",
            variable=radio_variable,
            value="5 minutes",
            tristatevalue="__tristate__"
        )
        
        radio_button_4 = tk.Radiobutton(
            radio_frame,
            text="Rest of the match",
            variable=radio_variable,
            value="Rest of the match",
            tristatevalue="__tristate__"
        )    
        radio_button_1.pack(anchor="w")
        radio_button_2.pack(anchor="w")
        radio_button_3.pack(anchor="w")
        radio_button_4.pack(anchor="w")
    
        summary_frame = ttk.Frame(penalty_window)
        summary_frame.pack(side="top", fill="both", expand=True)
    
        summary_label = ttk.Label(
            summary_frame,
            text="Stored Penalties (max 6):"
        )
        summary_label.pack(anchor="w")
    
        penalty_listbox = tk.Listbox(
            summary_frame,
            height=6,
            exportselection=0
        )
        penalty_listbox.pack(fill="both", expand=True)
    
        def refresh_penalty_listbox():
            selection = penalty_listbox.curselection()
            selected_index = selection[0] if selection else None
    
            penalty_listbox.delete(0, tk.END)
    
            for penalty in self.engine.active_penalties:
                if penalty["is_rest_of_match"]:
                    time_str = "REST OF MATCH"
                else:
                    mins, secs = divmod(penalty["seconds_remaining"], 60)
                    time_str = f"{int(mins):02d}:{int(secs):02d}"
    
                penalty_listbox.insert(
                    tk.END,
                    f"{penalty['team']} #{penalty['cap']} {time_str}"
                )
    
            for p in self.engine.stored_penalties:
                already_active = any(
                    ap["team"] == p["team"]
                    and ap["cap"] == p["cap"]
                    and ap["duration"] == p["duration"]
                    for ap in self.engine.active_penalties
                )
    
                if not already_active:
                    penalty_listbox.insert(
                        tk.END,
                        f"{p['team']} #{p['cap']} {p['duration']}"
                    )
    
            if selected_index is not None and penalty_listbox.size() > selected_index:
                penalty_listbox.selection_set(selected_index)
                penalty_listbox.activate(selected_index)
            else:
                penalty_listbox.selection_clear(0, tk.END)
    
        refresh_penalty_listbox()
    
        def periodic_refresh():
            try:
                if penalty_window.winfo_exists():
                    refresh_penalty_listbox()
                    penalty_window.after(1000, periodic_refresh)
            except tk.TclError:
                pass
    
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
    
            if duration == NO_PENALTY_DURATION_SELECTED:
                messagebox.showerror("Error", "Choose a penalty duration.")
                return
    
            if len(self.engine.stored_penalties) >= 6:
                messagebox.showerror(
                    "Error",
                    "Maximum 6 penalties can be stored."
                )
                return
    
            if self.start_penalty_timer(team, cap, duration):
                refresh_penalty_listbox()
                selected_team.set("")
                select_team("")
                dropdown_variable.set(dropdown_options[0])
                radio_variable.set(NO_PENALTY_DURATION_SELECTED)
            else:
                messagebox.showerror(
                    "Error",
                    "Failed to start penalty timer."
                )
    
        def remove_penalty():
            selection = penalty_listbox.curselection()
    
            if not selection:
                messagebox.showerror(
                    "Error",
                    "Please select a penalty to remove."
                )
                return
    
            idx = selection[0]
            active_count = len(self.engine.active_penalties)
    
            if idx < active_count:
                penalty_to_remove = self.engine.active_penalties[idx]
                self.remove_penalty(penalty_to_remove)
                refresh_penalty_listbox()
            else:
                stored_idx = idx - active_count
    
                if 0 <= stored_idx < len(self.engine.stored_penalties):
                    self.engine.stored_penalties.pop(stored_idx)
                    refresh_penalty_listbox()
    
        start_button_frame = ttk.Frame(penalty_window)
        start_button_frame.pack(side="bottom", fill="x", pady=10)
    
        button_container = ttk.Frame(start_button_frame)
        button_container.pack(expand=True, fill="x")
    
        start_button = ttk.Button(
            button_container,
            text="Start Penalty",
            command=start_penalty
        )
        start_button.pack(
            side="left",
            expand=True,
            fill="x",
            padx=(0, 5)
        )
    
        remove_button = ttk.Button(
            button_container,
            text="Remove Selected",
            command=remove_penalty
        )
        remove_button.pack(
            side="right",
            expand=True,
            fill="x",
            padx=(5, 0)
        )
    
        def on_close():
            penalty_window.destroy()
    
        close_button = ttk.Button(
            start_button_frame,
            text="Close",
            command=on_close
        )
        close_button.pack(
            side="bottom",
            fill="x",
            padx=10,
            pady=(0, 10)
        )
    
        penalty_window.protocol("WM_DELETE_WINDOW", on_close)
    
        # Position from the CURRENT live location of the Penalties button.
        # Do not use winfo_screenwidth()/winfo_screenheight() here, because that
        # can pull the popup back toward the original/primary monitor.
        penalty_window.update_idletasks()
    
        if trigger_button:
            button_x = trigger_button.winfo_rootx()
            button_y = trigger_button.winfo_rooty()
            button_w = trigger_button.winfo_width()
    
            popup_x = button_x + (button_w // 2) - (penalty_width // 2)
            popup_y = button_y - penalty_height - gap
        else:
            popup_x = self.master.winfo_rootx() + 100
            popup_y = self.master.winfo_rooty() + 100
    
        penalty_window.geometry(
            f"{penalty_width}x{penalty_height}+{popup_x}+{popup_y}"
        )
    
        penalty_window.deiconify()
        penalty_window.lift()
        penalty_window.focus_force()
        penalty_window.grab_set()
    
    def toggle_referee_timeout(self):
        cur_period = self.engine.get_current_period()
        was_sudden_death = (
            cur_period
            and self.engine.is_sudden_death(cur_period["name"])
        )

        if not self.referee_timeout_active:
            self.referee_timeout_active = True

            self.referee_timeout_button.config(
                bg=self.referee_timeout_active_bg,
                fg=self.referee_timeout_active_fg,
                activebackground=self.referee_timeout_active_bg,
                activeforeground=self.referee_timeout_active_fg
            )

            self.engine.saved_state = {
                "timer_seconds": self.engine.timer_seconds,
                "timer_running": self.engine.timer_running,
                "sudden_death_seconds": self.engine.sudden_death_seconds,
                "was_sudden_death": was_sudden_death,
                "current_index": self.engine.current_index,
                "half_label_text": self.half_label_var.get(),
                "half_label_bg": self.half_label.cget("bg"),
                "court_time_paused": self.court_time_paused,
            }

            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None

            if self.sudden_death_timer_job:
                game_flow.stop_sudden_death_timer(self)

            if self.court_time_job:
                self.master.after_cancel(self.court_time_job)
                self.court_time_job = None

            self.engine.stop_timer()
            self.court_time_paused = True
            self.pause_all_penalty_timers()
            self.referee_timeout_elapsed = 0

            self.half_label_var.set("Ref Time-Out")
            self.half_label.config(bg="red")

            self.referee_timeout_timer_label.grid()

            try:
                if (
                    hasattr(self, "display_referee_timeout_timer_label")
                    and self.display_referee_timeout_timer_label.winfo_exists()
                ):
                    self.display_referee_timeout_timer_label.grid()
            except tk.TclError:
                pass

            self.referee_timeout_countup()

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

            self.referee_timeout_timer_label.grid_remove()

            try:
                if (
                    hasattr(self, "display_referee_timeout_timer_label")
                    and self.display_referee_timeout_timer_label.winfo_exists()
                ):
                    self.display_referee_timeout_timer_label.grid_remove()
            except tk.TclError:
                pass

            self.engine.timer_seconds = self.engine.saved_state["timer_seconds"]
            self.engine.timer_running = self.engine.saved_state["timer_running"]
            self.engine.current_index = self.engine.saved_state["current_index"]
            self.engine.sudden_death_seconds = self.engine.saved_state.get(
                "sudden_death_seconds",
                self.engine.sudden_death_seconds
            )

            was_sudden_death = self.engine.saved_state.get(
                "was_sudden_death",
                False
            )

            self.half_label_var.set(
                self.engine.saved_state["half_label_text"]
            )
            self.half_label.config(
                bg=self.engine.saved_state["half_label_bg"]
            )

            self.court_time_paused = self.engine.saved_state.get(
                "court_time_paused",
                False
            )

            cur_period = self.engine.get_current_period()

            if (
                cur_period
                and not self.engine.is_penalty_pause_period(cur_period["name"])
            ):
                self.resume_all_penalty_timers()

            self.update_timer_display()

            if self.in_timeout:
                if self.timer_job:
                    self.master.after_cancel(self.timer_job)
                    self.timer_job = None

                self.timer_job = self.master.after(
                    1000,
                    self.timeout_countdown
                )

            elif was_sudden_death and self.engine.timer_running:
                self.sudden_death_timer_job = self.master.after(
                    1000,
                    lambda: game_flow.start_sudden_death_timer(self)
                )

            elif self.engine.timer_running:
                self.timer_job = self.master.after(
                    1000,
                    self.countdown_timer
                )

            if not self.court_time_paused:
                self.court_time_job = self.master.after(
                    1000,
                    self.update_court_time
                )

            if cur_period and self.engine.is_penalty_disabled_period(
                cur_period["name"]
            ):
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
        self.engine.sudden_death_goal_scored = False
        self.engine.go_to_period('Sudden Death')
        self.engine.sudden_death_seconds = self.engine.sudden_death_restore_time
        self.engine.sudden_death_restore_active = False
        self.engine.sudden_death_restore_time = None
        self.start_current_period()

    def adjust_score_with_confirm(self, score_var, team_name):
        if score_var.get() == 0:
            return
        if not messagebox.askyesno(
            "Subtract Goal",
            f"Are you sure you want to remove goal from {team_name}?"
        ):
            return
        cur_period = self.engine.get_current_period()
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
                and self.engine.sudden_death_restore_time is not None
                and self.engine.timer_seconds > 30):
                score_var.set(score_var.get() - 1)
                self.restore_sudden_death_after_goal_removal()
                return
            score_var.set(score_var.get() - 1)
        if cur_period['name'] == 'Sudden Death':
            return

    def add_goal_with_confirmation(self, score_var, team_name, trigger_button=None):
        cur_period = self.engine.get_current_period()
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
            cap_number = self.show_cap_number_dialog(trigger_button)
            if cap_number is None:
                # User canceled the dialog, don't add the goal
                return
        
        score_var.set(score_var.get() + 1)
        
        self.engine.record_goal_scorer(
            team_name,
            cap_number
        )
        
        # Log the goal with cap number and break/timeout status
        break_status = None
        if is_team_timeout:
            break_status = "Team Time-Out"
        elif is_referee_timeout:
            break_status = "Referee Time-Out"
        elif is_break:
            break_status = "Break"
        
        self.log_game_event(
            "Goal",
            team=team_name,
            cap_number=cap_number,
            break_status=break_status
        )

        # Saves the current Sudden Death timer value for possible restoration.
        # Flags that a goal has been scored in Sudden Death.
        # Progresses the game to the next period.

        if (
            cur_period
            and self.engine.is_sudden_death(cur_period["name"])
            and not self.engine.sudden_death_goal_scored
        ):

            self.engine.mark_sudden_death_goal(
                self.engine.sudden_death_seconds
            )

            self.engine.stop_timer()
            game_flow.stop_sudden_death_timer(self)
            self.next_period()
            return

        # If goal added during Between Game Break and scores are now EVEN
        if cur_period['name'] == 'Between Game Break':
            if self.white_score_var.get() == self.black_score_var.get():
                if self.is_overtime_enabled():
                    self.engine.go_to_period('Overtime Game Break')
                    self.start_current_period()
                    return
                elif self.is_sudden_death_enabled():
                    self.engine.go_to_period('Sudden Death Game Break')
                    self.start_current_period()
                    return

        # If goal added during Overtime Game Break and scores are now UNEVEN, skip Overtime
        if cur_period['name'] == 'Overtime Game Break':
            if self.white_score_var.get() != self.black_score_var.get():
                # Skip Overtime, go straight to Between Game Break
                self.engine.go_to_period('Between Game Break')
                self.start_current_period()
                return

        # Logic for Sudden Death Game Break after Overtime
        if cur_period['name'] == 'Sudden Death Game Break':
            # If scores are now unequal, progress to Between Game Break
            if self.white_score_var.get() != self.black_score_var.get():
                self.engine.go_to_period('Between Game Break')
                self.start_current_period()
                return

    def test_siren_via_mqtt(self):
        self.add_to_zigbee_log("Testing siren via MQTT...")
    
        try:
            self.zigbee_controller.test_siren()
            self.add_to_zigbee_log("MQTT siren ON command sent")
    
            self.master.after(
                1000,
                self._stop_test_siren_via_mqtt
            )
    
        except Exception as e:
            self.add_to_zigbee_log(f"MQTT siren test failed: {e}")
    
    
    def _stop_test_siren_via_mqtt(self):
        try:
            self.zigbee_controller.stop_test_siren()
            self.add_to_zigbee_log("MQTT siren OFF command sent")
    
        except Exception as e:
            self.add_to_zigbee_log(f"MQTT siren stop failed: {e}")

def is_zigbee2mqtt_running():
    """
    Check if Zigbee2MQTT process is running.
    Uses pgrep to search for zigbee2mqtt process.
    Returns True if running, False otherwise.
    """
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'zigbee2mqtt'],
            capture_output=True,
            text=True,
            timeout=5
        )
        # pgrep returns 0 if process found, 1 if not found
        return result.returncode == 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False

def start_zigbee2mqtt():
    """
    Start Zigbee2MQTT as a subprocess if not already running.
    Starts from the standard installation path /opt/zigbee2mqtt.
    Logs to console if started or already running.
    """
    if is_zigbee2mqtt_running():
        print("Zigbee2MQTT is already running")
        return True
    
    print("Zigbee2MQTT not detected, attempting to start...")
    
    # Standard installation path for Zigbee2MQTT
    zigbee2mqtt_path = '/opt/zigbee2mqtt'
    
    # Check if the directory exists
    if not os.path.exists(zigbee2mqtt_path):
        print(f"Warning: Zigbee2MQTT installation not found at {zigbee2mqtt_path}")
        print("Zigbee2MQTT will not be started automatically")
        return False
    
    try:
        # Start Zigbee2MQTT using npm start in the installation directory
        # Run as a detached subprocess in the background
        subprocess.Popen(
            ['npm', 'start'],
            cwd=zigbee2mqtt_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print(f"Started Zigbee2MQTT from {zigbee2mqtt_path}")
        # Give it a moment to start
        time.sleep(2)
        return True
    except (FileNotFoundError, OSError) as e:
        print(f"Failed to start Zigbee2MQTT: {e}")
        return False

if __name__ == "__main__":
    # Check and start Zigbee2MQTT if needed (Linux/Raspberry Pi only)
    import platform
    if platform.system() == 'Linux':
        start_zigbee2mqtt()
    
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

    def refresh_csv_dropdown(self, event=None):
        current_selection = self.csv_var.get()

        csv_files = self.get_csv_files()

        self.csv_dropdown["values"] = csv_files

        if current_selection in csv_files:
            self.csv_var.set(current_selection)

