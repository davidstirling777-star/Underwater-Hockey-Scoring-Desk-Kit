"""Tests for atomic settings saves and timestamped previous-file backups.

The GUI, serial dongle and MQTT broker are not required.
"""
import ast
import datetime
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import settings_manager


def _backups(folder):
    return sorted(Path(folder).glob("settings_old_*.json"))


class SettingsBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = self.temp.name
        self.active = Path(self.directory) / "settings.json"

    def _save(self, settings):
        settings_manager.save_unified_settings(self.directory, settings)

    def test_first_save_has_no_previous_version(self):
        first = {"zigbeeSettings": {"mqtt_password": "private"}, "gameSettings": {}}
        self._save(first)
        self.assertEqual(settings_manager.load_unified_settings(self.directory), first)
        self.assertEqual(_backups(self.directory), [])

    def test_new_file_active_and_timestamped_backup_keeps_all_old_sections(self):
        first = {"soundSettings": {"siren": "a"},
                 "zigbeeSettings": {"mqtt_password": "private"},
                 "gameSettings": {"sudden_death_game_break": 0.6}}
        updated = {**first, "gameSettings": {"sudden_death_game_break": 1.0}}
        self._save(first)
        self._save(updated)
        self.assertEqual(settings_manager.load_unified_settings(self.directory), updated)
        backups = _backups(self.directory)
        self.assertEqual(len(backups), 1)
        self.assertTrue(backups[0].name.startswith("settings_old_"))
        datetime.datetime.strptime(
            backups[0].name[len("settings_old_"):-len(".json")],
            "%Y-%m-%d_%H-%M-%S_%f"
        )
        self.assertEqual(json.loads(backups[0].read_text()), first)

    def test_rapid_successive_saves_have_distinct_preserved_backups(self):
        for version in range(6):
            self._save({"version": version})
        self.assertEqual(json.loads(self.active.read_text()), {"version": 5})
        self.assertEqual(len(_backups(self.directory)), 5)
        self.assertEqual(
            [json.loads(f.read_text())["version"] for f in _backups(self.directory)],
            list(range(5))
        )

    def test_same_settings_do_not_make_spurious_backup(self):
        self._save({"settings": [1, 2]})
        self._save({"settings": [1, 2]})
        self.assertEqual(_backups(self.directory), [])

    def test_invalid_existing_json_is_not_overwritten_or_reset(self):
        original = b'{"zigbeeSettings": {"password": "secret",'
        self.active.write_bytes(original)
        with self.assertRaisesRegex(ValueError, "not been overwritten"):
            self._save({"zigbeeSettings": {}})
        self.assertEqual(self.active.read_bytes(), original)
        self.assertEqual(_backups(self.directory), [])
        with patch.object(settings_manager, "migrate_legacy_settings") as migrate:
            with self.assertRaisesRegex(ValueError, "not been overwritten"):
                settings_manager.load_unified_settings(self.directory)
            migrate.assert_not_called()

    def test_invalid_utf8_is_preserved(self):
        original = bytes([0xff, 0xfe, 0x80])
        self.active.write_bytes(original)
        with self.assertRaisesRegex(ValueError, "not been overwritten"):
            self._save({"version": 2})
        self.assertEqual(self.active.read_bytes(), original)

    def test_existing_valid_non_object_is_never_replaced(self):
        self.active.write_text("[1, 2]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "expected a JSON object"):
            self._save({"version": 2})
        self.assertEqual(self.active.read_text(), "[1, 2]")

    def test_invalid_new_value_fails_without_touching_old(self):
        self._save({"version": 1})
        old = self.active.read_bytes()
        with self.assertRaises(TypeError):
            self._save({"bad": object()})
        self.assertEqual(self.active.read_bytes(), old)
        self.assertEqual(_backups(self.directory), [])

    def test_failed_atomic_replacement_leaves_live_file_intact(self):
        self._save({"version": 1})
        original_replace = os.replace

        def deny_active(src, dst):
            if os.fspath(dst) == os.fspath(self.active):
                raise PermissionError("settings.json locked")
            return original_replace(src, dst)

        with patch.object(settings_manager.os, "replace", side_effect=deny_active):
            with self.assertRaisesRegex(PermissionError, "locked"):
                self._save({"version": 2})

        self.assertEqual(json.loads(self.active.read_text()), {"version": 1})
        self.assertEqual(json.loads(_backups(self.directory)[0].read_text()), {"version": 1})
        self.assertEqual(list(Path(self.directory).glob("*.tmp")), [])

    def test_backup_collision_gets_unique_filename(self):
        self._save({"version": 1})
        with patch.object(settings_manager, "_previous_settings_backup_path",
                          wraps=settings_manager._previous_settings_backup_path):
            self._save({"version": 2})
        self._save({"version": 3})
        self.assertEqual(len(_backups(self.directory)), 2)

    def test_backup_folder_is_same_as_active_settings(self):
        self._save({"version": 1})
        self._save({"version": 2})
        self.assertEqual(_backups(self.directory)[0].parent, self.active.parent)


def _extract_method(path, function_name, globals_dict):
    source = Path(__file__).resolve().parents[1] / path
    parsed = ast.parse(source.read_text(encoding="utf-8"))
    matching = [
        node for node in ast.walk(parsed)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    if len(matching) != 1:
        raise AssertionError(f"Expected one {function_name}, found {len(matching)}")
    extracted = matching[0]
    # For these methods, loading only the function avoids optional USB and
    # MQTT dependencies on GitHub's headless test runners.
    module = ast.fix_missing_locations(
        ast.Module(body=[extracted], type_ignores=[])
    )
    globals_dict.setdefault("Dict", dict)
    globals_dict.setdefault("Any", object)
    exec(compile(module, str(source), "exec"), globals_dict)
    return globals_dict[function_name]


class IndependentWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = self.temp.name

    def test_zigbee_uses_central_backup_save_without_losing_other_sections(self):
        settings_manager.save_unified_settings(self.directory, {
            "gameSettings": {"half_period": 15},
            "zigbeeSettings": {"mqtt_broker": "old"},
        })
        save = _extract_method("zigbee_siren.py", "save_config", {
            "settings_manager": settings_manager,
            "_settings_directory": lambda: self.directory,
        })
        controller = type("Controller", (), {
            "logger": Mock(), "config": {}
        })()
        save(controller, {"mqtt_broker": "new"})
        result = settings_manager.load_unified_settings(self.directory)
        self.assertEqual(result["gameSettings"]["half_period"], 15)
        self.assertEqual(result["zigbeeSettings"]["mqtt_broker"], "new")
        self.assertEqual(len(_backups(self.directory)), 1)

    def test_zigbee_refuses_to_destroy_corrupt_old_file(self):
        active = Path(self.directory) / "settings.json"
        raw = b'{"half_period":'
        active.write_bytes(raw)
        save = _extract_method("zigbee_siren.py", "save_config", {
            "settings_manager": settings_manager,
            "_settings_directory": lambda: self.directory,
        })
        logger = Mock()
        controller = type("Controller", (), {"logger": logger, "config": {}})()
        with self.assertRaises(ValueError):
            save(controller, {"mqtt_broker": "changed"})
        logger.error.assert_called_once()
        self.assertEqual(active.read_bytes(), raw)

    def test_serial_port_cache_uses_central_writer(self):
        settings_manager.save_unified_settings(self.directory, {
            "gameSettings": {"half_period": 5}
        })
        save = _extract_method("serial_siren_listener.py",
                               "save_hardware_ports_to_json", {
                                   "settings_manager": settings_manager,
                                   "os": os, "time": __import__("time"),
                                   "_settings_path": lambda: str(Path(self.directory) / "settings.json"),
                                   "_debug": lambda message: None,
                               })
        save("COM3", "COM4")
        new = settings_manager.load_unified_settings(self.directory)
        self.assertEqual(new["gameSettings"]["half_period"], 5)
        self.assertEqual(new["hardwareDetection"]["arduino_port"], "COM3")
        self.assertEqual(len(_backups(self.directory)), 1)

    def test_serial_does_not_replace_corrupt_settings_with_port_only_file(self):
        active = Path(self.directory) / "settings.json"
        original = b'{"unclosed":'
        active.write_bytes(original)
        save = _extract_method("serial_siren_listener.py",
                               "save_hardware_ports_to_json", {
                                   "settings_manager": settings_manager,
                                   "os": os, "time": __import__("time"),
                                   "_settings_path": lambda: str(active),
                                   "_debug": lambda message: None,
                               })
        with patch("builtins.print") as output:
            save("COM3", "COM4")
        self.assertIn("Hardware port save failed", output.call_args.args[0])
        self.assertEqual(active.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
