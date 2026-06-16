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
