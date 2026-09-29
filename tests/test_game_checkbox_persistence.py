"""Regression tests for saving Game Variables that have both a value and a checkbox.

No Tk window or hardware is required. The real UWH variable callbacks are
extracted from the source to exercise the startup trace suppression as well.
"""
import ast
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import Mock

import game_settings_manager as settings


def load_callbacks():
    source = Path(__file__).resolve().parents[1] / "uwh.py"
    parsed = ast.parse(source.read_text(encoding="utf-8"))
    names = {
        "_on_single_variable_change",
        "_on_team_timeouts_change",
        "_on_overtime_change",
        "_on_settings_variable_change",
    }
    found = [
        item for cls in parsed.body if isinstance(cls, ast.ClassDef)
        for item in cls.body if isinstance(item, ast.FunctionDef)
        and item.name in names
    ]
    if {item.name for item in found} != names:
        raise AssertionError("Expected UWH variable-change handlers missing")
    cls = ast.ClassDef(
        name="UWHCallbacks", bases=[], keywords=[], body=found,
        decorator_list=[]
    )
    code = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    namespace = {}
    exec(compile(code, str(source), "exec"), namespace)
    return namespace["UWHCallbacks"]


class Entry:
    def __init__(self, value):
        self.value = str(value)

    def get(self):
        return self.value

    def delete(self, _first, _last):
        self.value = ""

    def insert(self, _index, value):
        self.value = str(value)


class Checkbox:
    def __init__(self, initial, callback=None):
        self.value = bool(initial)
        self.callback = callback

    def get(self):
        return self.value

    def set(self, value):
        self.value = bool(value)
        if self.callback is not None:
            self.callback()


class FakeApp(load_callbacks()):
    def __init__(self, saved_game=None):
        self._loading_game_settings = False
        self._saves = []
        self.storage = {
            "gameSettings": saved_game if saved_game is not None else {},
            "presetSettings": [{"text": "CMAS", "checkboxes": {
                "sudden_death_game_break": False,
            }, "values": {"sudden_death_game_break": "0.6"}}],
            "zigbeeSettings": {"mqtt_broker": "localhost"},
        }
        self.variables = {
            "sudden_death_game_break": {
                "checkbox": True, "default": 1, "value": "1", "used": True
            },
            "crib_time": {
                "checkbox": True, "default": 1, "value": "1", "used": True
            },
            "team_timeouts_allowed": {
                "checkbox": True, "default": True, "value": True, "used": True
            },
            "overtime_allowed": {
                "checkbox": True, "default": True, "value": True, "used": True
            },
            "record_scorers_cap_number": {
                "checkbox": True, "default": False, "value": False, "used": False
            },
            "half_period": {
                "checkbox": False, "default": 1, "value": "1", "used": True
            },
            "time_to_start_first_game": {
                "checkbox": False, "default": "", "value": "", "used": True
            },
        }
        self.widgets = []
        self.build_game_sequence = Mock()
        self.load_settings = Mock()
        self.update_team_timeouts_allowed = Mock()
        self.update_overtime_variables_state = Mock()
        self._update_start_first_game_in = Mock()
        self._update_time_to_start_first_game = Mock()

        for name, meta in self.variables.items():
            if name == "team_timeouts_allowed":
                cb = Checkbox(True, self._on_team_timeouts_change)
                self.team_timeouts_allowed_var = cb
                entry = None
            elif name == "overtime_allowed":
                cb = Checkbox(True, self._on_overtime_change)
                self.overtime_allowed_var = cb
                entry = None
            elif name == "record_scorers_cap_number":
                cb = Checkbox(False, lambda: self._on_single_variable_change(name))
                entry = None
            else:
                cb = (Checkbox(True, lambda name=name:
                               self._on_single_variable_change(name))
                      if meta["checkbox"] else None)
                entry = Entry(meta["value"])

            self.widgets.append({
                "name": name, "entry": entry, "checkbox": cb,
            })

    def field(self, name):
        return next(w for w in self.widgets if w["name"] == name)

    def load_unified_settings(self):
        return deepcopy(self.storage)

    def save_unified_settings(self, data):
        self.storage = deepcopy(data)
        self._saves.append(deepcopy(data))

    def save_game_settings(self):
        return settings.save_game_settings(self)


class GameCheckboxPersistenceTests(unittest.TestCase):
    def test_save_mixed_off_and_fractional_value_without_touching_presets(self):
        app = FakeApp()
        app.field("sudden_death_game_break")["entry"].value = "0.6"
        app.field("sudden_death_game_break")["checkbox"].set(False)
        app.field("crib_time")["entry"].value = "60"
        app.field("crib_time")["checkbox"].set(False)

        saved = app.storage["gameSettings"]
        self.assertEqual(saved["sudden_death_game_break"], 0.6)
        self.assertEqual(saved["crib_time"], 60)
        self.assertEqual(saved["checkboxes"], {
            "sudden_death_game_break": False, "crib_time": False
        })
        self.assertEqual(saved["team_timeouts_allowed"], True)
        self.assertEqual(saved["overtime_allowed"], True)
        self.assertEqual(app.storage["presetSettings"][0]["text"], "CMAS")
        self.assertEqual(app.storage["zigbeeSettings"]["mqtt_broker"], "localhost")

    def test_relaunch_restores_value_and_both_disabled_checkboxes(self):
        saved = {
            "sudden_death_game_break": 0.6, "crib_time": 60,
            "checkboxes": {
                "sudden_death_game_break": False, "crib_time": False
            },
            "team_timeouts_allowed": False, "overtime_allowed": False,
            "record_scorers_cap_number": True, "half_period": 15,
        }
        app = FakeApp(saved)
        settings.load_game_settings(app)
        self.assertEqual(app.field("sudden_death_game_break")["entry"].get(), "0.6")
        self.assertIs(app.field("sudden_death_game_break")["checkbox"].get(), False)
        self.assertEqual(app.field("crib_time")["entry"].get(), "60")
        self.assertIs(app.field("crib_time")["checkbox"].get(), False)
        self.assertIs(app.team_timeouts_allowed_var.get(), False)
        self.assertIs(app.overtime_allowed_var.get(), False)
        self.assertIs(app.field("record_scorers_cap_number")["checkbox"].get(), True)
        self.assertEqual(app.field("half_period")["entry"].get(), "15")
        self.assertEqual(app._saves, [])
        app.build_game_sequence.assert_not_called()
        app.update_team_timeouts_allowed.assert_called_once_with()
        app.update_overtime_variables_state.assert_called_once_with()

    def test_legacy_numeric_only_defaults_to_enabled(self):
        app = FakeApp({"sudden_death_game_break": 0.6, "crib_time": 20})
        settings.load_game_settings(app)
        self.assertEqual(app.field("sudden_death_game_break")["entry"].get(), "0.6")
        self.assertTrue(app.field("sudden_death_game_break")["checkbox"].get())
        self.assertTrue(app.field("crib_time")["checkbox"].get())

    def test_legacy_boolean_only_preserves_disabled(self):
        app = FakeApp({"sudden_death_game_break": False, "crib_time": True})
        settings.load_game_settings(app)
        self.assertFalse(app.field("sudden_death_game_break")["checkbox"].get())
        self.assertEqual(app.field("sudden_death_game_break")["entry"].get(), "1")
        self.assertTrue(app.field("crib_time")["checkbox"].get())
        self.assertEqual(app.field("crib_time")["entry"].get(), "1")

    def test_malformed_checkbox_section_safely_defaults_to_enabled(self):
        app = FakeApp({"sudden_death_game_break": 0.6, "checkboxes": "bad"})
        settings.load_game_settings(app)
        self.assertTrue(app.field("sudden_death_game_break")["checkbox"].get())
        app = FakeApp({
            "sudden_death_game_break": 0.6,
            "checkboxes": {"sudden_death_game_break": "false"}
        })
        settings.load_game_settings(app)
        self.assertTrue(app.field("sudden_death_game_break")["checkbox"].get())

    def test_numeric_presets_do_not_force_checkbox_back_on(self):
        app = FakeApp()
        # Simulate clicking a preset: entry is written, checkbox trace saves
        # the combined current state.
        item = app.field("sudden_death_game_break")
        item["entry"].value = "0.6"
        item["checkbox"].set(False)
        saved = deepcopy(app.storage)
        relaunched = FakeApp(saved["gameSettings"])
        settings.load_game_settings(relaunched)
        self.assertEqual(relaunched.field("sudden_death_game_break")["entry"].get(),
                         "0.6")
        self.assertFalse(
            relaunched.field("sudden_death_game_break")["checkbox"].get()
        )

    def test_failed_widget_update_restores_loading_guard(self):
        app = FakeApp({"sudden_death_game_break": 0.6})
        def fail(_x):
            raise RuntimeError("widget removed")
        app.field("sudden_death_game_break")["checkbox"].set = fail
        with self.assertRaisesRegex(RuntimeError, "widget removed"):
            settings.load_game_settings(app)
        self.assertFalse(app._loading_game_settings)

    def test_save_is_suppressed_during_load(self):
        app = FakeApp()
        app._loading_game_settings = True
        settings.save_game_settings(app)
        self.assertEqual(app._saves, [])

    def test_future_mixed_variables_get_their_own_checkbox(self):
        app = FakeApp()
        app.variables["future_period"] = {
            "checkbox": True, "default": 5, "value": "3.5", "used": False
        }
        app.widgets.append({
            "name": "future_period", "entry": Entry("3.5"),
            "checkbox": Checkbox(False)
        })
        settings.save_game_settings(app)
        data = app.storage["gameSettings"]
        self.assertEqual(data["future_period"], 3.5)
        self.assertFalse(data["checkboxes"]["future_period"])


if __name__ == "__main__":
    unittest.main()
