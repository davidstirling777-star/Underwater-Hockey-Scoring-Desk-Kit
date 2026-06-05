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
        
        # Look for Nano Every, standard Arduinos, or CH340 clones
        if ("Arduino" in description or
            "Nano" in description or
            "VID:PID=2341:0058" in hwid or # Nano Every standard VID:PID
            "VID:PID=2341:0042" in hwid or
            "1A86:7523" in hwid):          # CH340 USB Clone chip VID:PID
            return device
            
    # Fallback: Look for ANY active USB serial port on Windows
    for port in ports:
        description = port.description or ""
        device = port.device or ""
        if "USB Serial" in description or "COM" in device:
            return device
            
    return None

def serial_listener_thread(uwh_app):
    """Background loop that monitors the serial port for button presses."""
    while True:  # Outer loop keeps trying to reconnect if the USB is unplugged
        port = find_arduino_port()
        if not port:
            print("No Arduino serial port found for siren button. Retrying in 5s...")
            time.sleep(5)
            continue
            
        print(f"Attempting to connect to siren button on {port}...")
        try:
            # Open port with DTR and explicit timeouts
            with serial.Serial(port, 9600, timeout=1) as ser:
                ser.dtr = True
                ser.rts = True  # RTS combined with DTR ensures clone chips wake up stably
                time.sleep(2)   # Wait for the bootloader clear cycle
                ser.reset_input_buffer()
                print(f"Successfully connected to siren button on {port}!")
                
                button_state = False
                
                while True:
                    raw_data = ser.readline()
                    
                    if not raw_data:
                        continue
                        
                    # Safely remove hidden layout tokens and decode
                    line = raw_data.decode("utf-8", errors="replace").replace("\r", "").replace("\n", "").strip()
                    
                    if line == "SIREN_ON":
                        if not button_state:
                            print("Button Triggered: SIREN_ON matched.")
                            uwh_app.start_wireless_siren()
                            button_state = True
                    elif line == "SIREN_OFF":
                        if button_state:
                            print("Button Released: SIREN_OFF matched.")
                            uwh_app.stop_wireless_siren()
                            button_state = False
                            
        except serial.SerialException as se:
            print(f"Serial connection lost on {port}: {se}. Re-hunting for port in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            print(f"Serial listener encountered an error: {e}. Retrying...")
            time.sleep(3)

def start_serial_listener(uwh_app):
    """CRITICAL HOOK: Spawns the background daemon thread called by uwh.py."""
    t = threading.Thread(target=serial_listener_thread, args=(uwh_app,), daemon=True)
    t.start()
