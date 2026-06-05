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
                    
                    # Get the siren duration dynamically from the app settings (defaults to 1.5s)
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
                        
                        # 1. Keep the remote physical wireless box running
                        uwh_app.start_wireless_siren()
                        
                        # 2. ADDED: Explicitly force Python to play the MP3 through the computer speakers
                        if hasattr(uwh_app, 'trigger_siren_sound'):
                            uwh_app.trigger_siren_sound()
                        elif hasattr(uwh_app, 'play_siren'):
                            uwh_app.play_siren()

                    if not raw_data:
                        continue
                        
                    line = raw_data.decode("utf-8", errors="replace").replace("\r", "").replace("\n", "").strip()
                    
                    if line == "SIREN_ON":
                        if not button_held_down:
                            print("Button Triggered: SIREN_ON (Initial Press).")
                            button_held_down = True
                            last_trigger_time = current_time
                            
                            # Fire both targets on initial press
                            uwh_app.start_wireless_siren()
                            if hasattr(uwh_app, 'trigger_siren_sound'):
                                uwh_app.trigger_siren_sound()
                            elif hasattr(uwh_app, 'play_siren'):
                                uwh_app.play_siren()
                            
                    elif line == "SIREN_OFF":
                        if button_held_down:
                            print("Button Released: SIREN_OFF matched.")
                            button_held_down = False
                            uwh_app.stop_wireless_siren()
                            
                            # Optional: If your app has a sound stop function, call it here
                            if hasattr(uwh_app, 'stop_siren_sound'):
                                uwh_app.stop_siren_sound()
                            
        except serial.SerialException as se:
            print(f"Serial connection lost on {port}: {se}. Re-hunting for port in 3 seconds...")
            time.sleep(3)
        except Exception as e:
            print(f"Serial listener encountered an error: {e}. Retrying...")
            time.sleep(3)
