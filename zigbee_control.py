    def start_zigbee_connection(self):
        """Start the Zigbee siren connection."""
        # Mark as user-initiated action to prevent watchdog interference
        self.user_initiated_action = True
        self.stop_connection_watchdog()
        
        try:
            if self.zigbee_controller.start():
                self.toggle_connection_btn.config(text="Disconnect", state="normal")
                self.add_to_zigbee_log("Starting Zigbee connection...")
            else:
                self.add_to_zigbee_log("Failed to start Zigbee connection")
                messagebox.showerror("Connection Error", 
                                   "Failed to start Zigbee connection. Check MQTT library installation.")
        except Exception as e:
            self.add_to_zigbee_log(f"Error starting connection: {e}")
            messagebox.showerror("Connection Error", f"Error starting connection: {e}")
        finally:
            # Reset user action flag after a brief delay
            self.master.after(1000, lambda: setattr(self, 'user_initiated_action', False))

    def stop_zigbee_connection(self):
        """Stop the Zigbee siren connection."""
        # Mark as user-initiated action to prevent watchdog interference
        self.user_initiated_action = True
        self.stop_connection_watchdog()
        
        try:
            self.zigbee_controller.stop()
            self.toggle_connection_btn.config(text="Connect", state="normal")
            self.add_to_zigbee_log("Zigbee connection stopped")
        except Exception as e:
            self.add_to_zigbee_log(f"Error stopping connection: {e}")
        finally:
            # Reset user action flag after a brief delay
            self.master.after(1000, lambda: setattr(self, 'user_initiated_action', False))

    def toggle_zigbee_connection(self):
        """Toggle Zigbee connection (connect if disconnected, disconnect if connected)."""
        if self.zigbee_controller.connected:
            self.stop_zigbee_connection()
        else:
            self.start_zigbee_connection()

    def test_zigbee_connection(self):
        """Test the MQTT connection."""
        self.add_to_zigbee_log("Testing MQTT connection...")
        try:
            if self.zigbee_controller.test_connection():
                self.add_to_zigbee_log("Connection test successful")
                messagebox.showinfo("Connection Test", "MQTT connection test successful!")
            else:
                self.add_to_zigbee_log("Connection test failed")
                messagebox.showerror("Connection Test", "MQTT connection test failed. Check configuration.")
        except Exception as e:
            self.add_to_zigbee_log(f"Connection test error: {e}")
            messagebox.showerror("Connection Test", f"Connection test error: {e}")
          
    def start_connection_watchdog(self):
        """Start the connection watchdog to monitor and retry Zigbee connections."""
        if self.connection_watchdog_active:
            return  # Already running
        
        self.connection_watchdog_active = True
        self.connection_watchdog_attempts = 0
        self.user_initiated_action = False
        self.add_to_zigbee_log("Starting connection watchdog...")
        
        # Start the first connection attempt
        self.schedule_connection_check()
    
    def stop_connection_watchdog(self):
        """Stop the connection watchdog."""
        if self.connection_watchdog_job:
            self.master.after_cancel(self.connection_watchdog_job)
            self.connection_watchdog_job = None
        
        self.connection_watchdog_active = False
        self.connection_watchdog_attempts = 0
        
        if hasattr(self, 'zigbee_status_var'):
            self.add_to_zigbee_log("Connection watchdog stopped")

    def schedule_connection_check(self):
        """Schedule the next connection check after 10 seconds."""
        if not self.connection_watchdog_active:
            return
        
        # Cancel any existing scheduled check
        if self.connection_watchdog_job:
            self.master.after_cancel(self.connection_watchdog_job)
        
        # Schedule the next check in 10 seconds (10000 ms)
        self.connection_watchdog_job = self.master.after(10000, self.check_connection_status)

    def check_connection_status(self):
        """Check connection status and attempt reconnection if needed."""
        if not self.connection_watchdog_active or self.user_initiated_action:
            return
        
        # Check if already connected
        if self.zigbee_controller.connected:
            self.add_to_zigbee_log("Watchdog: Connection established successfully")
            self.stop_connection_watchdog()
            return
        
        # Not connected, attempt reconnection
        self.connection_watchdog_attempts += 1
        
        if self.connection_watchdog_attempts <= self.connection_watchdog_max_attempts:
            self.add_to_zigbee_log(f"Watchdog: Connection attempt {self.connection_watchdog_attempts}/{self.connection_watchdog_max_attempts}")
            
            try:
                if self.zigbee_controller.start():
                    # Connection attempt started, wait for callback
                    self.schedule_connection_check()
                else:
                    # Immediate failure, schedule next attempt
                    self.schedule_connection_check()
            except Exception as e:
                self.add_to_zigbee_log(f"Watchdog connection error: {e}")
                self.schedule_connection_check()
        else:
            # Max attempts reached
            self.add_to_zigbee_log(f"Watchdog: Max connection attempts ({self.connection_watchdog_max_attempts}) reached. Giving up.")
            self.toggle_connection_btn.config(text="Connect", state="normal")
            self.stop_connection_watchdog()

    def save_zigbee_config(self):
        """Save Zigbee configuration."""
        try:
            config = {}
            for key, widget in self.config_widgets.items():
                value = widget.get()
                if key == "mqtt_port":
                    config[key] = int(value) if value.isdigit() else 1883
                elif key == "siren_button_devices":
                    # Convert comma-separated string to list
                    device_names = [name.strip() for name in value.split(",") if name.strip()]
                    config["siren_button_devices"] = device_names
                    # Also set legacy single device for backward compatibility
                    config["siren_button_device"] = device_names[0] if device_names else "siren_button"
                else:
                    config[key] = value
            
            # Keep other settings from current config
            current_config = self.zigbee_controller.config.copy()
            current_config.update(config)
            
            # Save to both the Zigbee controller and unified settings
            self.zigbee_controller.save_config(current_config)
            
            # Also save to unified settings file
            unified_settings = load_unified_settings()
            unified_settings["zigbeeSettings"] = current_config
            save_unified_settings(unified_settings)
            
            self.add_to_zigbee_log("Configuration saved")
            messagebox.showinfo("Configuration", "Zigbee configuration saved successfully!")
        except Exception as e:
            self.add_to_zigbee_log(f"Error saving config: {e}")
            messagebox.showerror("Configuration Error", f"Error saving configuration: {e}")

    def update_zigbee_status(self, connected: bool, message: str = ""):
        """Update Zigbee connection status in UI."""
        try:
            if connected:
                status_text = "Connected"
                self.zigbee_status_label.config(fg="green")
                self.toggle_connection_btn.config(text="Disconnect", state="normal")

                if self.connection_watchdog_active and not self.user_initiated_action:
                    self.add_to_zigbee_log("Watchdog: Connection established successfully")
                    self.stop_connection_watchdog()
            else:
                status_text = "Disconnected"
                self.zigbee_status_label.config(fg="red")

                if not self.connection_watchdog_active or (
                    self.connection_watchdog_attempts >= self.connection_watchdog_max_attempts
                ):
                    self.toggle_connection_btn.config(text="Connect", state="normal")
                else:
                    self.toggle_connection_btn.config(text="Disconnect", state="normal")

            self.zigbee_status_var.set(status_text)

            if message and message != status_text:
                self.add_to_zigbee_log(f"Status: {status_text} - {message}")
            else:
                self.add_to_zigbee_log(f"Status: {status_text}")

        except Exception as e:
            print(f"Error updating Zigbee status: {e}")
