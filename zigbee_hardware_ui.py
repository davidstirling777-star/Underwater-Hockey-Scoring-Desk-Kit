import serial.tools.list_ports
import serial_siren_listener


def _safe_log(app, message):
    try:
        app.add_to_zigbee_log(message)
    except Exception:
        pass


def _port_exists(port_name):
    if not port_name:
        return False

    wanted = port_name.upper()

    for port in serial.tools.list_ports.comports():
        if (port.device or "").upper() == wanted:
            return True

    return False

def _port_display_name(port_name):
    return port_name if port_name else "Not detected"


def _apply_hardware_status(app, arduino_port, zigbee_port):
    """Apply detected hardware ports and log only actual connection changes."""

    # Never allow one COM port to represent both devices.
    if (
        arduino_port
        and zigbee_port
        and arduino_port.upper() == zigbee_port.upper()
    ):
        print(
            "Invalid duplicate port assignment prevented: "
            f"Arduino={arduino_port}, Zigbee={zigbee_port}"
        )
        zigbee_port = None

    previous_arduino_port = getattr(
        app,
        "_last_detected_arduino_port",
        None
    )
    previous_zigbee_port = getattr(
        app,
        "_last_detected_zigbee_port",
        None
    )

    # Always overwrite old values, including with None.
    app.arduino_port = arduino_port
    app.zigbee_port = zigbee_port

    if hasattr(app, "arduino_status_label"):
        if arduino_port:
            app.arduino_status_label.config(
                text=f"Connected ({arduino_port})",
                fg="green"
            )
        else:
            app.arduino_status_label.config(
                text="Disconnected",
                fg="red"
            )

    if hasattr(app, "usb_dongle_status_label"):
        if zigbee_port:
            app.usb_dongle_status_label.config(
                text=f"Connected ({zigbee_port})",
                fg="green"
            )
        else:
            app.usb_dongle_status_label.config(
                text="Disconnected",
                fg="red"
            )

    if hasattr(app, "hardware_ports_label"):
        arduino_text = arduino_port or "Not detected"
        zigbee_text = zigbee_port or "Not detected"

        app.hardware_ports_label.config(
            text=(
                f"Hardware Ports: Arduino={arduino_text}  "
                f"Zigbee={zigbee_text}"
            )
        )

    def log_port_change(device_name, old_port, new_port):
        if old_port == new_port:
            return

        if old_port is None and new_port is not None:
            _safe_log(
                app,
                f"{device_name}: Connected ({new_port})"
            )

        elif old_port is not None and new_port is None:
            _safe_log(
                app,
                f"{device_name}: Disconnected ({old_port})"
            )

        elif old_port is not None and new_port is not None:
            _safe_log(
                app,
                f"{device_name}: Moved from {old_port} to {new_port}"
            )

    # Log only genuine changes.
    log_port_change(
        "Arduino Siren",
        previous_arduino_port,
        arduino_port
    )

    log_port_change(
        "USB Dongle",
        previous_zigbee_port,
        zigbee_port
    )

    # Save new state after comparison and logging.
    app._last_detected_arduino_port = arduino_port
    app._last_detected_zigbee_port = zigbee_port

def update_usb_dongle_status(app, force_rescan=False):
    """Detect current Arduino/Zigbee ports and update the status display."""

    try:
        ports = serial_siren_listener.get_detected_ports(
            force_scan=force_rescan
        )

        _apply_hardware_status(
            app,
            ports.get("arduino_port"),
            ports.get("zigbee_port")
        )

    except Exception as e:
        print(f"Hardware detection error: {e}")


def monitor_usb_dongle_presence(app):
    """Continuously rescan both hardware devices every five seconds."""

    try:
        update_usb_dongle_status(
            app,
            force_rescan=True
        )

    except Exception as e:
        print(f"Hardware monitor error: {e}")

    app.usb_dongle_monitor_job = app.master.after(
        5000,
        app.monitor_usb_dongle_presence
    )


def monitor_arduino_presence(app):
    """
    Compatibility method.

    Both devices are checked by monitor_usb_dongle_presence(), so this
    deliberately does not start a second duplicate monitoring loop.
    """
    return
