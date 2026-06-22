import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime

from sound import (
    get_sound_files,
    play_sound_with_volume,
    check_audio_device_available,
    handle_no_audio_device_warning,
)

from settings_manager import save_sound_settings
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

