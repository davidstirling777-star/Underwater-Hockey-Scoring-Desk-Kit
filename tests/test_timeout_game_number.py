"""Exercise actual timeout handlers headlessly, without audio or a Tk window."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from game_engine import GameEngine
import game_flow


def load_handlers():
    path = Path(__file__).resolve().parents[1] / "uwh.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == "GameManagementApp")
    names = {"update_game_number_display", "white_team_timeout",
             "black_team_timeout", "end_timeout", "save_timer_state"}
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)
               and n.name in names]
    assert {n.name for n in methods} == names
    namespace = {"game_flow": game_flow,
                 "tk": SimpleNamespace(DISABLED="disabled")}
    exec(compile(ast.Module(body=methods, type_ignores=[]), str(path), "exec"),
         namespace)
    return {name: namespace[name] for name in names}


class TimeoutGameNumberTests(unittest.TestCase):
    def setUp(self):
        self.app = SimpleNamespace()
        app = self.app
        for name, handler in load_handlers().items():
            setattr(app, name, handler.__get__(app))
        app.engine = GameEngine()
        app.engine.set_sequence([{"name": "First Half", "type": "regular",
                                  "duration": 900}])
        app.engine.timer_seconds = 452
        app.engine.timer_running = True
        app.in_timeout = False
        app.pending_timeout = None
        app.team_timeout_saved_state = None
        app.timer_job = None
        app.court_time_job = "court-job"
        app.master = Mock()
        app.team_timeouts_allowed_var = Mock(get=lambda: True)
        app.game_number_var = Mock()
        app.half_label_var = Mock(get=lambda: "First Half")
        app.half_label = Mock()
        app.white_timeout_button = Mock()
        app.black_timeout_button = Mock()
        app.get_minutes = lambda key: 60
        app.get_current_game_number = lambda: "12"
        # game_flow reads the manual/tournament game selection here.
        app.use_tournament_list_var = Mock(get=lambda: False)
        app.starting_game_var = Mock(get=lambda: "12")
        app.game_numbers = ["12"]
        app.current_game_index = 0
        for name in ("_reset_second_deadlines", "pause_all_penalty_timers",
                     "resume_all_penalty_timers", "update_half_label_background",
                     "update_timer_display", "update_team_names_display",
                     "sync_display_widgets", "timeout_countdown",
                     "countdown_timer", "update_court_time", "show_timeout_popup"):
            setattr(app, name, Mock())
        app._after_one_second = Mock(return_value="timer-job")

    def test_each_team_shows_half_time_then_restores_game_number(self):
        for team in ("white", "black"):
            with self.subTest(team=team):
                self.setUp()
                app = self.app
                getattr(app, f"{team}_team_timeout")()
                app.game_number_var.set.assert_called_with("Time Remaining: 07:32")
                self.assertEqual(app.engine.timer_seconds, 60)
                app.engine.timer_seconds = 15
                app.update_game_number_display()
                app.game_number_var.set.assert_called_with("Time Remaining: 07:32")
                app.end_timeout()
                app.game_number_var.set.assert_called_with("Game #12")
                self.assertEqual(app.engine.timer_seconds, 452)

    def test_queued_timeout_preserves_original_half_time(self):
        app = self.app
        app.white_team_timeout()
        app.black_team_timeout()
        app.engine.timer_seconds = 0
        app.end_timeout()
        self.assertTrue(app.in_timeout)
        app.game_number_var.set.assert_called_with("Time Remaining: 07:32")
        app.end_timeout()
        app.game_number_var.set.assert_called_with("Game #12")

    def test_rejected_timeout_leaves_game_label_alone(self):
        self.app.team_timeouts_allowed_var.get = lambda: False
        self.app.white_team_timeout()
        self.app.game_number_var.set.assert_not_called()


if __name__ == "__main__":
    unittest.main()
