"""H:MM and HH:MM must agree in UI validation and both start-time paths.

Extract the real methods as AST so these tests need no Tk display, pygame,
serial device or installed MQTT broker.
"""
import ast
import datetime as real_datetime
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1]


class FixedDatetime(real_datetime.datetime):
    current = real_datetime.datetime(2026, 9, 30, 8, 0)

    @classmethod
    def now(cls):
        return cls.current


def load_uwh_start_time_methods():
    source = ROOT / "uwh.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body
               if isinstance(n, ast.ClassDef) and n.name == "GameManagementApp")
    names = {"_update_start_first_game_in", "load_settings",
             "build_game_sequence"}
    methods = [n for n in cls.body
               if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in methods} != names:
        raise AssertionError("Start-time handlers missing from UWH")
    subject = ast.ClassDef(
        name="StartTimeCallbacks", bases=[], keywords=[],
        body=methods, decorator_list=[]
    )
    code = ast.fix_missing_locations(
        ast.Module(body=[subject], type_ignores=[])
    )
    globals_for_methods = {
        "datetime": SimpleNamespace(
            datetime=FixedDatetime, timedelta=real_datetime.timedelta
        ),
        "re": re,
        "tk": SimpleNamespace(END="end"),
    }
    exec(compile(code, str(source), "exec"), globals_for_methods)
    return globals_for_methods["StartTimeCallbacks"]


def load_real_entry_validator(app, errors):
    source = ROOT / "settings_ui.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    create_tab = next(n for n in tree.body
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "create_settings_tab")
    validator = next(n for n in ast.walk(create_tab)
                     if isinstance(n, ast.FunctionDef)
                     and n.name == "validate_hhmm_on_focusout")
    module = ast.fix_missing_locations(
        ast.Module(body=[validator], type_ignores=[])
    )
    namespace = {
        "app": app,
        "re": re,
        "messagebox": SimpleNamespace(showerror=errors),
        "tk": SimpleNamespace(END="end"),
    }
    exec(compile(module, str(source), "exec"), namespace)
    return namespace[validator.name]


class Entry:
    def __init__(self, value):
        self.value = str(value)
        self.focus_set = Mock()
        self.selection_range = Mock()

    def get(self):
        return self.value

    def delete(self, first, last):
        self.value = ""

    def insert(self, first, value):
        self.value = str(value)


class FakeApp(load_uwh_start_time_methods()):
    def __init__(self, time_text):
        self.clock_entry = Entry(time_text)
        self.minutes_entry = Entry("5")
        self.widgets = [
            {"name": "time_to_start_first_game",
             "entry": self.clock_entry, "checkbox": None},
            {"name": "start_first_game_in",
             "entry": self.minutes_entry, "checkbox": None},
        ]
        self.variables = {
            "time_to_start_first_game": {
                "value": time_text, "default": "", "used": True
            },
            "start_first_game_in": {
                "value": "5", "default": "5", "used": True
            },
        }
        self.engine = SimpleNamespace(set_sequence=Mock())

    def get_minutes(self, name):
        return 60

    def is_overtime_enabled(self):
        return False

    def is_sudden_death_enabled(self):
        return False

    def first_period_seconds(self):
        self.build_game_sequence()
        sequence = self.engine.set_sequence.call_args.args[0]
        return sequence[0]["duration"]


class StartTimeFormatsTests(unittest.TestCase):
    def setUp(self):
        FixedDatetime.current = real_datetime.datetime(2026, 9, 30, 8, 0)

    def test_user_entry_accepts_one_or_two_digit_hour(self):
        app = SimpleNamespace(_on_single_variable_change=Mock())
        errors = Mock()
        validator = load_real_entry_validator(app, errors)
        for time_text in ("9:36", "09:36", "0:05", "00:05",
                          "19:36", "23:59"):
            with self.subTest(time=time_text):
                validator(SimpleNamespace(widget=Entry(time_text)))
        self.assertEqual(app._on_single_variable_change.call_count, 6)
        errors.assert_not_called()

    def test_invalid_clock_values_remain_rejected(self):
        app = SimpleNamespace(_on_single_variable_change=Mock())
        errors = Mock()
        validator = load_real_entry_validator(app, errors)
        for time_text in ("24:00", "9:6", "09:60", "99:36",
                          "9:36junk", "-1:00"):
            with self.subTest(time=time_text):
                widget = Entry(time_text)
                validator(SimpleNamespace(widget=widget))
                widget.focus_set.assert_called_once()
        self.assertEqual(errors.call_count, 6)
        app._on_single_variable_change.assert_not_called()

    def test_live_minutes_field_accepts_both_equivalent_forms(self):
        for time_text in ("9:36", "09:36"):
            with self.subTest(time=time_text):
                app = FakeApp(time_text)
                app._update_start_first_game_in()
                self.assertEqual(app.minutes_entry.get(), "96")
                self.assertEqual(
                    app.variables["start_first_game_in"]["value"], "96"
                )

    def test_loading_saved_one_digit_hour_recalculates_minutes(self):
        for time_text in ("9:36", "09:36"):
            with self.subTest(time=time_text):
                app = FakeApp(time_text)
                app.load_settings()
                self.assertEqual(app.minutes_entry.get(), "96")
                self.assertEqual(app.variables["start_first_game_in"]["value"],
                                 "96")
                self.assertEqual(
                    app.variables["time_to_start_first_game"]["value"],
                    time_text,
                )

    def test_game_sequence_schedules_same_instant_for_both_forms(self):
        for time_text in ("9:36", "09:36"):
            with self.subTest(time=time_text):
                app = FakeApp(time_text)
                self.assertEqual(app.first_period_seconds(), 96 * 60)

    def test_both_forms_roll_over_to_tomorrow_after_time_passed(self):
        FixedDatetime.current = real_datetime.datetime(
            2026, 9, 30, 10, 0
        )
        for time_text in ("9:36", "09:36"):
            with self.subTest(time=time_text):
                app = FakeApp(time_text)
                app._update_start_first_game_in()
                self.assertEqual(app.minutes_entry.get(), str(23 * 60 + 36))
                self.assertEqual(
                    app.first_period_seconds(), (23 * 60 + 36) * 60
                )

    def test_midnight_and_late_day_use_same_rules(self):
        for one_digit, two_digit, hour, minute in (
            ("0:05", "00:05", 0, 5),
            ("9:06", "09:06", 9, 6),
        ):
            expected = (hour * 60 + minute - 8 * 60) % (24 * 60)
            for time_text in (one_digit, two_digit):
                with self.subTest(time=time_text):
                    app = FakeApp(time_text)
                    app._update_start_first_game_in()
                    self.assertEqual(app.minutes_entry.get(), str(expected))
                    self.assertEqual(
                        app.first_period_seconds(), expected * 60
                    )


if __name__ == "__main__":
    unittest.main()
