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
    """Create the compact v1.3 Game Variables, presets and sequence tab."""
    tab = ttk.Frame(app.notebook, style="UWH.Tab.TFrame")
    app.notebook.add(tab, text="Game Variables")
    tab.grid_columnconfigure(0, weight=5)
    tab.grid_columnconfigure(1, weight=3)
    tab.grid_rowconfigure(0, weight=1)

    left = ttk.Frame(tab, style="UWH.Tab.TFrame")
    left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
    left.grid_columnconfigure(0, weight=1)
    left.grid_rowconfigure(0, weight=1)

    right = ttk.Frame(tab, style="UWH.Tab.TFrame")
    right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
    right.grid_columnconfigure(0, weight=1)
    right.grid_rowconfigure(0, weight=3)
    right.grid_rowconfigure(1, weight=2)

    # ------------------------------------------------------------------
    # Real Game Variables card.  Every row is backed by app.variables;
    # there are no display-only or invented timing controls here.
    # ------------------------------------------------------------------
    variables_card = ui_theme.card(left, padding=10)
    variables_card.grid(row=0, column=0, sticky="nsew")
    variables_card.grid_columnconfigure(0, weight=3)
    variables_card.grid_columnconfigure(1, weight=0, minsize=58)
    variables_card.grid_columnconfigure(2, weight=0, minsize=112)
    variables_card.grid_columnconfigure(3, weight=1, minsize=88)

    ui_theme.section_title(variables_card, "Game Variables").grid(
        row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
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
            padx=8,
            pady=6,
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
            padx=8,
            pady=4,
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
        frame = tk.Frame(variables_card, bg=ui_theme.COLORS["surface"])
        frame.grid(row=row, column=1, sticky="nsew")
        cb = ttk.Checkbutton(
            frame,
            variable=variable,
            style="UWH.TCheckbutton",
        )
        cb.pack(expand=True)
        return cb

    def entry_cell(row):
        entry = ttk.Entry(
            variables_card,
            width=10,
            style="UWH.TEntry",
            justify="center",
        )
        entry.grid(row=row, column=2, sticky="ew", padx=6, pady=3)
        return entry

    def bind_standard_entry(entry, var_name):
        entry.bind(
            "<FocusOut>",
            lambda _event, name=var_name: app._on_single_variable_change(name)
        )
        entry.bind(
            "<Return>",
            lambda _event, name=var_name: app._on_single_variable_change(name)
        )

    def bind_clock_entry(entry):
        def validate(event):
            value = event.widget.get().strip()
            if value == "":
                app._on_single_variable_change("time_to_start_first_game")
                return

            normalized = value.replace(".", ":")
            if not re.fullmatch(r"(?:[01]?[0-9]|2[0-3]):[0-5][0-9]", normalized):
                messagebox.showerror(
                    "Input Error",
                    "Please enter a 24-hour time as H.MM, HH.MM, H:MM or HH:MM "
                    "(for example 9.36, 09.36, 9:36 or 09:36)."
                )
                event.widget.focus_set()
                event.widget.selection_range(0, tk.END)
                return

            # Keep the v1.3 display convention (HH.mm) while remaining
            # backwards-compatible with colon-form settings.
            hh, mm = normalized.split(":")
            event.widget.delete(0, tk.END)
            event.widget.insert(0, f"{int(hh):02d}.{mm}")
            app._on_single_variable_change("time_to_start_first_game")

        entry.bind("<FocusOut>", validate)
        entry.bind("<Return>", validate)

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
                    0, app.last_valid_values.get(field_name, "1")
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
                                item["entry"].get().strip().replace(",", ".")
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
                        "Crib time too large. Between Game Break minus Crib "
                        "time must be more than 31 seconds."
                    )
                    event.widget.delete(0, tk.END)
                    event.widget.insert(
                        0, app.last_valid_values.get(field_name, "60")
                    )
                    event.widget.focus_set()
                    event.widget.selection_range(0, tk.END)
                    return

            app.last_valid_values[field_name] = value
            app._on_single_variable_change(field_name)

        entry.bind("<FocusOut>", validate)
        entry.bind("<Return>", validate)

    # Render in the actual runtime order. Team Time-Out permission and period
    # intentionally share one visual row, but remain two separate saved keys.
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
            info.get("label", f"{var_name.replace('_', ' ').title()}:")
        )

        # Entries are created for all numeric/time variables.
        entry = None
        if var_name not in ("overtime_allowed", "record_scorers_cap_number"):
            entry = entry_cell(row)
            entry.insert(0, "" if var_name == "time_to_start_first_game" else "1")
            unit_label(row, info.get("unit", ""))

            if var_name == "time_to_start_first_game":
                bind_clock_entry(entry)
            elif var_name in ("crib_time", "sudden_death_game_break"):
                bind_guarded_numeric(entry, var_name)
            else:
                bind_standard_entry(entry, var_name)
            app.last_valid_values[var_name] = entry.get()

        if var_name == "team_timeout_period":
            # One line in the new UI: the enable switch belongs to
            # team_timeouts_allowed; the value belongs to team_timeout_period.
            checkbox_cell(row, app.team_timeouts_allowed_var)
            app.team_timeouts_allowed_var.trace_add(
                "write", lambda *_args: app._on_team_timeouts_change()
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
            checkbox_cell(row, app.overtime_allowed_var)
            app.overtime_allowed_var.trace_add(
                "write", lambda *_args: app._on_overtime_change()
            )
            app.widgets.append({
                "name": var_name,
                "entry": None,
                "checkbox": app.overtime_allowed_var,
                "label_widget": label,
            })

        elif var_name == "record_scorers_cap_number":
            checkbox_cell(row, app.record_scorers_cap_number_var)
            app.record_scorers_cap_number_var.trace_add(
                "write",
                lambda *_args: app._on_single_variable_change(
                    "record_scorers_cap_number"
                )
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
                    app._on_single_variable_change(name)
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

    # Actual Crib-Time guidance is kept below the table rather than beside
    # individual variables, avoiding the invented inline help from mockups.
    crib_note = ui_theme.info_banner(
        variables_card,
        "Crib Time is subtracted from Between Game Break to help realign "
        "Court Time with local computer time. Decimal values such as 1.5 "
        "are accepted. After changing Game Variables, press Reset Timer."
    )
    crib_note.grid(
        row=row, column=0, columnspan=4, sticky="ew", pady=(8, 6)
    )
    row += 1

    controls = tk.Frame(variables_card, bg=ui_theme.COLORS["surface"])
    controls.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(2, 0))
    controls.grid_columnconfigure(1, weight=1)

    app.reset_timer_button = ui_theme.primary_button(
        controls, "Reset Timer", app.reset_timer
    )
    app.reset_timer_button.grid(row=0, column=0, sticky="w")

    tk.Label(
        controls,
        text=f"UWH v{APP_VERSION}",
        bg=ui_theme.COLORS["surface"],
        fg=ui_theme.COLORS["muted"],
        font=ui_theme.SMALL_FONT,
    ).grid(row=0, column=2, sticky="e")

    # ------------------------------------------------------------------
    # Presets: nine real editable slots, sourced from settings.json.
    # ------------------------------------------------------------------
    presets_card = ui_theme.card(right, padding=10)
    presets_card.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
    presets_card.grid_columnconfigure(0, weight=1)
    presets_card.grid_columnconfigure(1, weight=1)
    presets_card.grid_columnconfigure(2, weight=1)

    ui_theme.section_title(presets_card, "Presets").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
    )

    app.widget2_buttons = []
    preset_data = app.load_preset_settings()
    app.button_data = preset_data.copy()

    for index in range(9):
        btn = ui_theme.secondary_button(
            presets_card,
            app.button_data[index]["text"],
            lambda: None,
        )
        btn.configure(font=(ui_theme.FONT_FAMILY, 10, "bold"))
        btn.grid(
            row=1 + (index // 3),
            column=index % 3,
            sticky="nsew",
            padx=4,
            pady=4,
        )
        btn.bind("<ButtonPress-1>", app._make_press_handler(index))
        btn.bind("<ButtonRelease-1>", app._make_release_handler(index))
        app.widget2_buttons.append(btn)

    ui_theme.muted_label(
        presets_card,
        "Click to load a preset. Press and hold for 3 seconds to edit it.",
        justify="left",
    ).grid(
        row=4, column=0, columnspan=3, sticky="w", padx=4, pady=(8, 0)
    )

    # ------------------------------------------------------------------
    # Game Sequence: text is the existing real application sequence only.
    # ------------------------------------------------------------------
    sequence_card = ui_theme.card(right, padding=10)
    sequence_card.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
    sequence_card.grid_columnconfigure(0, weight=1)
    sequence_card.grid_rowconfigure(1, weight=1)

    ui_theme.section_title(sequence_card, "Game Sequence").grid(
        row=0, column=0, sticky="w", pady=(0, 6)
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
        "• 'First Game Starts In:' transitions directly to First Half\n"
        "• Crib time is subtracted from Between Game Break"
    )

    sequence_text = tk.Text(
        sequence_card,
        wrap="word",
        height=13,
        bg=ui_theme.COLORS["surface_alt"],
        fg=ui_theme.COLORS["text"],
        font=ui_theme.BODY_FONT,
        relief="flat",
        padx=8,
        pady=8,
    )
    sequence_text.grid(row=1, column=0, sticky="nsew")
    sequence_text.insert("1.0", explanation_text)
    sequence_text.config(state="disabled")

    exit_row = tk.Frame(sequence_card, bg=ui_theme.COLORS["surface"])
    exit_row.grid(row=2, column=0, sticky="e", pady=(8, 0))
    app.exit_program_button = ui_theme.danger_button(
        exit_row, "Exit Program", app.request_exit, width=14
    )
    app.exit_program_button.pack()

    app.update_overtime_variables_state()



def create_tournament_tab(app):
    """Create the standalone Tournament List and results-sync tab."""
    tab = ttk.Frame(app.notebook)
    app.tournament_tab = tab
    app.notebook.add(tab, text="Tournament List")

    tab.grid_rowconfigure(0, weight=1)
    tab.grid_columnconfigure(0, weight=1)

    default_font = font.nametofont("TkDefaultFont")
    new_size = default_font.cget("size") + 2
    small_size = default_font.cget("size") - 1

    # ------------------------------------------------------------
    # Tournament List controls
    # ------------------------------------------------------------
    widget4 = ttk.Frame(tab, borderwidth=1, relief="solid")
    widget4.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

    widget4.grid_columnconfigure(0, weight=0)
    widget4.grid_columnconfigure(1, weight=1)
    widget4.grid_columnconfigure(2, weight=0)
    widget4.grid_columnconfigure(3, weight=0, minsize=55)
    widget4.grid_columnconfigure(4, weight=0)

    widget4.grid_rowconfigure(0, weight=0)
    widget4.grid_rowconfigure(1, weight=0)
    widget4.grid_rowconfigure(2, weight=0)
    widget4.grid_rowconfigure(3, weight=0)
    widget4.grid_rowconfigure(4, weight=0)
    widget4.grid_rowconfigure(8, weight=0)

    tournament_header = tk.Label(
        widget4,
        text="Tournament List",
        font=(default_font.cget("family"), new_size, "bold")
    )
    tournament_header.grid(
        row=0,
        column=0,
        columnspan=5,
        padx=8,
        pady=(10, 8),
        sticky="ew"
    )

    # ------------------------------------------------------------
    # Tournament-list enable/disable control
    # ------------------------------------------------------------
    #
    # This deliberately defaults to True each time the application
    # starts. The checkbox controls whether tournament team names are
    # used, but does not prevent the CSV folder from being opened.
    app.use_tournament_list_var = tk.BooleanVar(
        master=app.master,
        value=True
    )

    use_tournament_list_checkbox = ttk.Checkbutton(
        widget4,
        text="Use Tournament List?",
        variable=app.use_tournament_list_var,
        command=app.on_use_tournament_list_changed
    )
    use_tournament_list_checkbox.grid(
        row=1,
        column=0,
        sticky="w",
        padx=(8, 4),
        pady=2
    )

    # ------------------------------------------------------------
    # Tournament-draw CSV dropdown
    # ------------------------------------------------------------
    csv_files = app.get_csv_files()

    app.csv_var = tk.StringVar(
        master=app.master,
        value=(
            csv_files[0]
            if csv_files
            else "No CSV files found"
        )
    )

    app.csv_dropdown = ttk.Combobox(
        widget4,
        textvariable=app.csv_var,
        values=csv_files,
        state="readonly",
        width=16,
        postcommand=app.refresh_csv_dropdown
    )
    app.csv_dropdown.grid(
        row=1,
        column=1,
        columnspan=3,
        sticky="ew",
        padx=(4, 4),
        pady=2
    )
    app.csv_dropdown.bind(
        "<<ComboboxSelected>>",
        app.on_csv_file_changed
    )

    # ------------------------------------------------------------
    # Open Folder button — promoted to the tournament CSV line
    # ------------------------------------------------------------
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
        row=1,
        column=4,
        sticky="e",
        padx=(4, 8),
        pady=2
    )

    # ------------------------------------------------------------
    # Starting game number
    # ------------------------------------------------------------
    tk.Label(
        widget4,
        text="Starting Game #:",
        font=(
            default_font.cget("family"),
            default_font.cget("size")
        ),
        anchor="w"
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=8,
        pady=(8, 2)
    )

    app.starting_game_var = tk.StringVar(
        master=app.master,
        value=""
    )

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
        padx=(4, 8),
        pady=(8, 2)
    )
    app.starting_game_dropdown.bind(
        "<<ComboboxSelected>>",
        app.on_game_selection_changed
    )

    # ------------------------------------------------------------
    # Court CSV numbering mode
    # ------------------------------------------------------------
    tk.Label(
        widget4,
        text="This court uses numbers:",
        font=(
            default_font.cget("family"),
            default_font.cget("size")
        ),
        anchor="w"
    ).grid(
        row=2,
        column=2,
        sticky="e",
        padx=(16, 4),
        pady=(8, 2)
    )
    app.court_game_mode_dropdown = ttk.Combobox(
        widget4,
        textvariable=app.court_game_mode_var,
        values=(
            "even",
            "odd",
            "consecutive"
        ),
        state="readonly",
        width=12
    )
    app.court_game_mode_dropdown.grid(
        row=2,
        column=3,
        sticky="w",
        padx=(4, 8),
        pady=(8, 2)
    )
    app.court_game_mode_dropdown.bind(
        "<<ComboboxSelected>>",
        app.on_court_game_mode_changed
    )

    # ------------------------------------------------------------
    # Results: local file + optional third-computer synchronisation
    # ------------------------------------------------------------
    # The result filename is derived from the draw. This read-only dropdown
    # intentionally cannot select a different file to overwrite.
    sync_settings = app.load_unified_settings().get("tournamentSync", {})
    app.tournament_results_var = tk.StringVar(
        master=app.master, value="No results file"
    )
    app.tournament_results_dropdown = ttk.Combobox(
        widget4, textvariable=app.tournament_results_var,
        values=(), state="readonly", width=18
    )
    ttk.Label(widget4, text="Tournament Results:").grid(
        row=3, column=0, sticky="w", padx=8, pady=(10, 2)
    )
    app.tournament_results_dropdown.grid(
        row=3, column=1, columnspan=3,
        sticky="ew", padx=4, pady=(10, 2)
    )
    ttk.Button(
        widget4, text="Results Folder", command=app.open_csv_folder
    ).grid(row=3, column=4, sticky="ew", padx=(4, 8), pady=(10, 2))

    app.tournament_sync_mode_var = tk.StringVar(
        master=app.master,
        value=sync_settings.get("mode", "Local only")
    )
    ttk.Label(widget4, text="Results sync:").grid(
        row=4, column=0, sticky="w", padx=8, pady=2
    )
    ttk.Combobox(
        widget4, textvariable=app.tournament_sync_mode_var,
        values=("Local only", "Shared server"),
        state="readonly", width=18
    ).grid(row=4, column=1, columnspan=3, sticky="ew", padx=4, pady=2)

    app.tournament_sync_url_var = tk.StringVar(
        master=app.master,
        value=sync_settings.get("server_url", "")
    )
    ttk.Label(widget4, text="Server URL:").grid(
        row=5, column=0, sticky="w", padx=8, pady=2
    )
    ttk.Entry(
        widget4, textvariable=app.tournament_sync_url_var,
        width=30
    ).grid(row=5, column=1, columnspan=4,
           sticky="ew", padx=(4, 8), pady=2)

    app.tournament_sync_token_var = tk.StringVar(
        master=app.master, value=sync_settings.get("token", "")
    )
    ttk.Label(widget4, text="Access token:").grid(
        row=6, column=0, sticky="w", padx=8, pady=2
    )
    ttk.Entry(
        widget4, textvariable=app.tournament_sync_token_var,
        show="*", width=20
    ).grid(row=6, column=1, columnspan=3,
           sticky="ew", padx=4, pady=2)
    ttk.Button(
        widget4, text="Save & Sync",
        command=app.save_tournament_sync_configuration
    ).grid(row=6, column=4, sticky="ew", padx=(4, 8), pady=2)

    app.tournament_sync_status_var = tk.StringVar(
        master=app.master,
        value="Local results saved · network sync off"
    )
    ttk.Label(
        widget4, textvariable=app.tournament_sync_status_var,
        font=(default_font.cget("family"), small_size),
        wraplength=490, justify="left"
    ).grid(row=7, column=0, columnspan=4,
           sticky="ew", padx=8, pady=(6, 2))
    ttk.Button(
        widget4, text="Sync Now", command=app.tournament_sync.wake
    ).grid(row=7, column=4, sticky="ew", padx=(4, 8), pady=(6, 2))

    # Create/resume results immediately but never make the network a
    # prerequisite for selecting or finishing a match.
    app.on_csv_file_changed()
    app.on_use_tournament_list_changed()

    csv_comment = tk.Label(
        widget4,
        text=(
            "Put tournament draw CSVs in the same folder as this program.\n"
            "The selected draw is read-only; completed games are saved locally "
            "first in a separate _Results.csv file.\n"
            "Shared-server sync sends one completed game at a time and retries "
            "every 10 seconds if the server is unavailable.\n"
            "Expected CSV headers: date,#,White,WScore,Black,BScore,"
            "Referees,Penalties,Comments\n"
            "(# is the game number; use quotes around team names containing commas)"
        ),
        font=(default_font.cget("family"), small_size),
        anchor="nw", justify="left", wraplength=600
    )
    csv_comment.grid(
        row=8, column=0, columnspan=5,
        sticky="nw", padx=8, pady=(6, 4)
    )



def create_about_tab(app, readme_path):
    """Create the About tab with credits and documentation links."""
    tab = ttk.Frame(app.notebook)
    app.about_tab = tab
    app.notebook.add(tab, text="About")

    tab.grid_rowconfigure(0, weight=1)
    tab.grid_columnconfigure(0, weight=1)

    outer = ttk.Frame(tab, padding=24)
    outer.grid(row=0, column=0, sticky="nsew")
    outer.grid_columnconfigure(0, weight=1)

    default_font = font.nametofont("TkDefaultFont")
    title_font = (
        default_font.cget("family"),
        default_font.cget("size") + 5,
        "bold"
    )
    body_font = (
        default_font.cget("family"),
        default_font.cget("size") + 1
    )
    link_font = (
        default_font.cget("family"),
        default_font.cget("size") + 1,
        "underline"
    )

    ttk.Label(
        outer,
        text="About UWH Scoring Desk",
        font=title_font
    ).grid(row=0, column=0, sticky="w", pady=(0, 18))

    ttk.Label(
        outer,
        text=f"Version {APP_VERSION}",
        font=body_font
    ).grid(row=1, column=0, sticky="w", pady=(0, 18))

    about_text = (
        "This app was started in Google AI, made workable by GitHub Copilot "
        "and extensively refactored, tweaked, improved, expanded and tested "
        "by ChatGPT, conducted by David Stirling (who can't write code) "
        "davidstirling777@gmail.com.\n\n"
        "The conductor seems to be the star of the show, even though they do "
        "not make any noise. They even get to come on to the stage all on "
        "their own, to rapturous applause."
    )
    ttk.Label(
        outer,
        text=about_text,
        font=body_font,
        justify="left",
        wraplength=920
    ).grid(row=2, column=0, sticky="w", pady=(0, 20))

    def open_readme():
        path = Path(readme_path)
        if not path.exists():
            messagebox.showerror(
                "README not found",
                f"The README file could not be found:\n{path}"
            )
            return
        webbrowser.open(path.resolve().as_uri())

    readme_link = tk.Label(
        outer,
        text="Open the README file in this installation",
        fg="#0066cc",
        cursor="hand2",
        font=link_font
    )
    readme_link.grid(row=3, column=0, sticky="w", pady=(0, 14))
    readme_link.bind("<Button-1>", lambda event: open_readme())

    ttk.Label(
        outer,
        text="This app can be downloaded free from:",
        font=body_font
    ).grid(row=4, column=0, sticky="w")

    repository_url = (
        "https://github.com/davidstirling777-star/"
        "Underwater-Hockey-Scoring-Desk-Kit"
    )
    repository_link = tk.Label(
        outer,
        text=repository_url,
        fg="#0066cc",
        cursor="hand2",
        font=link_font
    )
    repository_link.grid(row=5, column=0, sticky="w", pady=(4, 14))
    repository_link.bind(
        "<Button-1>",
        lambda event: webbrowser.open(repository_url)
    )

    email_link = tk.Label(
        outer,
        text="davidstirling777@gmail.com",
        fg="#0066cc",
        cursor="hand2",
        font=link_font
    )
    email_link.grid(row=6, column=0, sticky="w")
    email_link.bind(
        "<Button-1>",
        lambda event: webbrowser.open(
            "mailto:davidstirling777@gmail.com"
        )
    )


def create_screen_tab(app):
    """Create the Screens tab and its operator/display layout controls."""
    tab = ttk.Frame(app.notebook)
    app.screen_tab = tab
    app.notebook.add(tab, text="Screens")

    tab.grid_columnconfigure(0, weight=1)
    tab.grid_rowconfigure(0, weight=1)

    outer = ttk.Frame(tab, padding=18)
    outer.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
    outer.grid_columnconfigure(0, weight=1)

    default_font = font.nametofont("TkDefaultFont")
    title_font = (default_font.cget("family"), default_font.cget("size") + 4, "bold")
    label_font = (default_font.cget("family"), default_font.cget("size") + 2, "bold")

    tk.Label(outer, text="Screen Configuration", font=title_font).grid(
        row=0, column=0, sticky="w", pady=(0, 14)
    )

    operator_frame = ttk.LabelFrame(outer, text="Operator Screen", padding=12)
    operator_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
    operator_frame.grid_columnconfigure(0, weight=1)

    display_frame = ttk.LabelFrame(outer, text="Display Screen Options", padding=12)
    display_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
    display_frame.grid_columnconfigure(0, weight=1)

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

    ttk.Checkbutton(
        operator_frame,
        text="Standard (16:9)",
        variable=app.operator_standard_check_var,
        command=lambda: choose_operator("Standard"),
        style="Large.TCheckbutton"
    ).grid(row=0, column=0, sticky="w", pady=5)

    ttk.Checkbutton(
        operator_frame,
        text="Widescreen (21:9)",
        variable=app.operator_widescreen_check_var,
        command=lambda: choose_operator("Widescreen"),
        style="Large.TCheckbutton"
    ).grid(row=1, column=0, sticky="w", pady=5)

    display_options = [
        "Single Standard",
        "Single Widescreen",
        "Dual Standard",
        "Dual Widescreen",
    ]
    app.display_layout_check_vars = {
        option: tk.BooleanVar(
            value=(app.show_display_screen_var.get()
                   and app.display_layout_var.get() == option)
        )
        for option in display_options
    }

    def choose_display(value):
        # Tkinter has already toggled the clicked checkbox at this point.
        # Clicking the selected (ticked) layout again therefore turns it OFF.
        enabled = app.display_layout_check_vars[value].get()
        app.show_display_screen_var.set(enabled)
        if enabled:
            app.display_layout_var.set(value)
        # Keep the previously selected layout when disabled so it can be
        # restored next time without having to reconfigure the display.
        for option, var in app.display_layout_check_vars.items():
            var.set(enabled and option == app.display_layout_var.get())
        app.apply_screen_configuration()

    descriptions = {
        "Single Standard": "One complete 16:9 scoreboard on one external display.",
        "Single Widescreen": "One complete scoreboard sized for one 21:9 external display.",
        "Dual Standard": "Two identical complete scoreboards on two 16:9 external displays.",
        "Dual Widescreen": "Two identical complete scoreboards on two 21:9 external displays.",
    }

    for row, option in enumerate(display_options):
        line = ttk.Frame(display_frame)
        line.grid(row=row, column=0, sticky="ew", pady=4)
        line.grid_columnconfigure(1, weight=1)
        ttk.Checkbutton(
            line,
            text=option,
            variable=app.display_layout_check_vars[option],
            command=lambda value=option: choose_display(value),
            style="Large.TCheckbutton"
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            line,
            text=descriptions[option],
            justify="left",
            anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=(14, 0))

    ttk.Checkbutton(
        outer,
        text="Show Team Names",
        variable=app.show_display_team_names_var,
        command=lambda: (app.toggle_display_team_names(), app.save_screen_settings()),
        style="Large.TCheckbutton"
    ).grid(row=3, column=0, sticky="w", pady=(2, 12))

    button_row = ttk.Frame(outer)
    button_row.grid(row=4, column=0, sticky="w", pady=(4, 10))

    ttk.Button(
        button_row,
        text="Auto Detect Screens",
        command=app.auto_detect_screens
    ).grid(row=0, column=0, sticky="w", padx=(0, 10))

    ttk.Button(
        button_row,
        text="Test Displays",
        command=app.test_displays
    ).grid(row=0, column=1, sticky="w")

    detected_frame = ttk.LabelFrame(outer, text="These screens were detected", padding=12)
    detected_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
    detected_frame.grid_columnconfigure(0, weight=1)

    app.detected_screens_var = tk.StringVar(value=app.get_detected_screens_text())
    tk.Label(
        detected_frame,
        textvariable=app.detected_screens_var,
        justify="left",
        anchor="nw",
        font=("Consolas", default_font.cget("size")),
        wraplength=900,
    ).grid(row=0, column=0, sticky="ew")

    tk.Label(
        outer,
        text=(
            "Auto Detect uses the native Windows monitor list. "
            "On Raspberry Pi OS Bookworm/X11, it uses xrandr. "
            "If automatic detection is unavailable, select the screen layout manually. "
            "Test Displays labels every screen for eight seconds and can be closed "
            "by clicking or pressing Esc."
        ),
        justify="left",
        anchor="nw",
        wraplength=900,
        font=(default_font.cget("family"), default_font.cget("size"))
    ).grid(row=6, column=0, sticky="w", pady=(4, 0))

