"""Zigbee/MQTT tab and the editable, per-device siren action table.

The device-name list is the first allow-list; action mappings are a second,
explicit per-device allow-list. Auto-add From Log creates safe Ignore entries,
which the operator must deliberately edit and save. This module constructs
Tk widgets only: network callbacks belong in zigbee_siren.py and local audio
and queued events belong in uwh.py.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

import ui_theme

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
    if hasattr(app, "refresh_zigbee_device_list"):
        app.refresh_zigbee_device_list()


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


def _create_mapping_table(app, parent, config):
    """Create the compact, scrollable mapping table and operator actions."""
    mapping = ui_theme.card(parent, padding=10)
    mapping.grid_columnconfigure(0, weight=1)
    mapping.grid_rowconfigure(2, weight=1)

    # Keep the section title and actions in one compact header row.  The
    # buttons must be children of this toolbar; placing them directly in the
    # mapping card makes column 0 expand into a giant Add Mapping button and
    # covers the section title.
    mapping_header = tk.Frame(
        mapping,
        bg=ui_theme.COLORS["surface"],
    )
    mapping_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
    mapping_header.grid_columnconfigure(0, weight=1)

    ui_theme.section_title(
        mapping_header,
        "Button Action Mapping",
    ).grid(row=0, column=0, sticky="w")

    toolbar = tk.Frame(
        mapping_header,
        bg=ui_theme.COLORS["surface"],
    )
    toolbar.grid(row=0, column=1, sticky="e")

    buttons = (
        ("Add Mapping", lambda: _edit_mapping_dialog(app)),
        ("Edit Mapping", lambda: (
            _edit_mapping_dialog(app, index)
            if (index := _selected_mapping_index(app)) is not None
            else None
        )),
        ("Delete Mapping", lambda: _delete_mapping(app)),
        ("Auto-add From Log", lambda: _auto_add_from_log(app)),
        ("Save Action Mappings", lambda: save_action_mappings(app)),
    )

    for column, (label, command) in enumerate(buttons):
        if label == "Save Action Mappings":
            button = ui_theme.primary_button(toolbar, label, command)
        elif label == "Delete Mapping":
            button = ui_theme.danger_button(toolbar, label, command)
        else:
            button = ui_theme.secondary_button(toolbar, label, command)
        button.grid(row=0, column=column, padx=3)
        if label == "Add Mapping":
            app._zigbee_mapping_add_btn = button
        elif label == "Edit Mapping":
            app._zigbee_mapping_edit_btn = button
        elif label == "Save Action Mappings":
            app._zigbee_mapping_save_btn = button

    mapping_info = tk.Frame(
        mapping,
        bg=ui_theme.COLORS["surface"],
    )
    mapping_info.grid(row=1, column=0, sticky="ew", pady=(0, 6))
    mapping_info.grid_columnconfigure(0, weight=1)

    ui_theme.muted_label(
        mapping_info,
        "Match each configured device/action to a UWH siren action. "
        "Unrecognised actions are logged and ignored.",
        wraplength=760,
        justify="left",
    ).grid(row=0, column=0, sticky="w")

    app._zigbee_mapping_count = ui_theme.muted_label(mapping_info)
    app._zigbee_mapping_count.grid(
        row=0, column=1, sticky="e", padx=(12, 0)
    )

    frame = ttk.Frame(mapping, style="UWH.Surface.TFrame")
    frame.grid(row=2, column=0, sticky="nsew")
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    columns = ("device", "action", "uwh_action", "failsafe", "notes")
    tree = ttk.Treeview(
        frame,
        columns=columns,
        show="headings",
        height=4,
        selectmode="browse",
        style="UWH.Treeview",
    )
    app.zigbee_mapping_tree = tree
    for key, caption, width, anchor in (
        ("device", "Device name", 160, "w"),
        ("action", "Received action", 145, "w"),
        ("uwh_action", "UWH action", 190, "w"),
        ("failsafe", "Failsafe / safety", 220, "w"),
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

    devices = config.get("siren_button_devices", [])
    if not isinstance(devices, list):
        devices = [devices]
    app._zigbee_action_mappings_draft = normalize_action_mappings(
        config.get("action_mappings", legacy_action_mappings(devices))
    )
    app._zigbee_map_dirty = False
    _draw_action_mappings(app)
    tree.bind(
        "<Double-1>",
        lambda _event: (
            _edit_mapping_dialog(app, int(tree.selection()[0]))
            if tree.selection()
            else None
        ),
    )
    return mapping

def create_zigbee_siren_tab(app):
    """Create the approved v1.3 Zigbee/Arduino siren control dashboard."""
    tab = ttk.Frame(app.notebook, style="UWH.Tab.TFrame")
    app.notebook.add(
        tab,
        text=ui_theme.tab_label("Zigbee Siren"),
    )
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(2, weight=1)
    tab.grid_rowconfigure(3, weight=0)

    header = ui_theme.page_header(
        tab,
        "Zigbee and Arduino Siren Control",
        "Manage Zigbee buttons, MQTT mappings and the Arduino siren hardware.",
        symbol="⌁",
    )
    header.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=12,
        pady=(12, 6),
    )

    config = app.zigbee_controller.config
    app.config_widgets = {}

    # Top toolbar keeps the three high-frequency actions permanently visible.
    toolbar = ui_theme.card(tab, padding=10)
    toolbar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
    toolbar.grid_columnconfigure(3, weight=1)

    ui_theme.primary_button(
        toolbar, "Save Configuration", app.save_zigbee_config
    ).grid(row=0, column=0, padx=(0, 8))
    ui_theme.secondary_button(
        toolbar,
        "Open Zigbee2MQTT Frontend",
        lambda: webbrowser.open("http://localhost:8080"),
    ).grid(row=0, column=1, padx=(0, 8))
    ui_theme.secondary_button(
        toolbar, "Test App Siren", app.test_app_siren
    ).grid(row=0, column=2, padx=(0, 12))

    status_strip = tk.Frame(
        toolbar,
        bg=ui_theme.COLORS["primary_soft"],
        highlightbackground=ui_theme.COLORS["border"],
        highlightthickness=1,
        padx=10,
        pady=6,
    )
    status_strip.grid(row=0, column=3, sticky="ew")
    status_strip.grid_columnconfigure(1, weight=1)
    tk.Label(
        status_strip,
        text="MQTT",
        bg=ui_theme.COLORS["primary_soft"],
        fg=ui_theme.COLORS["muted"],
        font=ui_theme.SMALL_FONT,
    ).grid(row=0, column=0, sticky="w", padx=(0, 8))
    app.zigbee_status_label = tk.Label(
        status_strip,
        textvariable=app.zigbee_status_var,
        bg=ui_theme.COLORS["primary_soft"],
        fg=ui_theme.COLORS["danger"],
        font=(ui_theme.FONT_FAMILY, 10, "bold"),
        anchor="w",
    )
    app.zigbee_status_label.grid(row=0, column=1, sticky="w")

    body = ttk.Frame(tab, style="UWH.Tab.TFrame")
    body.grid(row=2, column=0, sticky="nsew", padx=12, pady=6)
    body.grid_columnconfigure(0, weight=5)
    body.grid_columnconfigure(1, weight=7)
    body.grid_rowconfigure(0, weight=1)

    left = ttk.Frame(body, style="UWH.Tab.TFrame")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    left.grid_columnconfigure(0, weight=1)

    right = ttk.Frame(body, style="UWH.Tab.TFrame")
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    right.grid_columnconfigure(0, weight=1)
    right.grid_rowconfigure(1, weight=1)

    # Connections and physical-port detection.
    connections = ui_theme.card(left, padding=12)
    connections.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    connections.grid_columnconfigure(1, weight=1)
    ui_theme.section_title(
        connections,
        "Connections",
        symbol="●",
    ).grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
    )

    ui_theme.body_label(connections, "Zigbee Dongle").grid(
        row=1, column=0, sticky="w", pady=5
    )
    app.usb_dongle_status_label = tk.Label(
        connections,
        text="Checking...",
        bg=ui_theme.COLORS["surface"],
        fg=ui_theme.COLORS["warn"],
        font=ui_theme.BODY_FONT,
        anchor="w",
    )
    app.usb_dongle_status_label.grid(row=1, column=1, sticky="w", padx=8)

    ui_theme.body_label(connections, "Arduino Port").grid(
        row=2, column=0, sticky="w", pady=5
    )
    app.arduino_status_label = tk.Label(
        connections,
        text="Checking...",
        bg=ui_theme.COLORS["surface"],
        fg=ui_theme.COLORS["warn"],
        font=ui_theme.BODY_FONT,
        anchor="w",
    )
    app.arduino_status_label.grid(row=2, column=1, sticky="w", padx=8)

    # Retained for hardware_detection's compact summary update.
    app.hardware_ports_label = ui_theme.muted_label(
        connections,
        f"Hardware Ports: Arduino={app.arduino_port or 'Not detected'}  "
        f"Zigbee={app.zigbee_port or 'Not detected'}",
    )
    app.hardware_ports_label.grid(
        row=3, column=0, columnspan=3, sticky="w", pady=(4, 8)
    )

    connection_actions = tk.Frame(
        connections, bg=ui_theme.COLORS["surface"]
    )
    connection_actions.grid(
        row=4, column=0, columnspan=3, sticky="ew", pady=(4, 0)
    )
    connection_actions.grid_columnconfigure(0, weight=1)
    connection_actions.grid_columnconfigure(1, weight=1)

    def connect_or_refresh():
        app.update_usb_dongle_status(force_rescan=True)
        if app.zigbee_controller.connected:
            app.test_zigbee_connection()
        else:
            app.start_zigbee_connection()

    app.toggle_connection_btn = ui_theme.primary_button(
        connection_actions, "Connect / Refresh", connect_or_refresh
    )
    app.toggle_connection_btn.grid(
        row=0, column=0, sticky="ew", padx=(0, 4), pady=3
    )
    app.test_btn = ui_theme.secondary_button(
        connection_actions, "Test Connection", app.test_zigbee_connection
    )
    app.test_btn.grid(
        row=0, column=1, sticky="ew", padx=(4, 0), pady=3
    )
    app.retest_usb_btn = ui_theme.secondary_button(
        connection_actions,
        "Retest Hardware",
        lambda: app.update_usb_dongle_status(force_rescan=True),
    )
    app.retest_usb_btn.grid(
        row=1, column=0, columnspan=2, sticky="ew", pady=3
    )

    ui_theme.info_banner(
        connections,
        "A remembered Arduino COM port is not treated as connected. If the "
        "Arduino is unplugged, hardware detection reports Not detected in red."
    ).grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 0))

    # Full MQTT configuration is retained: the visual redesign does not
    # remove any existing operator configuration fields.
    config_card = ui_theme.card(left, padding=12)
    config_card.grid(row=1, column=0, sticky="nsew")
    config_card.grid_columnconfigure(1, weight=1)
    config_card.grid_columnconfigure(3, weight=1)
    ui_theme.section_title(
        config_card,
        "MQTT Configuration",
        symbol="⚙",
    ).grid(
        row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
    )

    def add_entry(row, label, key, value, span=1, width=24, show=None):
        ui_theme.body_label(config_card, label).grid(
            row=row, column=0, sticky="w", padx=(0, 8), pady=3
        )
        entry = ttk.Entry(
            config_card,
            width=width,
            show=show,
            style="UWH.TEntry",
        )
        entry.insert(0, str(value))
        entry.grid(
            row=row,
            column=1,
            columnspan=span,
            sticky="ew",
            padx=(0, 8),
            pady=3,
        )
        app.config_widgets[key] = entry
        return entry

    add_entry(1, "MQTT Broker", "mqtt_broker",
              config.get("mqtt_broker", "localhost"))
    ui_theme.body_label(config_card, "Port").grid(
        row=1, column=2, sticky="w", padx=(8, 6)
    )
    port = ttk.Entry(config_card, width=8, style="UWH.TEntry")
    port.insert(0, str(config.get("mqtt_port", 1883)))
    port.grid(row=1, column=3, sticky="ew", pady=3)
    app.config_widgets["mqtt_port"] = port

    add_entry(2, "Username", "mqtt_username",
              config.get("mqtt_username", ""))
    ui_theme.body_label(config_card, "Password").grid(
        row=2, column=2, sticky="w", padx=(8, 6)
    )
    password = ttk.Entry(config_card, show="*", style="UWH.TEntry")
    password.insert(0, config.get("mqtt_password", ""))
    password.grid(row=2, column=3, sticky="ew", pady=3)
    app.config_widgets["mqtt_password"] = password

    add_entry(3, "MQTT Topic", "mqtt_topic",
              config.get("mqtt_topic", "zigbee2mqtt/+"), span=3)
    devices = config.get("siren_button_devices", [])
    devices_value = ", ".join(devices) if isinstance(devices, list) else str(devices)
    add_entry(
        4,
        "Button Device Names",
        "siren_button_devices",
        devices_value,
        span=3,
    )
    add_entry(
        5,
        "Siren Device Name",
        "siren_device_name",
        config.get("siren_device_name", "zigbee_siren"),
    )
    ui_theme.body_label(config_card, "Maximum hold (s)").grid(
        row=5, column=2, sticky="w", padx=(8, 6)
    )
    max_duration = ttk.Entry(config_card, width=8, style="UWH.TEntry")
    max_duration.insert(
        0, str(config.get("continuous_siren_max_seconds", 10))
    )
    max_duration.grid(row=5, column=3, sticky="ew", pady=3)
    app.config_widgets["continuous_siren_max_seconds"] = max_duration

    ui_theme.muted_label(
        config_card,
        "Siren Device Name is optional MQTT output; it is not one of the "
        "input referee buttons.",
        wraplength=480,
        justify="left",
    ).grid(row=6, column=0, columnspan=4, sticky="w", pady=(6, 0))

    # Four visible configured devices, scrollable when more are present.
    devices_card = ui_theme.card(right, padding=10)
    devices_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    devices_card.grid_columnconfigure(0, weight=1)

    device_header = tk.Frame(devices_card, bg=ui_theme.COLORS["surface"])
    device_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
    device_header.grid_columnconfigure(0, weight=1)
    ui_theme.section_title(
        device_header,
        "Configured Devices",
        symbol="▤",
    ).grid(
        row=0, column=0, sticky="w"
    )

    device_tree_frame = ttk.Frame(
        devices_card, style="UWH.Surface.TFrame"
    )
    device_tree_frame.grid(row=1, column=0, sticky="ew")
    device_tree_frame.grid_columnconfigure(0, weight=1)

    app.zigbee_device_tree = ttk.Treeview(
        device_tree_frame,
        columns=("name", "mappings"),
        show="headings",
        height=4,
        style="UWH.Treeview",
    )
    app.zigbee_device_tree.heading("name", text="Friendly Name")
    app.zigbee_device_tree.heading("mappings", text="Action mappings")
    app.zigbee_device_tree.column("name", width=260, anchor="w")
    app.zigbee_device_tree.column("mappings", width=120, anchor="center")
    app.zigbee_device_tree.grid(row=0, column=0, sticky="ew")
    device_scroll = ttk.Scrollbar(
        device_tree_frame,
        orient="vertical",
        command=app.zigbee_device_tree.yview,
    )
    device_scroll.grid(row=0, column=1, sticky="ns")
    app.zigbee_device_tree.configure(yscrollcommand=device_scroll.set)

    def refresh_devices():
        for item in app.zigbee_device_tree.get_children():
            app.zigbee_device_tree.delete(item)
        names = _friendly_names(app)
        draft = getattr(app, "_zigbee_action_mappings_draft", [])
        for name in names:
            count = sum(1 for row in draft if row.get("device") == name)
            app.zigbee_device_tree.insert(
                "", "end", values=(name, count)
            )

    app.refresh_zigbee_device_list = refresh_devices
    ui_theme.secondary_button(
        device_header, "Refresh Devices", refresh_devices
    ).grid(row=0, column=1, sticky="e")

    # Recent Events is deliberately tall because only four device rows show.
    log_card = ui_theme.card(right, padding=10)
    log_card.grid(row=1, column=0, sticky="nsew")
    log_card.grid_columnconfigure(0, weight=1)
    log_card.grid_rowconfigure(1, weight=1)
    ui_theme.section_title(
        log_card,
        "Recent Events",
        symbol="◷",
    ).grid(
        row=0, column=0, sticky="w", pady=(0, 6)
    )

    app.log_text = tk.Text(
        log_card,
        font=("Consolas", 9),
        wrap=tk.WORD,
        state=tk.DISABLED,
        bg=ui_theme.COLORS["surface_alt"],
        fg=ui_theme.COLORS["text"],
        relief="flat",
        padx=8,
        pady=8,
        height=14,
    )
    app.log_text.grid(row=1, column=0, sticky="nsew")
    log_scroll = ttk.Scrollbar(
        log_card, orient="vertical", command=app.log_text.yview
    )
    log_scroll.grid(row=1, column=1, sticky="ns")
    app.log_text.config(yscrollcommand=log_scroll.set)
    ui_theme.secondary_button(
        log_card, "Clear Log", app.clear_zigbee_log
    ).grid(row=2, column=0, columnspan=2, sticky="e", pady=(6, 0))

    mapping = _create_mapping_table(app, tab, config)
    mapping.grid(
        row=3, column=0, sticky="nsew", padx=12, pady=(6, 12)
    )
    refresh_devices()

    app.add_to_zigbee_log("Zigbee Siren tab initialized")
    if not is_mqtt_available():
        app.add_to_zigbee_log(
            "WARNING: paho-mqtt library not installed. "
            "Install with: pip install paho-mqtt"
        )
    return tab
