import time
import serial
import serial.tools.list_ports
import threading
import pygame  # Imported to check the real-time playback state of the audio mixer

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
    # Enforce global tracker state outside the engine connection loops
    button_held_down = False
    
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
                    raw_data = ser.readline()
                    
                    # --- CRITICAL RE-TRIGGER CHECK ---
                    # If the button is currently being held down, but PyGame's mixer has finished
                    # playing the MP3 file, automatically trigger the sound again to cycle it smoothly.
                    if button_held_down and not pygame.mixer.get_busy():
                        print("Button is still held, but audio finished. Cycling MP3 back to the start!")
                        uwh_app.start_wireless_siren()

                    if not raw_data:
                        continue
                        
                    line = raw_data.decode("utf-8", errors="replace").replace("\r", "").replace("\n", "").strip()
                    
                    if line == "SIREN_ON":
                        if not button_held_down:
                            print("Button Triggered: SIREN_ON (Initial Press).")
                            button_held_down = True
                            uwh_app.start_wireless_siren()
                            
                    elif line == "SIREN_OFF":
                        if button_held_down:
                            print("Button Released: SIREN_OFF matched.")
                            button_held_down = False
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
