"""Tournament progression, game selection, and safe post-game reset.

Export is a gate: do not log Game End, discard scores/penalties, or advance
the game number until the results writer confirms success. Retain the
original game number when an operator changes CSV selection to retry.
"""

# game_flow.py

def export_and_reset_game_at_break(app, game_number=None):
    """Save a completed game before discarding its live scores and penalties.

    False means the tournament CSV was not saved; the caller must leave the
    game intact and offer a retry. A manual game with no selected CSV keeps
    its existing no-export workflow.
    """
    current_game = (app.get_current_game_number()
                    if game_number is None else game_number)
    white_score = app.white_score_var.get()
    black_score = app.black_score_var.get()
    penalties_to_write = list(app.engine.stored_penalties)

    csv_name = str(app.csv_var.get()).strip()
    tournament_list = bool(app.use_tournament_list_var.get())
    needs_export = csv_name not in ("", "No CSV files found") or tournament_list

    if needs_export:
        if csv_name in ("", "No CSV files found") or not str(current_game).strip():
            return False
        # The writer reports False for a missing file, an invalid header,
        # or a game number that was not found. A write error may also raise.
        if not app.write_game_results_to_csv(
            current_game, white_score, black_score, penalties_to_write
        ):
            return False

    # Do not log Game End on a failed attempt: retrying must not duplicate it.
    app.log_game_event("Game End")
    app.white_score_var.set(0)
    app.black_score_var.set(0)
    app.engine.stored_penalties.clear()
    app.clear_all_penalties()
    app.engine.clear_goal_scorers()

    # Sudden Death restoration remains available only during the correction
    # window. Once the completed game has been safely committed, clear it so
    # a later game cannot inherit stale deciding-goal state.
    app.engine.clear_sudden_death_goal()

    # Reselect the completed game if choosing another CSV during recovery
    # altered the tournament dropdown; advance from its original position.
    if current_game in app.game_numbers:
        app.current_game_index = app.game_numbers.index(current_game)
        app.starting_game_var.set(current_game)
    app.advance_to_next_game()
    app.update_team_names_display()
    return True

def start_sudden_death_timer(app):
    """Compatibility wrapper; the Tk application owns the count-up tick."""
    return app.start_sudden_death_timer()


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
