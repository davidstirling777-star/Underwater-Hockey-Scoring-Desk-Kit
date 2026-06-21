    def update_usb_dongle_status(self):
        """Rescan COM ports and update USB dongle connection status in the UI."""

        if not hasattr(self, "usb_dongle_status_label"):
            return

        try:
            import serial.tools.list_ports

            # Force a fresh scan.
            try:
                import serial_siren_listener
                ports = serial_siren_listener.get_detected_ports()
                arduino_port = ports.get("arduino_port")
                zigbee_port = ports.get("zigbee_port")
            except Exception:
                arduino_port, zigbee_port = auto_detect_com_ports()

            if arduino_port:
                self.arduino_port = arduino_port

            if zigbee_port:
                self.zigbee_port = zigbee_port

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
                    self.zigbee_port = port.device
                    break

                if self.zigbee_port and device == self.zigbee_port.upper():
                    zigbee_detected = True
                    detected_port_text = port.device
                    break

            if hasattr(self, "hardware_ports_label"):
                self.hardware_ports_label.config(
                    text=(
                        f"Hardware Ports: Arduino={self.arduino_port}  "
                        f"Zigbee={self.zigbee_port}"
                    )
                )

            if zigbee_detected:
                self.usb_dongle_status_label.config(
                    text=f"Connected ({detected_port_text})",
                    fg="green"
                )
                self.add_to_zigbee_log(
                    f"USB Dongle: Connected ({detected_port_text})"
                )
            else:
                self.usb_dongle_status_label.config(
                    text="Disconnected",
                    fg="red"
                )
                self.add_to_zigbee_log("USB Dongle: Disconnected")

        except Exception as e:
            self.usb_dongle_status_label.config(
                text="Error",
                fg="red"
            )
            self.add_to_zigbee_log(f"USB Dongle check error: {e}")
            print(f"Error updating USB dongle status: {e}")

    def monitor_usb_dongle_presence(self):
        """Continuously check whether the configured Zigbee USB dongle is still present."""
        try:
            if not hasattr(self, "usb_dongle_status_label"):
                self.usb_dongle_monitor_job = self.master.after(
                    5000,
                    self.monitor_usb_dongle_presence
                )
                return
    
            import serial.tools.list_ports
    
            available_ports = list(serial.tools.list_ports.comports())
            current_zigbee_port = (self.zigbee_port or "").upper()
    
            port_still_present = False
    
            for port in available_ports:
                if (port.device or "").upper() == current_zigbee_port:
                    port_still_present = True
                    break
    
            if not port_still_present:
                self.usb_dongle_status_label.config(
                    text="Disconnected",
                    fg="red"
                )
    
                self.zigbee_status_var.set("Disconnected - USB dongle removed")
    
                if hasattr(self, "toggle_connection_btn"):
                    self.toggle_connection_btn.config(text="Connect")
    
                if getattr(self, "connected", False):
                    self.connected = False
    
                if (
                    hasattr(self, "zigbee_controller")
                    and self.zigbee_controller
                    and getattr(self.zigbee_controller, "connected", False)
                ):
                    self.zigbee_controller.connected = False
    
                self.add_to_zigbee_log(
                    f"USB Dongle removed from {self.zigbee_port}"
                )
    
            self.usb_dongle_monitor_job = self.master.after(
                5000,
                self.monitor_usb_dongle_presence
            )
    
        except Exception as e:
            try:
                self.add_to_zigbee_log(
                    f"USB dongle monitor error: {e}"
                )
            except Exception:
                pass
    
            self.usb_dongle_monitor_job = self.master.after(
                5000,
                self.monitor_usb_dongle_presence
            )
