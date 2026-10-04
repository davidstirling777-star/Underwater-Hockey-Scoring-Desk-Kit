#!/home/uwh/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main/.venv/bin/python

"""Tk composition root for the UWH Scoring Desk Kit.

GameEngine owns match state; game_flow and csv_export own tournament
transitions. settings_ui, scoreboard_ui and display_ui construct widgets.
zigbee_siren and serial_siren_listener work in background threads; only the
Tk event loop should touch Tk variables and pygame sound. settings_manager
owns the unified settings.json. See MAINTAINERS.md for a complete source map.
"""

import csv_export
import startup_selftest
import csv_helpers
import csv_ui
import tournament_files
import tournament_sync
import display_manager
import display_ui
import game_flow
import game_logging
import game_settings_manager
import hardware_detection
import penalties_ui
import preset_manager
import scoreboard_ui
import settings_manager
import settings_ui
import sounds_ui
import ui_scaling
import ui_theme
import zigbee_ui
import zigbee_control
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
        ('README.md', README_PATH)
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

# In a source ZIP the sample draw lives under assets/, not the root
# scanned by the tournament selector. Seed a working DRAW once on either OS.
# An existing draw or previously recorded _Results.csv is never replaced.
try:
    tournament_files.seed_sample_draw(BASE_DIR)
except OSError as error:
    print(f"TOURNAMENT DRAW: Could not install sample: {error}")

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
import queue
import subprocess
import json
import webbrowser

# ------------------------------------------------------------------
# Global settings
# ------------------------------------------------------------------

DEBUG_MODE = False

from zigbee_siren import ZigbeeSirenController, is_mqtt_available
from sound import (check_audio_device_available, handle_no_audio_device_warning,
                   get_sound_files, play_sound, play_timed_sound, preload_sounds)
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
    return settings_manager.migrate_legacy_settings(BASE_DIR)


def load_unified_settings():
    return settings_manager.load_unified_settings(BASE_DIR)


def save_unified_settings(settings):
    return settings_manager.save_unified_settings(BASE_DIR, settings)


def get_default_unified_settings():
    return settings_manager.get_default_unified_settings()


def load_sound_settings():
    return settings_manager.load_sound_settings(BASE_DIR)


def save_sound_settings(settings):
    return settings_manager.save_sound_settings(BASE_DIR, settings)


def load_preset_settings():
    return settings_manager.load_preset_settings(BASE_DIR)


def save_preset_settings(presets):
    return settings_manager.save_preset_settings(BASE_DIR, presets)

class GameManagementApp:

    def _on_display_window_close(self):
        """Close the display and remember that it should stay closed."""
        self.show_display_screen_var.set(False)
        self.close_all_display_windows()

        # The layout selection is retained for the next time it is opened.
        # Only the visible checkboxes are unticked.
        if hasattr(self, "display_layout_check_vars"):
            for check_var in self.display_layout_check_vars.values():
                check_var.set(False)

        self.save_screen_settings()
    def request_exit(self, event=None):
        """Confirm and cleanly close the complete UWH application."""
        print(
            "DEBUG: request_exit() WAS CALLED",
            f"event={event!r}"
        )
        try:
            confirmed = messagebox.askyesno(
                "Exit UWH Scoring Desk",
                "Close the Underwater Hockey Scoring Desk?",
                parent=self.master
            )
        except tk.TclError:
            confirmed = True

        if not confirmed:
            return "break"

        # Flush pending edits while widgets and the Tk event loop still exist.
        # If saving fails, keep the application open so edits are not lost.
        if not self._flush_pending_settings():
            try:
                messagebox.showerror(
                    "Settings not saved",
                    "The latest settings could not be saved. "
                    "The application will remain open; check the error "
                    "and retry closing.",
                    parent=self.master,
                )
            except tk.TclError:
                pass
            return "break"

        try:
            self._stop_wireless_siren()
            self._stop_arduino_siren()
        except Exception as e:
            print(f"Error stopping siren during exit: {e}")

        try:
            self.stop_connection_watchdog()
        except Exception as e:
            print(f"Error stopping connection watchdog: {e}")

        try:
            controller = getattr(
                self,
                "zigbee_controller",
                None
            )
            if controller is not None:
                controller.stop()
        except Exception as e:
            print(f"Error stopping Zigbee controller: {e}")

        # Local scores/results have already been written. An unfinished
        # network submission remains pending and is replayed after restart.
        # Fake/headless harnesses may exercise request_exit without building
        # the whole application. Production always has the worker.
        sync_worker = getattr(self, "tournament_sync", None)
        if sync_worker is not None:
            sync_worker.stop()

        try:
            self.close_all_display_windows()
        except Exception as e:
            print(f"Error closing display windows: {e}")

        try:
            self.master.destroy()
        except tk.TclError:
            pass

        return "break"
        
    def close_all_display_windows(self):
        """Close every profile-managed external display window."""
        return display_ui.close_all_display_windows(self)

    def apply_screen_configuration(self, *args):
        """Apply the selected operator and display screen layouts."""
        display_ui.apply_screen_configuration(self)
        self.update_penalty_display()
        self.toggle_display_team_names()
        self.save_screen_settings()

    def auto_detect_screens(self):
        """Detect attached monitors and choose suitable operator/display layouts."""
        display_ui.auto_detect_and_apply(self)
        self.save_screen_settings()

    def get_detected_screens_text(self):
        """Return a readable list of screens detected by the operating system."""
        return display_ui.describe_detected_screens(self)

    def refresh_detected_screens_text(self):
        """Refresh the detected-screen list on the Screens tab."""
        return display_ui.update_detected_screens_text(self)

    def test_displays(self):
        """Temporarily identify every connected display."""
        return display_ui.test_displays(self)

    def save_screen_settings(self):
        """Coalesce automatic screen changes into the next minute's save."""
        self._queue_settings_section("screenSettings", {
            "show_team_names": bool(self.show_display_team_names_var.get()),
            "operator_layout": self.operator_layout_var.get(),
            "display_layout": self.display_layout_var.get(),
            "show_display_screen": bool(self.show_display_screen_var.get()),
        })

    def _queue_settings_section(self, section, values):
        """Remember the latest UI state; do not write on every keystroke."""
        previous = self._pending_settings_sections.get(section)
        if previous == values:
            return
        self._pending_settings_sections[section] = values
        if self._settings_autosave_job is None:
            self._settings_autosave_job = self.master.after(
                60000, self._flush_pending_settings
            )

    def _flush_pending_settings(self):
        """Merge changed UI sections with fresh settings, once per minute.

        Presets, sound Save Settings, and explicit Zigbee Save remain immediate.
        A failed write retains the snapshot and retries in one minute.
        """
        job = self._settings_autosave_job
        self._settings_autosave_job = None
        if job is not None:
            try:
                self.master.after_cancel(job)
            except tk.TclError:
                pass

        if not self._pending_settings_sections:
            return True

        try:
            # Serial and MQTT configuration may have changed since the UI
            # edit; read and merge under the central writer's lock.
            settings_manager.update_unified_settings(
                BASE_DIR, self._pending_settings_sections
            )
        except Exception as error:
            print(f"Deferred settings save failed; will retry: {error}")
            self._settings_autosave_job = self.master.after(
                60000, self._flush_pending_settings
            )
            return False

        self._pending_settings_sections.clear()
        return True

    def toggle_display_team_names(self):
        """
        Show or hide tournament team names on all presentation windows.

        The existing Show Team Names setting still applies, but the
        Use Tournament List checkbox takes priority.
        """
        try:
            use_tournament_list = True

            if hasattr(self, "use_tournament_list_var"):
                use_tournament_list = bool(
                    self.use_tournament_list_var.get()
                )

            show_team_names = (
                use_tournament_list
                and bool(
                    self.show_display_team_names_var.get()
                )
            )

            white_name = ""
            black_name = ""

            if show_team_names:
                if hasattr(self, "white_team_name_widget"):
                    white_name = (
                        self.white_team_name_widget.cget(
                            "text"
                        )
                        or ""
                    )

                if hasattr(self, "black_team_name_widget"):
                    black_name = (
                        self.black_team_name_widget.cget(
                            "text"
                        )
                        or ""
                    )

            # Main presentation Display Window.
            if hasattr(
                self,
                "display_white_team_name_widget"
            ):
                self.display_white_team_name_widget.config(
                    text=white_name
                )

            if hasattr(
                self,
                "display_black_team_name_widget"
            ):
                self.display_black_team_name_widget.config(
                    text=black_name
                )

            # Any lightweight/simple public display windows.
            for white_label, black_label in getattr(
                self,
                "simple_display_name_labels",
                []
            ):
                try:
                    if not use_tournament_list:
                        simple_white_text = ""
                        simple_black_text = ""

                    elif show_team_names:
                        simple_white_text = white_name
                        simple_black_text = black_name

                    else:
                        # Preserve the existing behaviour when the
                        # Tournament List is enabled but the normal
                        # Show Team Names option is off.
                        simple_white_text = (
                            self.white_team_var.get()
                        )
                        simple_black_text = (
                            self.black_team_var.get()
                        )

                    white_label.config(
                        text=simple_white_text
                    )
                    black_label.config(
                        text=simple_black_text
                    )

                except tk.TclError:
                    pass

            # Any full mirrored presentation windows.
            for bundle in getattr(
                self,
                "display_mirror_bundles",
                []
            ):
                try:
                    widgets = bundle.get(
                        "widgets",
                        {}
                    )

                    if "white_name" in widgets:
                        widgets["white_name"].config(
                            text=white_name
                        )

                    if "black_name" in widgets:
                        widgets["black_name"].config(
                            text=black_name
                        )

                except (
                    AttributeError,
                    tk.TclError
                ):
                    pass

        except (
            AttributeError,
            tk.TclError
        ):
            pass

    def handle_hardware_siren_event(self, event_name="ON"):
        """Thread-safe input from MQTT and the Arduino serial listener.

        Worker threads must never read Tk variables or call pygame here. The
        existing Tk status queue poller processes hardware events on the UI thread.
        """
        self.hardware_siren_event_queue.put(event_name)

    def _stop_wireless_siren(self):
        """Cancel a wireless siren sequence, including a pending second blast."""
        self._wireless_siren_cycles_remaining = 0
        self._wireless_continuous_active = False
        self._wireless_continuous_device = None
        stop_job = getattr(self, "_wireless_siren_stop_job", None)
        self._wireless_siren_stop_job = None
        if stop_job is not None:
            try:
                self.master.after_cancel(stop_job)
            except tk.TclError:
                pass

        channel = getattr(self, "_wireless_siren_channel", None)
        self._wireless_siren_channel = None
        sound.stop_looping_sound(channel)

    def _play_wireless_siren_once(self, cycles=1):
        """Start one or two identical, duration-limited Zigbee siren blasts."""
        # Cancel the previous blast and any pending second blast. New wireless
        # events replace the sequence rather than stacking sound channels.
        self._stop_wireless_siren()
        if not self.enable_sound.get():
            return

        try:
            duration_seconds = float(self.siren_duration.get())
            if not 0 < duration_seconds < float("inf"):
                return

            # Each wireless blast respects the operator's safety cutoff.
            limit = sound.normalise_max_siren_duration(
                self.max_siren_duration.get()
            )
            self._wireless_siren_cycle_duration = min(duration_seconds, limit)
            self._wireless_siren_cycles_remaining = 2 if cycles == 2 else 1
            self._play_next_wireless_siren_cycle()
        except Exception as e:
            self._stop_wireless_siren()
            print(f"Timed wireless siren failed: {e}")

    def _play_next_wireless_siren_cycle(self):
        """Start one blast; the next starts after this one has stopped."""
        self._wireless_siren_stop_job = None
        if (
            not self.enable_sound.get()
            or self._wireless_siren_cycles_remaining <= 0
        ):
            self._stop_wireless_siren()
            return

        try:
            duration = self._wireless_siren_cycle_duration
            duration_ms = max(1, int(duration * 1000))
            self._wireless_siren_channel = sound.start_timed_siren(
                self.siren_var.get(),
                self.enable_sound.get(),
                self.get_sound_trim(self.siren_var.get()),
                duration,
                self.max_siren_duration.get(),
            )
            if self._wireless_siren_channel is None:
                self._stop_wireless_siren()
                return

            self._wireless_siren_cycles_remaining -= 1
            # Pygame's maxtime independently bounds playback even if Tk stalls.
            self._wireless_siren_stop_job = self.master.after(
                duration_ms, self._finish_wireless_siren_cycle
            )
        except Exception as e:
            self._stop_wireless_siren()
            print(f"Wireless siren cycle failed: {e}")

    def _finish_wireless_siren_cycle(self):
        """End this blast and start the next immediately, with no pause."""
        self._wireless_siren_stop_job = None
        channel = self._wireless_siren_channel
        self._wireless_siren_channel = None
        sound.stop_looping_sound(channel)

        if self._wireless_siren_cycles_remaining and self.enable_sound.get():
            # No scheduled delay: two duration-limited blasts play back-to-back.
            self._play_next_wireless_siren_cycle()
        else:
            self._wireless_siren_cycles_remaining = 0

    def _start_wireless_continuous(self, device_name):
        """Start a release-controlled siren with an independent audio cutoff.

        Pygame's maxtime enforces the maximum even if Tk's event loop stalls.
        The normal Tk after() also stops the sound and updates UI state.
        """
        if device_name in self._wireless_continuous_blocked:
            self.add_to_zigbee_log(
                f"Safety: repeated press for '{device_name}' blocked "
                "until a release is received."
            )
            return
        if self._wireless_continuous_active:
            # Never restart or extend the timer for duplicates, including
            # presses from another device while an existing hold is active.
            self.add_to_zigbee_log("Safety: duplicate continuous press ignored.")
            return
        if not self.enable_sound.get():
            return

        try:
            seconds = float(self.zigbee_controller.config.get(
                "continuous_siren_max_seconds", 10.0
            ))
            if not 1.0 <= seconds <= 30.0:
                seconds = 10.0
        except (ValueError, TypeError):
            seconds = 10.0

        # The Zigbee continuous limit and Sounds-tab limit both apply.
        seconds = min(
            seconds,
            sound.normalise_max_siren_duration(
                self.max_siren_duration.get()
            ),
        )

        # Replace any timed wireless cycle; the wired Arduino channel remains
        # untouched. Never stack separate wireless sound channels.
        self._stop_wireless_siren()
        channel = sound.start_timed_siren(
            self.siren_var.get(),
            self.enable_sound.get(),
            self.get_sound_trim(self.siren_var.get()),
            seconds,
            self.max_siren_duration.get(),
        )
        if channel is None:
            self.add_to_zigbee_log("Continuous siren could not start: no audio channel.")
            return

        self._wireless_siren_channel = channel
        self._wireless_continuous_active = True
        self._wireless_continuous_device = device_name
        self._wireless_siren_stop_job = self.master.after(
            max(1, int(seconds * 1000)), self._wireless_continuous_timeout
        )
        self.add_to_zigbee_log(
            f"Continuous siren started by '{device_name}' "
            f"(maximum {seconds:g} seconds)."
        )

    def _stop_wireless_continuous(self, device_name):
        """A release only stops a hold started by that exact device."""
        self._wireless_continuous_blocked.discard(device_name)
        if not self._wireless_continuous_active:
            return  # A late release must not touch a timed/Arduino siren.
        if device_name != self._wireless_continuous_device:
            self.add_to_zigbee_log(
                f"Safety: release from '{device_name}' ignored; "
                "another device started the hold."
            )
            return
        self._stop_wireless_siren()
        self.add_to_zigbee_log(
            f"Continuous siren stopped by release from '{device_name}'."
        )

    def _wireless_continuous_timeout(self):
        """Failsafe: stop even if the MQTT release never reaches the app."""
        if not self._wireless_continuous_active:
            return
        device_name = self._wireless_continuous_device
        self._stop_wireless_siren()
        self._wireless_continuous_blocked.add(device_name)
        self.add_to_zigbee_log(
            f"Safety: continuous siren from '{device_name}' "
            "stopped at maximum duration; waiting for release."
        )

    def _stop_arduino_siren(self):
        """Stop only the Arduino's local sound channel, not a wireless blast.
        """
        channel = getattr(self, "arduino_siren_channel", None)
        self.arduino_siren_channel = None
        sound.stop_looping_sound(channel)

    def _on_enable_sound_changed(self):
        """Unticking Enable Sound is an immediate audio stop as well as a mute."""
        if not self.enable_sound.get():
            self._stop_wireless_siren()
            self._stop_arduino_siren()
            # Also stop any currently playing score/timer siren or pip.
            try:
                if sound.PYGAME_INITIALIZED:
                    sound.pygame.mixer.stop()
            except Exception as e:
                print(f"Could not stop mixer on mute: {e}")

    def _process_hardware_siren_event(self, event_name):
        """Handle siren events ONLY on the Tk main thread."""
        if event_name.startswith("ARDUINO_SERIAL_OPEN:"):
            port = event_name.split(":", 1)[1]
            self.add_to_zigbee_log(
                f"Arduino siren serial listener opened {port} (9600 baud)"
            )
            return
        if event_name.startswith("ARDUINO_SERIAL_ERROR:"):
            detail = event_name.split(":", 1)[1]
            self.add_to_zigbee_log(
                f"Arduino siren serial listener error: {detail}"
            )
            return
        if event_name == "WIRELESS_MQTT_DISCONNECT":
            if self._wireless_continuous_active:
                device_name = self._wireless_continuous_device
                self._stop_wireless_siren()
                self._wireless_continuous_blocked.add(device_name)
                self.add_to_zigbee_log(
                    "Safety: MQTT disconnected; continuous siren stopped."
                )
            return

        if event_name.startswith("WIRELESS_PRESS:"):
            self._start_wireless_continuous(event_name.split(":", 1)[1])
            return

        if event_name.startswith("WIRELESS_RELEASE:"):
            self._stop_wireless_continuous(event_name.split(":", 1)[1])
            return

        if event_name == "PULSE":
            self._play_wireless_siren_once()
            return

        if event_name == "DOUBLE_PULSE":
            self._play_wireless_siren_once(cycles=2)
            return

        if event_name == "OFF":
            self.add_to_zigbee_log("Arduino button: SIREN_OFF received")
            self._stop_arduino_siren()
            try:
                self.zigbee_controller.handle_hardware_siren_event("OFF")
            except Exception as error:
                print(f"Arduino siren MQTT OFF failed: {error}")
            return

        if event_name != "ON":
            print(f"Unrecognised hardware siren event: {event_name!r}")
            return

        self.add_to_zigbee_log("Arduino button: SIREN_ON received")

        # The Arduino button has TWO outputs: local PC sound and the
        # MQTT-controlled siren. Muting the PC must not suppress the hardware
        # siren's ON command. A release always stops both outputs.
        if self.enable_sound.get():
            try:
                track = self.siren_var.get()
                trim_percent = self.get_sound_trim(track)
                normalized_volume = (
                    sound.normalise_trim_percent(trim_percent) / 100.0
                )
                sound_obj = sound._preloaded_sounds.get(track)

                if sound_obj is None:
                    print(
                        f"Arduino siren: selected local sound {track!r} "
                        "is not preloaded; MQTT siren will still be requested."
                    )
                else:
                    sound_obj.set_volume(normalized_volume)
                    self._stop_arduino_siren()
                    self.arduino_siren_channel = sound_obj.play(loops=-1)
                    if self.arduino_siren_channel is not None:
                        self.arduino_siren_channel.set_volume(1.0)
                    else:
                        print("Arduino siren: no local audio channel available.")
            except Exception as error:
                print(f"Arduino siren local audio failed: {error}")

        try:
            self.zigbee_controller.handle_hardware_siren_event("ON")
        except Exception as error:
            print(f"Arduino siren MQTT ON failed: {error}")

    def add_to_zigbee_log(self, message):
        """
        Safe Zigbee logger.

        It works during startup before the Zigbee tab and its log box
        have been created, then writes to the on-screen log afterwards.
        """
        print(f"Zigbee: {message}")

        log_text = getattr(self, "log_text", None)

        if log_text is None:
            return

        def write_to_log():
            try:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                log_text.config(state=tk.NORMAL)
                log_text.insert(
                    tk.END,
                    f"[{timestamp}] {message}\n"
                )
                log_text.see(tk.END)
                log_text.config(state=tk.DISABLED)

            except tk.TclError:
                pass

        try:
            self.master.after(0, write_to_log)
        except (AttributeError, tk.TclError):
            pass
    
    def __init__(self, master):
        """Build the live Tk application and restore operator settings.
        Initialize shared state before creating tabs or starting worker listeners.
        """
        self.master = master
        # Automatic Game Variables / Screen changes are saved at most once
        # per minute, in a single settings.json write.
        # Network synchronisation runs off the GUI thread; the queue below
        # brings only status text back to Tk.
        self._tournament_sync_status_queue = queue.Queue()
        self.tournament_sync = tournament_sync.TournamentSyncWorker(
            self._tournament_sync_status_queue
        )
        self._pending_settings_sections = {}
        self._settings_autosave_job = None
        self.master.title("UWH Scoring Desk")
        self.master.geometry("1280x840")
        self.master.minsize(1100, 720)
        ui_theme.configure_styles(self.master)
        ui_theme.apply_app_icon(self.master)
        self.notebook = ttk.Notebook(master, style="UWH.TNotebook")
        self.notebook.pack(expand=True, fill="both")

        # Ctrl+Q always provides a way out of the application.
        self.master.bind_all(
            "<Control-q>",
            self.request_exit
        )

        # --- Variable and font setup ---
        # The UI must present this exact set of real game variables.  Labels
        # are operator-facing only; keys remain stable for settings/presets.
        self.variables = {
            "time_to_start_first_game": {
                "default": "", "checkbox": False, "unit": "HH.mm",
                "label": "Clock Time to Start First Game at:"
            },
            "start_first_game_in": {
                "default": 1, "checkbox": False, "unit": "minutes",
                "label": "First Game Starts In:"
            },
            "team_timeouts_allowed": {
                "default": True, "checkbox": True, "unit": "",
                "label": "Team Time-Outs allowed?"
            },
            "team_timeout_period": {
                "default": 1, "checkbox": False, "unit": "minutes",
                "label": "Team Time out period:"
            },
            "half_period": {
                "default": 1, "checkbox": False, "unit": "minutes",
                "label": "Half Period:"
            },
            "half_time_break": {
                "default": 1, "checkbox": False, "unit": "minutes",
                "label": "Half Time Break:"
            },
            "overtime_allowed": {
                "default": True, "checkbox": True, "unit": "",
                "label": "Overtime allowed?"
            },
            "overtime_game_break": {
                "default": 1, "checkbox": False, "unit": "minutes",
                "label": "Overtime Game Break:"
            },
            "overtime_half_period": {
                "default": 1, "checkbox": False, "unit": "minutes",
                "label": "Overtime Half Period:"
            },
            "overtime_half_time_break": {
                "default": 1, "checkbox": False, "unit": "minutes",
                "label": "Overtime Half Time Break:"
            },
            "sudden_death_game_break": {
                "default": 1, "checkbox": True, "unit": "minutes",
                "label": "Sudden Death Game Break:"
            },
            "between_game_break": {
                "default": 1, "checkbox": False, "unit": "minutes",
                "label": "Between Game Break:"
            },
            "record_scorers_cap_number": {
                "default": False, "checkbox": True, "unit": "",
                "label": "Record Scorers Cap Number"
            },
            "crib_time": {
                "default": 1, "checkbox": True, "unit": "seconds",
                "label": "Crib Time:"
            }
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
            "timer": font.Font(family="Arial", size=110, weight="bold"),
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
            "timer": font.Font(family="Arial", size=110, weight="bold"),
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
        self.all_game_numbers = []
        self.game_numbers = []
        self.court_game_mode_var = tk.StringVar(value="consecutive")
        
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
        self.team_timeout_saved_state = None
        self.sudden_death_timer_job = None
        self.next_game_transition_job = None
        self.next_game_preview_job = None
        self.next_game_transition_done = False
        # Preserve a completed game's identity while a failed CSV export awaits retry.
        self._game_export_pending = False
        self._pending_export_game_number = None
        self._game_export_timer_was_running = False
        self._game_export_dialog = None
        self._game_export_error_label = None
        self.next_game_preview_active = False
        self.next_game_preview_number = None
        self.next_game_notice_active = False
        self.engine.sudden_death_seconds = 0
        self.widgets = []
        self.last_valid_values = {}
        self.team_timeouts_allowed_var = tk.BooleanVar(value=self.variables["team_timeouts_allowed"]["default"])
        self.overtime_allowed_var = tk.BooleanVar(value=self.variables["overtime_allowed"]["default"])
        self.record_scorers_cap_number_var = tk.BooleanVar(value=self.variables["record_scorers_cap_number"]["default"])
        screen_settings = load_unified_settings().get("screenSettings", {})
        self.show_display_team_names_var = tk.BooleanVar(
            value=screen_settings.get("show_team_names", True)
        )
        legacy_profile = screen_settings.get("display_profile", "Single Standard")
        self.operator_layout_var = tk.StringVar(
            value=screen_settings.get(
                "operator_layout",
                "Widescreen" if legacy_profile == "Operator Ultrawide" else "Standard"
            )
        )
        legacy_display_map = {
            "Single Standard": "Single Standard",
            "Dual Standard": "Dual Standard",
            "Public Single": "Single Standard",
            "Public Dual": "Dual Standard",
            "Operator Ultrawide": "Single Standard",
            "Auto": "Single Standard",
        }
        # New explicit display-visibility setting. For older settings files,
        # preserve the previous selection: an empty saved layout meant closed.
        saved_display_layout = screen_settings.get(
            "display_layout",
            legacy_display_map.get(legacy_profile, "Single Standard")
        )
        self.show_display_screen_var = tk.BooleanVar(
            value=bool(screen_settings.get(
                "show_display_screen", bool(saved_display_layout)
            ))
        )
        # Remember the last selected layout even while the window is hidden.
        self.display_layout_var = tk.StringVar(
            value=saved_display_layout or "Single Standard"
        )
        self.display_windows = []
        self.display_test_windows = []
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

        # Load the active pip/siren selections, per-file attenuation trims and
        # siren timing. Overall loudness is intentionally controlled by the
        # OS/DAC/amplifier rather than by a second software master volume.
        sound_settings = load_sound_settings()
        self.enable_sound = tk.BooleanVar(
            value=sound_settings.get("enable_sound", True)
        )
        self.siren_duration = tk.DoubleVar(
            value=sound_settings.get("siren_duration", 1.5)
        )
        # Separate, user-configurable safety cutoff for timed siren blasts.
        # StringVar keeps an invalid entry editable until validation on save.
        self.max_siren_duration = tk.StringVar(
            value=str(sound.normalise_max_siren_duration(
                sound_settings.get("max_siren_duration", 10.0)
            ))
        )

        sound_files = get_sound_files()
        available_audio_files = (
            sound_files
            if sound_files != ["No sound files found"]
            else []
        )
        pips_files = [
            name for name in available_audio_files
            if "pip" in name.lower()
        ]
        siren_files = [
            name for name in available_audio_files
            if "siren" in name.lower()
        ]

        pips_default = sound_settings.get("pips_sound", "")
        siren_default = sound_settings.get("siren_sound", "")
        if pips_default not in pips_files:
            pips_default = pips_files[0] if pips_files else ""
        if siren_default not in siren_files:
            if "siren-police.mp3" in siren_files:
                siren_default = "siren-police.mp3"
            else:
                siren_default = siren_files[0] if siren_files else ""

        self.pips_var = tk.StringVar(value=pips_default)
        self.siren_var = tk.StringVar(value=siren_default)

        # Per-file trims default to 100%. When upgrading an older settings
        # file, preserve the previous selected Pips/Siren software levels for
        # those two selected files so the first upgraded run does not jump in
        # level unexpectedly. New/discovered files still begin at 100%.
        self.sound_trims = {}
        saved_trims = sound_settings.get("sound_trims", {})
        if isinstance(saved_trims, dict):
            for filename, value in saved_trims.items():
                self.sound_trims[str(filename)] = (
                    sound.normalise_trim_percent(value)
                )
        if "sound_trims" not in sound_settings:
            if pips_default:
                self.sound_trims[pips_default] = sound.normalise_trim_percent(
                    sound_settings.get("pips_volume", 100.0)
                )
            if siren_default:
                self.sound_trims[siren_default] = sound.normalise_trim_percent(
                    sound_settings.get("siren_volume", 100.0)
                )
        
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
        splash_width = 620

        # Use about three quarters of the available screen height.
        # This keeps the complete self-test visible without making the
        # startup window dominate the screen.
        screen_height = master.winfo_screenheight()
        available_height = max(
            400,
            screen_height - 80
        )
        splash_height = max(
            560,
            int(available_height * 0.75)
        )
        splash_height = min(
            splash_height,
            available_height
        )

        splash.geometry(
            f"{splash_width}x{splash_height}"
        )
        splash.resizable(False, False)
        
        # Position splash screen
        # Position the splash relative to the main window, rather than
        # the primary monitor. This keeps it on the same display screen.
        master.update_idletasks()
        splash.update_idletasks()

        main_x = master.winfo_rootx()
        main_y = master.winfo_rooty()

        main_width = max(
            master.winfo_width(),
            master.winfo_reqwidth()
        )
        main_height = max(
            master.winfo_height(),
            master.winfo_reqheight()
        )

        x = main_x + max(
            0,
            (main_width - splash_width) // 2
        )

        # Position in the upper third of the Game Management window.
        y = main_y + max(
            20,
            (main_height // 5) - (splash_height // 2)
        )

        splash.geometry(f"+{x}+{y}")

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
                    print(
                        "DEBUG: finish_startup() starting"
                    )

                    splash.destroy()

                    print(
                        "DEBUG: startup splash destroyed"
                    )

                    try:
                        print(
                            "DEBUG: main root exists:",
                            self.master.winfo_exists()
                        )
                    except Exception as e:
                        print(
                            "DEBUG: unable to check root:",
                            e
                        )

                    self.master.lift()
                    self.master.focus_force()

                    print(
                        "DEBUG: finish_startup() completed"
                    )
        
                splash.after(2000, finish_startup)
        
            except tk.TclError:
                pass

        splash_report("Game engine loaded", True)
        splash_report("Settings system available", True)

        # The MQTT broker and Zigbee2MQTT can run as Windows services or
        # background processes without their executables being on PATH.
        # Verify broker connectivity rather than testing command locations.
        # Perform MQTT stability check
        mqtt_connection_stable = startup_selftest.check_mqtt_stability(
            splash_report=splash_report,
            is_mqtt_available=is_mqtt_available,
            timeout_seconds=30,
            stable_threshold=3,
            mqtt_config=load_unified_settings().get("zigbeeSettings", {})
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
        self._wireless_siren_channel = None
        self._wireless_siren_stop_job = None
        self._wireless_siren_cycles_remaining = 0
        self._wireless_continuous_active = False
        self._wireless_continuous_device = None
        # After a maximum-duration timeout, require a release before any
        # repeat press can restart the same wireless continuous siren.
        self._wireless_continuous_blocked = set()
        self.hardware_siren_event_queue = queue.Queue()
        self.enable_sound.trace_add(
            "write", lambda *_: self._on_enable_sound_changed()
        )
        self.connection_watchdog_active = False
        self.connection_watchdog_attempts = 0
        self.connection_watchdog_max_attempts = 3
        self.connection_watchdog_job = None
        self.user_initiated_action = False
        
        # Thread-safe handoff from the Zigbee/MQTT worker thread
        # to the Tkinter main thread.
        self.zigbee_status_queue = queue.Queue()
        self._zigbee_status_queue_job = None
        
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
        splash_report("Game Variables tab created", True)

        self.create_tournament_tab()
        # The Tournament List tab's initial selection configures the worker.
        # Starting the daemon here lets its first network request happen off
        # the Tk thread.
        self.tournament_sync.start()
        self._poll_tournament_sync_status()
        splash_report("Tournament List tab created", True)

        self.create_screen_tab()
        splash_report("Screen tab created", True)

        self.create_sounds_tab()
        splash_report("Sounds tab created", True)

        self.create_zigbee_siren_tab()
        splash_report("Siren control tab created", True)

        self.create_about_tab()
        splash_report("About tab created", True)

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
        self.master.after(
            1500,
            lambda: self.update_zigbee_status(
                getattr(self.zigbee_controller, "connected", False),
                "Startup sync"
            )
        )

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

        # Screen configurations
        self.apply_screen_configuration()
        splash_report("Screen configuration applied", True)

        self.start_penalty_display_updates()
        splash_report("Penalty display updates started", True)

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

    def load_unified_settings(self):
        return load_unified_settings()

    def save_unified_settings(self, settings):
        return save_unified_settings(settings)

    def save_sound_settings(self, settings):
        return save_sound_settings(settings)
    
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
        # Local CSV is the durable source of truth for this court. The remote
        # submission happens later and cannot delay game advancement.
        saved = csv_export.write_game_results_to_csv(
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
        if saved:
            self.tournament_sync.wake()
        return saved
    
    def create_scoreboard_tab(self):
        return scoreboard_ui.create_scoreboard_tab(self)
        
    def update_penalty_display(self):
        """
        Show active penalties in row 2.

        After the completed game's data has been written, show a red
        Next Game banner in the penalty area until the next game starts.
        The Game Number remains visible in row 3 at all times.
        """

        def place_game_label(
            label,
            row=3,
            column=3,
            columnspan=3
        ):
            """
            Keep a Game Number label in its intended layout position.

            The operator label uses the default 9-column layout.
            The presentation label supplies its 12-column position.
            """
            try:
                grid_info = label.grid_info()

                current_row = int(
                    grid_info.get("row", -1)
                )
                current_column = int(
                    grid_info.get("column", -1)
                )
                current_columnspan = int(
                    grid_info.get("columnspan", 1)
                )

                if (
                    label.winfo_manager() != "grid"
                    or current_row != row
                    or current_column != column
                    or current_columnspan != columnspan
                ):
                    label.grid(
                        row=row,
                        column=column,
                        columnspan=columnspan,
                        padx=1,
                        pady=1,
                        sticky="nsew"
                    )

            except (
                AttributeError,
                tk.TclError,
                TypeError,
                ValueError
            ):
                pass

        def place_penalty_grid(grid_frame, area_frame_name):
            """Show the penalty grid only if it is not already shown."""

            try:
                # Avoid repeating the same grid operation every second.
                if grid_frame.winfo_manager() == "grid":
                    return

                area_frame = getattr(self, area_frame_name, None)

                if area_frame is not None:
                    grid_frame.grid(
                        row=0,
                        column=0,
                        padx=0,
                        pady=0,
                        sticky="nsew"
                    )
                else:
                    grid_frame.grid(
                        row=2,
                        column=3,
                        columnspan=3,
                        padx=1,
                        pady=1,
                        sticky="nsew"
                    )

            except (AttributeError, tk.TclError):
                pass

        def show_next_game_banner(
            banner_attribute,
            area_frame_name,
            grid_frame,
            banner_font
        ):
            """Create, position, and show the red Next Game banner."""
            area_frame = getattr(self, area_frame_name, None)

            if area_frame is not None:
                parent = area_frame
                grid_options = {
                    "row": 0,
                    "column": 0,
                    "padx": 0,
                    "pady": 0,
                    "sticky": "nsew"
                }
            else:
                parent = grid_frame.master
                grid_options = {
                    "row": 2,
                    "column": 3,
                    "columnspan": 3,
                    "padx": 1,
                    "pady": 1,
                    "sticky": "nsew"
                }

            banner = getattr(self, banner_attribute, None)

            if banner is None or not banner.winfo_exists():
                banner = tk.Label(
                    parent,
                    text="Next Game",
                    font=banner_font,
                    bg="lightcoral",
                    fg="black",
                    anchor="center"
                )
                setattr(self, banner_attribute, banner)

            try:
                between_game_colour = self.half_label.cget("bg")
            except (AttributeError, tk.TclError):
                between_game_colour = "lightcoral"

            # Keep the banner's text/foreground set at creation; only the
            # period colour can change during a running game.
            if banner.cget("bg") != between_game_colour:
                banner.config(bg=between_game_colour)

            # A grid operation triggers layout work, so do this once per
            # visibility transition instead of every one-second refresh.
            if banner.winfo_manager() != "grid":
                banner.grid(**grid_options)

        def hide_next_game_banner(banner_attribute):
            banner = getattr(self, banner_attribute, None)

            try:
                if banner is not None and banner.winfo_manager() == "grid":
                    banner.grid_remove()
            except (AttributeError, tk.TclError):
                pass

        show_next_game = bool(
            getattr(self, "next_game_notice_active", False)
        )

        main_has_penalties = bool(
            self.engine.active_penalties
            or self.engine.stored_penalties
        )

        try:
            if show_next_game:
                if self.penalty_grid_frame.winfo_manager() == "grid":
                    self.penalty_grid_frame.grid_remove()

                show_next_game_banner(
                    "next_game_banner",
                    "penalty_area_frame",
                    self.penalty_grid_frame,
                    self.fonts["game_no"]
                )

            else:
                hide_next_game_banner("next_game_banner")

                if main_has_penalties:
                    place_penalty_grid(
                        self.penalty_grid_frame,
                        "penalty_area_frame"
                    )
                    self.update_penalty_grid()

                else:
                    if self.penalty_grid_frame.winfo_manager() == "grid":
                        self.penalty_grid_frame.grid_remove()

            place_game_label(self.game_label)
            self.update_game_number_display()

        except (AttributeError, tk.TclError):
            pass

        try:
            display_has_penalties = bool(
                self.engine.active_penalties
                or self.engine.stored_penalties
            )

            if show_next_game:
                if self.display_penalty_grid_frame.winfo_manager() == "grid":
                    self.display_penalty_grid_frame.grid_remove()

                show_next_game_banner(
                    "display_next_game_banner",
                    "display_penalty_area_frame",
                    self.display_penalty_grid_frame,
                    self.display_fonts["game_no"]
                )

            else:
                hide_next_game_banner("display_next_game_banner")

                if display_has_penalties:
                    place_penalty_grid(
                        self.display_penalty_grid_frame,
                        "display_penalty_area_frame"
                    )
                    self.update_display_penalty_grid()

                else:
                    if self.display_penalty_grid_frame.winfo_manager() == "grid":
                        self.display_penalty_grid_frame.grid_remove()

            place_game_label(
                self.display_game_label,
                row=1,
                column=3,
                columnspan=6
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
        return ui_scaling.scale_fonts(self, event)

    def scale_display_fonts(self, event=None):
        return ui_scaling.scale_display_fonts(self, event)

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
            # Accept the established colon form plus the v1.3 UI's HH.mm
            # display form. Internally both represent the same 24-hour time.
            normalized_time = time_val.strip().replace(".", ":")
            match = re.fullmatch(
                r"(?:[01]?[0-9]|2[0-3]):[0-5][0-9]",
                normalized_time
            )
            if match:
                hh, mm = map(int, normalized_time.split(":"))
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
        return settings_ui.create_settings_tab(self)

    def create_tournament_tab(self):
        return settings_ui.create_tournament_tab(self)

    def create_screen_tab(self):
        return settings_ui.create_screen_tab(self)

    def create_about_tab(self):
        return settings_ui.create_about_tab(self, README_PATH)

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

    def _selected_tournament_draw(self):
        """Return the source draw path; never return a results file."""
        filename = self.csv_var.get()
        if filename in ("", "No CSV files found"):
            return ""
        return os.path.join(BASE_DIR, filename)

    def _configure_tournament_sync(self):
        """Read SAVED options; uncommitted UI text cannot redirect results."""
        settings = load_unified_settings().get("tournamentSync", {})
        self.tournament_sync.configure(
            self._selected_tournament_draw(),
            settings.get("mode") == "Shared server",
            settings.get("server_url", ""),
            settings.get("token", ""),
        )

    def save_tournament_sync_configuration(self):
        """Validate and immediately save server details, then start syncing."""
        mode = self.tournament_sync_mode_var.get()
        address = self.tournament_sync_url_var.get().strip()
        token = self.tournament_sync_token_var.get().strip()
        if mode == "Shared server":
            try:
                address = tournament_sync.normalise_url(address)
                if len(token) < 16:
                    raise ValueError(
                        "Enter the shared results server token (16+ characters)"
                    )
            except ValueError as error:
                messagebox.showerror(
                    "Tournament Results", str(error), parent=self.master
                )
                return
        try:
            settings_manager.update_unified_settings(BASE_DIR, {
                "tournamentSync": {
                    "mode": mode,
                    "server_url": address,
                    "token": token,
                }
            })
        except OSError as error:
            messagebox.showerror(
                "Tournament Results",
                f"Could not save results configuration:\n{error}",
                parent=self.master,
            )
            return

        self._configure_tournament_sync()
        self.tournament_sync.wake()

    def _poll_tournament_sync_status(self):
        """Only the Tk thread edits the Game Variables status label."""
        try:
            while True:
                self.tournament_sync_status_var.set(
                    self._tournament_sync_status_queue.get_nowait()
                )
        except queue.Empty:
            pass
        self.master.after(500, self._poll_tournament_sync_status)

    def on_csv_file_changed(self, event=None):
        # Game selection/team names always come from the ORIGINAL draw.
        game_flow.on_csv_file_changed(self, event)

        draw_path = self._selected_tournament_draw()
        if draw_path:
            try:
                # Create only if missing; retain completed games after reboot.
                result_path = tournament_files.ensure_results_file(draw_path)
                self.tournament_results_var.set(
                    os.path.basename(result_path)
                )
                self.tournament_results_dropdown.configure(
                    values=(os.path.basename(result_path),)
                )
            except (OSError, ValueError) as error:
                print(f"TOURNAMENT RESULTS: {error}")
                self.tournament_results_var.set("Results unavailable")
                if event is not None:
                    messagebox.showerror(
                        "Tournament Results",
                        f"Cannot prepare the results file:\n{error}",
                        parent=self.master
                    )
        else:
            self.tournament_results_var.set("No results file")
        self._configure_tournament_sync()

    def on_court_game_mode_changed(self, event=None):
        return game_flow.on_court_game_mode_changed(
            self,
            event
        )

    def get_current_game_number(self):
        return game_flow.get_current_game_number(self)

    def update_game_number_display(self):
        """Update the visible game number, including next-game preview."""
        if (
            getattr(self, "next_game_preview_active", False)
            and getattr(self, "next_game_preview_number", None)
        ):
            self.game_number_var.set(
                f"Game #{self.next_game_preview_number}"
            )
            self.update_team_names_display()
            return

        return game_flow.update_game_number_display(self)

    def on_use_tournament_list_changed(self):
        """
        Apply the Use Tournament List checkbox state.

        When disabled:
        - the tournament CSV dropdown is greyed out;
        - operator team-name widgets are cleared;
        - presentation team-name widgets are cleared.

        Re-enabling immediately reloads the selected tournament game.
        """
        try:
            use_tournament_list = bool(
                self.use_tournament_list_var.get()
            )

        except (
            AttributeError,
            tk.TclError
        ):
            use_tournament_list = True

        try:
            if hasattr(self, "csv_dropdown"):
                self.csv_dropdown.configure(
                    state=(
                        "readonly"
                        if use_tournament_list
                        else "disabled"
                    )
                )

        except tk.TclError:
            pass

        self.update_team_names_display()

    def update_team_names_display(self):
        """Update team names from the selected tournament game."""
        try:
            use_tournament_list = True

            if hasattr(self, "use_tournament_list_var"):
                use_tournament_list = bool(
                    self.use_tournament_list_var.get()
                )

            # When the Tournament List is disabled, explicitly clear
            # both operator team-name widgets and all display names.
            if not use_tournament_list:
                if hasattr(self, "white_team_name_widget"):
                    self.white_team_name_widget.config(
                        text=""
                    )

                if hasattr(self, "black_team_name_widget"):
                    self.black_team_name_widget.config(
                        text=""
                    )

                self.toggle_display_team_names()
                return

            current_game = (
                self.next_game_preview_number
                if (
                    getattr(self, "next_game_preview_active", False)
                    and getattr(self, "next_game_preview_number", None)
                )
                else self.get_current_game_number()
            )

            # After the final tournament game, deliberately show no teams.
            if not current_game:
                white_team = ""
                black_team = ""

            else:
                csv_file = (
                    self.csv_var.get()
                    if hasattr(self, "csv_var")
                    else None
                )

                white_team, black_team = (
                    self.parse_csv_team_names(
                        csv_file,
                        current_game
                    )
                )

            if hasattr(self, "white_team_name_widget"):
                self.white_team_name_widget.config(
                    text=white_team or ""
                )

            if hasattr(self, "black_team_name_widget"):
                self.black_team_name_widget.config(
                    text=black_team or ""
                )

            self.toggle_display_team_names()

        except Exception as error:
            print(
                f"Error updating team names display: "
                f"{error}"
            )

            if hasattr(self, "white_team_name_widget"):
                self.white_team_name_widget.config(
                    text=""
                )

            if hasattr(self, "black_team_name_widget"):
                self.black_team_name_widget.config(
                    text=""
                )

            self.toggle_display_team_names()
                
    def advance_to_next_game(self):
        return game_flow.advance_to_next_game(self)

    def on_game_selection_changed(self, event=None):
        return game_flow.on_game_selection_changed(self, event)

    def open_csv_folder(self):
        """Open the folder containing CSV files in the system file manager."""
        # CHANGED: Use BASE_DIR instead of os.getcwd() so it always opens the folder containing the EXE and CSVs
        csv_folder = BASE_DIR
        open_folder_in_file_manager(csv_folder)

    def get_sound_trim(self, filename):
        """Return one file's attenuation trim; unknown files default to 100%."""
        return sound.normalise_trim_percent(
            self.sound_trims.get(str(filename), 100.0)
        )

    def set_sound_trim(self, filename, value):
        """Update one file's in-memory trim without changing master volume."""
        self.sound_trims[str(filename)] = sound.normalise_trim_percent(value)

    def create_sounds_tab(self):
        return sounds_ui.create_sounds_tab(self)
        
    def create_zigbee_siren_tab(self):
        return zigbee_ui.create_zigbee_siren_tab(self)
   
    def test_app_siren(self):
        """Test the app siren sound using the same path as timer sirens."""
    
        self.add_to_zigbee_log("Testing app siren sound...")
    
        try:
            play_timed_sound(
                self.siren_var.get(),
                "siren",
                self.enable_sound,
                self.get_sound_trim(self.siren_var.get()),
                self.siren_duration,
                self.max_siren_duration
            )
    
            self.add_to_zigbee_log("App siren sound started")
    
        except Exception as e:
            self.add_to_zigbee_log(f"App siren test failed: {e}")

    def _make_press_handler(self, idx):
        return lambda event: self._start_button_hold(event, idx)

    def _make_release_handler(self, idx):
        return lambda event: self._button_release(event, idx)

    def set_widget2_button_text(self, idx, new_text):
        return preset_manager.set_widget2_button_text(
            self,
            idx,
            new_text
        )

    def save_preset_settings(self):
        return save_preset_settings(self.button_data)

    def load_preset_settings(self):
        return settings_manager.load_preset_settings(BASE_DIR)

    def _start_button_hold(self, event, idx):
        return preset_manager.start_button_hold(
            self,
            event,
            idx
        )

    def _button_release(self, event, idx):
        return preset_manager.button_release(
            self,
            event,
            idx
        )

    def _apply_button_data(self, idx):
        return preset_manager.apply_button_data(
            self,
            idx
        )
    
    def _open_button_dialog(self, idx, trigger_button=None):
        return preset_manager.open_button_dialog(
            self,
            idx,
            trigger_button
        )

    def _on_settings_variable_change(self, *args):
        if getattr(self, "_loading_game_settings", False):
            return
        self.load_settings()
        self.build_game_sequence()
        # Save game settings when variables change
        self.save_game_settings()
    
    def _on_single_variable_change(self, var_name):
        """Handle change to a single variable without updating all widgets."""
        if getattr(self, "_loading_game_settings", False):
            return
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
        """Calculate First Game Starts In for H.MM/HH.MM or colon clock times."""
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
                normalized_time = time_entry_val.replace(".", ":")
                time_match = re.match(
                    r"^(?:[01]?[0-9]|2[0-3]):[0-5][0-9]$",
                    normalized_time
                )
                if time_match:
                    hh, mm = map(int, normalized_time.split(":"))
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
                
                # v1.3 presents clock times as HH.mm.
                time_str = f"{target.hour:02d}.{target.minute:02d}"
                
                # Update the widget
                time_widget.delete(0, tk.END)
                time_widget.insert(0, time_str)
                self.variables["time_to_start_first_game"]["value"] = time_str
            except Exception:
                pass  # If parsing fails, don't update

    def load_settings(self):
        """Restore saved Game Variables and screen preferences into Tk.
        """
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
                # Use the same H:MM / HH:MM 24-hour rule as the input
                # validator and build_game_sequence; 9:36 and 09:36 are equal.
                time_match = re.match(r"^(?:[01]?[0-9]|2[0-3]):[0-5][0-9]$", time_entry_val)
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
        return sounds_ui.save_sound_settings_method(self)
        
    def load_game_settings(self):
        return game_settings_manager.load_game_settings(self)
                        
    def save_game_settings(self):
        """Queue automatic Game Variables changes for the minute save."""
        game_settings = game_settings_manager.build_game_settings(self)
        if game_settings is not None:
            self._queue_settings_section("gameSettings", game_settings)

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
        """
        Receive Zigbee status changes from any thread.
    
        Do not touch Tkinter here.  The MQTT/Zigbee controller can call this
        method from a worker thread, so place the update in a thread-safe queue.
        """
        self.zigbee_status_queue.put(
            (connected, message)
        )
    
    def process_zigbee_status_queue(self):
        """
        Process queued Zigbee status updates from the Tkinter main thread.
        """
        try:
            while True:
                connected, message = self.zigbee_status_queue.get_nowait()
    
                zigbee_control.update_zigbee_status(
                    self,
                    connected,
                    message
                )
    
        except queue.Empty:
            pass
    
        except tk.TclError:
            # Application is closing.
            return

        # MQTT and serial events enter through a Queue, never Tk from a worker.
        # Bound each pass so a burst of presses cannot starve the UI.
        for _ in range(32):
            try:
                event_name = self.hardware_siren_event_queue.get_nowait()
            except queue.Empty:
                break
            try:
                self._process_hardware_siren_event(event_name)
            except Exception as e:
                print(f"Error processing hardware siren event: {e}")

        try:
            self._zigbee_status_queue_job = self.master.after(
                100,
                self.process_zigbee_status_queue
            )
        except tk.TclError:
            pass

    def update_usb_dongle_status(self, force_rescan=False):
        return zigbee_hardware_ui.update_usb_dongle_status(
            self,
            force_rescan=force_rescan
        )

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
                    port = int(value) if value.isdigit() else 0
                    if not 1 <= port <= 65535:
                        raise ValueError("MQTT port must be between 1 and 65535")
                    config[key] = port
                elif key == "continuous_siren_max_seconds":
                    seconds = float(value.strip().replace(",", "."))
                    if not 1.0 <= seconds <= 30.0:
                        raise ValueError("Maximum continuous siren must be 1 to 30 seconds")
                    config[key] = seconds
                elif key == "siren_button_devices":
                    # Convert comma-separated string to list
                    device_names = [name.strip() for name in value.split(",") if name.strip()]
                    config["siren_button_devices"] = device_names
                    # Also set legacy single device for backward compatibility
                    config["siren_button_device"] = device_names[0] if device_names else ""
                else:
                    config[key] = value
            
            # Keep other settings from current config
            current_config = self.zigbee_controller.config.copy()
            current_config.update(config)
            if hasattr(self, "_zigbee_action_mappings_draft"):
                # The displayed table is part of the configuration: saving
                # general MQTT settings must never discard unsaved row edits.
                current_config["action_mappings"] = [
                    dict(row) for row in self._zigbee_action_mappings_draft
                ]
            
            # Save to both the Zigbee controller and unified settings
            self.zigbee_controller.save_config(current_config)
            
            # Also save to unified settings file
            unified_settings = load_unified_settings()
            unified_settings["zigbeeSettings"] = current_config
            save_unified_settings(unified_settings)
            
            if hasattr(self, "_zigbee_map_dirty"):
                self._zigbee_map_dirty = False
            if hasattr(self, "_zigbee_mapping_save_btn"):
                self._zigbee_mapping_save_btn.config(text="Save Action Mappings")
            if hasattr(self, "refresh_zigbee_device_list"):
                self.refresh_zigbee_device_list()
            self.add_to_zigbee_log("Configuration saved")
            messagebox.showinfo("Configuration", "Zigbee configuration saved successfully!")
        except Exception as e:
            self.add_to_zigbee_log(f"Error saving config: {e}")
            messagebox.showerror("Configuration Error", f"Error saving configuration: {e}")

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
        if getattr(self, "_loading_game_settings", False):
            return
        # Update the variable
        self.variables["team_timeouts_allowed"]["used"] = self.team_timeouts_allowed_var.get()
        # Update UI state
        self.update_team_timeouts_allowed()
        # team_timeouts_allowed doesn't affect game sequence structure, only UI state
        # So we don't need to rebuild the sequence
        self.save_game_settings()
    
    def _on_overtime_change(self):
        """Handle overtime_allowed checkbox change."""
        if getattr(self, "_loading_game_settings", False):
            return
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
        return display_ui.create_display_window(self)
    
    def sync_display_widgets(self):
        """
        Synchronise presentation period backgrounds only when needed.

        Called when the period background changes or when a
        presentation window is first created. No polling.
        """
        try:
            background = self.half_label.cget("bg")
        except (AttributeError, tk.TclError):
            return

        # Primary presentation window.
        labels = [
            getattr(self, "display_half_label", None)
        ]

        # Additional mirrored presentation windows, if present.
        for bundle in getattr(
            self,
            "display_mirror_bundles",
            []
        ):
            labels.append(
                bundle.get("widgets", {}).get("half")
            )

        for label in labels:
            if label is None:
                continue

            try:
                if (
                    label.winfo_exists()
                    and label.cget("bg") != background
                ):
                    label.config(bg=background)

            except (AttributeError, tk.TclError):
                pass
    
    def reset_timer(self):
        """Apply the current Game Variables to the engine and restart its clock.
        """
        self.white_score_var.set(0)
        self.black_score_var.set(0)

        self.engine.reset_to_first_period()
        self.engine.start_timer()
        self.engine.clear_sudden_death_goal()

        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        if self.court_time_job:
            self.master.after_cancel(self.court_time_job)
            self.court_time_job = None

        if self.sudden_death_timer_job:
            self.master.after_cancel(self.sudden_death_timer_job)
            self.sudden_death_timer_job = None

        # clear_sudden_death_goal() above also resets the count-up seconds
        # and any correction-window restoration timestamp.

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
        """Advance court time on Tk's event loop while respecting pauses.
        """
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
        """Refresh displayed timer values from the current engine state.
        """
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
        """Shorten the break when needed to realign court and local time.
        """
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
        """Apply the chosen period's timer, widgets and sound cues.
        """
        if self.engine.current_index >= len(self.engine.full_sequence):
            self.engine.reset_to_between_game_break()

        cur_period = self.engine.get_current_period()

        # Cancel any old Between Game Break jobs before configuring
        # the current period. New jobs are scheduled after the effective
        # break duration has been adjusted for crib time.
        for job_attribute in (
            "next_game_transition_job",
            "next_game_preview_job"
        ):
            job = getattr(self, job_attribute, None)

            if job:
                try:
                    self.master.after_cancel(job)
                except tk.TclError:
                    pass

                setattr(self, job_attribute, None)

        if cur_period["name"] == "Between Game Break":
            self.next_game_transition_done = False
            self.next_game_preview_active = False
            self.next_game_preview_number = None
            self.next_game_notice_active = False

        else:
            # A new game or other period has started. Remove any
            # next-game preview and Next Game message.
            self.next_game_preview_active = False
            self.next_game_preview_number = None
            self.next_game_notice_active = False

        # Shorten Between Game Break if court time is behind local time
        # because of a referee timeout, etc.
        if cur_period["name"] == "Between Game Break":
            # Reset Between Game Break to configured duration before
            # applying crib-time adjustment.
            cur_period["duration"] = self.get_minutes(
                "between_game_break"
            )

            now = datetime.datetime.now()
            local_seconds = (
                now.hour * 3600
                + now.minute * 60
                + now.second
            )
            court_seconds = self.court_time_seconds

            if local_seconds > court_seconds:
                delta = local_seconds - court_seconds
                crib_time = 0

                try:
                    crib_var = self.variables["crib_time"]
                    crib_time = int(
                        float(
                            crib_var.get(
                                "value",
                                crib_var["default"]
                            )
                        )
                    )
                except Exception:
                    crib_time = 0

                # Only reduce by crib_time maximum, never by more.
                reduce_by = min(delta, crib_time)

                if (
                    reduce_by > 0
                    and cur_period["duration"] is not None
                ):
                    # Preserve the existing minimum duration.
                    new_duration = (
                        cur_period["duration"] - reduce_by
                    )
                    cur_period["duration"] = max(
                        32,
                        new_duration
                    )

            # Show the next game no later than 30 seconds after the
            # previous game and at least 30 seconds before the next one.
            #
            # Examples:
            #   45-second break  -> preview after 15 seconds
            #   120-second break -> preview after 30 seconds
            break_duration = max(
                0,
                int(round(float(cur_period.get("duration") or 0)))
            )
            preview_after_seconds = max(
                0,
                min(30, break_duration - 30)
            )

            self.next_game_preview_job = self.master.after(
                preview_after_seconds * 1000,
                self.run_next_game_preview
            )

            # Export is intentionally driven by countdown_timer, not an
            # independent time-after-break-start job. It runs as 31 seconds
            # becomes 30, before the 30-second warning pip can sound.
            # This also follows pauses and changes to the break duration.

        if self.engine.is_regular_timeout_reset_period(
            cur_period["name"]
        ):
            self.engine.reset_half_timeouts()

        self.half_label_var.set(cur_period["name"])
        self.update_half_label_background(cur_period["name"])

        # Always enable penalties during Referee Time-Out, even if
        # entered from First Game Starts In.
        if self.engine.is_referee_timeout(cur_period["name"]):
            self.penalties_button.config(state=tk.NORMAL)
            self.white_timeout_button.config(
                state=tk.DISABLED,
                bg="#d3d3d3",
                fg="#888"
            )
            self.black_timeout_button.config(
                state=tk.DISABLED,
                bg="#d3d3d3",
                fg="#888"
            )

        elif self.engine.is_timeout_disabled_period(
            cur_period["name"]
        ):
            self.white_timeout_button.config(
                state=tk.DISABLED,
                bg="#d3d3d3",
                fg="#888"
            )
            self.black_timeout_button.config(
                state=tk.DISABLED,
                bg="#d3d3d3",
                fg="#888"
            )

            if self.engine.is_penalty_disabled_period(
                cur_period["name"]
            ):
                self.penalties_button.config(state=tk.DISABLED)
            else:
                self.penalties_button.config(state=tk.NORMAL)

        elif cur_period["name"] == "Between Game Break":
            self.white_timeout_button.config(
                state=tk.DISABLED,
                bg="#d3d3d3",
                fg="#888"
            )
            self.black_timeout_button.config(
                state=tk.DISABLED,
                bg="#d3d3d3",
                fg="#888"
            )
            self.penalties_button.config(state=tk.DISABLED)

        else:
            if self.team_timeouts_allowed_var.get():
                self.white_timeout_button.config(
                    state=tk.NORMAL,
                    bg="white",
                    fg="black"
                )
                self.black_timeout_button.config(
                    state=tk.NORMAL,
                    bg="black",
                    fg="white"
                )
            else:
                self.white_timeout_button.config(
                    state=tk.DISABLED,
                    bg="#d3d3d3",
                    fg="#888"
                )
                self.black_timeout_button.config(
                    state=tk.DISABLED,
                    bg="#d3d3d3",
                    fg="#888"
                )

            self.penalties_button.config(state=tk.NORMAL)

        if self.engine.is_penalty_pause_period(
            cur_period["name"]
        ):
            self.pause_all_penalty_timers()
        else:
            self.resume_all_penalty_timers()

        if self.engine.is_court_time_paused_period(
            cur_period["name"]
        ):
            self.court_time_paused = True
        else:
            self.court_time_paused = False

        if self.engine.is_sudden_death(cur_period["name"]):
            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None

            if self.sudden_death_timer_job:
                self.master.after_cancel(
                    self.sudden_death_timer_job
                )
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
                cur_period["duration"]
                if cur_period["duration"] is not None
                else 0
            )
            self.update_timer_display()
            self.engine.start_timer()

            if self.timer_job:
                self.master.after_cancel(self.timer_job)
                self.timer_job = None

            self.timer_job = self.master.after(
                1000,
                self.countdown_timer
            )

            event_name = self.engine.period_start_event_name(
                cur_period["name"]
            )

            if event_name:
                self.log_game_event(event_name)

        # Refresh penalty / Next Game area whenever a period begins.
        self.update_penalty_display()

    def get_next_game_number_for_preview(self):
        """Return the next tournament game without advancing internal state."""
        try:
            if not self.game_numbers:
                return None

            current_game = self.get_current_game_number()

            if current_game in self.game_numbers:
                current_index = self.game_numbers.index(current_game)
            else:
                current_index = int(
                    getattr(self, "current_game_index", 0)
                )

            next_index = (current_index + 1) % len(self.game_numbers)
            return self.game_numbers[next_index]

        except (
            AttributeError,
            TypeError,
            ValueError
        ):
            return None

    def run_next_game_preview(self):
        """Show the next game while retaining the completed result internally."""
        self.next_game_preview_job = None

        cur_period = self.engine.get_current_period()

        if not cur_period or cur_period["name"] != "Between Game Break":
            return

        try:
            if (
                hasattr(self, "use_tournament_list_var")
                and not self.use_tournament_list_var.get()
            ):
                return
        except tk.TclError:
            return

        next_game = self.get_next_game_number_for_preview()

        if next_game is None:
            return

        self.next_game_preview_number = next_game
        self.next_game_preview_active = True
        self.next_game_notice_active = True

        # This changes only the visible game number and team names.
        # The completed game's scores and penalties remain internally
        # available for buzzer corrections until 30 seconds remain in the break.
        self.update_game_number_display()
        self.update_penalty_display()

    def _show_game_export_error(self, reason):
        """Keep the finished game intact; offer a non-modal CSV export retry."""
        if not self._game_export_pending:
            return

        # A failed export must not allow the break timer to advance into the
        # next game while its scores still belong to the completed game.
        self._game_export_timer_was_running |= bool(self.engine.timer_running)
        self.engine.stop_timer()
        if self.timer_job is not None:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        # Preview is cosmetic; reverting it makes the unsaved game unmistakable.
        self.next_game_preview_active = False
        self.next_game_preview_number = None
        self.next_game_notice_active = False
        self.update_game_number_display()
        self.update_penalty_display()
        self.update_timer_display()

        message = (
            f"Results for game {self._pending_export_game_number or '(unspecified)'} "
            "were NOT saved. Scores, penalties and goal scorers are intact; "
            "the break timer is paused.\n\n"
            f"{reason}\n\n"
            "Correct the selected tournament CSV or its file permissions, "
            "then press Retry Export. You can still use the main window "
            "while this warning is open."
        )
        print(f"CSV EXPORT FAILURE: {message}")
        popup = self._game_export_dialog
        if popup is None or not popup.winfo_exists():
            popup = tk.Toplevel(self.master)
            popup.title("Game results not saved")
            popup.transient(self.master)
            popup.resizable(False, False)
            self._game_export_dialog = popup
            panel = ttk.Frame(popup, padding=14)
            panel.pack(fill="both", expand=True)
            self._game_export_error_label = ttk.Label(
                panel, justify="left", wraplength=470,
            )
            self._game_export_error_label.pack(anchor="w", pady=(0, 12))
            buttons = ttk.Frame(panel)
            buttons.pack(fill="x")
            ttk.Button(
                buttons, text="Retry Export",
                command=self.run_next_game_transition,
            ).pack(side="right", padx=(8, 0))
            # The dialog is non-modal, so the operator can correct the CSV.
            # Closing it would otherwise strand the unsaved match without a
            # visible Retry button, so keep it available until the save works.
            popup.protocol("WM_DELETE_WINDOW", lambda: popup.lift())
            self._game_export_error_label.config(text=message)

            # Keep the dialog with its parent, including on a second monitor.
            popup.update_idletasks()
            left = self.master.winfo_rootx()
            width = self.master.winfo_width()
            popup_width = popup.winfo_reqwidth()
            x = left + max(10, (width - popup_width) // 2)
            y = self.master.winfo_rooty() + 90
            popup.geometry(f"+{x}+{y}")

        self._game_export_error_label.config(text=message)
        popup.lift()

    def run_next_game_transition(self):
        """Export the finished game before clearing it or advancing."""
        self.next_game_transition_job = None

        cur_period = self.engine.get_current_period()
        if not cur_period or cur_period["name"] != "Between Game Break":
            return
        if self.next_game_transition_done:
            return

        # A CSV selection might change while the operator resolves an export
        # error. Never silently substitute the new selection's game number.
        if not self._game_export_pending:
            self._game_export_pending = True
            self._pending_export_game_number = self.get_current_game_number()

        try:
            exported = game_flow.export_and_reset_game_at_break(
                self, game_number=self._pending_export_game_number
            )
        except Exception as error:
            self._show_game_export_error(str(error))
            return

        if not exported:
            self._show_game_export_error(
                "The selected CSV is unavailable, missing required columns "
                "(WScore, BScore, Penalties, Comments), or has no matching "
                "game-number row."
            )
            return

        self.next_game_transition_done = True
        self._game_export_pending = False
        self._pending_export_game_number = None
        popup = self._game_export_dialog
        self._game_export_dialog = None
        self._game_export_error_label = None
        if popup is not None and popup.winfo_exists():
            popup.destroy()

        # A failed export paused the break. Continue its remaining seconds
        # only after the CSV has been saved successfully.
        if self._game_export_timer_was_running:
            self.engine.start_timer()
            if self.timer_job is None and self.engine.timer_seconds > 0:
                self.timer_job = self.master.after(1000, self.countdown_timer)
        self._game_export_timer_was_running = False

        self.next_game_preview_active = False
        self.next_game_preview_number = None
        self.next_game_notice_active = True
        self.update_game_number_display()
        self.update_penalty_display()

    def next_period(self):
        """End this period and enter the next, respecting any pending export.
        """
        # An operator can advance the break before its last 30 seconds.
        # Still save the completed game before entering the next period.
        cur_period = self.engine.get_current_period()
        if (cur_period and cur_period["name"] == "Between Game Break"
                and not self.next_game_transition_done):
            self.run_next_game_transition()
        if self._game_export_pending:
            return
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
        """Tick the game timer and dispatch period sounds and export.
        Export must precede the 30-second pip; failure prevents advance.
        """
        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        if not self.engine.timer_running:
            self.update_timer_display()
            return

        if self.engine.timer_seconds > 0:
            cur_period = self.engine.get_current_period()

            # The 30-second warning pip fires while timer_seconds == 31,
            # immediately before the display changes to 00:30. Export
            # FIRST, on this same countdown callback. A failed write pauses
            # at 00:31 so neither the pip nor next game can proceed.
            # <= 31 also handles exceptionally short/adjusted breaks.
            if (cur_period and cur_period["name"] == "Between Game Break"
                    and not self.next_game_transition_done
                    and self.engine.timer_seconds <= 31):
                self.run_next_game_transition()
                if self._game_export_pending or not self.engine.timer_running:
                    self.update_timer_display()
                    return

            if self.engine.should_play_period_end_siren(cur_period):
                try:
                    play_timed_sound(
                        self.siren_var.get(),
                        "siren",
                        self.enable_sound,
                        self.get_sound_trim(self.siren_var.get()),
                        self.siren_duration,
                        self.max_siren_duration
                    )
                except Exception as e:
                    print(f"Error playing period-end siren: {e}")

            if (
                cur_period
                and cur_period.get("type") == "break"
                and self.engine.should_play_break_countdown_pip(cur_period)
            ):
                try:
                    play_timed_sound(
                        self.pips_var.get(),
                        "pips",
                        self.enable_sound,
                        self.get_sound_trim(self.pips_var.get()),
                        self.siren_duration,
                        self.max_siren_duration
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
        """Enable only the remaining team timeouts for this half.
        """
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
        """Start or resume the White team's timeout.
        """
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
        """Start or resume the Black team's timeout.
        """
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
        """Update the active timeout and its displayed count.
        """
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
                    play_timed_sound(
                        self.pips_var.get(),
                        "pips",
                        self.enable_sound,
                        self.get_sound_trim(self.pips_var.get()),
                        self.siren_duration,
                        self.max_siren_duration
                    )
                except Exception as e:
                    print(f"Error playing pip sound at 16s timeout: {e}")

            # Enhancement: Play end-of-timeout siren at 1 second.
            # Plays BEFORE decrementing, so the siren command is sent before
            # the screen changes from 00:01 to 00:00.
            # Only play if no pending timeout exists.
            if self.engine.timer_seconds == 1 and self.pending_timeout is None:
                try:
                    play_timed_sound(
                        self.siren_var.get(),
                        "siren",
                        self.enable_sound,
                        self.get_sound_trim(self.siren_var.get()),
                        self.siren_duration,
                        self.max_siren_duration
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
        """End a team timeout and restore the interrupted game timer.
        """
        self.in_timeout = False
        prev_active_team = self.engine.active_timeout_team
        self.engine.end_timeout()
        self.court_time_paused = False
        # Restart the court-time callback if it was cancelled,
        # for example during an intervening referee time-out.
        if self.court_time_job is None:
            self.court_time_job = self.master.after(
                1000,
                self.update_court_time
            )
        self.resume_all_penalty_timers()
        state = self.team_timeout_saved_state

        self.engine.timer_running = state["timer_running"]
        self.engine.timer_seconds = state["timer_seconds"]
        self.engine.current_index = state["current_index"]

        self.half_label_var.set(state["half_label"])
        self.half_label.config(bg=state["half_label_bg"])
        self.sync_display_widgets()
        self.update_timer_display()

        if self.timer_job:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        # End-of-timeout siren is now played in timeout_countdown()
        # when timer_seconds == 1, before display changes to 00:00.
        # Do not play it here or it will be late / double-trigger.

        # Start a queued second team time-out, if permitted.
        pending = self.pending_timeout
        self.pending_timeout = None

        if (
            pending == "white"
            and self.engine.white_timeouts_this_half < 1
        ):
            self.white_team_timeout(preserve_saved_state=True)
            if self.in_timeout:
                return

        elif (
            pending == "black"
            and self.engine.black_timeouts_this_half < 1
        ):
            self.black_team_timeout(preserve_saved_state=True)
            if self.in_timeout:
                return

        # No second time-out started. Restore the original game clock,
        # but only if it was running before the time-out.
        if self.engine.timer_running:
            self.timer_job = self.master.after(
                1000,
                self.countdown_timer
            )

        print(
            "TEAM TIMEOUT END:",
            f"running={self.engine.timer_running}",
            f"seconds={self.engine.timer_seconds}",
            f"job={self.timer_job}",
            f"pending={pending}",
            flush=True
        )

    def save_timer_state(self):
        """Capture the clock before a timeout temporarily replaces it.
        """
    
        self.team_timeout_saved_state = {
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
            background = "red"
        else:
            background = "lightblue"

        if self.half_label.cget("bg") != background:
            self.half_label.config(bg=background)

        # Event-driven update of presentation backgrounds.
        self.sync_display_widgets()

    def convert_duration_to_seconds(self, duration):
        if duration == "1 minute":
            return 60
        elif duration == "2 minutes":
            return 120
        elif duration == "5 minutes":
            return 300
        elif duration in (
            "Total Dismissal",
            "Rest of the match"
        ):
            # Accept the former wording for compatibility with any
            # existing saved data, but use Total Dismissal in the UI.
            return -1
        return 0

    def start_penalty_timer(self, team, cap, duration):
        """Create an active penalty from the referee's choice.
        """
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
        """Schedule the next active-penalty tick.
        """
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
        """Remove the chosen penalty and refresh the displayed list.
        """
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
        """Suspend penalties while the game clock is paused.
        """
        self.penalty_timers_paused = True
        for penalty in self.engine.active_penalties:
            if penalty["timer_job"]:
                self.master.after_cancel(penalty["timer_job"])
                penalty["timer_job"] = None
        self.update_penalty_display()

    def resume_all_penalty_timers(self):
        """Reschedule penalties after play resumes.
        """
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
        return penalties_ui.show_penalties(self, trigger_button)
    
    def toggle_referee_timeout(self):
        """Pause or resume the affected clocks and penalty timers together.
        """
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
            self.sync_display_widgets()

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
            self.sync_display_widgets()

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
        """Restore Sudden Death after correcting the deciding goal.
        """
        self.engine.sudden_death_goal_scored = False
        self.engine.go_to_period('Sudden Death')
        self.engine.sudden_death_seconds = self.engine.sudden_death_restore_time
        self.engine.sudden_death_restore_active = False
        self.engine.sudden_death_restore_time = None
        self.start_current_period()

    def adjust_score_with_confirm(self, score_var, team_name):
        """Confirm a subtraction, with extra warning during a break.
        """
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
        """Confirm break-period goals and optional scorer before scoring.
        Cancellation must leave the current score unchanged.
        """
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
    
    # The title-bar close button, Exit Program button and Ctrl+Q
    # all use the same clean shutdown path.
    root.protocol("WM_DELETE_WINDOW", app.request_exit)

    def debug_root_destroy(event):
        if event.widget == root:
            print("DEBUG: ROOT WINDOW IS BEING DESTROYED")

    root.bind(
        "<Destroy>",
        debug_root_destroy,
        add="+"
    )
    # Start processing Zigbee worker-thread status messages once
    # Tkinter's event loop begins.
    root.after(
        0,
        app.process_zigbee_status_queue
    )
    print("DEBUG: ABOUT TO ENTER TK MAINLOOP")
    root.mainloop()
    print("DEBUG: TK MAINLOOP RETURNED")
