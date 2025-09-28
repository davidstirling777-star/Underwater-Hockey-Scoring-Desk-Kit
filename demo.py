import tkinter as tk
from tkinter import ttk
import json
import os

SETTINGS_FILE = "game_settings.json"

def get_sound_files():
    # Dummy sound files for demo purposes.
    return ['pip1.wav', 'pip2.mp3', 'siren1.wav', 'siren2.mp3']

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

class DemoApp:
    def __init__(self, master):
        self.master = master
        master.title("UWH Demo - Sounds UI")
        master.geometry('900x500')

        main = tk.Frame(master)
        main.pack(expand=True, fill='both')

        # Sounds widget: 10 rows, 6 columns (0 to 5)
        sounds = tk.LabelFrame(main, text="Sounds", borderwidth=2, relief="solid")
        sounds.pack(expand=True, fill='both')

        for r in range(10):
            sounds.grid_rowconfigure(r, weight=1)
        for c in range(6):
            sounds.grid_columnconfigure(c, weight=1)
        sounds.grid_columnconfigure(3, weight=0)

        sound_files = get_sound_files()
        pips_options = ["Default"] + sound_files
        siren_options = ["Default"] + sound_files

        # Load settings if present
        settings = load_settings()
        self.pips_var = tk.StringVar(value=settings.get("pips_sound", "Default"))
        self.siren_var = tk.StringVar(value=settings.get("siren_sound", "Default"))
        self.pips_volume = tk.DoubleVar(value=settings.get("pips_volume", 50.0))
        self.siren_volume = tk.DoubleVar(value=settings.get("siren_volume", 50.0))
        self.air_volume = tk.DoubleVar(value=settings.get("air_volume", 50.0))
        self.water_volume = tk.DoubleVar(value=settings.get("water_volume", 50.0))

        # Row 0, column 0: Save Settings button
        save_btn = tk.Button(sounds, text="Save Settings", font=("Arial", 11), command=self.save_settings)
        save_btn.grid(row=0, column=0)

        # Row 0, column 4, columnspan=2: "Volume"
        tk.Label(sounds, text="Volume", font=("Arial", 12)).grid(row=0, column=4, columnspan=2, sticky="nsew")

        # Row 1, column 4: "Air"
        tk.Label(sounds, text="Air", font=("Arial", 12)).grid(row=1, column=4, sticky="nsew")

        # Row 1, column 5: "Water"
        tk.Label(sounds, text="Water", font=("Arial", 12)).grid(row=1, column=5, sticky="nsew")

        # Row 2, column 0: "Pips"
        tk.Label(sounds, text="Pips", font=("Arial", 12)).grid(row=2, column=0, sticky="nsew")

        # Row 2, column 1, columnspan=2: Pips dropdown (sticky="ew", padx=(0, 10))
        pips_dropdown = ttk.Combobox(sounds, textvariable=self.pips_var, values=pips_options, state="readonly")
        pips_dropdown.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, 10))

        # Row 2, column 3: Play button for pips demo sound
        pips_play_btn = tk.Button(sounds, text="Play", font=("Arial", 11), width=5)
        pips_play_btn.grid(row=2, column=3)

        # Row 3, column 0: "Pips Vol"
        tk.Label(sounds, text="Pips Vol", font=("Arial", 11)).grid(row=3, column=0, sticky="ew")

        # Row 3, column 1, columnspan=2: Pips slider (sticky="ew"), no value text
        pips_vol_slider = tk.Scale(
            sounds, from_=0, to=100, orient="horizontal", variable=self.pips_volume,
            font=("Arial", 10), showvalue=False
        )
        pips_vol_slider.grid(row=3, column=1, columnspan=2, sticky="ew")

        # Row 5, column 0: "Siren"
        tk.Label(sounds, text="Siren", font=("Arial", 12)).grid(row=5, column=0, sticky="nsew")

        # Row 5, column 1, columnspan=2: Siren dropdown (sticky="ew", padx=(0, 10))
        siren_dropdown = ttk.Combobox(sounds, textvariable=self.siren_var, values=siren_options, state="readonly")
        siren_dropdown.grid(row=5, column=1, columnspan=2, sticky="ew", padx=(0, 10))

        # Row 5, column 3: Play button for siren demo sound
        siren_play_btn = tk.Button(sounds, text="Play", font=("Arial", 11), width=5)
        siren_play_btn.grid(row=5, column=3)

        # Row 6, column 0: "Siren Vol"
        tk.Label(sounds, text="Siren Vol", font=("Arial", 11)).grid(row=6, column=0, sticky="ew")

        # Row 6, column 1, columnspan=2: Siren slider (sticky="ew"), no value text
        siren_vol_slider = tk.Scale(
            sounds, from_=0, to=100, orient="horizontal", variable=self.siren_volume,
            font=("Arial", 10), showvalue=False
        )
        siren_vol_slider.grid(row=6, column=1, columnspan=2, sticky="ew")

        # Air slider: row=2, column=4, rowspan=5, sticky="ns" (no text)
        air_vol_slider = tk.Scale(
            sounds, from_=100, to=0, orient="vertical", variable=self.air_volume,
            font=("Arial", 10), showvalue=False
        )
        air_vol_slider.grid(row=2, column=4, rowspan=5, sticky="ns")

        # Water slider: row=2, column=5, rowspan=5, sticky="ns" (no text)
        water_vol_slider = tk.Scale(
            sounds, from_=100, to=0, orient="vertical", variable=self.water_volume,
            font=("Arial", 10), showvalue=False
        )
        water_vol_slider.grid(row=2, column=5, rowspan=5, sticky="ns")

        # Demo info at the bottom (optional)
        tk.Label(
            sounds,
            text="Demo: 10 rows, 6 columns, custom layout for Sounds widget.",
            fg="blue"
        ).grid(row=9, column=0, columnspan=6, sticky="nsew")

    def save_settings(self):
        settings = {
            "pips_sound": self.pips_var.get(),
            "siren_sound": self.siren_var.get(),
            "pips_volume": self.pips_volume.get(),
            "siren_volume": self.siren_volume.get(),
            "air_volume": self.air_volume.get(),
            "water_volume": self.water_volume.get()
        }
        save_settings(settings)
        # Optionally show a message
        tk.messagebox.showinfo("Settings Saved", "Sound settings have been saved.")

if __name__ == "__main__":
    root = tk.Tk()
    # Add messagebox support for feedback
    import tkinter.messagebox
    app = DemoApp(root)
    root.mainloop()
