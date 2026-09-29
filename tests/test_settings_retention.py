"""Keep five settings backups and avoid clock-driven hardware port writes."""
import ast
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import settings_manager


def _isolated_function(file, name, namespace):
    path = Path(__file__).resolve().parents[1] / file
    module = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [n for n in module.body
             if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(nodes) != 1:
        raise AssertionError(f"Missing function {name} in {file}")
    subset = ast.fix_missing_locations(
        ast.Module(body=nodes, type_ignores=[])
    )
    exec(compile(subset, str(path), "exec"), namespace)
    return namespace[name]


class FiveBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = self.temp.name
        self.active = Path(self.directory) / "settings.json"

    def backups(self):
        return sorted(Path(self.directory).glob("settings_old_*.json"))

    def save(self, v):
        settings_manager.save_unified_settings(self.directory, {"version": v})

    def test_latest_five_versions_are_retained_after_many_saves(self):
        for v in range(12):
            self.save(v)
        self.assertEqual(len(self.backups()), 5)
        self.assertEqual(
            [json.loads(p.read_text())["version"] for p in self.backups()],
            [6, 7, 8, 9, 10]
        )
        self.assertEqual(json.loads(self.active.read_text()), {"version": 11})

    def test_unrelated_files_are_not_purged(self):
        self.save(0)
        unrelated = Path(self.directory) / "settings_old_manual_backup.json"
        unrelated.write_text('{"manual": true}', encoding="utf-8")
        other = Path(self.directory) / "zigbee_config.json"
        other.write_text("{}")
        for version in range(1, 9):
            self.save(version)
        self.assertEqual(len(self.backups()), 6)
        self.assertTrue(unrelated.exists())
        self.assertTrue(other.exists())
        self.assertEqual(len([
            p for p in self.backups() if p.name != unrelated.name
        ]), 5)

    def test_no_op_save_cleans_preexisting_backups(self):
        self.save(0)
        for version in range(1, 10):
            timestamp = f"2026-09-29_16-10-{version:02d}_000000"
            (Path(self.directory) /
             f"settings_old_{timestamp}.json").write_text(
                json.dumps({"version": version}),
                encoding="utf-8"
            )
        settings_manager.save_unified_settings(
            self.directory, {"version": 0}
        )
        self.assertEqual(len(self.backups()), 5)
        self.assertEqual(json.loads(self.active.read_text()), {"version": 0})

    def test_replacement_failure_does_not_discard_existing_backups(self):
        self.save(0)
        self.save(1)
        old_names = {p.name for p in self.backups()}
        original_replace = os.replace

        def deny_new(src, dst):
            if os.fspath(dst) == os.fspath(self.active):
                raise PermissionError("active locked")
            return original_replace(src, dst)

        with patch.object(settings_manager.os, "replace",
                          side_effect=deny_new):
            with self.assertRaises(PermissionError):
                self.save(2)
        self.assertTrue(old_names.issubset({p.name for p in self.backups()}))
        self.assertEqual(json.loads(self.active.read_text()), {"version": 1})

    def test_failure_to_delete_one_old_backup_does_not_break_live_save(self):
        for v in range(7):
            self.save(v)
        first = self.backups()[0]
        real_unlink = os.unlink

        def deny_one(path, *args, **kwargs):
            if str(path) == str(first):
                raise PermissionError("backup locked")
            return real_unlink(path, *args, **kwargs)

        # Saving the next version must succeed even when Windows or an
        # antivirus holds an old backup open.
        with patch.object(settings_manager.os, "unlink",
                          side_effect=deny_one):
            self.save(7)
        self.assertEqual(json.loads(self.active.read_text()), {"version": 7})
        self.assertTrue(first.exists())


class HardwareCacheWriteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = self.temp.name
        self.file = Path(self.directory) / "settings.json"

    def save_ports(self, arduino, zigbee):
        fn = _isolated_function(
            "serial_siren_listener.py",
            "save_hardware_ports_to_json",
            {"os": os, "time": time, "settings_manager": settings_manager,
             "_settings_path": lambda: str(self.file),
             "_debug": lambda text: None},
        )
        fn(arduino, zigbee)

    def test_unchanged_ports_skip_timestamp_rewrites_and_backups(self):
        self.save_ports("COM3", "COM4")
        before = self.file.read_bytes()
        for _ in range(30):
            self.save_ports("COM3", "COM4")
        self.assertEqual(self.file.read_bytes(), before)
        self.assertEqual(
            list(Path(self.directory).glob("settings_old_*.json")), []
        )

    def test_changed_port_still_saved_and_archived(self):
        self.save_ports("COM3", "COM4")
        self.save_ports("COM5", "COM4")
        data = settings_manager.load_unified_settings(self.directory)
        self.assertEqual(data["hardwareDetection"]["arduino_port"], "COM5")
        self.assertEqual(
            len(list(Path(self.directory).glob("settings_old_*.json"))), 1
        )

    def test_startup_hardware_cache_avoids_unchanged_port_backup(self):
        fn = _isolated_function(
            "hardware_detection.py", "save_hardware_detection_cache",
            {"datetime": __import__("datetime")},
        )
        settings_manager.save_unified_settings(self.directory, {
            "hardwareDetection": {"arduino_port": "COM3",
                                  "zigbee_port": "COM4",
                                  "last_detected": "older"}
        })
        orig = self.file.read_bytes()
        fn("COM3", "COM4",
           lambda: settings_manager.load_unified_settings(self.directory),
           lambda data: settings_manager.save_unified_settings(
               self.directory, data
           ))
        self.assertEqual(self.file.read_bytes(), orig)


if __name__ == "__main__":
    unittest.main()
