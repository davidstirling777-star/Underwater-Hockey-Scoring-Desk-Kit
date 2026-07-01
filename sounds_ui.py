import datetime
import os
import tkinter as tk
from tkinter import messagebox, ttk

from sound import (
    check_audio_device_available,
    get_sound_files,
    play_sound_with_volume,
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

    for row in range(10):
        sounds_widget.grid_rowconfigure(row, weight=1)

    for column in range(6):
        sounds_widget.grid_columnconfigure(column, weight=1)

    sounds_widget.grid_columnconfigure(3, weight=0)

    # The dropdowns contain only actual files with the required text
    # in their names. "Default" is not added to either list.
    sound_files = get_sound_files()
    if sound_files == ["No sound files found"]:
        sound_files = []

    pips_options = [
        filename
        for filename in sound_files
        if "pip" in filename.lower()
    ]

    siren_options = [
        filename
        for filename in sound_files
        if "siren" in filename.lower()
    ]

    # Clean up old saved values, including "Default", and choose the
    # first valid file for each sound type when one is available.
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
        """
        Warn once when sound is enabled but no usable audio device exists.
        Clear the selected file rather than setting it to "Default".
        """
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
            os.startfile(sounds_folder)
        except OSError as error:
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

            if sound_type == "pips":
                volume = app.pips_volume.get()
            else:
                volume = app.siren_volume.get()

            print(
                f"[{timestamp}] {sound_type.title()} sound test started: "
                f"file='{sound_file}', volume={volume}%"
            )
            app_log(
                f"{sound_type.title()} test: "
                f"{sound_file} (Vol: {volume}%)"
            )

            play_sound_with_volume(
                sound_file,
                sound_type,
                app.enable_sound,
                app.pips_volume,
                app.siren_volume,
                app.air_volume,
                app.water_volume,
                app.siren_duration
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

    # Row 0: Save settings
    save_btn = tk.Button(
        sounds_widget,
        text="Save Settings",
        font=("Arial", 11),
        command=app.save_sound_settings_method
    )
    save_btn.grid(row=0, column=0)

    # Row 1: Sound enable control
    enable_sound_cb = tk.Checkbutton(
        sounds_widget,
        text="Enable Sound?",
        font=("Arial", 11),
        variable=app.enable_sound
    )
    enable_sound_cb.grid(row=1, column=0, sticky="w")

    # Row 0-1: Linux volume headings
    tk.Label(
        sounds_widget,
        text="Volume",
        font=("Arial", 12)
    ).grid(row=0, column=4, columnspan=2, sticky="nsew")

    tk.Label(
        sounds_widget,
        text="Air",
        font=("Arial", 12)
    ).grid(row=1, column=4, sticky="nsew")

    tk.Label(
        sounds_widget,
        text="Water",
        font=("Arial", 12)
    ).grid(row=1, column=5, sticky="nsew")

    # Row 2: Pips sound
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

    pips_play_btn = tk.Button(
        sounds_widget,
        text="Play",
        font=("Arial", 11),
        width=5,
        command=lambda: play_selected_sound(app.pips_var, "pips")
    )
    pips_play_btn.grid(row=2, column=3)

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

    # Row 4: button vertically between Pips volume and Siren controls
    open_sounds_folder_btn = tk.Button(
        sounds_widget,
        text="Open Sounds Folder",
        font=("Arial", 11),
        command=open_sounds_folder
    )
    open_sounds_folder_btn.grid(
        row=4,
        column=1,
        columnspan=2,
        pady=6
    )

    # Row 5: Siren sound
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

    siren_play_btn = tk.Button(
        sounds_widget,
        text="Play",
        font=("Arial", 11),
        width=5,
        command=lambda: play_selected_sound(app.siren_var, "siren")
    )
    siren_play_btn.grid(row=5, column=3)

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

    # Row 7: Siren duration
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

            app.siren_duration.set(
                float(raw_value.replace(",", "."))
            )

        except (ValueError, tk.TclError):
            app.siren_duration.set(1.5)

    siren_duration_entry.bind("<FocusOut>", normalize_siren_duration)
    siren_duration_entry.bind("<Return>", normalize_siren_duration)

    # Air volume (Linux only)
    air_vol_slider = tk.Scale(
        sounds_widget,
        from_=100,
        to=0,
        orient="vertical",
        variable=app.air_volume,
        font=("Arial", 10),
        showvalue=False
    )
    air_vol_slider.grid(
        row=2,
        column=4,
        rowspan=5,
        sticky="ns"
    )

    air_vol_label = tk.Label(
        sounds_widget,
        text=f"{app.air_volume.get()}%",
        font=("Arial", 11)
    )
    air_vol_label.grid(row=8, column=4, sticky="n")

    def on_air_slider_interaction(event=None):
        air_vol_label.config(text=f"{app.air_volume.get()}%")

    air_vol_slider.bind("<Button-1>", on_air_slider_interaction)
    air_vol_slider.bind("<B1-Motion>", on_air_slider_interaction)
    air_vol_slider.bind(
        "<ButtonRelease-1>",
        on_air_slider_interaction
    )

    # Water volume (Linux only)
    water_vol_slider = tk.Scale(
        sounds_widget,
        from_=100,
        to=0,
        orient="vertical",
        variable=app.water_volume,
        font=("Arial", 10),
        showvalue=False
    )
    water_vol_slider.grid(
        row=2,
        column=5,
        rowspan=5,
        sticky="ns"
    )

    water_vol_label = tk.Label(
        sounds_widget,
        text=f"{app.water_volume.get()}%",
        font=("Arial", 11)
    )
    water_vol_label.grid(row=8, column=5, sticky="n")

    def on_water_slider_interaction(event=None):
        water_vol_label.config(text=f"{app.water_volume.get()}%")

    water_vol_slider.bind("<Button-1>", on_water_slider_interaction)
    water_vol_slider.bind("<B1-Motion>", on_water_slider_interaction)
    water_vol_slider.bind(
        "<ButtonRelease-1>",
        on_water_slider_interaction
    )

    warning_label = tk.Label(
        sounds_widget,
        text=(
            "These Volume controls do not work on Windows Machines, "
            "only Linux-based machines"
        ),
        font=("Arial", 9, "italic"),
        fg="gray"
    )
    warning_label.grid(
        row=9,
        column=0,
        columnspan=6,
        sticky="ew",
        pady=(10, 0)
    )


def save_sound_settings_method(app):
    """Save current sound settings to the main settings.json file."""
    settings = {
        "pips_sound": app.pips_var.get(),
        "siren_sound": app.siren_var.get(),
        "pips_volume": app.pips_volume.get(),
        "siren_volume": app.siren_volume.get(),
        "air_volume": app.air_volume.get(),
        "water_volume": app.water_volume.get(),
        "enable_sound": app.enable_sound.get(),
        "siren_duration": app.siren_duration.get(),
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
