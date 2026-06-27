import tkinter as tk
from tkinter import ttk
import webbrowser

from zigbee_siren import is_mqtt_available


def create_zigbee_siren_tab(app):
    """Create the Zigbee Siren configuration tab."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Zigbee Siren")

    label_font = ("Arial", 11)
    label_bold_font = ("Arial", 11, "bold")
    entry_font = ("Arial", 10)
    button_font = ("Arial", 9)
    small_button_font = ("Arial", 9)

    tab.grid_rowconfigure(0, weight=1)
    tab.grid_columnconfigure(0, weight=1)

    main_frame = tk.LabelFrame(
        tab,
        text="Zigbee2MQTT Wireless Siren Control",
        borderwidth=2,
        relief="solid"
    )
    main_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    for r in range(5):
        main_frame.grid_rowconfigure(r, weight=0)

    main_frame.grid_rowconfigure(3, weight=1)
    main_frame.grid_rowconfigure(4, weight=4)

    for c in range(4):
        main_frame.grid_columnconfigure(c, weight=1)

    status_frame = tk.LabelFrame(
        main_frame,
        text="Connection Status",
        borderwidth=1,
        relief="solid"
    )
    status_frame.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

    tk.Label(status_frame, text="Status:", font=label_bold_font).grid(
        row=0, column=0, sticky="w", padx=8, pady=4
    )

    app.zigbee_status_label = tk.Label(
        status_frame,
        textvariable=app.zigbee_status_var,
        font=label_font,
        fg="red"
    )
    app.zigbee_status_label.grid(row=0, column=1, sticky="w", padx=8, pady=4)

    mqtt_available = is_mqtt_available()
    mqtt_status = "Available" if mqtt_available else "Not Available (install paho-mqtt)"
    mqtt_color = "green" if mqtt_available else "red"

    tk.Label(status_frame, text="MQTT Library:", font=label_bold_font).grid(
        row=1, column=0, sticky="w", padx=8, pady=4
    )

    tk.Label(status_frame, text=mqtt_status, font=label_font, fg=mqtt_color).grid(
        row=1, column=1, sticky="w", padx=8, pady=4
    )

    tk.Label(status_frame, text="USB Dongle:", font=label_bold_font).grid(
        row=2, column=0, sticky="w", padx=8, pady=4
    )

    app.usb_dongle_status_label = tk.Label(
        status_frame,
        text="Checking...",
        font=label_font,
        fg="orange"
    )
    app.usb_dongle_status_label.grid(row=2, column=1, sticky="w", padx=8, pady=4)

    tk.Label(status_frame, text="Arduino Siren:", font=label_bold_font).grid(
        row=3, column=0, sticky="w", padx=8, pady=4
    )

    app.arduino_status_label = tk.Label(
        status_frame,
        text="Checking...",
        font=label_font,
        fg="orange"
    )
    app.arduino_status_label.grid(row=3, column=1, sticky="w", padx=8, pady=4)

    app.hardware_ports_label = tk.Label(
        status_frame,
        text=f"Hardware Ports: Arduino={app.arduino_port}  Zigbee={app.zigbee_port}",
        font=("Arial", 9),
        fg="blue"
    )
    app.hardware_ports_label.grid(
        row=4,
        column=0,
        columnspan=2,
        sticky="w",
        padx=8,
        pady=4
    )

    status_button_frame = tk.Frame(status_frame)
    status_button_frame.grid(
        row=0,
        column=2,
        rowspan=5,
        columnspan=2,
        sticky="n",
        padx=8,
        pady=4
    )
    status_button_frame.grid_columnconfigure(0, weight=1)

    app.toggle_connection_btn = tk.Button(
        status_button_frame,
        text="Connect",
        font=small_button_font,
        height=1,
        width=18,
        command=app.toggle_zigbee_connection
    )
    app.toggle_connection_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=2)

    app.test_btn = tk.Button(
        status_button_frame,
        text="Test Connection",
        font=small_button_font,
        height=1,
        width=18,
        command=app.test_zigbee_connection
    )
    app.test_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=2)

    app.retest_usb_btn = tk.Button(
        status_button_frame,
        text="Retest Hardware",
        font=small_button_font,
        height=1,
        width=18,
        command=lambda: app.update_usb_dongle_status(
            force_rescan=True
        )
    )
    app.retest_usb_btn.grid(row=2, column=0, sticky="ew", padx=5, pady=2)

    config_frame = tk.LabelFrame(
        main_frame,
        text="MQTT Configuration",
        borderwidth=1,
        relief="solid"
    )
    config_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

    app.config_widgets = {}
    config = app.zigbee_controller.config

    row = 0

    tk.Label(config_frame, text="MQTT Broker:", font=entry_font).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    app.config_widgets["mqtt_broker"] = tk.Entry(config_frame, font=entry_font)
    app.config_widgets["mqtt_broker"].insert(0, config["mqtt_broker"])
    app.config_widgets["mqtt_broker"].grid(row=row, column=1, sticky="ew", padx=5, pady=2)

    tk.Label(config_frame, text="Port:", font=entry_font).grid(
        row=row, column=2, sticky="w", padx=5, pady=2
    )
    app.config_widgets["mqtt_port"] = tk.Entry(config_frame, font=entry_font, width=8)
    app.config_widgets["mqtt_port"].insert(0, str(config["mqtt_port"]))
    app.config_widgets["mqtt_port"].grid(row=row, column=3, sticky="w", padx=5, pady=2)

    row += 1

    tk.Label(config_frame, text="Username:", font=entry_font).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    app.config_widgets["mqtt_username"] = tk.Entry(config_frame, font=entry_font)
    app.config_widgets["mqtt_username"].insert(0, config["mqtt_username"])
    app.config_widgets["mqtt_username"].grid(row=row, column=1, sticky="ew", padx=5, pady=2)

    tk.Label(config_frame, text="Password:", font=entry_font).grid(
        row=row, column=2, sticky="w", padx=5, pady=2
    )
    app.config_widgets["mqtt_password"] = tk.Entry(config_frame, font=entry_font, show="*")
    app.config_widgets["mqtt_password"].insert(0, config["mqtt_password"])
    app.config_widgets["mqtt_password"].grid(row=row, column=3, sticky="ew", padx=5, pady=2)

    row += 1

    tk.Label(config_frame, text="MQTT Topic:", font=entry_font).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )
    app.config_widgets["mqtt_topic"] = tk.Entry(config_frame, font=entry_font)
    app.config_widgets["mqtt_topic"].insert(0, config["mqtt_topic"])
    app.config_widgets["mqtt_topic"].grid(
        row=row,
        column=1,
        columnspan=3,
        sticky="ew",
        padx=5,
        pady=2
    )

    row += 1

    tk.Label(
        config_frame,
        text="Button Device Names (comma-separated):",
        font=entry_font
    ).grid(row=row, column=0, sticky="w", padx=5, pady=2)

    if "siren_button_devices" in config and isinstance(config["siren_button_devices"], list):
        device_value = ", ".join(config["siren_button_devices"])
    else:
        device_value = config.get("siren_button_device", "")

    app.config_widgets["siren_button_devices"] = tk.Entry(config_frame, font=entry_font)
    app.config_widgets["siren_button_devices"].insert(0, device_value)
    app.config_widgets["siren_button_devices"].grid(
        row=row,
        column=1,
        columnspan=3,
        sticky="ew",
        padx=5,
        pady=2
    )

    row += 1

    tk.Label(config_frame, text="Siren Device Name:", font=entry_font).grid(
        row=row, column=0, sticky="w", padx=5, pady=2
    )

    app.config_widgets["siren_device_name"] = tk.Entry(config_frame, font=entry_font)
    app.config_widgets["siren_device_name"].insert(
        0,
        config.get("siren_device_name", "zigbee_siren")
    )
    app.config_widgets["siren_device_name"].grid(
        row=row,
        column=1,
        columnspan=3,
        sticky="ew",
        padx=5,
        pady=2
    )

    config_frame.grid_columnconfigure(1, weight=1)
    config_frame.grid_columnconfigure(3, weight=1)

    button_row_frame = tk.Frame(main_frame)
    button_row_frame.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

    for c in range(4):
        button_row_frame.grid_columnconfigure(c, weight=1)

    save_config_btn = tk.Button(
        button_row_frame,
        text="Save Configuration",
        font=button_font,
        height=1,
        command=app.save_zigbee_config
    )
    save_config_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=4)

    open_frontend_btn = tk.Button(
        button_row_frame,
        text="Linux Open Zigbee2MQTT Frontend",
        font=button_font,
        height=1,
        command=lambda: webbrowser.open("http://localhost:8080")
    )
    open_frontend_btn.grid(row=0, column=1, sticky="ew", padx=5, pady=4)

    windows_frontend_btn = tk.Button(
        button_row_frame,
        text="Windows Open Zigbee2MQTT Frontend",
        font=button_font,
        height=1,
        command=lambda: webbrowser.open("http://localhost:8080")
    )
    windows_frontend_btn.grid(row=0, column=2, sticky="ew", padx=5, pady=4)

    test_siren_btn = tk.Button(
        button_row_frame,
        text="Test App Siren",
        font=button_font,
        height=1,
        command=app.test_app_siren
    )
    test_siren_btn.grid(row=0, column=3, sticky="ew", padx=5, pady=4)

    info_frame = tk.LabelFrame(
        main_frame,
        text="Setup Information",
        borderwidth=1,
        relief="solid"
    )
    info_frame.grid(row=3, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)

    info_frame.grid_rowconfigure(0, weight=1)
    info_frame.grid_columnconfigure(0, weight=1)

    info_scroll_frame = tk.Frame(info_frame)
    info_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    info_scroll_frame.grid_rowconfigure(0, weight=1)
    info_scroll_frame.grid_columnconfigure(0, weight=1)

    info_scrollbar = tk.Scrollbar(info_scroll_frame)
    info_scrollbar.grid(row=0, column=1, sticky="ns")

    info_text_widget = tk.Text(
        info_scroll_frame,
        height=5,
        font=("Arial", 9),
        wrap=tk.WORD,
        yscrollcommand=info_scrollbar.set
    )
    info_text_widget.grid(row=0, column=0, sticky="nsew")

    info_scrollbar.config(command=info_text_widget.yview)

    info_text_widget.insert(
        "1.0",
        """Zigbee Siren Setup

WINDOWS 11
1. Install Mosquitto MQTT Broker:
   https://mosquitto.org/download/

2. Install Zigbee2MQTT for Windows:
   https://www.zigbee2mqtt.io/guide/installation/05_windows.html

   This requires Node.js and a Zigbee2MQTT data/config folder.

3. Configure Zigbee2MQTT to use the detected Zigbee COM port.

4. Start Mosquitto MQTT Broker.

5. Start Zigbee2MQTT.

6. Use 'Windows Open Zigbee2MQTT Frontend' to open:
   http://localhost:8080

LINUX / RASPBERRY PI
1. Install Zigbee2MQTT as a service.
2. Install Mosquitto MQTT Broker.
3. Use 'Linux Open Zigbee2MQTT Frontend'.

Recommended PM2 commands:
sudo npm install -g pm2
pm2 start zigbee2mqtt --name zigbee2mqtt
pm2 save
pm2 startup

Python MQTT Library:
python3 -m venv ~/myenv
source ~/myenv/bin/activate
pip install paho-mqtt

Usage:
- Arduino Siren Button: press and hold to sound, release to stop.
- Test App Siren: tests local siren sound.
- Timer sirens use the same sound file and volume settings.
- Hardware ports are automatically detected and shown above.
"""
    )

    info_text_widget.config(state="disabled")

    log_frame = tk.LabelFrame(
        main_frame,
        text="Activity Log",
        borderwidth=1,
        relief="solid"
    )
    log_frame.grid(row=4, column=0, columnspan=4, sticky="nsew", padx=5, pady=5)

    log_frame.grid_rowconfigure(0, weight=1)
    log_frame.grid_columnconfigure(0, weight=1)

    log_scroll_frame = tk.Frame(log_frame)
    log_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    log_scroll_frame.grid_rowconfigure(0, weight=1)
    log_scroll_frame.grid_columnconfigure(0, weight=1)

    app.log_text = tk.Text(
        log_scroll_frame,
        height=10,
        font=("Courier", 9),
        wrap=tk.WORD,
        state=tk.DISABLED
    )

    log_scrollbar = tk.Scrollbar(
        log_scroll_frame,
        orient="vertical",
        command=app.log_text.yview
    )

    app.log_text.config(yscrollcommand=log_scrollbar.set)

    app.log_text.grid(row=0, column=0, sticky="nsew")
    log_scrollbar.grid(row=0, column=1, sticky="ns")

    clear_log_btn = tk.Button(
        log_frame,
        text="Clear Log",
        font=small_button_font,
        height=1,
        command=app.clear_zigbee_log
    )
    clear_log_btn.grid(row=1, column=0, pady=2)

    app.add_to_zigbee_log("Zigbee Siren tab initialized")

    if not is_mqtt_available():
        app.add_to_zigbee_log(
            "WARNING: paho-mqtt library not installed. "
            "Install with: pip install paho-mqtt"
        )
