"""Zigbee/MQTT tab, including editable, per-device siren action mappings.

This module constructs Tk widgets only. MQTT callbacks and local audio remain
in zigbee_siren.py and uwh.py, respectively.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

from zigbee_siren import (
    is_mqtt_available,
    legacy_action_mappings,
    normalize_action_mappings,
)


ACTION_NAMES = {
    "one_cycle": "One siren cycle",
    "two_cycles": "Two siren cycles",
    "start_continuous": "Start continuous siren",
    "stop_continuous": "Stop continuous siren",
    "ignore": "Ignore",
}
ACTION_IDS = {name: key for key, name in ACTION_NAMES.items()}


def _safety_text(action_id):
    return {
        "one_cycle": "Timed stop",
        "two_cycles": "Two timed stops",
        "start_continuous": "Max timer + MQTT stop",
        "stop_continuous": "Ignore late/wrong release",
        "ignore": "No sound",
    }.get(action_id, "No sound")


def _friendly_names(app):
    # Use the field currently displayed, not a stale default in settings.json.
    widget = app.config_widgets.get("siren_button_devices")
    value = widget.get() if widget is not None else ""
    return [name.strip() for name in value.split(",") if name.strip()]


def _mark_mappings_dirty(app):
    app._zigbee_map_dirty = True
    app._zigbee_mapping_save_btn.config(text="Save Action Mappings *")


def _draw_action_mappings(app, selected=None):
    tree = app.zigbee_mapping_tree
    current = selected
    if current is None:
        picked = tree.selection()
        if picked:
            try:
                current = int(picked[0])
            except (ValueError, TypeError):
                pass
    for item in tree.get_children():
        tree.delete(item)
    for index, row in enumerate(app._zigbee_action_mappings_draft):
        tree.insert("", tk.END, iid=str(index), values=(
            row["device"], row["action"],
            ACTION_NAMES[row["uwh_action"]],
            _safety_text(row["uwh_action"]), row.get("notes", ""),
        ))
    if current is not None and 0 <= current < len(app._zigbee_action_mappings_draft):
        tree.selection_set(str(current))
        tree.focus(str(current))
        tree.see(str(current))
    app._zigbee_mapping_count.config(
        text=f"{len(app._zigbee_action_mappings_draft)} saved/draft mappings"
    )


def _selected_mapping_index(app):
    selected = app.zigbee_mapping_tree.selection()
    if not selected:
        messagebox.showinfo("Action Mapping", "Select a mapping row first.", parent=app.master)
        return None
    return int(selected[0])


def _edit_mapping_dialog(app, index=None):
    existing = (app._zigbee_action_mappings_draft[index]
                if index is not None else {})
    dialog = tk.Toplevel(app.master)
    # Hide the window until its position has been calculated: otherwise Tk may
    # briefly place it at the top-left of a different monitor.
    dialog.withdraw()
    dialog.title("Edit Button Action Mapping" if existing else "Add Button Action Mapping")
    dialog.resizable(False, False)
    dialog.transient(app.master)

    body = ttk.Frame(dialog, padding=14)
    body.pack(fill="both", expand=True)
    body.columnconfigure(1, weight=1)

    ttk.Label(body, text="Device name:").grid(row=0, column=0, sticky="w", pady=5)
    device_var = tk.StringVar(value=existing.get("device", ""))
    devices = _friendly_names(app)
    ttk.Combobox(body, textvariable=device_var, values=devices, width=32).grid(
        row=0, column=1, sticky="ew", padx=(12, 0), pady=5
    )

    ttk.Label(body, text="Received action:").grid(row=1, column=0, sticky="w", pady=5)
    action_var = tk.StringVar(value=existing.get("action", ""))
    ttk.Entry(body, textvariable=action_var, width=35).grid(
        row=1, column=1, sticky="ew", padx=(12, 0), pady=5
    )

    ttk.Label(body, text="UWH action:").grid(row=2, column=0, sticky="w", pady=5)
    choice_var = tk.StringVar(value=ACTION_NAMES.get(
        existing.get("uwh_action", "ignore"), "Ignore"
    ))
    ttk.Combobox(body, textvariable=choice_var, state="readonly",
                 values=list(ACTION_NAMES.values()), width=32).grid(
        row=2, column=1, sticky="ew", padx=(12, 0), pady=5
    )

    ttk.Label(body, text="Notes (optional):").grid(row=3, column=0, sticky="w", pady=5)
    notes_var = tk.StringVar(value=existing.get("notes", ""))
    ttk.Entry(body, textvariable=notes_var, width=35).grid(
        row=3, column=1, sticky="ew", padx=(12, 0), pady=5
    )

    ttk.Label(body, text=(
        "Continuous sirens stop on release, MQTT disconnect, or the local "
        "maximum-duration timer. A missed release cannot sound indefinitely."
    ), wraplength=480, foreground="#795300").grid(
        row=4, column=0, columnspan=2, sticky="w", pady=(8, 12)
    )

    def apply_edit():
        device = device_var.get().strip()
        received = action_var.get().strip().lower()
        action_id = ACTION_IDS.get(choice_var.get())
        if device not in _friendly_names(app):
            messagebox.showerror(
                "Unknown button", "The device must appear in Button Device Names. "
                "Add it there and save the MQTT configuration first.", parent=dialog
            )
            return
        if not received or len(received) > 128:
            messagebox.showerror(
                "Invalid action", "Enter a received action (up to 128 characters).",
                parent=dialog
            )
            return
        if action_id is None:
            return
        for row_idx, row in enumerate(app._zigbee_action_mappings_draft):
            if row_idx != index and row["device"] == device and row["action"] == received:
                messagebox.showerror("Duplicate mapping", (
                    f"A mapping for '{device}' / '{received}' already exists. "
                    "Edit that row instead."
                ), parent=dialog)
                return
        result = {"device": device, "action": received,
                  "uwh_action": action_id, "notes": notes_var.get()[:200]}
        if index is None:
            app._zigbee_action_mappings_draft.append(result)
            target = len(app._zigbee_action_mappings_draft) - 1
        else:
            app._zigbee_action_mappings_draft[index] = result
            target = index
        _draw_action_mappings(app, selected=target)
        _mark_mappings_dirty(app)
        dialog.destroy()

    buttons = ttk.Frame(body)
    buttons.grid(row=5, column=0, columnspan=2, sticky="e")
    ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(
        side="right", padx=(8, 0)
    )
    ttk.Button(buttons, text="Apply", command=apply_edit).pack(side="right")
    dialog.bind("<Escape>", lambda _event: dialog.destroy())

    # Both Add and Edit appear immediately ABOVE the corresponding toolbar
    # button. Screen coordinates come from the button itself, so moving the
    # main window to a different monitor also moves these popups correctly.
    anchor = (app._zigbee_mapping_add_btn if index is None
              else app._zigbee_mapping_edit_btn)
    dialog.update_idletasks()
    anchor.update_idletasks()
    width = dialog.winfo_reqwidth()
    height = dialog.winfo_reqheight()
    gap = 10
    popup_x = anchor.winfo_rootx() + (anchor.winfo_width() - width) // 2
    popup_y = anchor.winfo_rooty() - height - gap

    # Keep the dialog horizontally within the app window. Do not clamp
    # against the primary monitor: secondary monitors may use negative or
    # larger-than-primary desktop coordinates.
    main_x = app.master.winfo_rootx()
    main_y = app.master.winfo_rooty()
    main_width = app.master.winfo_width()
    popup_x = max(main_x + 10, min(popup_x, main_x + main_width - width - 10))
    popup_y = max(main_y + 10, popup_y)
    dialog.geometry(f"+{popup_x}+{popup_y}")
    dialog.deiconify()
    dialog.wait_visibility()
    dialog.lift()
    dialog.grab_set()
    dialog.focus_force()


def _delete_mapping(app):
    index = _selected_mapping_index(app)
    if index is None:
        return
    row = app._zigbee_action_mappings_draft[index]
    if not messagebox.askyesno("Delete Mapping", (
        f"Delete mapping for '{row['device']}' / '{row['action']}'?\n\n"
        "This action will be ignored until mapped again."
    ), parent=app.master):
        return
    del app._zigbee_action_mappings_draft[index]
    _draw_action_mappings(app)
    _mark_mappings_dirty(app)


def _auto_add_from_log(app):
    """Import only actually observed, unknown actions; they start at Ignore."""
    found = app.zigbee_controller.consume_unmapped_actions()
    existing = {(row["device"], row["action"])
                for row in app._zigbee_action_mappings_draft}
    added = 0
    for device, action in found:
        if device not in _friendly_names(app) or (device, action) in existing:
            continue
        app._zigbee_action_mappings_draft.append({
            "device": device, "action": action,
            "uwh_action": "ignore", "notes": "Discovered from MQTT log",
        })
        existing.add((device, action))
        added += 1
    if added:
        _draw_action_mappings(app)
        _mark_mappings_dirty(app)
        app.add_to_zigbee_log(
            f"Auto-add: added {added} observed action(s) as Ignore; "
            "edit and save them to enable sound."
        )
    else:
        messagebox.showinfo("Auto-add From Log", (
            "No new unmapped actions have been received from configured buttons. "
            "Press a button first, then try again."
        ), parent=app.master)


def save_action_mappings(app):
    """Save mappings in unified settings.json without modifying other sections."""
    mappings = normalize_action_mappings(app._zigbee_action_mappings_draft)
    if len(mappings) != len(app._zigbee_action_mappings_draft):
        messagebox.showerror("Invalid mappings", (
            "Mapping rows contain duplicates or invalid values. Correct them before saving."
        ), parent=app.master)
        return
    try:
        settings = app.load_unified_settings()
        settings.setdefault("zigbeeSettings", {})["action_mappings"] = mappings
        app.save_unified_settings(settings)
        # Replace atomically for the MQTT worker; never expose half-edited rows.
        app.zigbee_controller.config["action_mappings"] = mappings
    except Exception as error:
        messagebox.showerror("Save Action Mappings", str(error), parent=app.master)
        app.add_to_zigbee_log(f"Error saving action mappings: {error}")
        return
    app._zigbee_map_dirty = False
    app._zigbee_mapping_save_btn.config(text="Save Action Mappings")
    app.add_to_zigbee_log(f"Saved {len(mappings)} button action mapping(s) in settings.json")
    messagebox.showinfo("Saved", "Button action mappings saved.", parent=app.master)


def _create_mapping_table(app, config_frame, config):
    mapping = tk.LabelFrame(config_frame, text="Button Action Mapping", bd=1,
                            relief="solid", padx=7, pady=7)
    mapping.grid(row=7, column=0, columnspan=4, sticky="nsew",
                 padx=5, pady=(4, 6))
    mapping.columnconfigure(0, weight=1)
    mapping.rowconfigure(2, weight=1)

    ttk.Label(mapping, text=(
        "Match each device and incoming action to a UWH action. "
        "Unrecognised actions are logged and ignored."
    )).grid(row=0, column=0, sticky="w", pady=(0, 4))

    ttk.Label(mapping, foreground="#795300", text=(
        "Continuous mode: bounded local timer + audio cutoff; "
        "stop on MQTT disconnect; duplicates/late releases ignored."
    )).grid(row=1, column=0, sticky="w", pady=(0, 5))

    frame = ttk.Frame(mapping)
    frame.grid(row=2, column=0, sticky="nsew")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    columns = ("device", "action", "uwh_action", "failsafe", "notes")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=13,
                        selectmode="browse")
    app.zigbee_mapping_tree = tree
    for key, caption, width, anchor in (
        ("device", "Device name", 165, "w"),
        ("action", "Received action", 150, "w"),
        ("uwh_action", "UWH action", 200, "w"),
        ("failsafe", "Failsafe / safety", 230, "w"),
        ("notes", "Notes", 210, "w"),
    ):
        tree.heading(key, text=caption)
        tree.column(key, width=width, minwidth=85, anchor=anchor, stretch=True)
    tree.grid(row=0, column=0, sticky="nsew")
    vert = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    horiz = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vert.set, xscrollcommand=horiz.set)
    vert.grid(row=0, column=1, sticky="ns")
    horiz.grid(row=1, column=0, sticky="ew")

    toolbar = ttk.Frame(mapping)
    toolbar.grid(row=3, column=0, sticky="ew", pady=(8, 0))
    for c in range(5):
        toolbar.columnconfigure(c, weight=1)
    buttons = (
        ("Add Mapping", lambda: _edit_mapping_dialog(app)),
        ("Edit Mapping", lambda: (
            _edit_mapping_dialog(app, index) if (
                index := _selected_mapping_index(app)) is not None else None
        )),
        ("Delete Mapping", lambda: _delete_mapping(app)),
        ("Auto-add From Log", lambda: _auto_add_from_log(app)),
        ("Save Action Mappings", lambda: save_action_mappings(app)),
    )
    for col, (label, command) in enumerate(buttons):
        button = ttk.Button(toolbar, text=label, command=command)
        button.grid(row=0, column=col, sticky="ew", padx=3)
        if label == "Add Mapping":
            app._zigbee_mapping_add_btn = button
        elif label == "Edit Mapping":
            app._zigbee_mapping_edit_btn = button
        elif label == "Save Action Mappings":
            app._zigbee_mapping_save_btn = button

    app._zigbee_mapping_count = ttk.Label(mapping, foreground="#666666")
    app._zigbee_mapping_count.grid(row=4, column=0, sticky="w", pady=(5, 0))
    devices = config.get("siren_button_devices", [])
    if not isinstance(devices, list):
        devices = [devices]
    app._zigbee_action_mappings_draft = normalize_action_mappings(
        config.get("action_mappings", legacy_action_mappings(devices))
    )
    app._zigbee_map_dirty = False
    _draw_action_mappings(app)
    tree.bind("<Double-1>", lambda _event: (
        _edit_mapping_dialog(app, int(tree.selection()[0]))
        if tree.selection() else None
    ))


def create_zigbee_siren_tab(app):
    """Create the live Zigbee tab, using the approved 62/38 split layout."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Zigbee Siren")
    tab.columnconfigure(0, weight=1)
    tab.rowconfigure(0, weight=1)

    outer = tk.LabelFrame(tab, text="Zigbee2MQTT Wireless Siren Control",
                          bd=2, relief="solid", padx=5, pady=5)
    outer.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
    outer.columnconfigure(0, weight=62, uniform="zigbee_split")
    outer.columnconfigure(1, weight=38, uniform="zigbee_split")
    outer.rowconfigure(0, weight=1)

    left = ttk.Frame(outer)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
    left.columnconfigure(0, weight=1)
    left.rowconfigure(0, weight=0)
    left.rowconfigure(1, weight=1)

    # Status is shallow and as wide as MQTT Configuration below it.
    status = tk.LabelFrame(left, text="Connection Status", bd=1, relief="solid",
                           padx=7, pady=7)
    status.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    status.columnconfigure(0, weight=0)
    status.columnconfigure(1, weight=1)
    status.columnconfigure(2, weight=0)
    status.configure(height=205)
    status.grid_propagate(False)

    for idx, (caption, text, var, color) in enumerate((
        ("Status:", None, app.zigbee_status_var, "red"),
        ("MQTT Library:",
         "Available" if is_mqtt_available() else "Not Available (install paho-mqtt)",
         None, "green" if is_mqtt_available() else "red"),
        ("USB Dongle:", "Checking...", None, "orange"),
        ("Arduino Siren:", "Checking...", None, "orange"),
    )):
        tk.Label(status, text=caption, font=("Arial", 10, "bold")).grid(
            row=idx, column=0, sticky="w", padx=7, pady=4
        )
        textlabel = tk.Label(status, text=text or "", textvariable=var,
                             font=("Arial", 10), fg=color)
        textlabel.grid(row=idx, column=1, sticky="w", padx=7, pady=4)
        if idx == 0:
            app.zigbee_status_label = textlabel
        elif idx == 2:
            app.usb_dongle_status_label = textlabel
        elif idx == 3:
            app.arduino_status_label = textlabel

    controls = ttk.Frame(status)
    controls.grid(row=0, column=2, rowspan=4, sticky="ne", padx=12, pady=0)
    app.toggle_connection_btn = tk.Button(
        controls, text="Connect", width=18, command=app.toggle_zigbee_connection
    )
    app.toggle_connection_btn.grid(row=0, column=0, sticky="ew", pady=2)
    app.test_btn = tk.Button(
        controls, text="Test Connection", width=18, command=app.test_zigbee_connection
    )
    app.test_btn.grid(row=1, column=0, sticky="ew", pady=2)
    app.retest_usb_btn = tk.Button(
        controls, text="Retest Hardware", width=18,
        command=lambda: app.update_usb_dongle_status(force_rescan=True),
    )
    app.retest_usb_btn.grid(row=2, column=0, sticky="ew", pady=2)
    app.hardware_ports_label = tk.Label(
        status, text=f"Hardware Ports: Arduino={app.arduino_port}  "
                     f"Zigbee={app.zigbee_port}",
        font=("Arial", 9), fg="blue",
    )
    app.hardware_ports_label.grid(
        row=4, column=0, columnspan=3, sticky="w", padx=7, pady=(8, 2)
    )

    config_frame = tk.LabelFrame(left, text="MQTT Configuration", bd=1,
                                 relief="solid", padx=7, pady=7)
    config_frame.grid(row=1, column=0, sticky="nsew")
    config_frame.columnconfigure(0, weight=0)
    config_frame.columnconfigure(1, weight=3)
    config_frame.columnconfigure(2, weight=0)
    config_frame.columnconfigure(3, weight=1)
    config_frame.rowconfigure(7, weight=1)
    app.config_widgets = {}
    config = app.zigbee_controller.config

    def add_entry(row, label, key, value, span=1, width=24, show=None):
        ttk.Label(config_frame, text=label).grid(
            row=row, column=0, sticky="w", padx=(5, 10), pady=4
        )
        entry = ttk.Entry(config_frame, width=width, show=show)
        entry.insert(0, str(value))
        entry.grid(row=row, column=1, columnspan=span, sticky="ew",
                   padx=(0, 8) if span == 1 else (0, 5), pady=4)
        app.config_widgets[key] = entry
        return entry

    add_entry(0, "MQTT Broker:", "mqtt_broker", config.get("mqtt_broker", "localhost"))
    ttk.Label(config_frame, text="Port:").grid(
        row=0, column=2, sticky="w", padx=(4, 8)
    )
    port = ttk.Entry(config_frame, width=8)
    port.insert(0, str(config.get("mqtt_port", 1883)))
    port.grid(row=0, column=3, sticky="ew", padx=(0, 5), pady=4)
    app.config_widgets["mqtt_port"] = port

    add_entry(1, "Username:", "mqtt_username", config.get("mqtt_username", ""))
    ttk.Label(config_frame, text="Password:").grid(
        row=1, column=2, sticky="w", padx=(4, 8)
    )
    password = ttk.Entry(config_frame, show="*")
    password.insert(0, config.get("mqtt_password", ""))
    password.grid(row=1, column=3, sticky="ew", padx=(0, 5), pady=4)
    app.config_widgets["mqtt_password"] = password

    add_entry(2, "MQTT Topic:", "mqtt_topic", config.get("mqtt_topic", "zigbee2mqtt/+"), span=3)
    devices = config.get("siren_button_devices", [])
    devices_value = ", ".join(devices) if isinstance(devices, list) else str(devices)
    add_entry(3, "Button Device Names (comma-separated):",
              "siren_button_devices", devices_value, span=3)
    add_entry(4, "Siren Device Name:", "siren_device_name",
              config.get("siren_device_name", "zigbee_siren"))
    ttk.Label(config_frame, text="Maximum hold (s):").grid(
        row=4, column=2, sticky="w", padx=(4, 8)
    )
    max_duration = ttk.Entry(config_frame, width=8)
    max_duration.insert(0, str(config.get("continuous_siren_max_seconds", 10)))
    max_duration.grid(row=4, column=3, sticky="ew", padx=(0, 5), pady=4)
    app.config_widgets["continuous_siren_max_seconds"] = max_duration

    ttk.Label(
        config_frame,
        text="Siren Device Name is an optional MQTT output, not one of the input buttons.",
        foreground="#626262",
    ).grid(row=5, column=0, columnspan=4, sticky="w", padx=5, pady=(1, 0))

    actionbar = ttk.Frame(config_frame)
    actionbar.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(7, 9))
    for c in range(3):
        actionbar.columnconfigure(c, weight=1)
    for i, (name, callback) in enumerate((
        ("Save Configuration", app.save_zigbee_config),
        ("Open Zigbee2MQTT Frontend", lambda: webbrowser.open("http://localhost:8080")),
        ("Test App Siren", app.test_app_siren),
    )):
        ttk.Button(actionbar, text=name, command=callback).grid(
            row=0, column=i, sticky="ew", padx=3
        )

    _create_mapping_table(app, config_frame, config)

    # One frontend shortcut works on both Windows and Linux. It opens the
    # browser on THIS computer, so a remote Zigbee2MQTT host needs its LAN URL.
    # A tall, scrollable log fills the full right-hand column.
    log_frame = tk.LabelFrame(outer, text="Activity Log", bd=1,
                              relief="solid", padx=7, pady=7)
    log_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(0, weight=1)
    app.log_text = tk.Text(log_frame, font=("Courier New", 9),
                           wrap=tk.WORD, state=tk.DISABLED)
    app.log_text.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(log_frame, orient="vertical",
                              command=app.log_text.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    app.log_text.config(yscrollcommand=scrollbar.set)
    ttk.Button(log_frame, text="Clear Log", command=app.clear_zigbee_log).grid(
        row=1, column=0, columnspan=2, pady=6
    )

    app.add_to_zigbee_log("Zigbee Siren tab initialized")
    if not is_mqtt_available():
        app.add_to_zigbee_log(
            "WARNING: paho-mqtt library not installed. Install with: pip install paho-mqtt"
        )
    return tab
