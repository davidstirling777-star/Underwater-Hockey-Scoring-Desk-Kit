"""Headless UI tests for one-minute coalesced settings saves and safe exit."""
import ast
import json
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import settings_manager

ROOT = Path(__file__).resolve().parents[1]


def app_class(directory):
    """Exercise the real UWH methods without creating windows or a mixer."""
    path = ROOT / "uwh.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in module.body if isinstance(n, ast.ClassDef)
               and n.name == "GameManagementApp")
    names = {
        "_queue_settings_section", "_flush_pending_settings",
        "save_game_settings", "save_screen_settings", "request_exit",
    }
    methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)
               and n.name in names]
    assert {n.name for n in methods} == names
    fake_cls = ast.ClassDef(name="App", bases=[], keywords=[],
                            body=methods, decorator_list=[])
    top = ast.fix_missing_locations(ast.Module(body=[fake_cls], type_ignores=[]))
    messagebox = SimpleNamespace(
        askyesno=Mock(return_value=True), showerror=Mock()
    )
    fake_game_manager = SimpleNamespace(
        build_game_settings=lambda app: app.game_snapshot
    )
    ns = {"BASE_DIR": directory, "settings_manager": settings_manager,
          "game_settings_manager": fake_game_manager,
          "messagebox": messagebox, "tk": tk}
    exec(compile(top, str(path), "exec"), ns)
    return ns["App"], messagebox


class Var:
    def __init__(self, v):
        self.v = v

    def get(self):
        return self.v


class MinuteSaveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = self.temp.name
        self.file = Path(self.directory) / "settings.json"
        settings_manager.save_unified_settings(self.directory, {
            "soundSettings": {"volume": 65},
            "gameSettings": {"half_period": 15},
            "screenSettings": {"operator_layout": "Standard"},
        })
        cls, self.messagebox = app_class(self.directory)
        self.app = cls()
        self.app._pending_settings_sections = {}
        self.app._settings_autosave_job = None
        self.app.master = Mock()
        self.app.master.after.side_effect = lambda duration, fn: (
            "job", self.app.master.after.call_count
        )
        self.app.game_snapshot = {"half_period": 15}
        self.app.show_display_team_names_var = Var(True)
        self.app.operator_layout_var = Var("Standard")
        self.app.display_layout_var = Var("Single Standard")
        self.app.show_display_screen_var = Var(True)
        self.app._stop_wireless_siren = Mock()
        self.app._stop_arduino_siren = Mock()
        self.app.stop_connection_watchdog = Mock()
        self.app.close_all_display_windows = Mock()
        self.app.zigbee_controller = Mock()

    def disk(self):
        return json.loads(self.file.read_text(encoding="utf-8"))

    def backups(self):
        return sorted(Path(self.directory).glob("settings_old_*.json"))

    def test_game_edit_does_not_immediately_write(self):
        self.app.game_snapshot = {"half_period": 9}
        self.app.save_game_settings()
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 15)
        self.app.master.after.assert_called_once_with(
            60000, self.app._flush_pending_settings
        )
        self.assertEqual(self.backups(), [])

    def test_many_edits_schedule_one_minute_write_for_latest_value(self):
        for val in range(1, 51):
            self.app.game_snapshot = {"half_period": val}
            self.app.save_game_settings()
        self.assertEqual(self.app.master.after.call_count, 1)
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 15)
        self.app._flush_pending_settings()
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 50)
        self.assertEqual(len(self.backups()), 1)
        self.assertEqual(self.app._pending_settings_sections, {})
        self.assertIsNone(self.app._settings_autosave_job)

    def test_duplicate_auto_update_does_not_reschedule(self):
        self.app.game_snapshot = {"half_period": 12}
        self.app.save_game_settings()
        self.app.save_game_settings()
        self.assertEqual(self.app.master.after.call_count, 1)

    def test_game_and_screen_updates_are_saved_together(self):
        self.app.game_snapshot = {"half_period": 8}
        self.app.save_game_settings()
        self.app.operator_layout_var = Var("Widescreen")
        self.app.save_screen_settings()
        self.assertEqual(self.app.master.after.call_count, 1)
        self.app._flush_pending_settings()
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 8)
        self.assertEqual(
            self.disk()["screenSettings"]["operator_layout"], "Widescreen"
        )
        self.assertEqual(len(self.backups()), 1)

    def test_concurrent_sound_save_is_preserved_when_ui_flushes(self):
        self.app.game_snapshot = {"half_period": 11}
        self.app.save_game_settings()
        settings_manager.update_unified_settings(
            self.directory, {"soundSettings": {"volume": 30}}
        )
        self.app._flush_pending_settings()
        self.assertEqual(self.disk()["soundSettings"]["volume"], 30)
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 11)

    def test_identical_ui_snapshot_does_not_create_backup(self):
        self.app.save_game_settings()
        self.app._flush_pending_settings()
        self.assertEqual(self.backups(), [])

    def test_second_change_schedules_another_minute(self):
        self.app.game_snapshot = {"half_period": 8}
        self.app.save_game_settings()
        self.app._flush_pending_settings()
        self.app.game_snapshot = {"half_period": 9}
        self.app.save_game_settings()
        self.assertEqual(self.app.master.after.call_count, 2)

    def test_error_preserves_pending_changes_and_retries(self):
        self.app.game_snapshot = {"half_period": 10}
        self.app.save_game_settings()
        with patch.object(settings_manager, "update_unified_settings",
                          side_effect=PermissionError("locked")):
            self.assertFalse(self.app._flush_pending_settings())
        self.assertEqual(
            self.app._pending_settings_sections["gameSettings"]["half_period"],
            10
        )
        self.assertEqual(self.app.master.after.call_count, 2)
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 15)
        self.assertTrue(self.app._flush_pending_settings())
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 10)

    def test_normal_exit_flushes_unsaved_settings(self):
        self.app.game_snapshot = {"half_period": 9}
        self.app.save_game_settings()
        self.assertEqual(self.app.request_exit(), "break")
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 9)
        self.app.master.destroy.assert_called_once_with()

    def test_exit_failure_keeps_app_open_for_retry(self):
        self.app.game_snapshot = {"half_period": 9}
        self.app.save_game_settings()
        with patch.object(settings_manager, "update_unified_settings",
                          side_effect=PermissionError("locked")):
            self.assertEqual(self.app.request_exit(), "break")
        self.app.master.destroy.assert_not_called()
        self.app._stop_arduino_siren.assert_not_called()
        self.messagebox.showerror.assert_called_once()
        self.assertEqual(self.disk()["gameSettings"]["half_period"], 15)


if __name__ == "__main__":
    unittest.main()
