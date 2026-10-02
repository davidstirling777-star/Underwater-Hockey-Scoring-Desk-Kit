"""Sounds tab: per-file trims, selection, output reporting and timing.

The tab lists up to ten pip files and ten siren files discovered in assets/.
Each row always shows a radio selector, filename cell and Trim % cell so the
tables retain a deliberate fixed-grid appearance. Unused rows are disabled.
Each file has an attenuation-only Trim % (0-100). Overall system loudness is
left to the operating system, DAC and amplifier. Click a file row to make it
the active pip/siren; double-click it to preview the current trim.
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


MAX_SOUND_ROWS = 10


def _visible_files(files, selected):
    """Return at most ten files, keeping the active selection visible."""
    files = list(files)
    if len(files) <= MAX_SOUND_ROWS:
        return files

    visible = files[:MAX_SOUND_ROWS]
    if selected and selected in files and selected not in visible:
        visible[-1] = selected
    return visible


def create_sounds_tab(app):
    """Create the Sounds tab and its per-file trim tables."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Sounds")

    tab.grid_rowconfigure(0, weight=1)
    tab.grid_columnconfigure(0, weight=1)

    sounds_widget = ttk.LabelFrame(
        tab,
        text="Sounds",
        padding=(12, 10),
    )
    sounds_widget.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=8,
        pady=8,
    )
    sounds_widget.grid_columnconfigure(0, weight=5, minsize=430)
    sounds_widget.grid_columnconfigure(1, weight=3, minsize=300)
    sounds_widget.grid_rowconfigure(2, weight=1)
    sounds_widget.grid_rowconfigure(3, weight=1)

    sound_files = get_sound_files()
    if sound_files == ["No sound files found"]:
        sound_files = []

    all_pips = [
        filename for filename in sound_files if "pip" in filename.lower()
    ]
    all_sirens = [
        filename for filename in sound_files if "siren" in filename.lower()
    ]

    if app.pips_var.get() not in all_pips:
        app.pips_var.set(all_pips[0] if all_pips else "")
    if app.siren_var.get() not in all_sirens:
        app.siren_var.set(all_sirens[0] if all_sirens else "")

    pips_files = _visible_files(all_pips, app.pips_var.get())
    siren_files = _visible_files(all_sirens, app.siren_var.get())

    # Tk variables exist only for currently displayed files. app.sound_trims
    # remains the persistent in-memory dictionary, including trims for files
    # temporarily removed from the assets folder.
    app.sound_trim_vars = {}

    def app_log(message):
        try:
            app.add_to_zigbee_log(message)
        except Exception:
            pass

    def ensure_audio_device(sound_type):
        """Warn once when sound is enabled but no usable audio device exists."""
        if check_audio_device_available(app.enable_sound):
            return True

        if not app.audio_device_warning_shown:
            messagebox.showwarning(
                "Audio Device Warning",
                f"No audio device detected. Cannot play {sound_type} sounds.",
            )
            app.audio_device_warning_shown = True
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
                f"Could not open the sounds folder:\n{error}",
            )

    def validate_trim(new_value):
        """Allow an empty edit-in-progress or a whole number from 0 to 100."""
        if new_value == "":
            return True
        if not new_value.isdigit():
            return False
        return 0 <= int(new_value) <= 100

    trim_validation = (sounds_widget.register(validate_trim), "%P")

    def commit_trim(filename, trim_var):
        """Validate one table entry and update the in-memory trim."""
        raw_value = trim_var.get().strip()
        try:
            trim = int(raw_value)
            if not 0 <= trim <= 100:
                raise ValueError
        except ValueError:
            previous = int(round(app.get_sound_trim(filename)))
            trim_var.set(str(previous))
            messagebox.showerror(
                "Invalid Trim %",
                "Trim % must be a whole number from 0 to 100.",
            )
            return False

        app.set_sound_trim(filename, trim)
        trim_var.set(str(trim))
        return True

    def trim_for_preview(filename):
        """Use an unsaved valid edit immediately when previewing a file."""
        trim_var = app.sound_trim_vars.get(filename)
        if trim_var is None:
            return app.get_sound_trim(filename)
        try:
            trim = int(trim_var.get().strip())
            if 0 <= trim <= 100:
                return trim
        except ValueError:
            pass
        return app.get_sound_trim(filename)

    def preview_sound(filename, sound_type):
        """Preview one file using the currently displayed per-file trim."""
        if not filename or not ensure_audio_device(sound_type):
            return

        trim = trim_for_preview(filename)
        try:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(
                f"[{timestamp}] {sound_type.title()} preview started: "
                f"file='{filename}', trim={trim}%"
            )
            app_log(
                f"{sound_type.title()} preview: {filename} "
                f"(Trim: {trim}%)"
            )
            play_timed_sound(
                filename,
                sound_type,
                app.enable_sound,
                trim,
                app.siren_duration,
                app.max_siren_duration,
            )
        except Exception as error:
            print(
                f"Error previewing {sound_type} sound: "
                f"{type(error).__name__}: {error}"
            )
            app_log(
                f"ERROR previewing {sound_type}: "
                f"{type(error).__name__}: {error}"
            )

    def build_sound_table(parent, title, files, selection_var, sound_type):
        """Build one polished fixed ten-row selector/filename/trim table."""
        frame = ttk.LabelFrame(
            parent,
            text=title,
            padding=(8, 7),
        )
        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=1, minsize=250)
        frame.grid_columnconfigure(2, weight=0)

        # A separate inner frame gives the three columns one continuous table
        # border instead of making each widget look like an unrelated control.
        table = tk.Frame(
            frame,
            borderwidth=1,
            relief="solid",
            background="#d6d6d6",
        )
        table.grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="nsew",
        )
        table.grid_columnconfigure(0, weight=0, minsize=54)
        table.grid_columnconfigure(1, weight=1, minsize=250)
        table.grid_columnconfigure(2, weight=0, minsize=78)

        header_options = {
            "font": ("Arial", 10, "bold"),
            "background": "#e9e9e9",
            "borderwidth": 1,
            "relief": "solid",
            "pady": 5,
        }

        tk.Label(
            table,
            text="Use",
            anchor="center",
            **header_options,
        ).grid(row=0, column=0, sticky="nsew")

        tk.Label(
            table,
            text="Sound File",
            anchor="center",
            **header_options,
        ).grid(row=0, column=1, sticky="nsew")

        tk.Label(
            table,
            text="Trim %",
            anchor="center",
            **header_options,
        ).grid(row=0, column=2, sticky="nsew")

        for index in range(MAX_SOUND_ROWS):
            row = index + 1
            table.grid_rowconfigure(row, minsize=30)

            if index < len(files):
                filename = files[index]
                trim = int(round(app.get_sound_trim(filename)))
                trim_var = tk.StringVar(value=str(trim))
                app.sound_trim_vars[filename] = trim_var

                radio_cell = tk.Frame(
                    table,
                    background="#ffffff",
                    borderwidth=1,
                    relief="solid",
                )
                radio_cell.grid(row=row, column=0, sticky="nsew")
                select_radio = ttk.Radiobutton(
                    radio_cell,
                    variable=selection_var,
                    value=filename,
                    command=lambda name=filename: selection_var.set(name),
                )
                select_radio.pack(expand=True)

                file_cell = tk.Label(
                    table,
                    text=filename,
                    anchor="w",
                    background="#ffffff",
                    borderwidth=1,
                    relief="solid",
                    padx=8,
                    font=("Arial", 10),
                    cursor="hand2",
                )
                file_cell.grid(
                    row=row,
                    column=1,
                    sticky="nsew",
                )
                file_cell.bind(
                    "<Button-1>",
                    lambda event, name=filename: selection_var.set(name),
                )
                file_cell.bind(
                    "<Double-Button-1>",
                    lambda event, name=filename, kind=sound_type:
                        preview_sound(name, kind),
                )

                trim_cell = tk.Frame(
                    table,
                    background="#ffffff",
                    borderwidth=1,
                    relief="solid",
                    padx=5,
                    pady=3,
                )
                trim_cell.grid(row=row, column=2, sticky="nsew")
                trim_entry = ttk.Entry(
                    trim_cell,
                    textvariable=trim_var,
                    width=6,
                    justify="center",
                    font=("Arial", 10),
                    validate="key",
                    validatecommand=trim_validation,
                )
                trim_entry.pack(fill="x", expand=True)
                trim_entry.bind(
                    "<FocusOut>",
                    lambda event, name=filename, var=trim_var:
                        commit_trim(name, var),
                )
                trim_entry.bind(
                    "<Return>",
                    lambda event, name=filename, var=trim_var:
                        commit_trim(name, var),
                )
            else:
                # Keep the same three visible cells for all ten rows. The
                # unused radio button has a unique sentinel value so it never
                # appears selected when the real selection variable is empty.
                disabled_background = "#eeeeee"

                radio_cell = tk.Frame(
                    table,
                    background=disabled_background,
                    borderwidth=1,
                    relief="solid",
                )
                radio_cell.grid(row=row, column=0, sticky="nsew")
                unused_radio = ttk.Radiobutton(
                    radio_cell,
                    variable=selection_var,
                    value=f"__unused_{sound_type}_{index}",
                )
                unused_radio.state(["disabled"])
                unused_radio.pack(expand=True)

                tk.Label(
                    table,
                    text="",
                    background=disabled_background,
                    borderwidth=1,
                    relief="solid",
                ).grid(
                    row=row,
                    column=1,
                    sticky="nsew",
                )

                trim_cell = tk.Frame(
                    table,
                    background=disabled_background,
                    borderwidth=1,
                    relief="solid",
                    padx=5,
                    pady=3,
                )
                trim_cell.grid(row=row, column=2, sticky="nsew")
                blank_trim = ttk.Entry(
                    trim_cell,
                    width=6,
                    justify="center",
                    font=("Arial", 10),
                )
                blank_trim.insert(0, "100")
                blank_trim.state(["disabled"])
                blank_trim.pack(fill="x", expand=True)

        ttk.Label(
            frame,
            text=(
                "Select one radio button for the active sound; "
                "double-click the filename to preview it."
            ),
            anchor="w",
        ).grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(6, 0),
        )
        return frame

    # Top action bar: primary actions on the left, Enable Sound aligned to
    # the right so the controls read as a deliberate toolbar.
    controls = ttk.Frame(sounds_widget)
    controls.grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(0, 2),
    )
    controls.grid_columnconfigure(2, weight=1)

    ttk.Button(
        controls,
        text="Save Settings",
        command=app.save_sound_settings_method,
    ).grid(row=0, column=0, padx=(0, 8))

    ttk.Button(
        controls,
        text="Open Sounds Folder",
        command=open_sounds_folder,
    ).grid(row=0, column=1, padx=(0, 12))

    ttk.Checkbutton(
        controls,
        text="Enable Sound?",
        variable=app.enable_sound,
    ).grid(row=0, column=3, padx=(16, 4))

    # Keep the diagnostic slightly below the top controls so it reads as
    # status information rather than another editable setting.
    diagnostic = ttk.Frame(
        sounds_widget,
        padding=(8, 5),
        relief="groove",
        borderwidth=1,
    )
    diagnostic.grid(
        row=1,
        column=0,
        columnspan=2,
        sticky="ew",
        pady=(7, 10),
    )
    ttk.Label(
        diagnostic,
        text=(
            f"Audio output in use: {AUDIO_OUTPUT_AT_STARTUP} "
            "(selected when UWH started)"
        ),
        justify="left",
        anchor="w",
    ).pack(fill="x")

    pips_frame = build_sound_table(
        sounds_widget,
        "Pips",
        pips_files,
        app.pips_var,
        "pips",
    )
    pips_frame.grid(
        row=2,
        column=0,
        sticky="nsew",
        padx=(0, 10),
        pady=(0, 7),
    )

    siren_frame = build_sound_table(
        sounds_widget,
        "Sirens",
        siren_files,
        app.siren_var,
        "siren",
    )
    siren_frame.grid(
        row=3,
        column=0,
        sticky="nsew",
        padx=(0, 10),
        pady=(0, 0),
    )

    timing_frame = ttk.LabelFrame(
        sounds_widget,
        text="Siren timing",
        padding=(10, 8),
    )
    timing_frame.grid(
        row=2,
        column=1,
        rowspan=2,
        sticky="nsew",
        padx=(0, 0),
        pady=(0, 0),
    )
    timing_frame.grid_columnconfigure(0, weight=1)
    timing_frame.grid_columnconfigure(1, weight=0)

    tk.Label(
        timing_frame,
        text="Number of seconds to play Siren",
        font=("Arial", 11),
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", padx=10, pady=(18, 8))

    siren_duration_entry = tk.Entry(
        timing_frame,
        textvariable=app.siren_duration,
        font=("Arial", 11),
        width=10,
    )
    siren_duration_entry.grid(
        row=0,
        column=1,
        sticky="w",
        padx=(0, 10),
        pady=(18, 8),
    )

    def validate_siren_duration(new_value):
        if new_value == "":
            return True
        try:
            float(new_value.replace(",", "."))
            return True
        except ValueError:
            return False

    duration_validation = (
        timing_frame.register(validate_siren_duration),
        "%P",
    )
    siren_duration_entry.config(
        validate="key",
        validatecommand=duration_validation,
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
        timing_frame,
        text="Maximum Siren Duration (seconds)",
        font=("Arial", 11),
        anchor="w",
    ).grid(row=1, column=0, sticky="ew", padx=10, pady=8)

    max_siren_duration_entry = tk.Entry(
        timing_frame,
        textvariable=app.max_siren_duration,
        font=("Arial", 11),
        width=10,
    )
    max_siren_duration_entry.grid(
        row=1,
        column=1,
        sticky="w",
        padx=(0, 10),
        pady=8,
    )

    last_valid_max = [str(app.max_siren_duration.get())]

    def normalize_max_siren_duration(event=None):
        """Accept 1-30 s; keep a valid value if the user mistypes."""
        try:
            seconds = float(
                str(app.max_siren_duration.get()).strip().replace(",", ".")
            )
            if not math.isfinite(seconds) or not 1.0 <= seconds <= 30.0:
                raise ValueError
        except (ValueError, TypeError, tk.TclError):
            messagebox.showerror(
                "Invalid Maximum Siren Duration",
                "Enter a number between 1 and 30 seconds.",
            )
            app.max_siren_duration.set(last_valid_max[0])
            return

        last_valid_max[0] = f"{seconds:g}"
        app.max_siren_duration.set(last_valid_max[0])

    max_siren_duration_entry.bind(
        "<FocusOut>",
        normalize_max_siren_duration,
    )
    max_siren_duration_entry.bind(
        "<Return>",
        normalize_max_siren_duration,
    )

    tk.Label(
        timing_frame,
        text=(
            "Overall loudness is set by the OS/DAC/amplifier. "
            "Trim % only attenuates individual files: 100% is native level "
            "and 0% mutes that file."
        ),
        font=("Arial", 10),
        justify="left",
        anchor="nw",
        wraplength=360,
    ).grid(
        row=2,
        column=0,
        columnspan=2,
        sticky="ew",
        padx=10,
        pady=(18, 8),
    )

    if len(all_pips) > MAX_SOUND_ROWS or len(all_sirens) > MAX_SOUND_ROWS:
        tk.Label(
            timing_frame,
            text=(
                "Up to 10 pip files and 10 siren files are shown. "
                "If more are present, the active selection is kept visible."
            ),
            font=("Arial", 9),
            justify="left",
            anchor="nw",
            wraplength=360,
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=10,
            pady=(8, 0),
        )


def save_sound_settings_method(app):
    """Validate and save active files, per-file trims and siren timing."""
    try:
        max_duration = float(
            str(app.max_siren_duration.get()).strip().replace(",", ".")
        )
        if not math.isfinite(max_duration) or not 1.0 <= max_duration <= 30.0:
            raise ValueError
    except (ValueError, TypeError, tk.TclError):
        messagebox.showerror(
            "Invalid Maximum Siren Duration",
            "Enter a number between 1 and 30 seconds.",
        )
        return

    for filename, trim_var in app.sound_trim_vars.items():
        try:
            trim = int(trim_var.get().strip())
            if not 0 <= trim <= 100:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Trim %",
                f"Trim % for '{filename}' must be a whole number from 0 to 100.",
            )
            return
        app.set_sound_trim(filename, trim)

    app.max_siren_duration.set(f"{max_duration:g}")
    settings = {
        "pips_sound": app.pips_var.get(),
        "siren_sound": app.siren_var.get(),
        "sound_trims": {
            filename: int(round(value))
            for filename, value in sorted(app.sound_trims.items())
        },
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
            f"Could not save sound settings:\n{error}",
        )
        return

    messagebox.showinfo(
        "Settings Saved",
        "Sound settings have been saved.",
    )
