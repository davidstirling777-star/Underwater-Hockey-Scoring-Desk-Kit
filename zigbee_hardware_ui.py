import serial.tools.list_ports
import serial_siren_listener


def update_usb_dongle_status(app):
    """Rescan COM ports and update USB dongle connection status in the UI."""

    if not hasattr(app, "usb_dongle_status_label"):
        return

    try:
        # Force a fresh scan.
        try:
            ports = serial_siren_listener.get_detected_ports()
            arduino_port = ports.get("arduino_port")
            zigbee_port = ports.get("zigbee_port")
        except Exception:
            arduino_port, zigbee_port = None, None

        if arduino_port:
            app.arduino_port = arduino_port

        if zigbee_port:
            app.zigbee_port = zigbee_port

        available_ports = list(serial.tools.list_ports.comports())

        zigbee_detected = False
        detected_port_text = None

        for port in available_ports:
            device = (port.device or "").upper()
            desc = (port.description or "").lower()
            hwid = (port.hwid or "").lower()

            looks_like_zigbee = (
                "zigbee" in desc
                or "sonoff" in desc
                or "itead" in desc
                or "silicon labs" in desc
                or "cp210" in desc
                or "cc2531" in desc
                or "cc2652" in desc
                or "10c4:ea60" in hwid
            )

            if looks_like_zigbee:
                zigbee_detected = True
                detected_port_text = port.device
                app.zigbee_port = port.device
                break

            if app.zigbee_port and device == app.zigbee_port.upper():
                zigbee_detected = True
                detected_port_text = port.device
                break

        if hasattr(app, "hardware_ports_label"):
            app.hardware_ports_label.config(
                text=(
                    f"Hardware Ports: Arduino={app.arduino_port}  "
                    f"Zigbee={app.zigbee_port}"
                )
            )

        if zigbee_detected:
            app.usb_dongle_status_label.config(
                text=f"Connected ({detected_port_text})",
                fg="green"
            )
            app.add_to_zigbee_log(
                f"USB Dongle: Connected ({detected_port_text})"
            )
        else:
            app.usb_dongle_status_label.config(
                text="Disconnected",
                fg="red"
            )
            app.add_to_zigbee_log("USB Dongle: Disconnected")

    except Exception as e:
        app.usb_dongle_status_label.config(
            text="Error",
            fg="red"
        )
        app.add_to_zigbee_log(f"USB Dongle check error: {e}")
        print(f"Error updating USB dongle status: {e}")


def monitor_usb_dongle_presence(app):
    """Continuously check whether the configured Zigbee USB dongle is still present."""

    try:
        if not hasattr(app, "usb_dongle_status_label"):
            app.usb_dongle_monitor_job = app.master.after(
                5000,
                app.monitor_usb_dongle_presence
            )
            return

        available_ports = list(serial.tools.list_ports.comports())
        current_zigbee_port = (app.zigbee_port or "").upper()

        port_still_present = False

        for port in available_ports:
            if (port.device or "").upper() == current_zigbee_port:
                port_still_present = True
                break

        if not port_still_present:
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

            app.add_to_zigbee_log(
                f"USB Dongle removed from {app.zigbee_port}"
            )

        app.usb_dongle_monitor_job = app.master.after(
            5000,
            app.monitor_usb_dongle_presence
        )

    except Exception as e:
        try:
            app.add_to_zigbee_log(
                f"USB dongle monitor error: {e}"
            )
        except Exception:
            pass

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

        available_ports = list(serial.tools.list_ports.comports())
        current_arduino_port = (app.arduino_port or "").upper()

        port_still_present = any(
            (port.device or "").upper() == current_arduino_port
            for port in available_ports
        )

        if port_still_present:
            app.arduino_status_label.config(
                text=f"Connected ({app.arduino_port})",
                fg="green"
            )
        else:
            app.arduino_status_label.config(
                text="Disconnected",
                fg="red"
            )
            app.add_to_zigbee_log(
                f"Arduino Siren removed from {app.arduino_port}"
            )

        app.arduino_monitor_job = app.master.after(
            5000,
            app.monitor_arduino_presence
        )

    except Exception as e:
        try:
            app.add_to_zigbee_log(f"Arduino monitor error: {e}")
        except Exception:
            pass

        app.arduino_monitor_job = app.master.after(
            5000,
            app.monitor_arduino_presence
        )
