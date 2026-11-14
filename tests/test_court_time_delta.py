"""Court Time lag remains unsigned and refreshes even while its clock is paused."""
import ast
import datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class Clock(datetime.datetime):
    current = datetime.datetime(2026, 11, 15, 12, 0, 0)

    @classmethod
    def now(cls):
        return cls.current


def load_methods():
    path = Path(__file__).resolve().parents[1] / "uwh.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {"_refresh_court_time_delta", "_poll_court_time_delta", "_credit_crib_time"}
    methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in methods} == names
    namespace = {"datetime": SimpleNamespace(datetime=Clock)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[])),
                 str(path), "exec"), namespace)
    return namespace


METHODS = load_methods()


class CourtTimeDeltaTests(unittest.TestCase):
    def setUp(self):
        Clock.current = datetime.datetime(2026, 11, 15, 12, 0, 0)
        self.app = Mock(court_time_seconds=43200, court_time_delta_job=None)
        self.app._refresh_court_time_delta = lambda: METHODS["_refresh_court_time_delta"](self.app)

    def test_equal_or_ahead_or_uninitialised_is_hidden(self):
        for seconds in (43200, 43201, None):
            self.app.court_time_seconds = seconds
            self.app._refresh_court_time_delta()
            self.app.court_time_delta_var.set.assert_called_with("")
            self.app.court_time_delta_label.place_forget.assert_called()
        self.app.court_time_delta_label.place.assert_not_called()

    def test_unsigned_minutes_seconds_at_right(self):
        for lag, text in ((23, "Δ 00:23"), (65, "Δ 01:05"), (3605, "Δ 60:05")):
            self.app.court_time_seconds = 43200 - lag
            self.app._refresh_court_time_delta()
            self.app.court_time_delta_var.set.assert_called_with(text)
            self.app.court_time_delta_label.place.assert_called_with(
                relx=1.0, rely=0.5, x=-10, anchor="e")

    def test_referee_pause_refresh_does_not_advance_court_clock(self):
        self.app.court_time_paused = True
        METHODS["_poll_court_time_delta"](self.app)
        Clock.current += datetime.timedelta(seconds=23)
        METHODS["_poll_court_time_delta"](self.app)
        self.assertEqual(self.app.court_time_seconds, 43200)
        self.app.court_time_delta_var.set.assert_called_with("Δ 00:23")
        self.app.master.after.assert_called_with(250, self.app._poll_court_time_delta)
        self.app.master.after_cancel.assert_called_once()

    def test_recovery_updates_delta_immediately(self):
        self.app.court_time_seconds -= 23
        METHODS["_credit_crib_time"](self.app, 10)
        self.app.court_time_delta_var.set.assert_called_with("Δ 00:13")
        METHODS["_credit_crib_time"](self.app, 13)
        self.app.court_time_delta_var.set.assert_called_with("")
        self.app.court_time_delta_label.place_forget.assert_called()

    def test_midnight_wrap_and_court_time_over_one_day(self):
        Clock.current = datetime.datetime(2026, 11, 16, 0, 0, 5)
        for court, text in ((86382, "Δ 00:23"), (86405, ""), (86406, "")):
            self.app.court_time_seconds = court
            self.app._refresh_court_time_delta()
            self.app.court_time_delta_var.set.assert_called_with(text)


if __name__ == "__main__":
    unittest.main()
