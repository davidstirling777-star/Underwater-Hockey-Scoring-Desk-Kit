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
