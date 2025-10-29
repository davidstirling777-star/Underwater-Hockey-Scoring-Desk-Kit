import serial
import serial.tools.list_ports
import threading

def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Look for Nano Every or generic Arduino descriptors
        if ("Arduino" in port.description or
            "Nano Every" in port.description or
            "VID:PID=2341:0058" in port.hwid or
            "VID:PID=2341:0042" in port.hwid):
            return port.device
    # If not found, return first found USB serial port
    for port in ports:
        if "USB" in port.device:
            return port.device
    return None

def serial_listener_thread(uwh_app):
    port = find_arduino_port()
    if not port:
        print("No Arduino serial port found for siren button.")
        return
    print(f"Listening for siren button on {port}")
    try:
        with serial.Serial(port, 9600, timeout=1) as ser:
            button_state = False
            while True:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                if line == "SIREN_ON":
                    if not button_state:
                        uwh_app.start_wireless_siren()
                        button_state = True
                elif line == "SIREN_OFF":
                    if button_state:
                        uwh_app.stop_wireless_siren()
                        button_state = False
    except Exception as e:
        print(f"Serial listener error: {e}")

def start_serial_listener(uwh_app):
    t = threading.Thread(target=serial_listener_thread, args=(uwh_app,), daemon=True)
    t.start()
