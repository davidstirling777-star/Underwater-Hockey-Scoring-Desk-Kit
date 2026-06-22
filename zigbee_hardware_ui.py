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


def update_usb_dongle_status(app):
    """Rescan COM ports and update Arduino/Zigbee hardware status labels."""

    try:
        ports = serial_siren_listener.get_detected_ports()
        arduino_port = ports.get("arduino_port")
        zigbee_port = ports.get("zigbee_port")
    except Exception:
        arduino_port = None
        zigbee_port = None

    if arduino_port:
        app.arduino_port = arduino_port

    if zigbee_port:
        app.zigbee_port = zigbee_port

    arduino_present = _port_exists(app.arduino_port)
    zigbee_present = _port_exists(app.zigbee_port)

    if hasattr(app, "arduino_status_label"):
        if arduino_present:
            app.arduino_status_label.config(
                text=f"Connected ({app.arduino_port})",
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
                text=f"Connected ({app.zigbee_port})",
                fg="green"
            )
            _safe_log(app, f"USB Dongle: Connected ({app.zigbee_port})")
        else:
            app.usb_dongle_status_label.config(
                text="Disconnected",
                fg="red"
            )
            _safe_log(app, "USB Dongle: Disconnected")

    if hasattr(app, "hardware_ports_label"):
        app.hardware_ports_label.config(
            text=(
                f"Hardware Ports: Arduino={app.arduino_port}  "
                f"Zigbee={app.zigbee_port}"
            )
        )


def monitor_usb_dongle_presence(app):
    """Continuously check whether the configured Zigbee USB dongle is still present."""

    try:
        if not hasattr(app, "usb_dongle_status_label"):
            app.usb_dongle_monitor_job = app.master.after(
                5000,
                app.monitor_usb_dongle_presence
            )
            return

        zigbee_present = _port_exists(app.zigbee_port)

        if zigbee_present:
            app.usb_dongle_status_label.config(
                text=f"Connected ({app.zigbee_port})",
                fg="green"
            )

        else:
            app.usb_dongle_status_label.config(
                text="Disconnected",
                fg="red"
            )

            app.zigbee_status_var.set(
                "Disconnected - USB dongle removed"
            )

            if hasattr(app, "toggle_connection_btn"):
                app.toggle_connection_btn.config(text="Connect")

            if getattr(app, "connected", False):
                app.connected = False

            if (
                hasattr(app, "zigbee_controller")
                and app.zigbee_controller
                and getattr(app.zigbee_controller, "connected", False)
            ):
                app.zigbee_controller.connected = False

            _safe_log(app, f"USB Dongle removed from {app.zigbee_port}")

        app.usb_dongle_monitor_job = app.master.after(
            5000,
            app.monitor_usb_dongle_presence
        )

    except Exception as e:
        _safe_log(app, f"USB dongle monitor error: {e}")

        app.usb_dongle_monitor_job = app.master.after(
            5000,
            app.monitor_usb_dongle_presence
        )


def monitor_arduino_presence(app):
    """Continuously check whether the configured Arduino siren is still present."""

    try:
        if not hasattr(app, "arduino_status_label"):
            app.arduino_monitor_job = app.master.after(
                5000,
                app.monitor_arduino_presence
            )
            return

        arduino_present = _port_exists(app.arduino_port)

        if arduino_present:
            app.arduino_status_label.config(
                text=f"Connected ({app.arduino_port})",
                fg="green"
            )

        else:
            app.arduino_status_label.config(
                text="Disconnected",
                fg="red"
            )

            _safe_log(app, f"Arduino Siren removed from {app.arduino_port}")

        app.arduino_monitor_job = app.master.after(
            5000,
            app.monitor_arduino_presence
        )

    except Exception as e:
        _safe_log(app, f"Arduino monitor error: {e}")

        app.arduino_monitor_job = app.master.after(
            5000,
            app.monitor_arduino_presence
        )
