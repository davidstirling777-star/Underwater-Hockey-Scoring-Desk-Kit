import time
import serial
import serial.tools.list_ports
import threading
import pygame
import sound  # Direct link to your custom preloaded sound system

def find_arduino_port():
    """Searches for an attached Arduino or active USB Serial COM port on Windows."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        description = port.description or ""
        hwid = port.hwid or ""
        device = port.device or ""
        
        if ("Arduino" in description or
            "Nano" in description or
            "VID:PID=2341:0058" in hwid or 
            "VID:PID=2341:0042" in hwid or
            "1A86:7523" in hwid):          
            return device
            
    for port in ports:
        description = port.description or ""
        device = port.device or ""
        if "USB Serial" in description or "COM" in device:
            return device
            
    return None

def is_local_audio_playing():
    """Checks if Pygame is actively blasting audio out of the laptop speakers."""
    try:
        return pygame.mixer.get_busy()
    except Exception:
        return False

def trigger_dual_siren_systems(uwh_app):
    """Triggers both the remote wireless Zigbee system and local computer speakers with all required variables."""
    # 1. Fire the wireless hardware siren over MQTT
    try:
        uwh_app.start_wireless_siren()
    except Exception as net_err:
        print(f"Wireless Trigger Note: {net_err}")
        
    # 2. Fire the preloaded MP3 track through your laptop speakers using all 8 required arguments
    try:
        # Extract variables dynamically from uwh_app context
        track = uwh_app.siren_var.get() if hasattr(uwh_app, 'siren_var') else "siren-police.mp3"
        vol = float(uwh_app.siren_volume.get()) if hasattr(uwh_app, 'siren_volume') else 50.0
        
        # Pull the remaining 6 positional arguments required by your sound.py module
        enable_sound = uwh_app.enable_sound.get() if hasattr(uwh_app, 'enable_sound') else True
        pips_vol = float(uwh_app.pips_volume.get()) if hasattr(uwh_app, 'pips_volume') else 50.0
        siren_vol = float(uwh_app.siren_volume.get()) if hasattr(uwh_app, 'siren_volume') else 50.0
        air_vol = float(uwh_app.air_volume.get()) if hasattr(uwh_app, 'air_volume') else 50.0
        water_vol = float(uwh_app.water_volume.get()) if hasattr(uwh_app, 'water_volume') else 50.0
        duration = float(uwh_app.siren_duration.get()) if hasattr(uwh_app, 'siren_duration') else 1.5

        # Execute with all 8 arguments in the exact order required by your function signature
        sound.play_sound_with_volume(
            track, 
            vol, 
            enable_sound, 
            pips_vol, 
            siren_vol, 
            air_vol, 
            water_vol, 
            duration
        )
        print(f"Local Audio Played Successfully: '{track}'")
    except Exception as audio_err:
        print(f"Local Speaker Playback Error: {audio_err}")

def serial_listener_thread(uwh_app):
    """Background loop that monitors the serial port for button presses."""
    button_held_down = False
    
    while True:
        port = find_arduino_port()
        if not port:
            print("No Arduino serial port found for siren button. Retrying in 5s...")
            time.sleep(5)
            continue
            
        print(f"Attempting to connect to siren button on {port}...")
        try:
            with serial.Serial(port, 9600, timeout=0.1) as ser:
                ser.dtr = True
                ser.rts = True
                time.sleep(4)  # Let system architectures boot cleanly first
                ser.reset_input_buffer()
                print(f"Successfully connected to siren button on {port}!")
                
                while True:
                    raw_data = ser.readline()
                    
                    # If the button is still physically held down, but the speaker audio has finished playing:
                    if button_held_down and not is_local_audio_playing():
                        print("Button is still held, but the MP3 finished playing. Cycling track again!")
                        trigger_dual_siren_systems(uwh_app)

                    if not raw_data:
                        continue
                        
                    line = raw_data.decode("utf-8", errors="replace").replace("\r", "").replace("\n", "").strip()
                    
                    if line == "SIREN_ON":
                        if not button_held_down:
                            print("Button Triggered: SIREN_ON (Initial Press Captured).")
                            button_held_down = True
                            trigger_dual_siren_systems(uwh_app)
                            
                    elif line == "SIREN_OFF":
                        if button_held_down:
                            print("Button Released: SIREN_OFF matched.")
                            button_held_down = False
                            try:
                                uwh_app.stop_wireless_siren()
                            except Exception:
                                pass
                            
        except serial.SerialException as se:
            print(f"Serial connection lost on {port}: {se}. Re-hunting for port in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            print(f"Serial listener encountered an error: {e}. Retrying...")
            time.sleep(3)

def start_serial_listener(uwh_app):
    """Spawns the background daemon thread called by uwh.py."""
    t = threading.Thread(target=serial_listener_thread, args=(uwh_app,), daemon=True)
    t.start()
