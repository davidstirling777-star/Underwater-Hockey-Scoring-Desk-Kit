import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import time


def open_button_dialog(app, idx, trigger_button=None):
    dialog_width = 400
    dialog_height = 700
    gap = 8

    dlg = tk.Toplevel(app.master)
    dlg.withdraw()
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

        if var_name in ["time_to_start_first_game", "start_first_game_in"]:
            continue

        if var_name == "sudden_death_game_break":
            tk.Label(
                dlg,
                text="Sudden Death Allowed?"
            ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)

            default_checkbox_val = app.variables[var_name].get("used", True)

            check_value = app.button_data[idx]["checkboxes"].get(
                var_name,
                default_checkbox_val
            )

            check_var = tk.BooleanVar(value=check_value)

            ttk.Checkbutton(
                dlg,
                variable=check_var
            ).grid(
                row=row_num,
                column=1,
                sticky="w",
                padx=6,
                pady=4
            )

            checks[var_name] = check_var
            row_num += 1

            tk.Label(
                dlg,
                text="Sudden Death Game Break:"
            ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)

            sudden_death_value = app.button_data[idx]["values"].get(
                "sudden_death_game_break",
                "1"
            )

            sudden_death_entry_var = tk.StringVar(
                value=sudden_death_value
            )

            ttk.Entry(
                dlg,
                textvariable=sudden_death_entry_var,
                width=10
            ).grid(
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
            if idx == 0 and var_name in [
                "team_timeouts_allowed",
                "overtime_allowed"
            ]:
                check_value = True
            else:
                default_checkbox_val = app.variables[var_name].get(
                    "used",
                    True
                )

                check_value = app.button_data[idx]["checkboxes"].get(
                    var_name,
                    default_checkbox_val
                )

            check_var = tk.BooleanVar(value=check_value)

            ttk.Checkbutton(
                dlg,
                variable=check_var
            ).grid(
                row=row_num,
                column=1,
                sticky="w",
                padx=6,
                pady=4
            )

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
                default_values = {
                    "team_timeout_period": "1",
                    "half_period": "15",
                    "half_time_break": "3",
                    "overtime_game_break": "3",
                    "overtime_half_period": "5",
                    "overtime_half_time_break": "1",
                    "sudden_death_game_break": "1",
                    "between_game_break": "5",
                    "crib_time": "60"
                }

                value = app.button_data[idx]["values"].get(
                    var_name,
                    default_values.get(
                        var_name,
                        str(app.variables[var_name]["default"])
                    )
                )
            else:
                default_entry_value = str(
                    app.variables[var_name]["default"]
                )

                value = app.button_data[idx]["values"].get(
                    var_name,
                    default_entry_value
                )

            entry_var = tk.StringVar(value=value)

            ttk.Entry(
                dlg,
                textvariable=entry_var,
                width=10
            ).grid(
                row=row_num,
                column=1,
                sticky="w",
                padx=6,
                pady=4
            )

            entries[var_name] = entry_var

        row_num += 1

    tk.Label(
        dlg,
        text="Crib Time (seconds):"
    ).grid(row=row_num, column=0, sticky="w", padx=6, pady=4)

    crib_time_value = app.button_data[idx]["values"].get(
        "crib_time",
        "60"
    )

    crib_time_entry_var = tk.StringVar(value=crib_time_value)

    ttk.Entry(
        dlg,
        textvariable=crib_time_entry_var,
        width=10
    ).grid(
        row=row_num,
        column=1,
        sticky="w",
        padx=6,
        pady=4
    )

    entries["crib_time"] = crib_time_entry_var
    row_num += 1

    def get_dialog_state():
        return {
            "text": btn_text_var.get(),
            "entries": {
                name: value.get()
                for name, value in entries.items()
            },
            "checks": {
                name: bool(value.get())
                for name, value in checks.items()
            }
        }

    saved_dialog_state = get_dialog_state()

    def has_unsaved_changes():
        return get_dialog_state() != saved_dialog_state

    def save_changes():
        nonlocal saved_dialog_state

        new_values = {}

        for var_name, entry_var in entries.items():
            if var_name in [
                "time_to_start_first_game",
                "start_first_game_in"
            ]:
                continue

            value = entry_var.get().strip().replace(",", ".")

            try:
                float(value)
            except ValueError:
                messagebox.showerror(
                    "Invalid Value",
                    f"'{value}' is not a valid number for "
                    f"{var_name.replace('_', ' ').title()}.",
                    parent=dlg
                )
                return

            new_values[var_name] = value

        for var_name, value in new_values.items():
            app.button_data[idx]["values"][var_name] = value

        for var_name, check_var in checks.items():
            app.button_data[idx]["checkboxes"][var_name] = bool(
                check_var.get()
            )

        new_button_text = btn_text_var.get()[:max_btn_text_len]
        btn_text_var.set(new_button_text)

        app.button_data[idx]["text"] = new_button_text

        try:
            # This updates the visible preset button and saves all preset data.
            app.set_widget2_button_text(idx, new_button_text)

        except Exception as e:
            messagebox.showerror(
                "Save Error",
                f"Could not save preset settings:\n{e}",
                parent=dlg
            )
            return

        saved_dialog_state = get_dialog_state()

    def close_dialog():
        if has_unsaved_changes():
            discard_changes = messagebox.askyesno(
                "Unsaved Changes",
                "You have changed preset settings that have not been saved.\n\n"
                "Close without saving these changes?",
                parent=dlg
            )

            if not discard_changes:
                return

        try:
            dlg.grab_release()
        except tk.TclError:
            pass

        dlg.destroy()

    button_frame = ttk.Frame(dlg)
    button_frame.grid(
        row=row_num,
        column=0,
        columnspan=2,
        pady=16
    )

    button_width = 10

    ttk.Button(
        button_frame,
        text="Save",
        width=button_width,
        command=save_changes
    ).grid(
        row=0,
        column=0,
        padx=(0, 4)
    )

    ttk.Button(
        button_frame,
        text="Close",
        width=button_width,
        command=close_dialog
    ).grid(
        row=0,
        column=1,
        padx=(4, 0)
    )

    dlg.protocol("WM_DELETE_WINDOW", close_dialog)

    dlg.update_idletasks()

    if trigger_button:
        button_x = trigger_button.winfo_rootx()
        button_y = trigger_button.winfo_rooty()

        popup_x = button_x - dialog_width - gap
        popup_y = button_y
    else:
        popup_x = app.master.winfo_rootx() + 100
        popup_y = app.master.winfo_rooty() + 100

    dlg.geometry(
        f"{dialog_width}x{dialog_height}+{popup_x}+{popup_y}"
    )

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
        lambda: app._open_button_dialog(
            idx,
            app._button_hold_widget
        )
    )


def button_release(app, event, idx):
    if (
        hasattr(app, "_button_hold_timer")
        and app._button_hold_timer is not None
    ):
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


def apply_button_data(app, idx):
    for widget in app.widgets:
        var_name = widget["name"]

        if var_name in [
            "time_to_start_first_game",
            "start_first_game_in"
        ]:
            continue

        if widget["checkbox"] is not None:
            value = app.button_data[idx]["checkboxes"].get(
                var_name,
                widget["checkbox"].get()
            )
            widget["checkbox"].set(value)

        else:
            value = app.button_data[idx]["values"].get(
                var_name,
                widget["entry"].get()
            )

            widget["entry"].delete(0, tk.END)
            widget["entry"].insert(0, value)

    crib_time_value = app.button_data[idx]["values"].get(
        "crib_time",
        None
    )

    if crib_time_value is not None:
        for widget in app.widgets:
            if (
                widget["name"] == "crib_time"
                and widget["entry"] is not None
            ):
                widget["entry"].delete(0, tk.END)
                widget["entry"].insert(0, crib_time_value)

    crib_time_seconds = None
    between_game_break_minutes = None

    for widget in app.widgets:
        if (
            widget["name"] == "crib_time"
            and widget["entry"] is not None
        ):
            try:
                crib_time_seconds = float(
                    widget["entry"].get().strip().replace(",", ".")
                )
            except (ValueError, AttributeError):
                pass

        elif widget["name"] == "between_game_break":
            try:
                between_game_break_minutes = float(
                    widget["entry"].get().strip().replace(",", ".")
                )
            except (ValueError, AttributeError):
                pass

    if (
        crib_time_seconds is not None
        and between_game_break_minutes is not None
        and (between_game_break_minutes * 60) - crib_time_seconds <= 31
    ):
        for widget in app.widgets:
            if (
                widget["name"] == "crib_time"
                and widget["entry"] is not None
            ):
                widget["entry"].delete(0, tk.END)
                widget["entry"].insert(
                    0,
                    app.last_valid_values.get("crib_time", "60")
                )

        messagebox.showerror(
            "Input Error",
            "Crib time too large. Between Game Break minus "
            "Crib time must be more than 31 seconds."
        )
        return

    app.load_settings()
    app.build_game_sequence()


def set_widget2_button_text(app, idx, new_text):
    if not (0 <= idx < len(app.widget2_buttons)):
        return

    app.widget2_buttons[idx].config(text=new_text)

    if 0 <= idx < len(app.button_data):
        app.button_data[idx]["text"] = new_text

    try:
        app.save_preset_settings()
    except Exception as e:
        print(f"Error saving preset button text: {e}")
