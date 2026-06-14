import os
import json
import time
import serial
import serial.tools.list_ports
import threading
import pygame
import sound

DEBUG_MODE = False
SETTINGS_FILE = "settings.json"

_serial_listener_started = False
_serial_listener_lock = threading.Lock()

_detected_ports = {
    "arduino_port": None,
    "zigbee_port": None,
}


def _debug(message):
    if DEBUG_MODE:
        print(message)


def _settings_path():
    return os.path.join(os.getcwd(), SETTINGS_FILE)


def load_hardware_ports_from_json():
    try:
        path = _settings_path()
        if not os.path.exists(path):
            return None, None

        with open(path, "r", encoding="utf-8") as f:
            settings = json.load(f)

        hardware = settings.get("hardwareDetection", {})
        return hardware.get("arduino_port"), hardware.get("zigbee_port")

    except Exception as e:
        _debug(f"Hardware port load failed: {e}")
        return None, None


def save_hardware_ports_to_json(arduino_port, zigbee_port):
    try:
        path = _settings_path()
        settings = {}

        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except Exception:
                settings = {}

        settings["hardwareDetection"] = {
            "arduino_port": arduino_port,
            "zigbee_port": zigbee_port,
            "last_detected": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)

        _debug(
            f"Saved hardware detection cache: "
            f"Arduino={arduino_port}, Zigbee={zigbee_port}"
        )

    except Exception as e:
        print(f"Hardware port save failed: {e}")


def _port_exists(port_name):
    if not port_name:
        return False

    ports = list(serial.tools.list_ports.comports())
    return any(p.device.upper() == port_name.upper() for p in ports)


def _is_arduino_port(port):
    description = (port.description or "").lower()
    hwid = (port.hwid or "").lower()

    return (
        "arduino" in description
        or "nano" in description
        or "ch340" in description
        or "usb-serial" in description
        or "vid:pid=2341:0058" in hwid
        or "vid:pid=2341:0042" in hwid
        or "1a86:7523" in hwid
    )


def _is_zigbee_port(port):
    description = (port.description or "").lower()
    hwid = (port.hwid or "").lower()

    return (
        "zigbee" in description
        or "sonoff" in description
        or "itead" in description
        or "silicon labs" in description
        or "cp210" in description
        or "cc2531" in description
        or "cc2652" in description
        or "10c4:ea60" in hwid
    )


def detect_hardware_ports(force_scan=False):
    global _detected_ports

    if (
        not force_scan
        and _detected_ports["arduino_port"]
        and _detected_ports["zigbee_port"]
    ):
        return _detected_ports["arduino_port"], _detected_ports["zigbee_port"]

    cached_arduino, cached_zigbee = load_hardware_ports_from_json()

    if (
        not force_scan
        and _port_exists(cached_arduino)
        and _port_exists(cached_zigbee)
        and cached_arduino != cached_zigbee
    ):
        _debug(
            f"Using cached hardware ports: "
            f"Arduino={cached_arduino}, Zigbee={cached_zigbee}"
        )

        _detected_ports["arduino_port"] = cached_arduino
        _detected_ports["zigbee_port"] = cached_zigbee

        return cached_arduino, cached_zigbee

    _debug("Cached hardware ports missing or invalid. Scanning COM ports...")

    arduino_port = None
    zigbee_port = None

    ports = list(serial.tools.list_ports.comports())
    assigned_ports = set()

    _debug(f"Scanning system... Found {len(ports)} available COM ports.")

    for port in ports:
        if _is_arduino_port(port):
            arduino_port = port.device
            assigned_ports.add(port.device)
            _debug(f"Found Arduino candidate on {port.device}")
            break

    for port in ports:
        if port.device in assigned_ports:
            continue

        if _is_zigbee_port(port):
            zigbee_port = port.device
            assigned_ports.add(port.device)
            _debug(f"Found Zigbee Dongle on {port.device}")
            break

    if not arduino_port:
        arduino_port = cached_arduino if _port_exists(cached_arduino) else "COM5"
        print(f"Warning: Arduino fallback set to {arduino_port}")

    if not zigbee_port:
        zigbee_port = cached_zigbee if _port_exists(cached_zigbee) else "COM6"
        print(f"Warning: Zigbee fallback set to {zigbee_port}")

    _detected_ports["arduino_port"] = arduino_port
    _detected_ports["zigbee_port"] = zigbee_port

    save_hardware_ports_to_json(arduino_port, zigbee_port)

    return arduino_port, zigbee_port


def get_arduino_port():
    arduino_port, _ = detect_hardware_ports()
    return arduino_port


def get_zigbee_port():
    _, zigbee_port = detect_hardware_ports()
    return zigbee_port


def get_detected_ports():
    arduino_port, zigbee_port = detect_hardware_ports()
    return {
        "arduino_port": arduino_port,
        "zigbee_port": zigbee_port,
    }


def serial_listener_thread(uwh_app):
    button_held_down = False
    last_local_siren_refresh = 0

    while True:
        arduino_port, zigbee_port = detect_hardware_ports()

        if not arduino_port:
            print("No Arduino serial port found for siren button. Retrying in 5s...")
            time.sleep(5)
            continue

        _debug(
            f"Attempting to connect to siren button on {arduino_port} "
            f"(Zigbee reserved on {zigbee_port})..."
        )

        try:
            with serial.Serial(arduino_port, 9600, timeout=0.1) as ser:
                ser.dtr = True
                ser.rts = True

                time.sleep(1.5)
                ser.reset_input_buffer()

                button_held_down = False
                last_local_siren_refresh = 0

                _debug(f"Successfully connected to siren button on {arduino_port}!")

                while True:
                    try:
                        raw_data = ser.readline()

                        if not raw_data:
                            continue

                        line = raw_data.decode(
                            "utf-8",
                            errors="replace"
                        ).strip()

                        if line == "SIREN_ON":
                            now = time.monotonic()

                            if not button_held_down:
                                _debug("Button Triggered: SIREN_ON")
                                button_held_down = True

                                try:
                                    uwh_app.zigbee_controller.start_siren_continuous()
                                except Exception as net_err:
                                    print(f"Wireless Trigger Note: {net_err}")

                            try:
                                duration = (
                                    float(uwh_app.siren_duration.get())
                                    if hasattr(uwh_app, "siren_duration")
                                    else 1.5
                                )

                                refresh_interval = max(0.5, duration - 0.25)

                                if now - last_local_siren_refresh >= refresh_interval:
                                    track = (
                                        uwh_app.siren_var.get()
                                        if hasattr(uwh_app, "siren_var")
                                        else "siren-police.mp3"
                                    )

                                    _debug(
                                        "Local Speaker Audio refreshed via "
                                        f"play_sound_with_volume: '{track}' "
                                        f"for {duration}s"
                                    )

                                    sound.play_sound_with_volume(
                                        track,
                                        "siren",
                                        uwh_app.enable_sound,
                                        uwh_app.pips_volume,
                                        uwh_app.siren_volume,
                                        uwh_app.air_volume,
                                        uwh_app.water_volume,
                                        uwh_app.siren_duration,
                                    )

                                    last_local_siren_refresh = now

                            except Exception as audio_err:
                                print(f"Local Speaker Playback Error: {audio_err}")

                        elif line == "SIREN_OFF":
                            if button_held_down:
                                _debug("Button Released: SIREN_OFF matched.")
                                button_held_down = False
                                last_local_siren_refresh = 0

                                try:
                                    uwh_app.zigbee_controller.stop_siren_continuous()
                                except Exception:
                                    pass

                                try:
                                    pygame.mixer.stop()
                                    _debug("Local Speaker Audio Stopped.")
                                except Exception as stop_err:
                                    print(f"Error stopping local audio: {stop_err}")

                    except serial.SerialException:
                        raise

        except Exception as e:
            button_held_down = False
            last_local_siren_refresh = 0

            try:
                pygame.mixer.stop()
            except Exception:
                pass

            print(
                f"Serial listener encountered an error on {arduino_port}: {e}. "
                "Forcing hardware rescan and retrying in 3s..."
            )

            detect_hardware_ports(force_scan=True)
            time.sleep(3)


def start_serial_listener(uwh_app):
    global _serial_listener_started

    with _serial_listener_lock:
        if _serial_listener_started:
            _debug("Serial listener thread already active. Skipping duplicate initialization.")
            return

        detect_hardware_ports()

        _serial_listener_started = True

        t = threading.Thread(
            target=serial_listener_thread,
            args=(uwh_app,),
            daemon=True,
        )
        t.start()

        _debug("Serial listener thread spawned successfully.")
