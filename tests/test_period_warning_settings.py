"""Headless checks for the independently saved 30-second warning controls.

The actual Sounds-tab save function is extracted from its AST so tests never
create a Tk window or initialise audio hardware.
"""
import ast
import math
from pathlib import Path
import types
import unittest


class Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Messages:
    def __init__(self):
        self.errors = []
        self.infos = []

    def showerror(self, title, message):
        self.errors.append((title, message))

    def showinfo(self, title, message):
        self.infos.append((title, message))


def load_sound_save(messages):
    path = Path(__file__).resolve().parents[1] / "sounds_ui.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    methods = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "save_sound_settings_method"
    ]
    if len(methods) != 1:
        raise AssertionError("Sounds settings save function not found")
    module = ast.fix_missing_locations(ast.Module(body=methods, type_ignores=[]))
    namespace = dict(
        math=math,
        tk=types.SimpleNamespace(TclError=RuntimeError),
        messagebox=messages,
    )
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["save_sound_settings_method"]


class FakeApp:
    def __init__(self):
        self.pips_var = Var("pip-beep.mp3")
        self.siren_var = Var("siren-car-honk.mp3")
        self.period_warning_file_var = Var("pip-warning.mp3")
        self.period_warning_trim = Var("100")
        self.period_warning_duration_ms = Var("750")
        self.sound_trim_vars = {"pip-beep.mp3": Var("30")}
        self.sound_trims = {"pip-beep.mp3": 30}
        self.enable_sound = Var(True)
        self.siren_duration = Var(1.5)
        self.max_siren_duration = Var("10")
        self.saved = None

    def set_sound_trim(self, filename, trim):
        self.sound_trims[filename] = trim

    def save_sound_settings(self, settings):
        self.saved = settings


class IndependentWarningSettingsTests(unittest.TestCase):
    def setUp(self):
        self.messages = Messages()
        self.save = load_sound_save(self.messages)
        self.app = FakeApp()

    def test_warning_sound_trim_and_duration_are_independent(self):
        self.save(self.app)
        settings = self.app.saved
        self.assertEqual(settings["pips_sound"], "pip-beep.mp3")
        self.assertEqual(settings["sound_trims"]["pip-beep.mp3"], 30)
        self.assertEqual(settings["period_warning_sound"], "pip-warning.mp3")
        self.assertEqual(settings["period_warning_trim"], 100)
        self.assertEqual(settings["period_warning_duration_ms"], 750)
        self.assertFalse(self.messages.errors)

    def test_same_audio_file_still_has_two_distinct_trims(self):
        self.app.period_warning_file_var.set("pip-beep.mp3")
        self.save(self.app)
        self.assertEqual(self.app.saved["sound_trims"]["pip-beep.mp3"], 30)
        self.assertEqual(self.app.saved["period_warning_trim"], 100)

    def test_bad_warning_trim_or_duration_prevents_saving(self):
        for field, bad_value in (
            ("period_warning_trim", "101"),
            ("period_warning_trim", "-1"),
            ("period_warning_duration_ms", "0"),
            ("period_warning_duration_ms", "5001"),
        ):
            with self.subTest(field=field, value=bad_value):
                self.app = FakeApp()
                getattr(self.app, field).set(bad_value)
                self.save(self.app)
                self.assertIsNone(self.app.saved)
                self.assertTrue(self.messages.errors)


if __name__ == "__main__":
    unittest.main()
