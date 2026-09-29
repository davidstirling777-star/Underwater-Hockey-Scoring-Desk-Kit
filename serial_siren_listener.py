"""Identify Arduino and coordinator serial ports; read wired button events.

Only the Arduino port is opened here. The Zigbee USB coordinator remains
owned by Zigbee2MQTT. Detection merely reports that COMx exists; the
"listener opened" event is the proof that pyserial actually acquired it.
Worker-thread events go through GameManagementApp's queue to the Tk thread.
"""

import os
import json
import time
import serial
import serial.tools.list_ports
import threading
import sys
import settings_manager

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
    # Use the same persistent settings directory as uwh.py and zigbee_siren.
    # A shortcut/Task Scheduler launch may have an unrelated working folder.
    directory = (
        os.path.dirname(os.path.abspath(sys.executable))
        if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__))
    )
    return os.path.join(directory, SETTINGS_FILE)


def load_hardware_ports_from_json():
    try:
        path = _settings_path()
        if not os.path.exists(path):
            return None, None

        settings = settings_manager.load_unified_settings(
            os.path.dirname(path)
        )

        hardware = settings.get("hardwareDetection", {})
        return hardware.get("arduino_port"), hardware.get("zigbee_port")

    except Exception as e:
        _debug(f"Hardware port load failed: {e}")
        return None, None


def save_hardware_ports_to_json(arduino_port, zigbee_port):
    try:
        # Same directory as the active UWH settings; protected central writer.
        settings_dir = os.path.dirname(_settings_path())
        settings = settings_manager.load_unified_settings(settings_dir)
        old_ports = settings.get("hardwareDetection", {})
        # The five-second hardware poll must not write a new timestamp
        # and create twelve backups per minute for unchanged ports.
        if (
            old_ports.get("arduino_port") == arduino_port
            and old_ports.get("zigbee_port") == zigbee_port
        ):
            return
        settings["hardwareDetection"] = {
            "arduino_port": arduino_port,
            "zigbee_port": zigbee_port,
            "last_detected": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        settings_manager.save_unified_settings(settings_dir, settings)

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

    # A Zigbee USB serial adapter may also advertise "USB-Serial".
    # Prefer explicit Zigbee identity rather than opening its COM port as
    # the Arduino button and waiting forever for SIREN_ON.
    if _is_zigbee_port(port):
        return False

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
        and _port_exists(_detected_ports["arduino_port"])
        and _port_exists(_detected_ports["zigbee_port"])
    ):
        return (
            _detected_ports["arduino_port"],
            _detected_ports["zigbee_port"]
        )

    cached_arduino, cached_zigbee = load_hardware_ports_from_json()

    if (
        not force_scan
        and _port_exists(cached_arduino)
        and _port_exists(cached_zigbee)
        and cached_arduino != cached_zigbee
        and any(
            port.device.upper() == cached_arduino.upper()
            and _is_arduino_port(port)
            for port in serial.tools.list_ports.comports()
        )
        and any(
            port.device.upper() == cached_zigbee.upper()
            and _is_zigbee_port(port)
            for port in serial.tools.list_ports.comports()
        )
    ):
        _detected_ports["arduino_port"] = cached_arduino
        _detected_ports["zigbee_port"] = cached_zigbee

        return cached_arduino, cached_zigbee

    _debug("Scanning COM ports for currently connected hardware...")

    arduino_port = None
    zigbee_port = None

    ports = list(serial.tools.list_ports.comports())
    assigned_ports = set()

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

    # Never invent a COM port for missing hardware.
    # None means the device is not physically detected.
    if not arduino_port:
        _debug("Arduino not detected.")

    if not zigbee_port:
        _debug("Zigbee dongle not detected.")

    # Safety: one COM port can never be both devices.
    if (
        arduino_port
        and zigbee_port
        and arduino_port.upper() == zigbee_port.upper()
    ):
        _debug(
            f"Invalid duplicate port assignment prevented: "
            f"Arduino={arduino_port}, Zigbee={zigbee_port}"
        )
        zigbee_port = None

    _detected_ports["arduino_port"] = arduino_port
    _detected_ports["zigbee_port"] = zigbee_port

    # Save the real detection result, including None for missing devices.
    save_hardware_ports_to_json(
        arduino_port,
        zigbee_port
    )

    return arduino_port, zigbee_port


def get_arduino_port():
    arduino_port, _ = detect_hardware_ports()
    return arduino_port


def get_zigbee_port():
    _, zigbee_port = detect_hardware_ports()
    return zigbee_port


def get_detected_ports(force_scan=False):
    arduino_port, zigbee_port = detect_hardware_ports(
        force_scan=force_scan
    )

    return {
        "arduino_port": arduino_port,
        "zigbee_port": zigbee_port,
    }


def _send_app_siren_event(uwh_app, event_name):
    try:
        uwh_app.handle_hardware_siren_event(event_name)
    except Exception as event_err:
        print(f"Local siren callback error ({event_name}): {event_err}")


def serial_listener_thread(uwh_app):
    button_held_down = False

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

                print(
                    f"Arduino siren serial listener opened {arduino_port} "
                    "at 9600 baud; waiting for SIREN_ON / SIREN_OFF."
                )
                _send_app_siren_event(
                    uwh_app, f"ARDUINO_SERIAL_OPEN:{arduino_port}"
                )

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
                            if not button_held_down:
                                print(f"Arduino siren button ON received on {arduino_port}")
                                button_held_down = True
                                _send_app_siren_event(uwh_app, "ON")

                        elif line == "SIREN_OFF":
                            if button_held_down:
                                print(f"Arduino siren button OFF received on {arduino_port}")
                                button_held_down = False
                                _send_app_siren_event(uwh_app, "OFF")

                    except serial.SerialException:
                        raise

        except Exception as e:
            button_held_down = False
            _send_app_siren_event(uwh_app, "OFF")

            print(
                f"Serial listener encountered an error on {arduino_port}: {e}. "
                "Forcing hardware rescan and retrying in 3s..."
            )
            _send_app_siren_event(
                uwh_app, f"ARDUINO_SERIAL_ERROR:{arduino_port}: {e}"
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
