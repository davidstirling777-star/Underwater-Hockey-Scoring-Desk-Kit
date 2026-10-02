"""Sounds tab: audio-file choices, volume tests, output reporting and timing.

The ordinary siren duration controls a timed blast; Maximum Siren Duration
caps it independently. The Arduino's wired hold-to-sound path is deliberately
different. sound.py owns playback and its independent audio timeout.
"""

import datetime
import math
import os
import tkinter as tk
from tkinter import messagebox, ttk

from sound import (
    AUDIO_OUTPUT_AT_STARTUP,
    check_audio_device_available,
    get_sound_files,
    play_timed_sound,
    resource_path,
)


def create_sounds_tab(app):
    """Create the Sounds tab and its controls."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Sounds")

    tab.grid_rowconfigure(0, weight=1)
    tab.grid_columnconfigure(0, weight=1)

    sounds_widget = tk.LabelFrame(
        tab,
        text="Sounds",
        borderwidth=2,
        relief="solid"
    )
    sounds_widget.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=8,
        pady=8
    )

    for row in range(9):
        sounds_widget.grid_rowconfigure(row, weight=1)
    for column in range(4):
        sounds_widget.grid_columnconfigure(column, weight=1)
    sounds_widget.grid_columnconfigure(3, weight=0)

    sound_files = get_sound_files()
    if sound_files == ["No sound files found"]:
        sound_files = []

    pips_options = [
        filename for filename in sound_files if "pip" in filename.lower()
    ]
    siren_options = [
        filename for filename in sound_files if "siren" in filename.lower()
    ]

    if app.pips_var.get() not in pips_options:
        app.pips_var.set(pips_options[0] if pips_options else "")
    if app.siren_var.get() not in siren_options:
        app.siren_var.set(siren_options[0] if siren_options else "")

    def app_log(message):
        try:
            app.add_to_zigbee_log(message)
        except Exception:
            pass

    def ensure_audio_device(sound_var, sound_type):
        """Warn once when sound is enabled but no usable audio device exists."""
        if check_audio_device_available(app.enable_sound):
            return True

        if not app.audio_device_warning_shown:
            messagebox.showwarning(
                "Audio Device Warning",
                f"No audio device detected. Cannot play {sound_type} sounds.\n\n"
                "The sound selection has been cleared."
            )
            app.audio_device_warning_shown = True

        sound_var.set("")
        return False

    def open_sounds_folder():
        """Open the same assets folder that get_sound_files() scans."""
        sounds_folder = resource_path("assets")

        try:
            os.makedirs(sounds_folder, exist_ok=True)
            if os.name == "nt":
                os.startfile(sounds_folder)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", sounds_folder])
        except (OSError, AttributeError) as error:
            messagebox.showerror(
                "Open Sounds Folder",
                f"Could not open the sounds folder:\n{error}"
            )

    def play_selected_sound(sound_var, sound_type):
        """Play the selected test sound after basic validation."""
        sound_file = sound_var.get().strip()

        if not sound_file:
            messagebox.showwarning(
                "No Sound Selected",
                f"Choose a {sound_type} sound file first."
            )
            return

        if not ensure_audio_device(sound_var, sound_type):
            return

        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            volume = (
                app.pips_volume.get()
                if sound_type == "pips"
                else app.siren_volume.get()
            )
            print(
                f"[{timestamp}] {sound_type.title()} sound test started: "
                f"file='{sound_file}', volume={volume}%"
            )
            app_log(
                f"{sound_type.title()} test: "
                f"{sound_file} (Vol: {volume}%)"
            )

            play_timed_sound(
                sound_file,
                sound_type,
                app.enable_sound,
                app.pips_volume,
                app.siren_volume,
                app.siren_duration,
                app.max_siren_duration
            )

            app_log(
                f"{sound_type.title()} sound playback initiated successfully"
            )

        except Exception as error:
            print(
                f"Error testing {sound_type} sound: "
                f"{type(error).__name__}: {error}"
            )
            app_log(
                f"ERROR testing {sound_type}: "
                f"{type(error).__name__}: {error}"
            )

    save_btn = tk.Button(
        sounds_widget,
        text="Save Settings",
        font=("Arial", 11),
        command=app.save_sound_settings_method
    )
    save_btn.grid(row=0, column=0)

    enable_sound_cb = tk.Checkbutton(
        sounds_widget,
        text="Enable Sound?",
        font=("Arial", 11),
        variable=app.enable_sound
    )
    enable_sound_cb.grid(row=1, column=0, sticky="w")

    audio_output_label = tk.Label(
        sounds_widget,
        text=(
            f"Audio output in use: {AUDIO_OUTPUT_AT_STARTUP}\n"
            "(selected when UWH started)"
        ),
        font=("Arial", 10),
        justify="left",
        anchor="w",
    )
    audio_output_label.grid(
        row=0,
        column=1,
        columnspan=3,
        rowspan=2,
        sticky="w",
        padx=(10, 0),
    )

    tk.Label(
        sounds_widget,
        text="Pips",
        font=("Arial", 12)
    ).grid(row=2, column=0, sticky="nsew")

    pips_dropdown = ttk.Combobox(
        sounds_widget,
        textvariable=app.pips_var,
        values=pips_options,
        state="readonly"
    )
    pips_dropdown.grid(
        row=2,
        column=1,
        columnspan=2,
        sticky="ew",
        padx=(0, 10)
    )
    pips_dropdown.bind(
        "<<ComboboxSelected>>",
        lambda event: ensure_audio_device(app.pips_var, "pips")
    )

    tk.Button(
        sounds_widget,
        text="Play",
        font=("Arial", 11),
        width=5,
        command=lambda: play_selected_sound(app.pips_var, "pips")
    ).grid(row=2, column=3)

    # Row 3: Pips volume
    tk.Label(
        sounds_widget,
        text="Pips Vol",
        font=("Arial", 11)
    ).grid(row=3, column=0, sticky="ew")

    pips_vol_slider = tk.Scale(
        sounds_widget,
        from_=0,
        to=100,
        orient="horizontal",
        variable=app.pips_volume,
        font=("Arial", 10),
        showvalue=False
    )
    pips_vol_slider.grid(
        row=3,
        column=1,
        columnspan=2,
        sticky="ew"
    )

    pips_vol_label = tk.Label(
        sounds_widget,
        text=f"{app.pips_volume.get()}%",
        font=("Arial", 11),
        width=5
    )
    pips_vol_label.grid(row=3, column=3, sticky="w")

    def on_pips_slider_interaction(event=None):
        pips_vol_label.config(text=f"{app.pips_volume.get()}%")
        ensure_audio_device(app.pips_var, "pips")

    pips_vol_slider.bind("<Button-1>", on_pips_slider_interaction)
    pips_vol_slider.bind("<B1-Motion>", on_pips_slider_interaction)
    pips_vol_slider.bind(
        "<ButtonRelease-1>",
        on_pips_slider_interaction
    )

    tk.Button(
        sounds_widget,
        text="Open Sounds Folder",
        font=("Arial", 11),
        command=open_sounds_folder
    ).grid(row=4, column=1, columnspan=2, pady=6)

    tk.Label(
        sounds_widget,
        text="Siren",
        font=("Arial", 12)
    ).grid(row=5, column=0, sticky="nsew")

    siren_dropdown = ttk.Combobox(
        sounds_widget,
        textvariable=app.siren_var,
        values=siren_options,
        state="readonly"
    )
    siren_dropdown.grid(
        row=5,
        column=1,
        columnspan=2,
        sticky="ew",
        padx=(0, 10)
    )
    siren_dropdown.bind(
        "<<ComboboxSelected>>",
        lambda event: ensure_audio_device(app.siren_var, "siren")
    )

    tk.Button(
        sounds_widget,
        text="Play",
        font=("Arial", 11),
        width=5,
        command=lambda: play_selected_sound(app.siren_var, "siren")
    ).grid(row=5, column=3)

    # Row 6: Siren volume
    tk.Label(
        sounds_widget,
        text="Siren Vol",
        font=("Arial", 11)
    ).grid(row=6, column=0, sticky="ew")

    siren_vol_slider = tk.Scale(
        sounds_widget,
        from_=0,
        to=100,
        orient="horizontal",
        variable=app.siren_volume,
        font=("Arial", 10),
        showvalue=False
    )
    siren_vol_slider.grid(
        row=6,
        column=1,
        columnspan=2,
        sticky="ew"
    )

    siren_vol_label = tk.Label(
        sounds_widget,
        text=f"{app.siren_volume.get()}%",
        font=("Arial", 11),
        width=5
    )
    siren_vol_label.grid(row=6, column=3, sticky="w")

    def on_siren_slider_interaction(event=None):
        siren_vol_label.config(text=f"{app.siren_volume.get()}%")
        ensure_audio_device(app.siren_var, "siren")

    siren_vol_slider.bind("<Button-1>", on_siren_slider_interaction)
    siren_vol_slider.bind("<B1-Motion>", on_siren_slider_interaction)
    siren_vol_slider.bind(
        "<ButtonRelease-1>",
        on_siren_slider_interaction
    )

    tk.Label(
        sounds_widget,
        text="Number of seconds to play Siren",
        font=("Arial", 11)
    ).grid(row=7, column=0, sticky="ew")

    siren_duration_entry = tk.Entry(
        sounds_widget,
        textvariable=app.siren_duration,
        font=("Arial", 11),
        width=10
    )
    siren_duration_entry.grid(
        row=7,
        column=1,
        columnspan=2,
        sticky="w",
        padx=(0, 10)
    )

    def validate_siren_duration(new_value):
        if new_value == "":
            return True
        try:
            float(new_value.replace(",", "."))
            return True
        except ValueError:
            return False

    validation_command = (
        sounds_widget.register(validate_siren_duration),
        "%P"
    )
    siren_duration_entry.config(
        validate="key",
        validatecommand=validation_command
    )

    def normalize_siren_duration(event=None):
        try:
            raw_value = siren_duration_entry.get().strip()
            if not raw_value:
                app.siren_duration.set(1.5)
                return
            app.siren_duration.set(float(raw_value.replace(",", ".")))
        except (ValueError, tk.TclError):
            app.siren_duration.set(1.5)

    siren_duration_entry.bind("<FocusOut>", normalize_siren_duration)
    siren_duration_entry.bind("<Return>", normalize_siren_duration)

    tk.Label(
        sounds_widget,
        text="Maximum Siren Duration (seconds)",
        font=("Arial", 11)
    ).grid(row=8, column=0, sticky="ew")

    max_siren_duration_entry = tk.Entry(
        sounds_widget,
        textvariable=app.max_siren_duration,
        font=("Arial", 11),
        width=10
    )
    max_siren_duration_entry.grid(
        row=8, column=1, columnspan=2, sticky="w", padx=(0, 10)
    )

    last_valid_max = [str(app.max_siren_duration.get())]

    def normalize_max_siren_duration(event=None):
        """Accept 1-30 s; keep a valid value if the user mistypes."""
        try:
            seconds = float(
                str(app.max_siren_duration.get()).strip().replace(",", ".")
            )
            if not math.isfinite(seconds) or not 1.0 <= seconds <= 30.0:
                raise ValueError("Maximum siren duration must be 1-30 seconds.")
        except (ValueError, TypeError, tk.TclError):
            messagebox.showerror(
                "Invalid Maximum Siren Duration",
                "Enter a number between 1 and 30 seconds."
            )
            app.max_siren_duration.set(last_valid_max[0])
            return

        last_valid_max[0] = f"{seconds:g}"
        app.max_siren_duration.set(last_valid_max[0])

    max_siren_duration_entry.bind(
        "<FocusOut>", normalize_max_siren_duration
    )
    max_siren_duration_entry.bind(
        "<Return>", normalize_max_siren_duration
    )


def save_sound_settings_method(app):
    """Save current sound settings to the main settings.json file."""
    try:
        max_duration = float(
            str(app.max_siren_duration.get()).strip().replace(",", ".")
        )
        if not math.isfinite(max_duration) or not 1.0 <= max_duration <= 30.0:
            raise ValueError("Maximum siren duration must be 1-30 seconds.")
    except (ValueError, TypeError, tk.TclError):
        messagebox.showerror(
            "Invalid Maximum Siren Duration",
            "Enter a number between 1 and 30 seconds."
        )
        return

    app.max_siren_duration.set(f"{max_duration:g}")
    settings = {
        "pips_sound": app.pips_var.get(),
        "siren_sound": app.siren_var.get(),
        "pips_volume": app.pips_volume.get(),
        "siren_volume": app.siren_volume.get(),
        "enable_sound": app.enable_sound.get(),
        "siren_duration": app.siren_duration.get(),
        "max_siren_duration": max_duration,
    }

    try:
        app.save_sound_settings(settings)
        print(f"Sound settings saved: {settings}")

    except Exception as error:
        print(f"Error saving sound settings: {error}")
        messagebox.showerror(
            "Save Error",
            f"Could not save sound settings:\n{error}"
        )
        return

    messagebox.showinfo(
        "Settings Saved",
        "Sound settings have been saved."
    )
