import time
import serial
import serial.tools.list_ports
import threading

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
                            
                            # ─── NATIVE APP HOOKS ───
                            # We toggle your app's built-in looping attributes to handle the sound natively
                            uwh_app.siren_loop_active = True
                            
                            # Execute the app's native master siren trigger functions
                            if hasattr(uwh_app, 'start_siren_loop'):
                                uwh_app.start_siren_loop()
                            elif hasattr(uwh_app, 'start_siren'):
                                uwh_app.start_siren()
                            else:
                                # Fallback to standard wireless call if loops aren't named standard
                                uwh_app.start_wireless_siren()
                            
                    elif line == "SIREN_OFF":
                        if button_held_down:
                            print("Button Released: SIREN_OFF matched.")
                            button_held_down = False
                            
                            # ─── NATIVE APP HOOKS ───
                            uwh_app.siren_loop_active = False
                            
                            if hasattr(uwh_app, 'stop_siren_loop'):
                                uwh_app.stop_siren_loop()
                            elif hasattr(uwh_app, 'stop_siren'):
                                uwh_app.stop_siren()
                            else:
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
