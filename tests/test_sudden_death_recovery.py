"""Regression tests for repeated Sudden Death games and goal correction.

These tests exercise the real goal/period methods without creating a Tk window.
They protect two rules:
1. a deciding Sudden Death goal immediately enters Between Game Break;
2. that goal can be retracted during the correction window to resume Sudden
   Death at its saved elapsed time;
3. after the completed game is committed, stale Sudden Death state must not
   prevent a later game from ending in Sudden Death.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import game_flow
from game_engine import GameEngine


ROOT = Path(__file__).resolve().parents[1]


class Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def load_uwh_methods():
    source = ROOT / "uwh.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    wanted = {
        "add_goal_with_confirmation",
        "adjust_score_with_confirm",
        "restore_sudden_death_after_goal_removal",
        "next_period",
    }
    app_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "GameManagementApp"
    )
    methods = [
        node for node in app_class.body
        if isinstance(node, ast.FunctionDef) and node.name in wanted
    ]
    if {node.name for node in methods} != wanted:
        raise AssertionError("Expected Sudden Death handlers are missing")

    shell = ast.ClassDef(
        name="SuddenDeathCallbacks",
        bases=[],
        keywords=[],
        body=methods,
        decorator_list=[],
    )
    module = ast.fix_missing_locations(
        ast.Module(body=[shell], type_ignores=[])
    )
    namespace = {
        "game_flow": game_flow,
        "messagebox": SimpleNamespace(askyesno=lambda *_a, **_k: True),
    }
    exec(compile(module, str(source), "exec"), namespace)
    return namespace["SuddenDeathCallbacks"]


class FakeApp(load_uwh_methods()):
    def __init__(self):
        self.engine = GameEngine()
        self.engine.set_sequence([
            {"name": "Sudden Death", "type": "game", "duration": None},
            {"name": "Between Game Break", "type": "break", "duration": 120},
        ])
        self.engine.go_to_period("Sudden Death")
        self.engine.start_timer()

        self.white_score_var = Var(0)
        self.black_score_var = Var(0)
        self.record_scorers_cap_number_var = Var(False)

        self.in_timeout = False
        self.referee_timeout_active = False
        self.timer_job = None
        self.sudden_death_timer_job = None
        self._game_export_pending = False
        self._pending_export_game_number = None
        self.next_game_transition_done = False

        # Minimal tournament/export surface used by game_flow.
        self.csv_var = Var("")
        self.use_tournament_list_var = Var(False)
        self.game_numbers = []
        self.current_game_index = 0
        self.starting_game_var = Var("")
        self.write_game_results_to_csv = Mock(return_value=True)
        self.clear_all_penalties = Mock()
        self.update_team_names_display = Mock()
        self.advance_to_next_game = Mock()

        self.events = []
        self.period_starts = []

    def show_cap_number_dialog(self, _trigger):
        raise AssertionError("Cap dialog should be disabled in this test")

    def log_game_event(self, event_type, **kwargs):
        self.events.append((event_type, kwargs))

    def start_current_period(self):
        # The real method configures the appropriate timer. The regression
        # only needs to prove which period was selected and that it runs.
        period = self.engine.get_current_period()
        self.period_starts.append(period["name"])
        self.engine.start_timer()

    def get_current_game_number(self):
        return self.starting_game_var.get()


class SuddenDeathRecoveryTests(unittest.TestCase):
    def test_deciding_goal_immediately_enters_between_game_break(self):
        app = FakeApp()
        app.engine.sudden_death_seconds = 725

        app.add_goal_with_confirmation(app.white_score_var, "White")

        self.assertEqual(app.white_score_var.get(), 1)
        self.assertEqual(app.black_score_var.get(), 0)
        self.assertEqual(
            app.engine.get_current_period()["name"],
            "Between Game Break",
        )
        self.assertTrue(app.engine.sudden_death_goal_scored)
        self.assertTrue(app.engine.sudden_death_restore_active)
        self.assertEqual(app.engine.sudden_death_restore_time, 725)

    def test_retracting_deciding_goal_restores_sudden_death(self):
        app = FakeApp()
        app.engine.sudden_death_seconds = 725
        app.add_goal_with_confirmation(app.white_score_var, "White")

        # The completed game remains correctable before the existing
        # 30-second finalisation/export gate.
        app.engine.timer_seconds = 60
        app.adjust_score_with_confirm(app.white_score_var, "White")

        self.assertEqual(app.white_score_var.get(), 0)
        self.assertEqual(app.black_score_var.get(), 0)
        self.assertEqual(
            app.engine.get_current_period()["name"],
            "Sudden Death",
        )
        self.assertEqual(app.engine.sudden_death_seconds, 725)
        self.assertFalse(app.engine.sudden_death_goal_scored)
        self.assertFalse(app.engine.sudden_death_restore_active)
        self.assertIsNone(app.engine.sudden_death_restore_time)
        self.assertTrue(app.engine.timer_running)

    def test_second_game_can_also_end_in_sudden_death(self):
        app = FakeApp()

        # Game 1: Sudden Death goal works normally.
        app.engine.sudden_death_seconds = 720
        app.add_goal_with_confirmation(app.white_score_var, "White")
        self.assertEqual(
            app.engine.get_current_period()["name"],
            "Between Game Break",
        )
        self.assertTrue(app.engine.sudden_death_goal_scored)

        # Finalise Game 1. This is the state boundary that used to leave
        # sudden_death_goal_scored=True and jam the next Sudden Death.
        self.assertTrue(game_flow.export_and_reset_game_at_break(app))
        self.assertFalse(app.engine.sudden_death_goal_scored)
        self.assertFalse(app.engine.sudden_death_restore_active)
        self.assertIsNone(app.engine.sudden_death_restore_time)
        self.assertEqual(app.engine.sudden_death_seconds, 0)
        self.assertEqual(app.white_score_var.get(), 0)

        # Game 2 reaches Sudden Death too. Its deciding goal must again take
        # the game immediately to Between Game Break.
        app.engine.go_to_period("Sudden Death")
        app.engine.start_timer()
        app.engine.sudden_death_seconds = 2105
        app.add_goal_with_confirmation(app.black_score_var, "Black")

        self.assertEqual(app.white_score_var.get(), 0)
        self.assertEqual(app.black_score_var.get(), 1)
        self.assertEqual(
            app.engine.get_current_period()["name"],
            "Between Game Break",
        )
        self.assertTrue(app.engine.sudden_death_goal_scored)
        self.assertEqual(app.engine.sudden_death_restore_time, 2105)


if __name__ == "__main__":
    unittest.main()
