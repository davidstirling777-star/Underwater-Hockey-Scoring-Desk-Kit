
import tkinter as tk
from tkinter import ttk
import time

def open_button_dialog(app, idx, trigger_button=None):
    dialog_width = 400
    dialog_height = 700
    gap = 8

    dlg = tk.Toplevel(app.master)
    dlg.withdraw()  # Hide until fully built and positioned
    dlg.title(f"Button {idx + 1} Settings")
    dlg.resizable(False, False)
    dlg.transient(app.master)

    entries = {}
    checks = {}
    row_num = 0
    max_btn_text_len = 16

    tk.Label(
        dlg,
        text="Button Display Text:"
    ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)

    btn_text_var = tk.StringVar(
        value=app.button_data[idx].get("text", str(idx + 1))
    )

    text_entry = ttk.Entry(
        dlg,
        textvariable=btn_text_var,
        width=max_btn_text_len
    )
    text_entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)

    row_num += 1

    for widget in app.widgets:
        var_name = widget["name"]
        label = widget["label_widget"]

        # Skip these from preset dialog
        if var_name in ["time_to_start_first_game", "start_first_game_in"]:
            continue

        # Special handling for Sudden Death: checkbox plus value entry
        if var_name == "sudden_death_game_break":
            tk.Label(
                dlg,
                text="Sudden Death Allowed?"
            ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)

            default_checkbox_val = app.variables[var_name].get("used", True)
            val = app.button_data[idx]["checkboxes"].get(
                var_name,
                default_checkbox_val
            )

            check_var = tk.BooleanVar(value=val)
            cb = ttk.Checkbutton(dlg, variable=check_var)
            cb.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)

            checks[var_name] = check_var
            row_num += 1

            tk.Label(
                dlg,
                text="Sudden Death Game Break:"
            ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)

            sudden_death_val = app.button_data[idx]["values"].get(
                "sudden_death_game_break",
                "1"
            )

            sudden_death_entry_var = tk.StringVar(value=sudden_death_val)
            sudden_death_entry = ttk.Entry(
                dlg,
                textvariable=sudden_death_entry_var,
                width=10
            )
            sudden_death_entry.grid(
                row=row_num,
                column=1,
                sticky="w",
                padx=6,
                pady=4
            )

            entries["sudden_death_game_break"] = sudden_death_entry_var
            row_num += 1
            continue

        tk.Label(
            dlg,
            text=label.cget("text")
        ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)

        if widget["checkbox"] is not None:
            if idx == 0 and var_name in ["team_timeouts_allowed", "overtime_allowed"]:
                val = True
            else:
                default_checkbox_val = app.variables[var_name].get("used", True)
                val = app.button_data[idx]["checkboxes"].get(
                    var_name,
                    default_checkbox_val
                )

            check_var = tk.BooleanVar(value=val)
            cb = ttk.Checkbutton(dlg, variable=check_var)
            cb.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)

            checks[var_name] = check_var

        else:
            if idx == 0 and var_name in [
                "team_timeout_period",
                "half_period",
                "half_time_break",
                "overtime_game_break",
                "overtime_half_period",
                "overtime_half_time_break",
                "sudden_death_game_break",
                "between_game_break",
                "crib_time"
            ]:
                val = app.button_data[idx]["values"].get(
                    var_name,
                    {
                        "team_timeout_period": "1",
                        "half_period": "15",
                        "half_time_break": "3",
                        "overtime_game_break": "3",
                        "overtime_half_period": "5",
                        "overtime_half_time_break": "1",
                        "sudden_death_game_break": "1",
                        "between_game_break": "5",
                        "crib_time": "60"
                    }.get(var_name, str(app.variables[var_name]["default"]))
                )
            else:
                default_entry_val = str(app.variables[var_name]["default"])
                val = app.button_data[idx]["values"].get(
                    var_name,
                    default_entry_val
                )

            entry_var = tk.StringVar(value=val)
            entry = ttk.Entry(dlg, textvariable=entry_var, width=10)
            entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)

            entries[var_name] = entry_var

        row_num += 1

    # Crib Time entry below Crib Time checkbox and above Save button
    tk.Label(
        dlg,
        text="Crib Time (seconds):"
    ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)

    crib_time_val = app.button_data[idx]["values"].get("crib_time", "60")
    crib_time_entry_var = tk.StringVar(value=crib_time_val)

    crib_time_entry = ttk.Entry(
        dlg,
        textvariable=crib_time_entry_var,
        width=10
    )
    crib_time_entry.grid(row=row_num, column=1, sticky="w", padx=6, pady=4)

    entries["crib_time"] = crib_time_entry_var
    row_num += 1

    def save_and_close():
        for v in entries:
            if v in ["time_to_start_first_game", "start_first_game_in"]:
                continue

            try:
                val = entries[v].get().replace(",", ".")
                float(val)
                app.button_data[idx]["values"][v] = val
            except ValueError:
                continue

        for v in checks:
            app.button_data[idx]["checkboxes"][v] = checks[v].get()

        app.button_data[idx]["text"] = btn_text_var.get()[:max_btn_text_len]
        app.set_widget2_button_text(idx, app.button_data[idx]["text"])

        save_preset_settings(app.button_data)

        dlg.destroy()

    save_btn = ttk.Button(
        dlg,
        text="Save",
        command=save_and_close
    )
    save_btn.grid(row=row_num, column=0, columnspan=2, pady=16)

    # Position from the CURRENT live location of the held preset button.
    # The right edge of the popup sits just left of the button.
    dlg.update_idletasks()

    if trigger_button:
        button_x = trigger_button.winfo_rootx()
        button_y = trigger_button.winfo_rooty()

        popup_x = button_x - dialog_width - gap
        popup_y = button_y
    else:
        popup_x = app.master.winfo_rootx() + 100
        popup_y = app.master.winfo_rooty() + 100

    dlg.geometry(f"{dialog_width}x{dialog_height}+{popup_x}+{popup_y}")

    dlg.deiconify()
    dlg.wait_visibility()
    dlg.lift()
    dlg.focus_force()
    dlg.grab_set()

def start_button_hold(app, event, idx):
    app._button_hold_start_time = time.time()
    app._button_hold_index = idx
    app._button_hold_widget = event.widget

    app._button_hold_timer = app.master.after(
        3000,
        lambda: app._open_button_dialog(idx, app._button_hold_widget)
    )

def button_release(app, event, idx):
    if hasattr(app, "_button_hold_timer") and app._button_hold_timer is not None:
        app.master.after_cancel(app._button_hold_timer)
        app._button_hold_timer = None

    if (
        hasattr(app, "_button_hold_start_time")
        and app._button_hold_start_time is not None
        and (time.time() - app._button_hold_start_time < 2.9)
    ):
        app._apply_button_data(idx)

    app._button_hold_start_time = None
    app._button_hold_index = None
