import time
import serial

def serial_listener_thread(uwh_app):
    while True:  # Outer loop keeps trying to reconnect if the USB is unplugged
        port = find_arduino_port()
        if not port:
            print("No Arduino serial port found for siren button. Retrying in 5s...")
            time.sleep(5)
            continue
            
        print(f"Attempting to connect to siren button on {port}...")
        try:
            # 1. Open port with DTR and explicit timeouts
            with serial.Serial(port, 9600, timeout=1) as ser:
                ser.dtr = True
                ser.rts = True  # RTS signal combined with DTR ensures clone chips wake up stably
                time.sleep(2)   # Wait for the bootloader clear cycle
                ser.reset_input_buffer()
                print(f"Successfully connected to siren button on {port}!")
                
                button_state = False
                
                while True:
                    # Read the binary line directly from the serial hardware interface buffer
                    raw_data = ser.readline()
                    
                    # If data is empty but we didn't crash, the timeout reached; keep checking
                    if not raw_data:
                        continue
                        
                    # 2. FIX: Safely replace formatting characters and explicitly strip standard endline tokens
                    line = raw_data.decode("utf-8", errors="replace").replace("\r", "").replace("\n", "").strip()
                    
                    # Debug log to terminal: verify what Python visually intercepts
                    # print(f"Interpreted Serial Value: '{line}'") 
                    
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
            # Captures standard Windows physical interface disconnects cleanly
            print(f"Serial connection lost on {port}: {se}. Re-hunting for port in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            print(f"Serial listener encountered an error: {e}. Retrying...")
            time.sleep(3)
