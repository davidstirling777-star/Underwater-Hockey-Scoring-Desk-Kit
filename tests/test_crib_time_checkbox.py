"""Exercise real period-start code with decimal durations and Crib Time toggles."""
import ast
import datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from game_engine import GameEngine


class FixedDatetime(datetime.datetime):
    @classmethod
    def now(cls):
        return cls(2026, 11, 14, 12, 0, 0)


def load_methods():
    path = Path(__file__).resolve().parents[1] / "uwh.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    app_class = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                     and n.name == "GameManagementApp")
    names = {"get_minutes", "start_current_period",
             "_credit_crib_time"}
    methods = [n for n in app_class.body if isinstance(n, ast.FunctionDef)
               and n.name in names]
    assert {n.name for n in methods} == names
    namespace = {
        "datetime": SimpleNamespace(datetime=FixedDatetime,
                                    timedelta=datetime.timedelta),
        "tk": SimpleNamespace(NORMAL="normal", DISABLED="disabled", TclError=Exception),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])),
                 str(path), "exec"), namespace)
    return namespace


METHODS = load_methods()


def make_app(enabled, name="Between Game Break", value="2.5", lag=23, allowance=60):
    app = Mock()
    key = "between_game_break" if name == "Between Game Break" else "half_time_break"
    app.variables = {
        key: {"default": 1, "value": value},
        "crib_time": {"default": 1, "value": allowance, "used": enabled},
    }
    app.get_minutes = lambda key: METHODS["get_minutes"](app, key)
    app._credit_crib_time = lambda seconds: METHODS["_credit_crib_time"](app, seconds)
    app.engine = GameEngine()
    app.engine.set_sequence([{"name": name, "type": "break",
                              "duration": app.get_minutes(key)}])
    app.court_time_seconds = 43200 - lag
    app.timer_job = None
    app.next_game_transition_job = None
    app.next_game_preview_job = None
    return app


class CribTimeCheckboxTests(unittest.TestCase):
    def test_disabled_preserves_two_and_half_minutes(self):
        app = make_app(False)
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 150)
        self.assertEqual(app.engine.format_seconds_as_mmss(app.engine.timer_seconds), "02:30")
        self.assertEqual(app.variables["crib_time"]["value"], 60)

    def test_enabled_reproduces_reported_two_minutes_seven_seconds(self):
        app = make_app(True)
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 127)

    def test_enabled_reduction_is_capped_by_allowance(self):
        app = make_app(True, allowance=10)
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 140)

    def test_enabled_does_not_reduce_when_on_time(self):
        app = make_app(True, lag=0)
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 150)

    def test_half_time_remains_ninety_seconds_with_either_checkbox_state(self):
        for enabled in (False, True):
            for value in ("1.5", "1,5"):
                with self.subTest(enabled=enabled, value=value):
                    app = make_app(enabled, "Half Time", value)
                    METHODS["start_current_period"](app)
                    self.assertEqual(app.engine.timer_seconds, 90)
                    self.assertEqual(app.engine.format_seconds_as_mmss(app.engine.timer_seconds), "01:30")

    def test_disabling_after_enabled_restores_full_break(self):
        app = make_app(True)
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 127)
        app.variables["crib_time"]["used"] = False
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 150)

    def test_recovered_delay_is_not_deducted_from_later_breaks(self):
        app = make_app(True)
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 127)
        self.assertEqual(app.court_time_seconds, 43200)
        app.court_time_var.set.assert_called_with("Court Time is 12:00:00")
        for _ in range(3):
            METHODS["start_current_period"](app)
            self.assertEqual(app.engine.timer_seconds, 150)
            self.assertEqual(app.court_time_seconds, 43200)

    def test_later_timeout_adds_only_new_delay(self):
        app = make_app(True)
        METHODS["start_current_period"](app)
        app.court_time_seconds -= 17
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 133)
        self.assertEqual(app.court_time_seconds, 43200)
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 150)

    def test_partial_recovery_carries_only_remaining_delay(self):
        app = make_app(True, allowance=10)
        for remaining, duration in ((13, 140), (3, 140), (0, 147), (0, 150)):
            METHODS["start_current_period"](app)
            self.assertEqual(app.court_time_seconds, 43200 - remaining)
            self.assertEqual(app.engine.timer_seconds, duration)

    def test_minimum_break_credits_only_seconds_actually_removed(self):
        app = make_app(True, value="0.75", allowance=60)
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 32)
        self.assertEqual(app.court_time_seconds, 43190)  # 13 recovered, 10 remain

    def test_disabled_leaves_court_time_unchanged(self):
        app = make_app(False)
        METHODS["start_current_period"](app)
        self.assertEqual(app.court_time_seconds, 43177)

    def test_half_time_does_not_credit_delay(self):
        app = make_app(True, "Half Time", "1.5")
        METHODS["start_current_period"](app)
        self.assertEqual(app.court_time_seconds, 43177)

    def test_short_break_is_not_lengthened_or_credited(self):
        app = make_app(True, value="0.5")
        METHODS["start_current_period"](app)
        self.assertEqual(app.engine.timer_seconds, 30)
        self.assertEqual(app.court_time_seconds, 43177)


if __name__ == "__main__":
    unittest.main()
