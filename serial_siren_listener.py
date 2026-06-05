import time
import serial
import serial.tools.list_ports
import threading
import sound  # Direct reference to your custom preloaded sound system

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
    last_trigger_time = 0.0
    
    while True:
        port = find_arduino_port()
        if not port:
            print("No Arduino serial port found for siren button. Retrying in 5s...")
            time.sleep(5)
            continue
            
        print(f"Attempting to connect to siren button on {port}...")
        try:
            with serial.Serial(port, 9600, timeout=1) as ser:
                ser.dtr = True
                ser.rts = True
                time.sleep(4)  # Let MQTT and audio structures boot cleanly first
                ser.reset_input_buffer()
                print(f"Successfully connected to siren button on {port}!")
                
                while True:
                    current_time = time.time()
                    raw_data = ser.readline()
                    
                    # Get the siren duration dynamically from the app settings
                    siren_duration = 1.5
                    if hasattr(uwh_app, 'siren_duration'):
                        try:
                            siren_duration = float(uwh_app.siren_duration.get())
                        except Exception:
                            siren_duration = 1.5

                    # --- DUAL-TRIGGER RE-TRIGGER CHECK ---
                    if button_held_down and (current_time - last_trigger_time >= siren_duration):
                        print(f"Button is still held, and {siren_duration}s passed. Re-triggering MP3 cycle!")
                        last_trigger_time = current_time
                        
                        # 1. Keep the remote physical wireless network box running
                        uwh_app.start_wireless_siren()
                        
                        # 2. Re-trigger audio on computer speakers
                        try:
                            track = uwh_app.siren_var.get() if hasattr(uwh_app, 'siren_var') else "siren-police.mp3"
                            vol = float(uwh_app.siren_volume.get()) if hasattr(uwh_app, 'siren_volume') else 50.0
                            sound.play_sound_with_volume(track, vol)
                            print(f"Local Audio Cycled: {track} at {vol}% volume.")
                        except Exception as audio_err:
                            print(f"Local Audio Cycle Error: {audio_err}")

                    if not raw_data:
                        continue
                        
                    line = raw_data.decode("utf-8", errors="replace").replace("\r", "").replace("\n", "").strip()
                    
                    if line == "SIREN_ON":
                        if not button_held_down:
                            print("Button Triggered: SIREN_ON (Initial Press).")
                            button_held_down = True
                            last_trigger_time = current_time
                            
                            # 1. Fire the wireless hardware siren over MQTT
                            uwh_app.start_wireless_siren()
                            
                            # 2. Play the selected MP3 track through computer speakers directly
                            try:
                                track = uwh_app.siren_var.get() if hasattr(uwh_app, 'siren_var') else "siren-police.mp3"
                                vol = float(uwh_app.siren_volume.get()) if hasattr(uwh_app, 'siren_volume') else 50.0
                                sound.play_sound_with_volume(track, vol)
                                print(f"Local Audio Started: {track} at {vol}% volume.")
                            except Exception as audio_err:
                                print(f"Local Audio Start Error: {audio_err}")
                            
                    elif line == "SIREN_OFF":
                        if button_held_down:
                            print("Button Released: SIREN_OFF matched.")
                            button_held_down = False
                            
                            # Stop the remote hardware wireless signal
                            uwh_app.stop_wireless_siren()
                            
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
