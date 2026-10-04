"""Build the Game Variables, Tournament List, About and Screens control tabs.

The widgets write into GameManagementApp/engine state, not directly into
settings.json. Automatic edits are queued for a coalesced save; buttons that
explicitly say Save may use their own immediate persistence path.
"""


import tkinter as tk
from tkinter import ttk, font, messagebox
from pathlib import Path
import re
import webbrowser

from app_version import APP_VERSION
import ui_theme

def create_settings_tab(app):
    """Create the v1.3.4 Game Variables tab using the approved mockup style."""
    tab = ttk.Frame(app.notebook, style="UWH.Tab.TFrame")
    app.notebook.add(
        tab,
        text=ui_theme.tab_label("Game Variables"),
    )
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(2, weight=1)

    header = ui_theme.page_header(
        tab,
        "Game Variables",
        "Configure match timing, overtime, breaks and scoring options.",
        symbol="⚙",
    )
    header.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=12,
        pady=(12, 6),
    )

    info = ui_theme.info_banner(
        tab,
        "Game Variable changes are saved automatically. "
        "Press Reset Timer after changing match timing so the active "
        "game sequence is rebuilt from the new values."
    )
    info.grid(
        row=1,
        column=0,
        sticky="ew",
        padx=12,
        pady=(0, 6),
    )

    content = ttk.Frame(tab, style="UWH.Tab.TFrame")
    content.grid(
        row=2,
        column=0,
        sticky="nsew",
        padx=12,
        pady=(6, 12),
    )
    content.grid_columnconfigure(0, weight=6)
    content.grid_columnconfigure(1, weight=4)
    content.grid_rowconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Real Game Variables card. Every row maps to the actual runtime model;
    # the visual redesign deliberately introduces no mockup-only variables.
    # ------------------------------------------------------------------
    variables_card = ui_theme.card(content, padding=12)
    variables_card.grid(
        row=0,
        column=0,
        sticky="nsew",
        padx=(0, 6),
    )
    variables_card.grid_columnconfigure(0, weight=3)
    variables_card.grid_columnconfigure(1, weight=0, minsize=72)
    variables_card.grid_columnconfigure(2, weight=0, minsize=110)
    variables_card.grid_columnconfigure(3, weight=1, minsize=82)

    ui_theme.section_title(
        variables_card,
        "Game Variables",
        symbol="⚙",
    ).grid(
        row=0,
        column=0,
        columnspan=4,
        sticky="w",
        pady=(0, 10),
    )

    header_bg = ui_theme.COLORS["primary_soft"]
    for col, text in enumerate(("Variable", "Use?", "Value", "Units")):
        tk.Label(
            variables_card,
            text=text,
            bg=header_bg,
            fg=ui_theme.COLORS["navy"],
            font=(ui_theme.FONT_FAMILY, 9, "bold"),
            anchor="w" if col != 1 else "center",
            padx=9,
            pady=7,
        ).grid(row=1, column=col, sticky="nsew")

    app.widgets = []
    app.last_valid_values = {}

    def variable_label(row, text):
        label = tk.Label(
            variables_card,
            text=text,
            bg=ui_theme.COLORS["surface"],
            fg=ui_theme.COLORS["text"],
            font=ui_theme.BODY_FONT,
            anchor="w",
            padx=9,
            pady=3,
        )
        label.grid(row=row, column=0, sticky="ew")
        return label

    def unit_label(row, text):
        tk.Label(
            variables_card,
            text=text,
            bg=ui_theme.COLORS["surface"],
            fg=ui_theme.COLORS["muted"],
            font=ui_theme.SMALL_FONT,
            anchor="w",
            padx=8,
        ).grid(row=row, column=3, sticky="ew")

    def checkbox_cell(row, variable):
        frame = tk.Frame(
            variables_card,
            bg=ui_theme.COLORS["surface"],
        )
        frame.grid(row=row, column=1, sticky="nsew")
        cb = ui_theme.toggle_switch(frame, variable)
        cb.pack(expand=True, padx=4, pady=2)
        return cb

    def entry_cell(row):
        entry = ttk.Entry(
            variables_card,
            width=9,
            style="UWH.TEntry",
            justify="center",
        )
        entry.grid(
            row=row,
            column=2,
            sticky="ew",
            padx=7,
            pady=3,
        )
        return entry

    def bind_standard_entry(entry, var_name):
        entry.bind(
            "<FocusOut>",
            lambda _event, name=var_name:
                app._on_single_variable_change(name)
        )
        entry.bind(
            "<Return>",
            lambda _event, name=var_name:
                app._on_single_variable_change(name)
        )

    def validate_hhmm_on_focusout(event):
        """Validate either dot or colon 24-hour clock notation."""
        value = event.widget.get().strip()
        if value == "":
            app._on_single_variable_change(
                "time_to_start_first_game"
            )
            return

        normalized = value.replace(".", ":")
        if not re.fullmatch(
            r"(?:[01]?[0-9]|2[0-3]):[0-5][0-9]",
            normalized,
        ):
            messagebox.showerror(
                "Input Error",
                "Please enter a 24-hour time as H.MM, HH.MM, H:MM or "
                "HH:MM (for example 9.36, 09.36, 9:36 or 09:36)."
            )
            event.widget.focus_set()
            event.widget.selection_range(0, tk.END)
            return

        hh, mm = normalized.split(":")
        event.widget.delete(0, tk.END)
        event.widget.insert(0, f"{int(hh):02d}.{mm}")
        app._on_single_variable_change(
            "time_to_start_first_game"
        )

    def bind_clock_entry(entry):
        entry.bind("<FocusOut>", validate_hhmm_on_focusout)
        entry.bind("<Return>", validate_hhmm_on_focusout)

    def bind_guarded_numeric(entry, var_name):
        def validate(event, field_name=var_name):
            value = event.widget.get().strip()
            if value == "":
                return

            try:
                numeric = float(value.replace(",", "."))
            except ValueError:
                messagebox.showerror(
                    "Input Error",
                    f"Please enter a valid number for "
                    f"{field_name.replace('_', ' ').title()}."
                )
                event.widget.delete(0, tk.END)
                event.widget.insert(
                    0,
                    app.last_valid_values.get(field_name, "1"),
                )
                event.widget.focus_set()
                event.widget.selection_range(0, tk.END)
                return

            if field_name == "crib_time":
                between_game_break_minutes = None
                for item in app.widgets:
                    if item["name"] == "between_game_break":
                        try:
                            between_game_break_minutes = float(
                                item["entry"].get().strip().replace(
                                    ",", "."
                                )
                            )
                        except (ValueError, AttributeError):
                            pass
                        break

                if (
                    between_game_break_minutes is not None
                    and (between_game_break_minutes * 60) - numeric <= 31
                ):
                    messagebox.showerror(
                        "Input Error",
                        "Crib time too large. Between Game Break minus "
                        "Crib time must be more than 31 seconds."
                    )
                    event.widget.delete(0, tk.END)
                    event.widget.insert(
                        0,
                        app.last_valid_values.get(
                            field_name,
                            "60",
                        ),
                    )
                    event.widget.focus_set()
                    event.widget.selection_range(0, tk.END)
                    return

            app.last_valid_values[field_name] = value
            app._on_single_variable_change(field_name)

        entry.bind("<FocusOut>", validate)
        entry.bind("<Return>", validate)

    render_rows = [
        "time_to_start_first_game",
        "start_first_game_in",
        "team_timeout_period",
        "half_period",
        "half_time_break",
        "overtime_allowed",
        "overtime_game_break",
        "overtime_half_period",
        "overtime_half_time_break",
        "sudden_death_game_break",
        "between_game_break",
        "record_scorers_cap_number",
        "crib_time",
    ]

    row = 2
    for var_name in render_rows:
        info = app.variables[var_name]
        label = variable_label(
            row,
            info.get(
                "label",
                f"{var_name.replace('_', ' ').title()}:",
            ),
        )

        entry = None
        if var_name not in (
            "overtime_allowed",
            "record_scorers_cap_number",
        ):
            entry = entry_cell(row)
            entry.insert(
                0,
                "" if var_name == "time_to_start_first_game" else "1",
            )
            unit_label(row, info.get("unit", ""))

            if var_name == "time_to_start_first_game":
                bind_clock_entry(entry)
            elif var_name in (
                "crib_time",
                "sudden_death_game_break",
            ):
                bind_guarded_numeric(entry, var_name)
            else:
                bind_standard_entry(entry, var_name)

            app.last_valid_values[var_name] = entry.get()

        if var_name == "team_timeout_period":
            checkbox_cell(
                row,
                app.team_timeouts_allowed_var,
            )
            app.team_timeouts_allowed_var.trace_add(
                "write",
                lambda *_args: app._on_team_timeouts_change(),
            )
            app.widgets.append({
                "name": "team_timeouts_allowed",
                "entry": None,
                "checkbox": app.team_timeouts_allowed_var,
                "label_widget": label,
            })
            app.widgets.append({
                "name": "team_timeout_period",
                "entry": entry,
                "checkbox": None,
                "label_widget": label,
            })
            app.team_timeout_period_entry = entry
            app.team_timeout_period_label = label

        elif var_name == "overtime_allowed":
            checkbox_cell(
                row,
                app.overtime_allowed_var,
            )
            app.overtime_allowed_var.trace_add(
                "write",
                lambda *_args: app._on_overtime_change(),
            )
            app.widgets.append({
                "name": var_name,
                "entry": None,
                "checkbox": app.overtime_allowed_var,
                "label_widget": label,
            })

        elif var_name == "record_scorers_cap_number":
            checkbox_cell(
                row,
                app.record_scorers_cap_number_var,
            )
            app.record_scorers_cap_number_var.trace_add(
                "write",
                lambda *_args:
                    app._on_single_variable_change(
                        "record_scorers_cap_number"
                    ),
            )
            app.widgets.append({
                "name": var_name,
                "entry": None,
                "checkbox": app.record_scorers_cap_number_var,
                "label_widget": label,
            })

        elif info.get("checkbox"):
            check_var = tk.BooleanVar(value=True)
            checkbox_cell(row, check_var)
            check_var.trace_add(
                "write",
                lambda *_args, name=var_name:
                    app._on_single_variable_change(name),
            )
            app.widgets.append({
                "name": var_name,
                "entry": entry,
                "checkbox": check_var,
                "label_widget": label,
            })

        else:
            app.widgets.append({
                "name": var_name,
                "entry": entry,
                "checkbox": None,
                "label_widget": label,
            })

        row += 1

    footer = tk.Frame(
        variables_card,
        bg=ui_theme.COLORS["surface"],
    )
    footer.grid(
        row=row,
        column=0,
        columnspan=4,
        sticky="ew",
        pady=(9, 0),
    )
    footer.grid_columnconfigure(1, weight=1)

    app.reset_timer_button = ui_theme.primary_button(
        footer,
        "Reset Timer",
        app.reset_timer,
    )
    app.reset_timer_button.grid(
        row=0,
        column=0,
        sticky="w",
    )

    ui_theme.muted_label(
        footer,
        "Crib Time is subtracted from Between Game Break. "
        "Decimal values such as 1.5 are accepted.",
        wraplength=470,
        justify="left",
    ).grid(
        row=0,
        column=1,
        sticky="w",
        padx=12,
    )

    tk.Label(
        footer,
        text=f"UWH v{APP_VERSION}",
        bg=ui_theme.COLORS["surface"],
        fg=ui_theme.COLORS["muted"],
        font=ui_theme.SMALL_FONT,
    ).grid(
        row=0,
        column=2,
        sticky="e",
    )

    # ------------------------------------------------------------------
    # Right column: sequence above presets, matching the approved mockup.
    # ------------------------------------------------------------------
    right = ttk.Frame(
        content,
        style="UWH.Tab.TFrame",
    )
    right.grid(
        row=0,
        column=1,
        sticky="nsew",
        padx=(6, 0),
    )
    right.grid_columnconfigure(0, weight=1)
    right.grid_rowconfigure(0, weight=3)
    right.grid_rowconfigure(1, weight=2)

    sequence_card = ui_theme.card(right, padding=12)
    sequence_card.grid(
        row=0,
        column=0,
        sticky="nsew",
        pady=(0, 6),
    )
    sequence_card.grid_columnconfigure(0, weight=1)
    sequence_card.grid_rowconfigure(1, weight=1)

    ui_theme.section_title(
        sequence_card,
        "Game Sequence Info",
        symbol="ⓘ",
    ).grid(
        row=0,
        column=0,
        sticky="w",
        pady=(0, 8),
    )

    explanation_text = (
        "Game Sequence Flow:\n"
        "1. First Game Starts In: (runs once at app start)\n"
        "2. First Half → Half Time → Second Half\n"
        "3. If scores tied: Overtime Game Break → Overtime First Half "
        "→ Overtime Half Time → Overtime Second Half (if enabled)\n"
        "4. If still tied: Sudden Death Game Break → Sudden Death "
        "(if enabled)\n"
        "5. Between Game Break (loop back to step 2)\n\n"
        "Important Notes:\n"
        "• First Game Starts In: transitions directly to First Half\n"
        "• Crib time is subtracted from Between Game Break"
    )

    sequence_wrap = ttk.Frame(
        sequence_card,
        style="UWH.Surface.TFrame",
    )
    sequence_wrap.grid(
        row=1,
        column=0,
        sticky="nsew",
    )
    sequence_wrap.grid_columnconfigure(0, weight=1)
    sequence_wrap.grid_rowconfigure(0, weight=1)

    sequence_text = tk.Text(
        sequence_wrap,
        wrap="word",
        height=11,
        bg=ui_theme.COLORS["surface_alt"],
        fg=ui_theme.COLORS["text"],
        font=ui_theme.BODY_FONT,
        relief="flat",
        padx=10,
        pady=10,
    )
    sequence_text.grid(
        row=0,
        column=0,
        sticky="nsew",
    )
    sequence_scroll = ttk.Scrollbar(
        sequence_wrap,
        orient="vertical",
        command=sequence_text.yview,
    )
    sequence_scroll.grid(
        row=0,
        column=1,
        sticky="ns",
    )
    sequence_text.configure(
        yscrollcommand=sequence_scroll.set,
    )
    sequence_text.insert("1.0", explanation_text)
    sequence_text.config(state="disabled")

    exit_row = tk.Frame(
        sequence_card,
        bg=ui_theme.COLORS["surface"],
    )
    exit_row.grid(
        row=2,
        column=0,
        sticky="e",
        pady=(8, 0),
    )
    app.exit_program_button = ui_theme.danger_button(
        exit_row,
        "Exit Program",
        app.request_exit,
        width=13,
    )
    app.exit_program_button.pack()

    presets_card = ui_theme.card(right, padding=12)
    presets_card.grid(
        row=1,
        column=0,
        sticky="nsew",
        pady=(6, 0),
    )
    presets_card.grid_columnconfigure(0, weight=1)
    presets_card.grid_columnconfigure(1, weight=1)
    presets_card.grid_columnconfigure(2, weight=1)

    ui_theme.section_title(
        presets_card,
        "Presets",
        symbol="▤",
    ).grid(
        row=0,
        column=0,
        columnspan=3,
        sticky="w",
        pady=(0, 8),
    )

    app.widget2_buttons = []
    preset_data = app.load_preset_settings()
    app.button_data = preset_data.copy()

    for index in range(9):
        btn = ui_theme.secondary_button(
            presets_card,
            f"{index + 1}.  {app.button_data[index]['text']}",
            lambda: None,
        )
        btn.configure(
            width=17,
        )
        btn.grid(
            row=1 + (index // 3),
            column=index % 3,
            sticky="nsew",
            padx=4,
            pady=4,
        )
        btn.bind(
            "<ButtonPress-1>",
            app._make_press_handler(index),
        )
        btn.bind(
            "<ButtonRelease-1>",
            app._make_release_handler(index),
        )
        app.widget2_buttons.append(btn)

    ui_theme.muted_label(
        presets_card,
        "Click a preset to load it. Press and hold a preset for 3 seconds "
        "to edit it.",
        justify="left",
    ).grid(
        row=4,
        column=0,
        columnspan=3,
        sticky="w",
        padx=4,
        pady=(8, 0),
    )

    app.update_overtime_variables_state()



def create_tournament_tab(app):
    """Create the approved two-card Tournament List and results-sync tab."""
    tab = ttk.Frame(app.notebook, style="UWH.Tab.TFrame")
    app.tournament_tab = tab
    app.notebook.add(
        tab,
        text=ui_theme.tab_label("Tournament List"),
    )
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_columnconfigure(1, weight=1)
    tab.grid_rowconfigure(1, weight=1)
    tab.grid_rowconfigure(2, weight=0)

    header = ui_theme.page_header(
        tab,
        "Tournament List",
        "Load tournament draw data and manage local/shared result syncing.",
        symbol="▤",
    )
    header.grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="ew",
        padx=12,
        pady=(12, 6),
    )

    setup = ui_theme.card(tab, padding=14)
    setup.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(6, 6))
    setup.grid_columnconfigure(0, weight=0)
    setup.grid_columnconfigure(1, weight=1)
    setup.grid_columnconfigure(2, weight=0)

    results = ui_theme.card(tab, padding=14)
    results.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(6, 6))
    results.grid_columnconfigure(0, weight=0)
    results.grid_columnconfigure(1, weight=1)
    results.grid_columnconfigure(2, weight=0)

    info = ui_theme.card(tab, padding=14)
    info.grid(row=2, column=0, columnspan=2, sticky="ew",
              padx=12, pady=(6, 12))
    info.grid_columnconfigure(0, weight=1)

    ui_theme.section_title(setup, "Tournament Setup", symbol="▣").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
    )

    app.use_tournament_list_var = tk.BooleanVar(
        master=app.master, value=True
    )
    ui_theme.toggle_switch(
        setup,
        app.use_tournament_list_var,
        command=app.on_use_tournament_list_changed,
        text="Use Tournament List?",
    ).grid(row=1, column=0, sticky="w", pady=(0, 2))

    ui_theme.muted_label(
        setup,
        "Enables loading of game data from a tournament draw file",
    ).grid(row=1, column=1, columnspan=2, sticky="w", padx=(10, 0))

    ui_theme.body_label(setup, "Tournament draw file").grid(
        row=2, column=0, sticky="w", pady=(14, 4)
    )
    csv_files = app.get_csv_files()
    app.csv_var = tk.StringVar(
        master=app.master,
        value=csv_files[0] if csv_files else "No CSV files found",
    )
    app.csv_dropdown = ttk.Combobox(
        setup,
        textvariable=app.csv_var,
        values=csv_files,
        state="readonly",
        postcommand=app.refresh_csv_dropdown,
        style="UWH.TCombobox",
    )
    app.csv_dropdown.grid(row=2, column=1, sticky="ew", padx=8, pady=(14, 4))
    app.csv_dropdown.bind("<<ComboboxSelected>>", app.on_csv_file_changed)
    ui_theme.secondary_button(
        setup, "Open Folder", app.open_csv_folder
    ).grid(row=2, column=2, sticky="e", pady=(14, 4))

    ui_theme.body_label(setup, "Starting Game #").grid(
        row=3, column=0, sticky="w", pady=8
    )
    app.starting_game_var = tk.StringVar(master=app.master, value="")
    app.starting_game_dropdown = ttk.Combobox(
        setup,
        textvariable=app.starting_game_var,
        values=app.game_numbers,
        state="readonly",
        width=8,
        style="UWH.TCombobox",
    )
    app.starting_game_dropdown.grid(
        row=3, column=1, sticky="w", padx=8, pady=8
    )
    app.starting_game_dropdown.bind(
        "<<ComboboxSelected>>", app.on_game_selection_changed
    )

    ui_theme.body_label(setup, "This court uses numbers").grid(
        row=4, column=0, sticky="w", pady=8
    )
    app.court_game_mode_dropdown = ttk.Combobox(
        setup,
        textvariable=app.court_game_mode_var,
        values=("even", "odd", "consecutive"),
        state="readonly",
        width=16,
        style="UWH.TCombobox",
    )
    app.court_game_mode_dropdown.grid(
        row=4, column=1, sticky="w", padx=8, pady=8
    )
    app.court_game_mode_dropdown.bind(
        "<<ComboboxSelected>>", app.on_court_game_mode_changed
    )
    ui_theme.muted_label(
        setup,
        "Choose even, odd or consecutive draw game numbers for this court.",
        wraplength=460,
        justify="left",
    ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))

    ui_theme.section_title(results, "Tournament Results", symbol="✓").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 12)
    )
    sync_settings = app.load_unified_settings().get("tournamentSync", {})

    ui_theme.body_label(results, "Tournament Results").grid(
        row=1, column=0, sticky="w", pady=6
    )
    app.tournament_results_var = tk.StringVar(
        master=app.master, value="No results file"
    )
    app.tournament_results_dropdown = ttk.Combobox(
        results,
        textvariable=app.tournament_results_var,
        values=(),
        state="readonly",
        style="UWH.TCombobox",
    )
    app.tournament_results_dropdown.grid(
        row=1, column=1, sticky="ew", padx=8, pady=6
    )
    ui_theme.secondary_button(
        results, "Results Folder", app.open_csv_folder
    ).grid(row=1, column=2, sticky="e", pady=6)

    app.tournament_sync_mode_var = tk.StringVar(
        master=app.master,
        value=sync_settings.get("mode", "Local only"),
    )
    ui_theme.body_label(results, "Results sync").grid(
        row=2, column=0, sticky="w", pady=6
    )
    ttk.Combobox(
        results,
        textvariable=app.tournament_sync_mode_var,
        values=("Local only", "Shared server"),
        state="readonly",
        style="UWH.TCombobox",
    ).grid(row=2, column=1, columnspan=2, sticky="ew", padx=8, pady=6)

    app.tournament_sync_url_var = tk.StringVar(
        master=app.master,
        value=sync_settings.get("server_url", ""),
    )
    ui_theme.body_label(results, "Server URL").grid(
        row=3, column=0, sticky="w", pady=6
    )
    ttk.Entry(
        results,
        textvariable=app.tournament_sync_url_var,
        style="UWH.TEntry",
    ).grid(row=3, column=1, columnspan=2, sticky="ew", padx=8, pady=6)

    app.tournament_sync_token_var = tk.StringVar(
        master=app.master,
        value=sync_settings.get("token", ""),
    )
    ui_theme.body_label(results, "Access token").grid(
        row=4, column=0, sticky="w", pady=6
    )
    ttk.Entry(
        results,
        textvariable=app.tournament_sync_token_var,
        show="*",
        style="UWH.TEntry",
    ).grid(row=4, column=1, columnspan=2, sticky="ew", padx=8, pady=6)

    action_row = tk.Frame(results, bg=ui_theme.COLORS["surface"])
    action_row.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(14, 6))
    action_row.grid_columnconfigure(1, weight=1)
    ui_theme.primary_button(
        action_row,
        "Save & Sync",
        app.save_tournament_sync_configuration,
    ).grid(row=0, column=0, sticky="w")
    ui_theme.secondary_button(
        action_row,
        "Sync Now",
        app.tournament_sync.wake,
    ).grid(row=0, column=2, sticky="e")

    app.tournament_sync_status_var = tk.StringVar(
        master=app.master,
        value="Local results saved · network sync off",
    )
    status = ui_theme.info_banner(results, "")
    status.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(6, 0))
    # Replace the banner's static label with one bound to the live status.
    for child in status.winfo_children():
        child.destroy()
    tk.Label(
        status,
        textvariable=app.tournament_sync_status_var,
        bg=ui_theme.COLORS["primary_soft"],
        fg=ui_theme.COLORS["primary"],
        font=ui_theme.BODY_FONT,
        anchor="w",
        justify="left",
        wraplength=520,
    ).pack(fill="x")

    ui_theme.section_title(
        info,
        "About Tournament List and Results Sync",
        symbol="ⓘ",
    ).grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )
    ui_theme.body_label(
        info,
        "The selected tournament draw is read-only. Completed games are "
        "saved locally first in a separate _Results.csv file. Shared-server "
        "sync then sends one completed game at a time and retries every "
        "10 seconds if the server is unavailable.\n\n"
        "Expected CSV headers: date,#,White,WScore,Black,BScore,Referees,"
        "Penalties,Comments\n"
        "(# is the game number; use quotes around team names containing commas)",
        justify="left",
        wraplength=1120,
    ).grid(row=1, column=0, sticky="w")

    # Initialise draw/result controls immediately; network sync remains
    # background-only and never blocks selecting or finishing a match.
    app.on_csv_file_changed()
    app.on_use_tournament_list_changed()



def create_about_tab(app, readme_path):
    """Create the approved v1.3 About tab and its documentation links."""
    tab = ttk.Frame(app.notebook, style="UWH.Tab.TFrame")
    app.about_tab = tab
    app.notebook.add(
        tab,
        text=ui_theme.tab_label("About"),
    )
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(1, weight=1)

    hero = ui_theme.card(tab, padding=18)
    hero.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
    hero.grid_columnconfigure(1, weight=1)

    icon = getattr(app.master, "_uwh_app_icon", None)
    if icon is not None:
        tk.Label(
            hero,
            image=icon,
            bg=ui_theme.COLORS["surface"],
        ).grid(row=0, column=0, rowspan=4, sticky="nw", padx=(0, 18))

    tk.Label(
        hero,
        text="Underwater Hockey\nGame Management App",
        bg=ui_theme.COLORS["surface"],
        fg=ui_theme.COLORS["navy"],
        font=(ui_theme.FONT_FAMILY, 22, "bold"),
        justify="left",
        anchor="w",
    ).grid(row=0, column=1, sticky="w")

    tk.Label(
        hero,
        text=f"Version {APP_VERSION}",
        bg=ui_theme.COLORS["primary"],
        fg="white",
        font=(ui_theme.FONT_FAMILY, 10, "bold"),
        padx=12,
        pady=4,
    ).grid(row=1, column=1, sticky="w", pady=(8, 6))

    tk.Label(
        hero,
        text="A tool for sirens, scoring, penalties and happier players",
        bg=ui_theme.COLORS["surface"],
        fg=ui_theme.COLORS["primary"],
        font=(ui_theme.FONT_FAMILY, 12, "bold"),
        anchor="w",
    ).grid(row=2, column=1, sticky="w", pady=(2, 4))

    ui_theme.muted_label(
        hero,
        "The hero area deliberately uses the UWH logo only; a real "
        "underwater-hockey photograph can be added later without changing "
        "the About-tab layout.",
        wraplength=820,
        justify="left",
    ).grid(row=3, column=1, sticky="w", pady=(4, 0))

    body = ttk.Frame(tab, style="UWH.Tab.TFrame")
    body.grid(row=2, column=0, sticky="nsew", padx=12, pady=(6, 12))
    body.grid_columnconfigure(0, weight=1)
    body.grid_columnconfigure(1, weight=1)
    body.grid_rowconfigure(0, weight=1)

    project = ui_theme.card(body, padding=16)
    project.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    ui_theme.section_title(project, "About This Project", symbol="ⓘ").pack(
        anchor="w", pady=(0, 10)
    )

    about_text = (
        "This app was started in Google AI, made workable by GitHub Copilot "
        "and extensively refactored, tweaked, improved, expanded and tested "
        "by ChatGPT. Conducted by David Stirling (who can't write code).\n\n"
        "The conductor seems to be the star of the show, even though they do "
        "not make any noise. They even get to come on to the stage all on "
        "their own, to rapturous applause."
    )
    ui_theme.body_label(
        project,
        about_text,
        justify="left",
        wraplength=540,
    ).pack(anchor="w", fill="x")

    credits = (
        ("Initial concept and ideas", "Google AI"),
        ("Made workable", "GitHub Copilot"),
        ("Refactoring, improvements, testing and expansion", "ChatGPT"),
        ("Conducted by", "David Stirling (who cannot write code)"),
    )
    credits_frame = tk.Frame(project, bg=ui_theme.COLORS["surface"])
    credits_frame.pack(fill="x", pady=(18, 0))
    credits_frame.grid_columnconfigure(0, weight=1)
    credits_frame.grid_columnconfigure(1, weight=1)
    for row, (role, name) in enumerate(credits):
        ui_theme.muted_label(credits_frame, role).grid(
            row=row, column=0, sticky="w", pady=4
        )
        tk.Label(
            credits_frame,
            text=name,
            bg=ui_theme.COLORS["surface"],
            fg=ui_theme.COLORS["navy"],
            font=(ui_theme.FONT_FAMILY, 10, "bold"),
            anchor="w",
        ).grid(row=row, column=1, sticky="w", pady=4)

    links = ui_theme.card(body, padding=16)
    links.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    ui_theme.section_title(links, "Links & Contact", symbol="↗").pack(
        anchor="w", pady=(0, 10)
    )

    def open_readme():
        readme = Path(readme_path)
        if not readme.exists():
            messagebox.showerror(
                "README not found",
                f"The README file could not be found:\n{readme}",
            )
            return
        webbrowser.open(readme.resolve().as_uri())

    repository_url = (
        "https://github.com/davidstirling777-star/"
        "Underwater-Hockey-Scoring-Desk-Kit"
    )

    def link_card(title, detail, command):
        frame = tk.Frame(
            links,
            bg=ui_theme.COLORS["surface_alt"],
            highlightbackground=ui_theme.COLORS["border"],
            highlightthickness=1,
            padx=14,
            pady=12,
            cursor="hand2",
        )
        tk.Label(
            frame,
            text=title,
            bg=ui_theme.COLORS["surface_alt"],
            fg=ui_theme.COLORS["primary"],
            font=(ui_theme.FONT_FAMILY, 11, "bold"),
            anchor="w",
            cursor="hand2",
        ).pack(anchor="w")
        tk.Label(
            frame,
            text=detail,
            bg=ui_theme.COLORS["surface_alt"],
            fg=ui_theme.COLORS["text"],
            font=ui_theme.BODY_FONT,
            justify="left",
            anchor="w",
            wraplength=500,
            cursor="hand2",
        ).pack(anchor="w", pady=(4, 0))
        for widget in (frame, *frame.winfo_children()):
            widget.bind("<Button-1>", lambda _event, fn=command: fn())
        return frame

    link_card(
        "View README",
        "Open the local README file for full setup and usage information.",
        open_readme,
    ).pack(fill="x", pady=(0, 10))

    link_card(
        "GitHub Repository",
        repository_url,
        lambda: webbrowser.open(repository_url),
    ).pack(fill="x", pady=10)

    link_card(
        "Contact",
        "davidstirling777@gmail.com",
        lambda: webbrowser.open("mailto:davidstirling777@gmail.com"),
    ).pack(fill="x", pady=10)



def create_screen_tab(app):
    """Create the approved Screens tab without a layout-preview panel."""
    tab = ttk.Frame(app.notebook, style="UWH.Tab.TFrame")
    app.screen_tab = tab
    app.notebook.add(
        tab,
        text=ui_theme.tab_label("Screens"),
    )
    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(2, weight=1)

    header = ui_theme.page_header(
        tab,
        "Screens",
        "Choose operator/player layouts and verify the displays detected by the computer.",
        symbol="▱",
    )
    header.grid(
        row=0,
        column=0,
        sticky="ew",
        padx=12,
        pady=(12, 6),
    )

    toolbar = ui_theme.card(tab, padding=10)
    toolbar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
    toolbar.grid_columnconfigure(3, weight=1)

    ui_theme.primary_button(
        toolbar, "Auto Detect Screens", app.auto_detect_screens
    ).grid(row=0, column=0, padx=(0, 8))
    ui_theme.secondary_button(
        toolbar, "Test Displays", app.test_displays
    ).grid(row=0, column=1, padx=(0, 8))

    app.detected_screens_var = tk.StringVar(
        value=app.get_detected_screens_text()
    )
    status = tk.Label(
        toolbar,
        textvariable=app.detected_screens_var,
        bg=ui_theme.COLORS["primary_soft"],
        fg=ui_theme.COLORS["primary"],
        font=ui_theme.SMALL_FONT,
        justify="left",
        anchor="w",
        padx=10,
        pady=6,
    )
    status.grid(row=0, column=3, sticky="ew", padx=(12, 0))

    body = ttk.Frame(tab, style="UWH.Tab.TFrame")
    body.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))
    body.grid_columnconfigure(0, weight=1)
    body.grid_columnconfigure(1, weight=1)
    body.grid_rowconfigure(0, weight=1)

    options = ui_theme.card(body, padding=14)
    options.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
    options.grid_columnconfigure(0, weight=1)

    ui_theme.section_title(
        options,
        "Display Screen Options",
        symbol="▣",
    ).grid(
        row=0, column=0, sticky="w", pady=(0, 10)
    )

    app.operator_standard_check_var = tk.BooleanVar(
        value=app.operator_layout_var.get() == "Standard"
    )
    app.operator_widescreen_check_var = tk.BooleanVar(
        value=app.operator_layout_var.get() == "Widescreen"
    )

    def choose_operator(value):
        app.operator_layout_var.set(value)
        app.operator_standard_check_var.set(value == "Standard")
        app.operator_widescreen_check_var.set(value == "Widescreen")
        app.apply_screen_configuration()

    operator_box = tk.Frame(options, bg=ui_theme.COLORS["surface"])
    operator_box.grid(row=1, column=0, sticky="ew", pady=(0, 12))
    tk.Label(
        operator_box,
        text="Operator Screen",
        bg=ui_theme.COLORS["surface"],
        fg=ui_theme.COLORS["navy"],
        font=(ui_theme.FONT_FAMILY, 10, "bold"),
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

    ui_theme.radio_button(
        operator_box,
        text="Standard (16:9)",
        variable=app.operator_layout_var,
        value="Standard",
        command=lambda: choose_operator("Standard"),
    ).grid(row=1, column=0, sticky="w", padx=(0, 16), pady=4)
    ui_theme.radio_button(
        operator_box,
        text="Widescreen (21:9)",
        variable=app.operator_layout_var,
        value="Widescreen",
        command=lambda: choose_operator("Widescreen"),
    ).grid(row=1, column=1, sticky="w", pady=4)

    display_options = [
        "Single Standard",
        "Single Widescreen",
        "Dual Standard",
        "Dual Widescreen",
    ]
    descriptions = {
        "Single Standard": "One complete 16:9 scoreboard on one external display.",
        "Single Widescreen": "One complete scoreboard sized for one 21:9 external display.",
        "Dual Standard": "Two identical complete scoreboards on two 16:9 external displays.",
        "Dual Widescreen": "Two identical complete scoreboards on two 21:9 external displays.",
    }

    app.display_layout_check_vars = {
        option: tk.BooleanVar(
            value=(
                app.show_display_screen_var.get()
                and app.display_layout_var.get() == option
            )
        )
        for option in display_options
    }

    def choose_display(value):
        enabled = app.display_layout_check_vars[value].get()
        app.show_display_screen_var.set(enabled)
        if enabled:
            app.display_layout_var.set(value)
        for option, variable in app.display_layout_check_vars.items():
            variable.set(
                enabled and option == app.display_layout_var.get()
            )
        app.apply_screen_configuration()

    tk.Label(
        options,
        text="Player / spectator display",
        bg=ui_theme.COLORS["surface"],
        fg=ui_theme.COLORS["navy"],
        font=(ui_theme.FONT_FAMILY, 10, "bold"),
    ).grid(row=2, column=0, sticky="w", pady=(2, 6))

    for index, option in enumerate(display_options, start=3):
        row = tk.Frame(
            options,
            bg=ui_theme.COLORS["surface_alt"],
            highlightbackground=ui_theme.COLORS["border"],
            highlightthickness=1,
            padx=10,
            pady=8,
        )
        row.grid(row=index, column=0, sticky="ew", pady=3)
        row.grid_columnconfigure(1, weight=1)
        ui_theme.toggle_switch(
            row,
            app.display_layout_check_vars[option],
            command=lambda value=option: choose_display(value),
            text=option,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            row,
            text=descriptions[option],
            bg=ui_theme.COLORS["surface_alt"],
            fg=ui_theme.COLORS["muted"],
            font=ui_theme.SMALL_FONT,
            anchor="w",
            justify="left",
        ).grid(row=0, column=1, sticky="w", padx=(14, 0))

    ui_theme.toggle_switch(
        options,
        app.show_display_team_names_var,
        command=lambda: (
            app.toggle_display_team_names(),
            app.save_screen_settings(),
        ),
        text="Show team names",
    ).grid(row=7, column=0, sticky="w", pady=(12, 0))

    detected = ui_theme.card(body, padding=14)
    detected.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
    detected.grid_columnconfigure(0, weight=1)
    detected.grid_rowconfigure(2, weight=1)

    ui_theme.section_title(
        detected,
        "Detected Displays",
        symbol="●",
    ).grid(
        row=0, column=0, sticky="w", pady=(0, 8)
    )
    ui_theme.muted_label(
        detected,
        "Auto Detect Screens updates the list below. Test Displays labels "
        "each physical screen for eight seconds.",
        wraplength=520,
        justify="left",
    ).grid(row=1, column=0, sticky="w", pady=(0, 10))

    output = tk.Text(
        detected,
        wrap="word",
        state="normal",
        bg=ui_theme.COLORS["surface_alt"],
        fg=ui_theme.COLORS["text"],
        font=("Consolas", 10),
        relief="flat",
        padx=10,
        pady=10,
    )
    output.grid(row=2, column=0, sticky="nsew")
    output.insert("1.0", app.detected_screens_var.get())
    output.config(state="disabled")
    app.detected_screens_output = output

    def refresh_output(*_args):
        try:
            output.config(state="normal")
            output.delete("1.0", "end")
            output.insert("1.0", app.detected_screens_var.get())
            output.config(state="disabled")
        except tk.TclError:
            pass

    app.detected_screens_var.trace_add("write", refresh_output)

    ui_theme.info_banner(
        detected,
        "Windows uses the native monitor list. Raspberry Pi OS "
        "Bookworm/X11 uses xrandr. If automatic detection is unavailable, "
        "select the required display layout manually."
    ).grid(row=3, column=0, sticky="ew", pady=(10, 0))

