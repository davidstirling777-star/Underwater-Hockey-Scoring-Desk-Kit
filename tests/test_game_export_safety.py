"""Regression checks for the post-match CSV export safety gate.

These are headless unit tests: actual tournament-file and GUI testing remains
necessary before using a new release at a match.
"""
import ast
from pathlib import Path
import unittest
from unittest.mock import Mock

import game_flow


class Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Engine:
    def __init__(self):
        self.stored_penalties = [{"team": "White", "cap": "7", "duration": 120}]
        self.timer_running = True
        self.timer_seconds = 60
        # Model a just-finished Sudden Death game. These fields must remain
        # available while export is pending, then be cleared after commit.
        self.sudden_death_goal_scored = True
        self.sudden_death_restore_active = True
        self.sudden_death_restore_time = 725
        self.sudden_death_seconds = 725
        self.clear_goal_scorers = Mock()

    def clear_sudden_death_goal(self):
        self.sudden_death_restore_time = None
        self.sudden_death_restore_active = False
        self.sudden_death_goal_scored = False
        self.sudden_death_seconds = 0

    def stop_timer(self):
        self.timer_running = False

    def start_timer(self):
        self.timer_running = True

    def get_current_period(self):
        return {"name": "Between Game Break"}


class FakeApp:
    def __init__(self, result=True, csv_name="Draw.csv", tournament=True):
        self.white_score_var = Var(4)
        self.black_score_var = Var(3)
        self.csv_var = Var(csv_name)
        self.use_tournament_list_var = Var(tournament)
        self.game_numbers = ["1", "2", "3"]
        self.current_game_index = 0
        self.starting_game_var = Var("1")
        self.engine = Engine()
        self.write_game_results_to_csv = Mock(return_value=result)
        self.log_game_event = Mock()
        self.clear_all_penalties = Mock()
        self.update_team_names_display = Mock()
        self.advance_to_next_game = Mock()

    def get_current_game_number(self):
        return self.starting_game_var.get()


class ExportTests(unittest.TestCase):
    def test_false_preserves_scores_penalties_and_game_number(self):
        app = FakeApp(result=False)
        self.assertIs(game_flow.export_and_reset_game_at_break(app), False)
        self.assertEqual((app.white_score_var.get(), app.black_score_var.get()), (4, 3))
        self.assertEqual(len(app.engine.stored_penalties), 1)
        self.assertEqual(app.starting_game_var.get(), "1")
        app.clear_all_penalties.assert_not_called()
        app.engine.clear_goal_scorers.assert_not_called()
        app.advance_to_next_game.assert_not_called()
        app.log_game_event.assert_not_called()
        self.assertTrue(app.engine.sudden_death_goal_scored)
        self.assertTrue(app.engine.sudden_death_restore_active)
        self.assertEqual(app.engine.sudden_death_restore_time, 725)
        self.assertEqual(app.engine.sudden_death_seconds, 725)

    def test_write_exception_preserves_results(self):
        app = FakeApp()
        app.write_game_results_to_csv.side_effect = PermissionError("locked")
        with self.assertRaises(PermissionError):
            game_flow.export_and_reset_game_at_break(app)
        self.assertEqual(app.white_score_var.get(), 4)
        app.advance_to_next_game.assert_not_called()

    def test_successful_retry_clears_once(self):
        app = FakeApp(result=False)
        self.assertIs(game_flow.export_and_reset_game_at_break(app), False)
        app.write_game_results_to_csv.return_value = True
        self.assertIs(game_flow.export_and_reset_game_at_break(app), True)
        self.assertEqual(app.white_score_var.get(), 0)
        self.assertEqual(app.black_score_var.get(), 0)
        self.assertEqual(app.engine.stored_penalties, [])
        app.log_game_event.assert_called_once_with("Game End")
        app.clear_all_penalties.assert_called_once_with()
        app.engine.clear_goal_scorers.assert_called_once_with()
        self.assertFalse(app.engine.sudden_death_goal_scored)
        self.assertFalse(app.engine.sudden_death_restore_active)
        self.assertIsNone(app.engine.sudden_death_restore_time)
        self.assertEqual(app.engine.sudden_death_seconds, 0)
        app.advance_to_next_game.assert_called_once_with()

    def test_no_csv_manual_mode_preserves_existing_workflow(self):
        app = FakeApp(csv_name="", tournament=False)
        self.assertIs(game_flow.export_and_reset_game_at_break(app), True)
        app.write_game_results_to_csv.assert_not_called()
        app.advance_to_next_game.assert_called_once_with()

    def test_missing_csv_in_tournament_mode_blocks_export(self):
        app = FakeApp(csv_name="No CSV files found")
        self.assertIs(game_flow.export_and_reset_game_at_break(app), False)
        app.write_game_results_to_csv.assert_not_called()

    def test_no_game_number_blocks_export(self):
        app = FakeApp()
        app.starting_game_var.set("")
        self.assertIs(game_flow.export_and_reset_game_at_break(app), False)
        app.write_game_results_to_csv.assert_not_called()

    def test_retry_uses_original_game_after_dropdown_change(self):
        app = FakeApp()
        app.starting_game_var.set("3")
        self.assertIs(game_flow.export_and_reset_game_at_break(app, "1"), True)
        app.write_game_results_to_csv.assert_called_once_with(
            "1", 4, 3, [{"team": "White", "cap": "7", "duration": 120}]
        )
        self.assertEqual(app.starting_game_var.get(), "1")


def _load_transition_method():
    """Load the real Tk method without starting a GUI or audio subsystem."""
    source = Path(__file__).resolve().parents[1] / "uwh.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    target = next(
        member for cls in module.body if isinstance(cls, ast.ClassDef)
        for member in cls.body
        if isinstance(member, ast.FunctionDef)
        and member.name == "run_next_game_transition"
    )
    cls = ast.ClassDef(name="Transition", bases=[], keywords=[], body=[target],
                       decorator_list=[])
    small = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    namespace = {"game_flow": game_flow}
    exec(compile(small, str(source), "exec"), namespace)
    return namespace["Transition"]


class FakeTransition(_load_transition_method(), FakeApp):
    def __init__(self, result=False):
        FakeApp.__init__(self, result=result)
        self._game_export_pending = False
        self._pending_export_game_number = None
        self._game_export_timer_was_running = False
        self._game_export_dialog = None
        self._game_export_error_label = None
        self.next_game_transition_job = "scheduled"
        self.next_game_transition_done = False
        self.next_game_preview_active = True
        self.next_game_preview_number = "2"
        self.next_game_notice_active = False
        self.timer_job = None
        self.warnings = []
        self.master = Mock()
        self.master.after.return_value = "tick"
        self.update_game_number_display = Mock()
        self.update_penalty_display = Mock()
        self.countdown_timer = Mock()

    def _show_game_export_error(self, why):
        self.warnings.append(why)
        self._game_export_timer_was_running = self.engine.timer_running
        self.engine.stop_timer()


class TransitionTests(unittest.TestCase):
    def test_failure_then_retry_preserves_state_and_resumes_clock(self):
        app = FakeTransition(result=False)
        app.run_next_game_transition()
        self.assertTrue(app._game_export_pending)
        self.assertEqual(app._pending_export_game_number, "1")
        self.assertFalse(app.next_game_transition_done)
        self.assertFalse(app.engine.timer_running)
        self.assertEqual(app.white_score_var.get(), 4)
        app.advance_to_next_game.assert_not_called()
        app.write_game_results_to_csv.return_value = True
        app.run_next_game_transition()
        self.assertTrue(app.next_game_transition_done)
        self.assertFalse(app._game_export_pending)
        self.assertTrue(app.engine.timer_running)
        self.assertEqual(app.master.after.call_args.args[0], 1000)
        app.advance_to_next_game.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
