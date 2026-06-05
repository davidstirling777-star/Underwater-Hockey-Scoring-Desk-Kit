import time
import serial
import serial.tools.list_ports
import threading
import pygame
import sound

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

def is_siren_channel_playing():
    """Checks if our specific, dedicated siren audio channel is active."""
    try:
        # We target Channel 7 specifically to isolate it from your game clock pips
        return pygame.mixer.Channel(7).get_busy()
    except Exception:
        return False

def trigger_dual_siren_systems(uwh_app):
    """Triggers remote Zigbee hardware and forces local audio onto a dedicated channel."""
    # 1. Fire the wireless hardware siren over MQTT
    try:
        uwh_app.start_wireless_siren()
    except Exception as net_err:
        print(f"Wireless Trigger Note: {net_err}")
        
    # 2. Fire the preloaded MP3 track through your laptop speakers on a dedicated channel
    try:
        track = uwh_app.siren_var.get() if hasattr(uwh_app, 'siren_var') else "siren-police.mp3"
        vol = float(uwh_app.siren_volume.get()) if hasattr(uwh_app, 'siren_volume') else 50.0
        
        enable_sound = uwh_app.enable_sound.get() if hasattr(uwh_app, 'enable_sound') else True
        pips_vol = float(uwh_app.pips_volume.get()) if hasattr(uwh_app, 'pips_volume') else 50.0
        siren_vol = float(uwh_app.siren_volume.get()) if hasattr(uwh_app, 'siren_volume') else 50.0
        air_vol = float(uwh_app.air_volume.get()) if hasattr(uwh_app, 'air_volume') else 50.0
        water_vol = float(uwh_app.water_volume.get()) if hasattr(uwh_app, 'water_volume') else 50.0
        duration = float(uwh_app.siren_duration.get()) if hasattr(uwh_app, 'siren_duration') else 1.5

        # Execute your standard sound block so any GUI state logging triggers correctly
        sound.play_sound_with_volume(track, vol, enable_sound, pips_vol, siren_vol, air_vol, water_vol, duration)
        
        # FIX FOR THE LOOP: Explicitly force the active track onto Channel 7 for tracking
        if track in sound.SOUNDS:
            sound_object = sound.SOUNDS[track]
            # Set the volume specifically for Channel 7 (scaled 0.0 to 1.0)
            pygame.mixer.Channel(7).set_volume(siren_vol / 100.0)
            pygame.mixer.Channel(7).play(sound_object)
            
        print(f"Local Audio Played Successfully on Dedicated Channel 7: '{track}'")
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
                time.sleep(4)
                ser.reset_input_buffer()
                print(f"Successfully connected to siren button on {port}!")
                
                while True:
                    raw_data = ser.readline()
                    
                    # ─── FIXED DEDICATED CHANNEL RE-TRIGGER CHECK ───
                    # Tracks Channel 7 directly. If it drops to false while button is held, cycle it!
                    if button_held_down and not is_siren_channel_playing():
                        print("Button is still held, and the Channel 7 MP3 finished playing. Cycling track again!")
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
                                pygame.mixer.Channel(7).stop()  # Stop the audio channel immediately on release
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
