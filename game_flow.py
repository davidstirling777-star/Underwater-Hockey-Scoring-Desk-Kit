# game_flow.py

def export_and_reset_game_at_break(app):
    current_game = app.get_current_game_number()
    white_score = app.white_score_var.get()
    black_score = app.black_score_var.get()

    penalties_to_write = list(app.engine.stored_penalties)

    app.log_game_event("Game End")

    app.write_game_results_to_csv(
        current_game,
        white_score,
        black_score,
        penalties_to_write
    )

    app.white_score_var.set(0)
    app.black_score_var.set(0)

    app.engine.stored_penalties.clear()
    app.clear_all_penalties()
    app.engine.clear_goal_scorers()

    app.advance_to_next_game()
    app.update_team_names_display()

def start_sudden_death_timer(app):
    if not app.engine.timer_running:
        return

    app.engine.sudden_death_seconds += 1
    app.update_timer_display()

    app.sudden_death_timer_job = app.master.after(
        1000,
        lambda: start_sudden_death_timer(app)
    )


def stop_sudden_death_timer(app):
    if app.sudden_death_timer_job:
        app.master.after_cancel(app.sudden_death_timer_job)
        app.sudden_death_timer_job = None

def get_current_game_number(app):
    """Return the selected tournament game, or blank after the final game."""
    try:
        selected_game = app.starting_game_var.get()

        if selected_game and selected_game in app.game_numbers:
            return selected_game

        if (
            app.game_numbers
            and 0 <= app.current_game_index < len(app.game_numbers)
        ):
            return app.game_numbers[app.current_game_index]

        # Past the final listed tournament game.
        return ""

    except Exception:
        return ""

def advance_to_next_game(app):
    """
    Advance through the tournament draw.

    After the final listed game, remain in a blank game state rather
    than looping back to Game 1.
    """
    if not app.game_numbers:
        return False

    current_game = app.starting_game_var.get()

    if current_game in app.game_numbers:
        app.current_game_index = app.game_numbers.index(current_game)

    # Final tournament game has been completed.
    if app.current_game_index >= len(app.game_numbers) - 1:
        app.current_game_index = len(app.game_numbers)
        app.starting_game_var.set("")
        app.update_game_number_display()
        return False

    app.current_game_index += 1
    next_game = app.game_numbers[app.current_game_index]

    app.starting_game_var.set(next_game)
    app.update_game_number_display()

    return True

def update_game_number_display(app):
    """Update the main and external Game Number display."""
    current_game = get_current_game_number(app)

    if current_game:
        app.game_number_var.set(f"Game #{current_game}")
    else:
        app.game_number_var.set("")

    app.update_team_names_display()

def on_game_selection_changed(app, event=None):
    """Keep the active game index aligned with manual selection."""
    selected_game = app.starting_game_var.get()

    if selected_game in app.game_numbers:
        app.current_game_index = app.game_numbers.index(
            selected_game
        )

    update_game_number_display(app)

def _game_number_as_int(game_number):
    """Return a whole-number game value, or None when not numeric."""
    try:
        text = str(game_number).strip()
        return int(text)

    except (TypeError, ValueError):
        try:
            numeric_value = float(str(game_number).strip())

            if numeric_value.is_integer():
                return int(numeric_value)

        except (TypeError, ValueError):
            pass

    return None


def _game_number_sort_key(game_number):
    """Sort numeric game numbers in true numeric order."""
    numeric_game_number = _game_number_as_int(game_number)

    if numeric_game_number is not None:
        return (0, numeric_game_number)

    return (1, str(game_number).casefold())


def refresh_game_numbers_for_court(app):
    """
    Build the active game list for this court.

    consecutive = every game in numeric order
    even        = only even-numbered games
    odd         = only odd-numbered games
    """
    mode = app.court_game_mode_var.get().strip().lower()

    if mode not in ("even", "odd", "consecutive"):
        mode = "consecutive"
        app.court_game_mode_var.set(mode)

    all_games = sorted(
        list(getattr(app, "all_game_numbers", [])),
        key=_game_number_sort_key
    )

    if mode == "even":
        allowed_games = [
            game_number
            for game_number in all_games
            if (
                _game_number_as_int(game_number) is not None
                and _game_number_as_int(game_number) % 2 == 0
            )
        ]

    elif mode == "odd":
        allowed_games = [
            game_number
            for game_number in all_games
            if (
                _game_number_as_int(game_number) is not None
                and _game_number_as_int(game_number) % 2 == 1
            )
        ]

    else:
        allowed_games = all_games

    previous_game = app.starting_game_var.get()

    app.game_numbers = allowed_games

    if hasattr(app, "starting_game_dropdown"):
        app.starting_game_dropdown["values"] = app.game_numbers

    if previous_game in app.game_numbers:
        app.current_game_index = app.game_numbers.index(
            previous_game
        )

    elif app.game_numbers:
        app.current_game_index = 0
        app.starting_game_var.set(app.game_numbers[0])

    else:
        app.current_game_index = 0
        app.starting_game_var.set("")

    app.update_game_number_display()


def on_court_game_mode_changed(app, event=None):
    """Reload the starting-game list after changing court mode."""
    refresh_game_numbers_for_court(app)

def on_csv_file_changed(app, event=None):
    """Reload all CSV games, then filter them for this court."""
    csv_file = app.csv_var.get()

    app.all_game_numbers = sorted(
        app.parse_csv_game_numbers(csv_file),
        key=_game_number_sort_key
    )

    refresh_game_numbers_for_court(app)
