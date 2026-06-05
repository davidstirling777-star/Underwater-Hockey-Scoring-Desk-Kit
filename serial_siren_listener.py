import time

def serial_listener_thread(uwh_app):
    port = find_arduino_port()
    if not port:
        print("No Arduino serial port found for siren button.")
        return
        
    print(f"Listening for siren button on {port}")
    try:
        # Open connection
        with serial.Serial(port, 9600, timeout=1) as ser:
            # CRITICAL FOR NANO EVERY: Enable DTR to wake up the board
            ser.dtr = True 
            
            # Wait 2 full seconds for the Arduino hardware to clear its bootloader
            time.sleep(2) 
            
            # Clear any garbage data that filled the buffer during the boot cycle
            ser.reset_input_buffer() 
            
            button_state = False
            while True:
                line = ser.readline().decode("utf-8", errors="replace").strip()
                
                # Debugging log line: uncomment this if you need to watch raw incoming data
                # if line: print(f"Raw incoming: {line}") 
                
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
