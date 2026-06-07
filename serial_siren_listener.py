import time
import serial
import serial.tools.list_ports
import threading
import pygame
import sound

# Global flag to track if the serial listener thread is already active
_serial_listener_started = False
_serial_listener_lock = threading.Lock()

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
    # AMNESIA FIX: Moved outside the while True loop.
    # This ensures that even if the serial connection drops and restarts, 
    # the script remembers the siren is currently active.
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
                
                # BOOT DELAY FIX: Reduced from 4s to 1.5s.
                # 4 seconds was creating a massive blind spot where releases were missed.
                time.sleep(1.5)  
                ser.reset_input_buffer()
                print(f"Successfully connected to siren button on {port}!")
                
                while True:
                    try:
                        raw_data = ser.readline()
                        if not raw_data:
                            continue
                            
                        line = raw_data.decode("utf-8", errors="replace").strip()
                        
                        if line == "SIREN_ON":
                            if not button_held_down:
                                print("Button Triggered: SIREN_ON")
                                button_held_down = True
                                
                                # 1. Fire the wireless hardware siren
                                try:
                                    uwh_app.zigbee_controller.start_siren_continuous()
                                except Exception as net_err:
                                    print(f"Wireless Trigger Note: {net_err}")
                                
                                # 2. Fire the local speaker audio
                                try:
                                    track = uwh_app.siren_var.get() if hasattr(uwh_app, 'siren_var') else "siren-police.mp3"
                                    siren_vol = float(uwh_app.siren_volume.get()) if hasattr(uwh_app, 'siren_volume') else 50.0
                                    sound_enabled = uwh_app.enable_sound.get() if hasattr(uwh_app, 'enable_sound') else True
                                    
                                    if sound_enabled and hasattr(sound, '_preloaded_sounds') and track in sound._preloaded_sounds:
                                        siren_channel = pygame.mixer.Channel(7)
                                        siren_channel.set_volume(siren_vol / 100.0)
                                        siren_channel.play(sound._preloaded_sounds[track], loops=-1)
                                        print(f"Local Speaker Audio Looping Started: '{track}' on Channel 7")
                                except Exception as audio_err:
                                    print(f"Local Speaker Playback Error: {audio_err}")
                                
                        elif line == "SIREN_OFF":
                            if button_held_down:
                                print("Button Released: SIREN_OFF matched.")
                                button_held_down = False
                                
                                # 1. Terminate remote wireless broadcast
                                try:
                                    uwh_app.zigbee_controller.stop_siren_continuous()
                                except Exception:
                                    pass
                                    
                                # 2. Instantly stop the local audio channel
                                try:
                                    pygame.mixer.Channel(7).stop()
                                    print("Local Speaker Audio Stopped Instantly.")
                                except Exception as stop_err:
                                    print(f"Error stopping channel audio: {stop_err}")
                                    
                    except serial.SerialException:
                        # Re-raise to trigger outer reconnection logic
                        raise

        except Exception as e:
            # Handle "Access Denied" or other serial port errors
            print(f"Serial listener encountered an error on {port}: {e}. Retrying in 3s...")
            time.sleep(3)

def start_serial_listener(uwh_app):
    """Spawns the background daemon thread with thread-safety protection.
    
    Only one serial listener thread will be created, even if this function is called multiple times.
    Uses a lock to prevent race conditions and a global flag to track if the thread is already active.
    """
    global _serial_listener_started
    
    with _serial_listener_lock:
        # Check if thread is already started
        if _serial_listener_started:
            print("DEBUG: Serial listener thread already active. Skipping duplicate initialization.")
            return
        
        # Mark as started before spawning thread
        _serial_listener_started = True
        
        # Now spawn the daemon thread
        t = threading.Thread(target=serial_listener_thread, args=(uwh_app,), daemon=True)
        t.start()
        print("DEBUG: Serial listener thread spawned successfully (first and only time).")
