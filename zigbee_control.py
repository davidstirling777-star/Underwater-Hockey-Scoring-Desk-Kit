from tkinter import messagebox


def start_zigbee_connection(app):
    app.user_initiated_action = True
    app.stop_connection_watchdog()

    try:
        if app.zigbee_controller.start():
            app.toggle_connection_btn.config(text="Disconnect", state="normal")
            app.add_to_zigbee_log("Starting Zigbee connection...")
        else:
            app.add_to_zigbee_log("Failed to start Zigbee connection")
            messagebox.showerror(
                "Connection Error",
                "Failed to start Zigbee connection. Check MQTT library installation."
            )
    except Exception as e:
        app.add_to_zigbee_log(f"Error starting connection: {e}")
        messagebox.showerror("Connection Error", f"Error starting connection: {e}")
    finally:
        app.master.after(
            1000,
            lambda: setattr(app, "user_initiated_action", False)
        )


def stop_zigbee_connection(app):
    app.user_initiated_action = True
    app.stop_connection_watchdog()

    try:
        app.zigbee_controller.stop()
        app.toggle_connection_btn.config(text="Connect", state="normal")
        app.add_to_zigbee_log("Zigbee connection stopped")
    except Exception as e:
        app.add_to_zigbee_log(f"Error stopping connection: {e}")
    finally:
        app.master.after(
            1000,
            lambda: setattr(app, "user_initiated_action", False)
        )


def toggle_zigbee_connection(app):
    if app.zigbee_controller.connected:
        app.stop_zigbee_connection()
    else:
        app.start_zigbee_connection()


def test_zigbee_connection(app):
    app.add_to_zigbee_log("Testing MQTT connection...")

    try:
        if app.zigbee_controller.test_connection():
            app.add_to_zigbee_log("Connection test successful")
            messagebox.showinfo(
                "Connection Test",
                "MQTT connection test successful!"
            )
        else:
            app.add_to_zigbee_log("Connection test failed")
            messagebox.showerror(
                "Connection Test",
                "MQTT connection test failed. Check configuration."
            )
    except Exception as e:
        app.add_to_zigbee_log(f"Connection test error: {e}")
        messagebox.showerror("Connection Test", f"Connection test error: {e}")


def start_connection_watchdog(app):
    if app.connection_watchdog_active:
        return

    app.connection_watchdog_active = True
    app.connection_watchdog_attempts = 0
    app.user_initiated_action = False
    app.add_to_zigbee_log("Starting connection watchdog...")

    app.schedule_connection_check()


def stop_connection_watchdog(app):
    if app.connection_watchdog_job:
        app.master.after_cancel(app.connection_watchdog_job)
        app.connection_watchdog_job = None

    app.connection_watchdog_active = False
    app.connection_watchdog_attempts = 0

    if hasattr(app, "zigbee_status_var"):
        app.add_to_zigbee_log("Connection watchdog stopped")


def schedule_connection_check(app):
    if not app.connection_watchdog_active:
        return

    if app.connection_watchdog_job:
        app.master.after_cancel(app.connection_watchdog_job)

    app.connection_watchdog_job = app.master.after(
        10000,
        app.check_connection_status
    )


def check_connection_status(app):
    if not app.connection_watchdog_active or app.user_initiated_action:
        return

    if app.zigbee_controller.connected:
        app.add_to_zigbee_log("Watchdog: Connection established successfully")
        app.stop_connection_watchdog()
        return

    app.connection_watchdog_attempts += 1

    if app.connection_watchdog_attempts <= app.connection_watchdog_max_attempts:
        app.add_to_zigbee_log(
            f"Watchdog: Connection attempt "
            f"{app.connection_watchdog_attempts}/"
            f"{app.connection_watchdog_max_attempts}"
        )

        try:
            app.zigbee_controller.start()
            app.schedule_connection_check()
        except Exception as e:
            app.add_to_zigbee_log(f"Watchdog connection error: {e}")
            app.schedule_connection_check()

    else:
        app.add_to_zigbee_log(
            f"Watchdog: Max connection attempts "
            f"({app.connection_watchdog_max_attempts}) reached. Giving up."
        )
        app.toggle_connection_btn.config(text="Connect", state="normal")
        app.stop_connection_watchdog()


def update_zigbee_status(app, connected: bool, message: str = ""):
    try:
        if connected:
            status_text = "Connected"
            app.zigbee_status_label.config(fg="green")
            app.toggle_connection_btn.config(text="Disconnect", state="normal")

            if app.connection_watchdog_active and not app.user_initiated_action:
                app.add_to_zigbee_log("Watchdog: Connection established successfully")
                app.stop_connection_watchdog()

        else:
            status_text = "Disconnected"
            app.zigbee_status_label.config(fg="red")

            if not app.connection_watchdog_active or (
                app.connection_watchdog_attempts >= app.connection_watchdog_max_attempts
            ):
                app.toggle_connection_btn.config(text="Connect", state="normal")
            else:
                app.toggle_connection_btn.config(text="Disconnect", state="normal")

        app.zigbee_status_var.set(status_text)

        if message and message != status_text:
            app.add_to_zigbee_log(f"Status: {status_text} - {message}")
        else:
            app.add_to_zigbee_log(f"Status: {status_text}")

    except Exception as e:
        print(f"Error updating Zigbee status: {e}")
