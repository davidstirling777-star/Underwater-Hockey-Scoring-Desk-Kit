import time
import serial
import serial.tools.list_ports
import threading
import pygame
import sound  # Direct hook to read your _preloaded_sounds dictionary

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
                    if not raw_data:
                        continue
                        
                    line = raw_data.decode("utf-8", errors="replace").replace("\r", "").replace("\n", "").strip()
                    
                    if line == "SIREN_ON":
                        if not button_held_down:
                            print("Button Triggered: SIREN_ON (Initial Press Captured).")
                            button_held_down = True
                            
                            # 1. Trigger the wireless network siren over MQTT
                            try:
                                uwh_app.start_wireless_siren()
                            except Exception as net_err:
                                print(f"Wireless Trigger Note: {net_err}")
                            
                            # 2. Trigger the sound loop directly using Pygame on a dedicated channel
                            try:
                                track = uwh_app.siren_var.get() if hasattr(uwh_app, 'siren_var') else "siren-police.mp3"
                                siren_vol = float(uwh_app.siren_volume.get()) if hasattr(uwh_app, 'siren_volume') else 50.0
                                sound_enabled = uwh_app.enable_sound.get() if hasattr(uwh_app, 'enable_sound') else True
                                
                                if sound_enabled and track in sound._preloaded_sounds:
                                    # Target Channel 7 to isolate the siren loop from background clock pips
                                    siren_channel = pygame.mixer.Channel(7)
                                    sound_object = sound._preloaded_sounds[track]
                                    
                                    # Scale volume (Pygame scales between 0.0 and 1.0)
                                    siren_channel.set_volume(siren_vol / 100.0)
                                    
                                    # loops=-1 instructs Pygame to loop the MP3 file infinitely at the hardware level
                                    siren_channel.play(sound_object, loops=-1)
                                    print(f"Local Speaker Audio Looping Started: '{track}' at {siren_vol}% volume.")
                            except Exception as audio_err:
                                print(f"Local Speaker Playback Error: {audio_err}")
                            
                    elif line == "SIREN_OFF":
                        if button_held_down:
                            print("Button Released: SIREN_OFF matched.")
                            button_held_down = False
                            
                            # 1. Stop the remote wireless signal
                            try:
                                uwh_app.stop_wireless_siren()
                            except Exception:
                                pass
                                
                            # 2. Cut the local audio stream instantly down to 0 milliseconds
                            try:
                                pygame.mixer.Channel(7).stop()
                                print("Local Speaker Audio Stopped Instantly.")
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
