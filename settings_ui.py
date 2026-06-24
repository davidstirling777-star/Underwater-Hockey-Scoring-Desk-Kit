
import tkinter as tk
from tkinter import ttk, font, messagebox
import re

def create_settings_tab(app):
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Game Variables")

    tab.grid_rowconfigure(0, weight=3)
    tab.grid_rowconfigure(1, weight=1)
    tab.grid_rowconfigure(2, weight=1)
    tab.grid_rowconfigure(3, weight=1)
    tab.grid_columnconfigure(0, weight=2)
    tab.grid_columnconfigure(1, weight=1)

    default_font = font.nametofont("TkDefaultFont")
    new_size = default_font.cget("size") + 2
    small_size = default_font.cget("size") - 1
    headers = ["Use?", "Variable", "Value", "Units"]

    style = ttk.Style()
    style.configure(
        "Large.TCheckbutton",
        focuscolor="none",
        font=(default_font.cget("family"), default_font.cget("size") + 2)
    )

    # ------------------------------------------------------------
    # Widget 1 - Game Variables
    # ------------------------------------------------------------
    widget1 = ttk.Frame(tab, borderwidth=1, relief="solid")
    widget1.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=8, pady=8)

    for i in range(4):
        widget1.grid_columnconfigure(i, weight=1)

    for i in range(17):
        widget1.grid_rowconfigure(i, weight=1)

    for i, h in enumerate(headers):
        tk.Label(
            widget1,
            text=h,
            font=(default_font.cget("family"), new_size, "bold")
        ).grid(row=0, column=i, sticky="w", padx=5, pady=4)

    row_idx = 1
    app.widgets = []

    entry_order = list(app.variables.keys())

    for special_name in [
        "time_to_start_first_game",
        "start_first_game_in",
        "record_scorers_cap_number"
    ]:
        if special_name in entry_order:
            entry_order.remove(special_name)

    crib_time_index = (
        entry_order.index("crib_time")
        if "crib_time" in entry_order
        else len(entry_order)
    )

    entry_order = (
        ["time_to_start_first_game", "start_first_game_in"]
        + entry_order[:crib_time_index]
        + ["record_scorers_cap_number"]
        + entry_order[crib_time_index:]
    )

    for var_name in entry_order:
        var_info = app.variables[var_name]

        if (
            var_info["checkbox"]
            and var_name in [
                "team_timeouts_allowed",
                "overtime_allowed",
                "record_scorers_cap_number"
            ]
        ):
            var_info["default"] = var_info.get("default", True)

        if var_name == "team_timeouts_allowed":
            check_var = app.team_timeouts_allowed_var
            cb = ttk.Checkbutton(
                widget1,
                variable=check_var,
                style="Large.TCheckbutton"
            )
            cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))

            label_widget = tk.Label(
                widget1,
                text=var_info.get("label", "Team Time-Outs allowed?"),
                font=(default_font.cget("family"), new_size, "bold")
            )
            label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)

            check_var.trace_add(
                "write",
                lambda *args: app._on_team_timeouts_change()
            )

            app.widgets.append({
                "name": var_name,
                "entry": None,
                "checkbox": check_var,
                "label_widget": label_widget
            })

            row_idx += 1
            continue

        if var_name == "overtime_allowed":
            check_var = app.overtime_allowed_var
            cb = ttk.Checkbutton(
                widget1,
                variable=check_var,
                style="Large.TCheckbutton"
            )
            cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))

            label_widget = tk.Label(
                widget1,
                text=var_info.get("label", "Overtime allowed?"),
                font=(default_font.cget("family"), new_size, "bold")
            )
            label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)

            check_var.trace_add(
                "write",
                lambda *args: app._on_overtime_change()
            )

            app.widgets.append({
                "name": var_name,
                "entry": None,
                "checkbox": check_var,
                "label_widget": label_widget
            })

            row_idx += 1
            continue

        if var_name == "record_scorers_cap_number":
            check_var = app.record_scorers_cap_number_var
            cb = ttk.Checkbutton(
                widget1,
                variable=check_var,
                style="Large.TCheckbutton"
            )
            cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))

            label_widget = tk.Label(
                widget1,
                text=var_info.get("label", "Record Scorers Cap Number"),
                font=(default_font.cget("family"), new_size, "bold")
            )
            label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)

            check_var.trace_add(
                "write",
                lambda *args: app._on_single_variable_change(
                    "record_scorers_cap_number"
                )
            )

            app.widgets.append({
                "name": var_name,
                "entry": None,
                "checkbox": check_var,
                "label_widget": label_widget
            })

            row_idx += 1
            continue

        check_var = tk.BooleanVar(value=True) if var_info["checkbox"] else None

        if check_var:
            cb = ttk.Checkbutton(
                widget1,
                variable=check_var,
                style="Large.TCheckbutton"
            )
            cb.grid(row=row_idx, column=0, sticky="", pady=5, padx=(10, 0))
            check_var.trace_add(
                "write",
                lambda *args, name=var_name: app._on_single_variable_change(name)
            )

        label_text = var_info.get(
            "label",
            f"{var_name.replace('_', ' ').title()}:"
        )

        label_widget = tk.Label(
            widget1,
            text=label_text,
            font=(default_font.cget("family"), new_size, "bold")
        )
        label_widget.grid(row=row_idx, column=1, sticky="w", pady=4)

        entry = ttk.Entry(widget1, width=10)

        if var_name == "time_to_start_first_game":
            entry.insert(0, "")

            def validate_hhmm_on_focusout(event):
                val = event.widget.get().strip()

                if val == "":
                    return

                if not re.fullmatch(
                    r"(?:[0-9]|1[0-9]|2[0-3]):[0-5][0-9]",
                    val
                ):
                    messagebox.showerror(
                        "Input Error",
                        "Please enter time in HH:MM 24-hour format "
                        "(e.g., 19:36 or 9:36)."
                    )
                    event.widget.focus_set()
                    event.widget.selection_range(0, tk.END)
                    return

                app._on_single_variable_change("time_to_start_first_game")

            entry.bind("<FocusOut>", validate_hhmm_on_focusout)
            entry.bind("<Return>", validate_hhmm_on_focusout)

        else:
            entry.insert(0, "1")

            if var_name in ["crib_time", "sudden_death_game_break"]:

                def validate_numeric_on_focusout(event, field_name=var_name):
                    val = event.widget.get().strip()

                    if val == "":
                        return

                    try:
                        val_normalized = val.replace(",", ".")
                        val_float = float(val_normalized)

                        if field_name == "crib_time":
                            between_game_break_minutes = None

                            for widget in app.widgets:
                                if widget["name"] == "between_game_break":
                                    try:
                                        bgb_val = (
                                            widget["entry"]
                                            .get()
                                            .strip()
                                            .replace(",", ".")
                                        )
                                        between_game_break_minutes = float(bgb_val)
                                    except (ValueError, AttributeError):
                                        pass
                                    break

                            if between_game_break_minutes is not None:
                                crib_time_seconds = val_float

                                if (
                                    between_game_break_minutes * 60
                                ) - crib_time_seconds <= 31:
                                    messagebox.showerror(
                                        "Input Error",
                                        "Crib time too large. Between Game "
                                        "Break minus Crib time must be > "
                                        "31 seconds."
                                    )
                                    event.widget.delete(0, tk.END)
                                    event.widget.insert(
                                        0,
                                        app.last_valid_values[field_name]
                                    )
                                    event.widget.focus_set()
                                    event.widget.selection_range(0, tk.END)
                                    return

                        app.last_valid_values[field_name] = val
                        app._on_single_variable_change(field_name)

                    except ValueError:
                        messagebox.showerror(
                            "Input Error",
                            f"Please enter a valid number for "
                            f"{field_name.replace('_', ' ').title()}."
                        )
                        event.widget.delete(0, tk.END)
                        event.widget.insert(
                            0,
                            app.last_valid_values[field_name]
                        )
                        event.widget.focus_set()
                        event.widget.selection_range(0, tk.END)

                entry.bind("<FocusOut>", validate_numeric_on_focusout)
                entry.bind("<Return>", validate_numeric_on_focusout)

            else:
                entry.bind(
                    "<FocusOut>",
                    lambda e, name=var_name: app._on_single_variable_change(name)
                )
                entry.bind(
                    "<Return>",
                    lambda e, name=var_name: app._on_single_variable_change(name)
                )

        entry.grid(row=row_idx, column=2, sticky="w", padx=5, pady=4)

        tk.Label(
            widget1,
            text=var_info["unit"],
            font=(default_font.cget("family"), new_size, "bold")
        ).grid(row=row_idx, column=3, sticky="w", padx=5, pady=4)

        app.widgets.append({
            "name": var_name,
            "entry": entry,
            "checkbox": check_var,
            "label_widget": label_widget
        })

        app.last_valid_values[var_name] = entry.get()

        if var_name == "team_timeout_period":
            app.team_timeout_period_entry = entry
            app.team_timeout_period_label = label_widget

        row_idx += 1

        if var_name == "crib_time":
            combined_explanation = tk.Label(
                widget1,
                text=(
                    "• Crib Time is a period (in seconds) that is "
                    "subtracted from the \"Between Game Break\" time at "
                    "the start of each game\n"
                    "to try to realign Court Time with Local Computer Time.\n"
                    "• Value boxes accept decimal time e.g. 1.5 or 1,5 = "
                    "1 min, 30 sec"
                ),
                font=(default_font.cget("family"), small_size),
                anchor="w",
                justify="left",
                wraplength=600
            )
            combined_explanation.grid(
                row=row_idx,
                column=0,
                columnspan=4,
                pady=3,
                sticky="nsew"
            )

            row_idx += 1

            reset_warning_bullet = tk.Label(
                widget1,
                text=(
                    "• If you change any value in here, push the "
                    "'Reset Timer' Button!"
                ),
                font=(default_font.cget("family"), small_size, "bold"),
                fg="red",
                anchor="w",
                justify="left",
                wraplength=600
            )
            reset_warning_bullet.grid(
                row=row_idx,
                column=0,
                columnspan=4,
                pady=3,
                sticky="nsew"
            )

            row_idx += 1

    app.reset_timer_button = ttk.Button(
        widget1,
        text="Reset Timer",
        command=app.reset_timer
    )
    app.reset_timer_button.grid(
        row=row_idx,
        column=0,
        columnspan=4,
        pady=8
    )

    # ------------------------------------------------------------
    # Widget 2 - Presets
    # ------------------------------------------------------------
    widget2 = ttk.Frame(tab, borderwidth=1, relief="solid")
    widget2.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

    for col in range(3):
        widget2.grid_columnconfigure(col, weight=1)

    widget2.grid_rowconfigure(0, weight=0)
    widget2.grid_rowconfigure(1, weight=0, minsize=38)
    widget2.grid_rowconfigure(2, weight=0, minsize=38)
    widget2.grid_rowconfigure(3, weight=1)
    widget2.grid_rowconfigure(4, weight=0)
    widget2.grid_rowconfigure(5, weight=0)

    header_label = tk.Label(
        widget2,
        text="Presets",
        font=(default_font.cget("family"), new_size, "bold")
    )
    header_label.grid(
        row=0,
        column=0,
        columnspan=3,
        padx=4,
        pady=(8, 4),
        sticky="nsew"
    )

    app.widget2_buttons = []
    preset_data = app.load_preset_settings()
    app.button_data = preset_data.copy()

    for i in range(6):
        btn_row = 1 if i < 3 else 2
        btn_col = i % 3

        btn = tk.Button(
            widget2,
            text=app.button_data[i]["text"],
            font=(
                default_font.cget("family"),
                default_font.cget("size") + 1,
                "bold"
            ),
            width=12,
            height=1,
            relief="raised",
            borderwidth=2
        )

        btn.grid(
            row=btn_row,
            column=btn_col,
            padx=8,
            pady=4,
            sticky="nsew"
        )

        btn.bind("<ButtonPress-1>", app._make_press_handler(i))
        btn.bind("<ButtonRelease-1>", app._make_release_handler(i))

        app.widget2_buttons.append(btn)

    instruction1 = tk.Label(
        widget2,
        text="Click the buttons above to load preset times and allowed Game Periods",
        anchor="w",
        justify="left",
        font=(default_font.cget("family"), default_font.cget("size"))
    )
    instruction1.grid(
        row=4,
        column=0,
        columnspan=3,
        sticky="w",
        padx=8,
        pady=(4, 1)
    )

    instruction2 = tk.Label(
        widget2,
        text="Press and hold the button for >4 seconds to alter the stored preset values",
        anchor="w",
        justify="left",
        font=(default_font.cget("family"), default_font.cget("size"))
    )
    instruction2.grid(
        row=5,
        column=0,
        columnspan=3,
        sticky="w",
        padx=8,
        pady=(1, 6)
    )

    # ------------------------------------------------------------
    # Widget 4 - Tournament List
    # ------------------------------------------------------------
    widget4 = ttk.Frame(tab, borderwidth=1, relief="solid")
    widget4.grid(row=2, column=1, sticky="nsew", padx=8, pady=8)

    widget4.grid_columnconfigure(0, weight=0)
    widget4.grid_columnconfigure(1, weight=1)
    widget4.grid_columnconfigure(2, weight=0)

    widget4.grid_rowconfigure(0, weight=0)
    widget4.grid_rowconfigure(1, weight=0)
    widget4.grid_rowconfigure(2, weight=0)
    widget4.grid_rowconfigure(3, weight=0)
    widget4.grid_rowconfigure(4, weight=1)

    tournament_header = tk.Label(
        widget4,
        text="Tournament List",
        font=(default_font.cget("family"), new_size, "bold")
    )
    tournament_header.grid(
        row=0,
        column=0,
        columnspan=3,
        padx=8,
        pady=(10, 8),
        sticky="ew"
    )

    tk.Label(
        widget4,
        text="CSV File:",
        font=(default_font.cget("family"), default_font.cget("size")),
        anchor="w"
    ).grid(row=1, column=0, sticky="w", padx=8, pady=2)

    csv_files = app.get_csv_files()
    app.csv_var = tk.StringVar(
        value=csv_files[0] if csv_files else "No CSV files found"
    )

    app.csv_dropdown = ttk.Combobox(
        widget4,
        textvariable=app.csv_var,
        values=csv_files,
        state="readonly",
        width=20,
        postcommand=app.refresh_csv_dropdown
    )
    app.csv_dropdown.grid(
        row=1,
        column=1,
        columnspan=2,
        sticky="ew",
        padx=8,
        pady=2
    )

    app.csv_dropdown.bind(
        "<<ComboboxSelected>>",
        app.on_csv_file_changed
    )

    tk.Label(
        widget4,
        text="Starting Game #:",
        font=(default_font.cget("family"), default_font.cget("size")),
        anchor="w"
    ).grid(row=2, column=0, sticky="w", padx=8, pady=(8, 2))

    app.game_numbers = []
    app.starting_game_var = tk.StringVar(value="")

    app.starting_game_dropdown = ttk.Combobox(
        widget4,
        textvariable=app.starting_game_var,
        values=app.game_numbers,
        state="readonly",
        width=6
    )
    app.starting_game_dropdown.grid(
        row=2,
        column=1,
        sticky="w",
        padx=8,
        pady=(8, 2)
    )

    open_folder_btn = tk.Button(
        widget4,
        text="Open Folder",
        font=(
            default_font.cget("family"),
            default_font.cget("size")
        ),
        command=app.open_csv_folder,
        width=12
    )
    open_folder_btn.grid(
        row=2,
        column=2,
        sticky="e",
        padx=8,
        pady=(8, 2)
    )

    app.starting_game_dropdown.bind(
        "<<ComboboxSelected>>",
        app.on_game_selection_changed
    )

    app.on_csv_file_changed()

    csv_comment = tk.Label(
        widget4,
        text=(
            "Save a CSV file of games into the same folder as this program is in.\n"
            "Expected CSV headers: date,#,White,Score,Black,Score,"
            "Referees,Penalties,Comments\n"
            "(where # is the Game Number)"
        ),
        font=(default_font.cget("family"), small_size),
        anchor="nw",
        justify="left",
        wraplength=600
    )
    csv_comment.grid(
        row=3,
        column=0,
        columnspan=3,
        sticky="nw",
        padx=8,
        pady=(8, 4)
    )

    show_display_checkbox = ttk.Checkbutton(
        widget4,
        text="Show Display Screen",
        variable=app.show_display_screen_var,
        command=app.toggle_display_screen,
        style="Large.TCheckbutton"
    )
    show_display_checkbox.grid(
        row=4,
        column=0,
        columnspan=3,
        sticky="w",
        padx=8,
        pady=(4, 8)
    )

    # ------------------------------------------------------------
    # Widget 3 - Game Sequence
    # ------------------------------------------------------------
    widget3 = ttk.Frame(tab, borderwidth=1, relief="solid")
    widget3.grid(row=3, column=1, sticky="nsew", padx=8, pady=8)

    widget3.grid_columnconfigure(0, weight=1)
    widget3.grid_rowconfigure(0, weight=0)
    widget3.grid_rowconfigure(1, weight=1)

    explanation_header = tk.Label(
        widget3,
        text="Game Sequence",
        font=(default_font.cget("family"), new_size, "bold")
    )
    explanation_header.grid(
        row=0,
        column=0,
        padx=4,
        pady=(8, 2),
        sticky="ew"
    )

    explanation_text = (
        "Game Sequence Flow:\n"
        "1. First Game Starts In: (runs once at app start)\n"
        "2. First Half → Half Time → Second Half\n"
        "3. If scores tied: Overtime Game Break → Overtime First Half "
        "→ Overtime Half Time → Overtime Second Half (if enabled)\n"
        "4. If still tied: Sudden Death Game Break → Sudden Death (if enabled)\n"
        "5. Between Game Break (loop back to step 2)\n\n"
        "Important Notes:\n"
        "• 'First Game Starts In:' transitions directly to First Half\n"
        "• Crib time is subtracted from Between Game Break"
    )

    explanation_label = tk.Label(
        widget3,
        text=explanation_text,
        font=(default_font.cget("family"), small_size),
        justify="left",
        anchor="nw"
    )
    explanation_label.grid(
        row=1,
        column=0,
        padx=4,
        pady=(2, 4),
        sticky="nsew"
    )

    app.update_overtime_variables_state()
