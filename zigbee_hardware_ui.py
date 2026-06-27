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


def _apply_hardware_status(
    app,
    arduino_port,
    zigbee_port,
    log_result=False
):
    """Apply strictly detected hardware ports to the UI."""

    # Safety: one physical COM port must never be assigned to both devices.
    if (
        arduino_port
        and zigbee_port
        and arduino_port.upper() == zigbee_port.upper()
    ):
        _safe_log(
            app,
            f"Invalid duplicate port assignment prevented: "
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

    app._last_detected_arduino_port = arduino_port
    app._last_detected_zigbee_port = zigbee_port

    arduino_present = arduino_port is not None
    zigbee_present = zigbee_port is not None

    if hasattr(app, "arduino_status_label"):
        if arduino_present:
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
        if zigbee_present:
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
        app.hardware_ports_label.config(
            text=(
                "Hardware Ports: "
                f"Arduino={_port_display_name(arduino_port)}  "
                f"Zigbee={_port_display_name(zigbee_port)}"
            )
        )

    # Log only when the detected hardware changed, not every five seconds.
    if log_result or previous_arduino_port != arduino_port:
        if arduino_present:
            _safe_log(app, f"Arduino Siren: Connected ({arduino_port})")
        else:
            _safe_log(app, "Arduino Siren: Disconnected")

    if log_result or previous_zigbee_port != zigbee_port:
        if zigbee_present:
            _safe_log(app, f"USB Dongle: Connected ({zigbee_port})")
        else:
            _safe_log(app, "USB Dongle: Disconnected")


def update_usb_dongle_status(app, force_rescan=False):
    """Detect both hardware devices and update their status rows."""

    try:
        ports = serial_siren_listener.get_detected_ports(
            force_scan=force_rescan
        )

        _apply_hardware_status(
            app,
            ports.get("arduino_port"),
            ports.get("zigbee_port"),
            log_result=force_rescan
        )

    except Exception as e:
        _safe_log(app, f"Hardware detection error: {e}")

        _apply_hardware_status(
            app,
            None,
            None,
            log_result=True
        )


def monitor_usb_dongle_presence(app):
    """Continuously rescan both hardware devices every five seconds."""

    try:
        update_usb_dongle_status(
            app,
            force_rescan=True
        )

    except Exception as e:
        _safe_log(app, f"Hardware monitor error: {e}")

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
