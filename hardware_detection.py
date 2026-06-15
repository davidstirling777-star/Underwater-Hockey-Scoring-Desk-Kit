import os
import subprocess
import datetime
import serial
import serial.tools.list_ports


def load_hardware_detection_cache(load_unified_settings):
    try:
        unified_settings = load_unified_settings()
        return unified_settings.get("hardwareDetection", {})
    except Exception:
        return {}


def save_hardware_detection_cache(
    arduino_port,
    zigbee_port,
    load_unified_settings,
    save_unified_settings,
    debug_mode=False
):
    try:
        unified_settings = load_unified_settings()
        unified_settings["hardwareDetection"] = {
            "arduino_port": arduino_port,
            "zigbee_port": zigbee_port,
            "last_detected": datetime.datetime.now().isoformat()
        }
        save_unified_settings(unified_settings)

        if debug_mode:
            print(f"Saved hardware detection cache: Arduino={arduino_port}, Zigbee={zigbee_port}")

    except Exception as e:
        if debug_mode:
            print(f"Warning: Could not save hardware detection cache: {e}")


def is_usb_dongle_connected(load_unified_settings, debug_mode=False):
    import platform

    system = platform.system()

    if system == "Linux":
        try:
            dev_dir = os.path.join(os.sep, "dev")
            if os.path.exists(dev_dir):
                devices = [f for f in os.listdir(dev_dir) if f.startswith("ttyUSB")]
                if devices:
                    return True
        except (OSError, PermissionError):
            pass

        try:
            result = subprocess.run(
                ["lsusb"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                usb_output = result.stdout.lower()
                zigbee_keywords = [
                    "itead",
                    "sonoff",
                    "cc2531",
                    "cc2652",
                    "silicon labs",
                    "cp210"
                ]

                return any(keyword in usb_output for keyword in zigbee_keywords)

        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError
        ):
            pass

    elif system == "Windows":
        try:
            detection = load_hardware_detection_cache(load_unified_settings)
            zigbee_port = detection.get("zigbee_port")
            return bool(zigbee_port)

        except Exception as e:
            if debug_mode:
                print(f"USB dongle Windows check failed: {e}")

    return False


def auto_detect_com_ports(
    load_unified_settings,
    save_unified_settings,
    debug_mode=False
):
    arduino_port = None
    zigbee_port = None

    ports = list(serial.tools.list_ports.comports())
    assigned_ports = set()

    if debug_mode:
        print(f"Scanning system... Found {len(ports)} available COM ports.")

    for p in ports:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        device = p.device or ""

        if (
            "arduino" in desc
            or "ch340" in desc
            or "usb-serial" in desc
            or "vid:pid=2341" in hwid
            or "1a86:7523" in hwid
        ):
            if debug_mode:
                print(f"Found Arduino candidate via hardware profile on {device}")

            arduino_port = device
            assigned_ports.add(device)
            break

    for p in ports:
        if p.device in assigned_ports:
            continue

        desc = (p.description or "").lower()
        device = p.device or ""

        if debug_mode:
            print(f"Testing port {device} for Zigbee or missing devices...")

        if (
            "ti cc2531" in desc
            or "silicon labs" in desc
            or "cp210" in desc
            or "sonoff" in desc
            or "zigbee" in desc
        ):
            zigbee_port = device
            assigned_ports.add(device)

            if debug_mode:
                print(f"Found Zigbee Dongle on {device}")

            break

        try:
            with serial.Serial(device, 9600, timeout=1):
                if not zigbee_port:
                    zigbee_port = device
                    assigned_ports.add(device)

                    if debug_mode:
                        print(f"Found alternative device on {device}")

        except (serial.SerialException, PermissionError):
            if debug_mode:
                print(f"Port {device} is locked or unavailable. Skipping.")
            continue

    if not arduino_port:
        print("Warning: Arduino not detected automatically. Defaulting to COM5.")
        arduino_port = "COM5"

    if not zigbee_port:
        print("Warning: Zigbee not detected automatically. Defaulting to COM6.")
        zigbee_port = "COM6"

    save_hardware_detection_cache(
        arduino_port,
        zigbee_port,
        load_unified_settings,
        save_unified_settings,
        debug_mode
    )

    return arduino_port, zigbee_port
