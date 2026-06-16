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
    try:
        selected_game = app.starting_game_var.get()

        if selected_game and selected_game in app.game_numbers:
            return selected_game

        if app.game_numbers and len(app.game_numbers) > app.current_game_index:
            return app.game_numbers[app.current_game_index]

        return "1"

    except Exception:
        return "1"

def advance_to_next_game(app):
    if not app.game_numbers:
        return

    current_game = app.starting_game_var.get()

    if current_game in app.game_numbers:
        app.current_game_index = app.game_numbers.index(current_game)

    app.current_game_index = (
        app.current_game_index + 1
    ) % len(app.game_numbers)

    next_game = app.game_numbers[app.current_game_index]

    app.starting_game_var.set(next_game)
    app.update_game_number_display()

def update_game_number_display(app):
    current_game = get_current_game_number(app)

    app.game_number_var.set(
        f"Game #{current_game}"
    )

    app.update_team_names_display()
