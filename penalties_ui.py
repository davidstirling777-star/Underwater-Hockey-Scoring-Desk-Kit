import tkinter as tk
from tkinter import ttk, messagebox


def show_penalties(app, trigger_button=None):
    """Show the penalties dialog window."""
    penalty_width = 250
    penalty_height = 450
    gap = 8

    penalty_window = tk.Toplevel(app.master)
    penalty_window.withdraw()
    penalty_window.title("Penalties")
    penalty_window.resizable(False, False)
    penalty_window.transient(app.master)

    button_frame = ttk.Frame(penalty_window, padding="10")
    button_frame.pack(side="top", fill="x")

    selected_team = tk.StringVar(value="")

    def select_team(team):
        selected_team.set(team)

        button_white.config(
            relief=tk.SUNKEN if team == "White" else tk.RAISED
        )
        button_black.config(
            relief=tk.SUNKEN if team == "Black" else tk.RAISED
        )

    button_white = tk.Button(
        button_frame,
        text="White",
        width=10,
        command=lambda: select_team("White")
    )
    button_white.pack(side="left", padx=5, expand=True)

    button_black = tk.Button(
        button_frame,
        text="Black",
        width=10,
        command=lambda: select_team("Black")
    )
    button_black.pack(side="left", padx=5, expand=True)

    numbers = list(range(1, 16))
    dropdown_options = ["Pick Cap Number"] + numbers
    dropdown_variable = tk.StringVar(value=dropdown_options[0])

    dropdown = ttk.Combobox(
        penalty_window,
        textvariable=dropdown_variable,
        values=dropdown_options,
        state="readonly",
        height=16
    )
    dropdown.pack(pady=10)

    radio_frame = ttk.Frame(penalty_window)
    radio_frame.pack(side="top", anchor="w", pady=10, fill="both")

    no_duration_selected = "__none__"
    radio_variable = tk.StringVar(value=no_duration_selected)

    tk.Radiobutton(
        radio_frame,
        text="1 minute",
        variable=radio_variable,
        value="1 minute",
        tristatevalue="__tristate__"
    ).pack(anchor="w")

    tk.Radiobutton(
        radio_frame,
        text="2 minutes",
        variable=radio_variable,
        value="2 minutes",
        tristatevalue="__tristate__"
    ).pack(anchor="w")

    tk.Radiobutton(
        radio_frame,
        text="5 minutes",
        variable=radio_variable,
        value="5 minutes",
        tristatevalue="__tristate__"
    ).pack(anchor="w")

    tk.Radiobutton(
        radio_frame,
        text="Rest of the match",
        variable=radio_variable,
        value="Rest of the match",
        tristatevalue="__tristate__"
    ).pack(anchor="w")

    summary_frame = ttk.Frame(penalty_window)
    summary_frame.pack(side="top", fill="both", expand=True)

    ttk.Label(
        summary_frame,
        text="Stored Penalties (max 6):"
    ).pack(anchor="w")

    penalty_listbox = tk.Listbox(
        summary_frame,
        height=6,
        exportselection=0
    )
    penalty_listbox.pack(fill="both", expand=True)

    def refresh_penalty_listbox():
        selection = penalty_listbox.curselection()
        selected_index = selection[0] if selection else None

        penalty_listbox.delete(0, tk.END)

        for penalty in app.engine.active_penalties:
            if penalty["is_rest_of_match"]:
                time_str = "REST OF MATCH"
            else:
                mins, secs = divmod(penalty["seconds_remaining"], 60)
                time_str = f"{int(mins):02d}:{int(secs):02d}"

            penalty_listbox.insert(
                tk.END,
                f"{penalty['team']} #{penalty['cap']} {time_str}"
            )

        for penalty in app.engine.stored_penalties:
            already_active = any(
                active_penalty["team"] == penalty["team"]
                and active_penalty["cap"] == penalty["cap"]
                and active_penalty["duration"] == penalty["duration"]
                for active_penalty in app.engine.active_penalties
            )

            if not already_active:
                penalty_listbox.insert(
                    tk.END,
                    f"{penalty['team']} #{penalty['cap']} {penalty['duration']}"
                )

        if selected_index is not None and penalty_listbox.size() > selected_index:
            penalty_listbox.selection_set(selected_index)
            penalty_listbox.activate(selected_index)
        else:
            penalty_listbox.selection_clear(0, tk.END)

    refresh_penalty_listbox()

    def periodic_refresh():
        try:
            if penalty_window.winfo_exists():
                refresh_penalty_listbox()
                penalty_window.after(1000, periodic_refresh)
        except tk.TclError:
            pass

    penalty_window.after(1000, periodic_refresh)

    def start_penalty():
        team = selected_team.get()
        cap = dropdown_variable.get()
        duration = radio_variable.get()

        if team not in ["White", "Black"]:
            messagebox.showerror("Error", "Choose White or Black team.")
            return

        if cap == "Pick Cap Number":
            messagebox.showerror("Error", "Choose a cap number.")
            return

        if duration == no_duration_selected:
            messagebox.showerror("Error", "Choose a penalty duration.")
            return

        if len(app.engine.stored_penalties) >= 6:
            messagebox.showerror(
                "Error",
                "Maximum 6 penalties can be stored."
            )
            return

        if app.start_penalty_timer(team, cap, duration):
            refresh_penalty_listbox()
            selected_team.set("")
            select_team("")
            dropdown_variable.set(dropdown_options[0])
            radio_variable.set(no_duration_selected)
        else:
            messagebox.showerror(
                "Error",
                "Failed to start penalty timer."
            )

    def remove_selected_penalty():
        selection = penalty_listbox.curselection()

        if not selection:
            messagebox.showerror(
                "Error",
                "Please select a penalty to remove."
            )
            return

        index = selection[0]
        active_count = len(app.engine.active_penalties)

        if index < active_count:
            app.remove_penalty(app.engine.active_penalties[index])
            refresh_penalty_listbox()
            return

        stored_index = index - active_count

        if 0 <= stored_index < len(app.engine.stored_penalties):
            app.engine.stored_penalties.pop(stored_index)
            refresh_penalty_listbox()

    start_button_frame = ttk.Frame(penalty_window)
    start_button_frame.pack(side="bottom", fill="x", pady=10)

    button_container = ttk.Frame(start_button_frame)
    button_container.pack(expand=True, fill="x")

    ttk.Button(
        button_container,
        text="Start Penalty",
        command=start_penalty
    ).pack(
        side="left",
        expand=True,
        fill="x",
        padx=(0, 5)
    )

    ttk.Button(
        button_container,
        text="Remove Selected",
        command=remove_selected_penalty
    ).pack(
        side="right",
        expand=True,
        fill="x",
        padx=(5, 0)
    )

    def on_close():
        penalty_window.destroy()

    ttk.Button(
        start_button_frame,
        text="Close",
        command=on_close
    ).pack(
        side="bottom",
        fill="x",
        padx=10,
        pady=(0, 10)
    )

    penalty_window.protocol("WM_DELETE_WINDOW", on_close)

    penalty_window.update_idletasks()

    if trigger_button:
        button_x = trigger_button.winfo_rootx()
        button_y = trigger_button.winfo_rooty()
        button_width = trigger_button.winfo_width()

        popup_x = button_x + (button_width // 2) - (penalty_width // 2)
        popup_y = button_y - penalty_height - gap
    else:
        popup_x = app.master.winfo_rootx() + 100
        popup_y = app.master.winfo_rooty() + 100

    penalty_window.geometry(
        f"{penalty_width}x{penalty_height}+{popup_x}+{popup_y}"
    )

    penalty_window.deiconify()
    penalty_window.lift()
    penalty_window.focus_force()
    penalty_window.grab_set()
