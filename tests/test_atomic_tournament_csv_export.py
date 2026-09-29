"""Tournament CSV exports must never truncate the draw on failed writes."""
import csv
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import csv_export
import game_flow


class Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class AtomicTournamentExportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.draw = Path(self.folder.name) / "Draw.csv"
        with self.draw.open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream)
            writer.writerow([
                "Venue", "#", "White", "WScore",
                "Black", "BScore", "Penalties", "Comments"
            ])
            writer.writerow([
                "Pool, east", "1", 'White "A", team', "",
                "Black, B", "", "", ""
            ])
            writer.writerow([
                "Pool, west", "2", "Other White", "",
                "Other Black", "", "", ""
            ])

    def export(self, game="1"):
        return csv_export.write_game_results_to_csv(
            self.draw.name, self.folder.name, game, 4, 3,
            [{"team": "White", "cap": "7", "duration": "120"}],
            True, {"5": 2}, {"8": 1},
        )

    def rows(self):
        with self.draw.open("r", newline="", encoding="utf-8-sig") as source:
            return list(csv.reader(source))

    def staged(self):
        return list(self.draw.parent.glob(".uwh_draw_*.tmp"))

    def test_successful_replace_retains_entire_draw_and_utf8_bom(self):
        self.assertTrue(self.export())
        result = self.rows()
        self.assertEqual(result[1][0], "Pool, east")
        self.assertEqual(result[1][2], 'White "A", team')
        self.assertEqual(result[1][4], "Black, B")
        self.assertEqual(
            result[1][3:],
            ["4", "Black, B", "3", "W#7(120)", "W#5(2), B#8(1)"],
        )
        self.assertEqual(result[2][3], "")
        self.assertEqual(result[2][5], "")
        self.assertTrue(self.draw.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertEqual(self.staged(), [])

    def test_replace_gets_complete_staged_file_in_original_directory(self):
        before = self.draw.read_bytes()
        original_replace = os.replace
        captured = []

        def guarded_replace(source, target):
            self.assertEqual(self.draw.read_bytes(), before)
            self.assertEqual(Path(source).parent, self.draw.parent)
            self.assertEqual(Path(target), self.draw)
            self.assertNotEqual(Path(source), self.draw)
            with open(source, "r", newline="", encoding="utf-8-sig") as stream:
                staged_rows = list(csv.reader(stream))
            self.assertEqual(staged_rows[1][3], "4")
            self.assertEqual(staged_rows[1][5], "3")
            captured.append(source)
            original_replace(source, target)

        with patch.object(csv_export.os, "replace",
                          side_effect=guarded_replace):
            self.assertTrue(self.export())
        self.assertEqual(len(captured), 1)
        self.assertFalse(Path(captured[0]).exists())
        self.assertEqual(self.staged(), [])

    def test_partial_csv_writer_failure_leaves_original_intact(self):
        before = self.draw.read_bytes()

        class PartialWriter:
            def writerows(self, rows):
                # Simulate the disk write failing in the middle of the draw.
                self.stream.write("partial,tournament,")
                raise OSError("simulated disk-full condition")

            def __init__(self, stream):
                self.stream = stream

        with patch.object(csv_export.csv, "writer",
                          side_effect=PartialWriter):
            with self.assertRaisesRegex(OSError, "disk-full"):
                self.export()

        self.assertEqual(self.draw.read_bytes(), before)
        self.assertEqual(self.staged(), [])

    def test_flush_failure_leaves_original_intact(self):
        before = self.draw.read_bytes()
        with patch.object(csv_export.os, "fsync",
                          side_effect=OSError("simulated flush error")):
            with self.assertRaisesRegex(OSError, "flush error"):
                self.export()
        self.assertEqual(self.draw.read_bytes(), before)
        self.assertEqual(self.staged(), [])

    def test_replace_permission_denied_keeps_original_and_removes_temp(self):
        before = self.draw.read_bytes()
        with patch.object(csv_export.os, "replace",
                          side_effect=PermissionError("draw locked by Excel")):
            with self.assertRaisesRegex(PermissionError, "locked by Excel"):
                self.export()
        self.assertEqual(self.draw.read_bytes(), before)
        self.assertEqual(self.staged(), [])

    def test_chmod_failure_keeps_original_and_removes_temp(self):
        before = self.draw.read_bytes()
        with patch.object(csv_export.os, "chmod",
                          side_effect=OSError("permission failed")):
            with self.assertRaisesRegex(OSError, "permission failed"):
                self.export()
        self.assertEqual(self.draw.read_bytes(), before)
        self.assertEqual(self.staged(), [])

    def test_original_file_mode_is_preserved_on_replacement(self):
        # On Raspberry Pi OS this includes group read/write permissions;
        # on Windows os.chmod supports the read-only attribute subset.
        os.chmod(self.draw, 0o640)
        previous_mode = stat.S_IMODE(self.draw.stat().st_mode)
        self.assertTrue(self.export())
        self.assertEqual(
            stat.S_IMODE(self.draw.stat().st_mode), previous_mode
        )

    def test_invalid_game_keeps_original_and_does_not_make_temp_file(self):
        before = self.draw.read_bytes()
        with patch.object(csv_export.tempfile, "NamedTemporaryFile") as make:
            self.assertFalse(self.export("999"))
        make.assert_not_called()
        self.assertEqual(self.draw.read_bytes(), before)
        self.assertEqual(self.staged(), [])

    def test_locked_draw_does_not_advance_or_erase_live_game(self):
        before = self.draw.read_bytes()
        app = SimpleNamespace(
            get_current_game_number=lambda: "1",
            white_score_var=Var(4),
            black_score_var=Var(3),
            csv_var=Var(self.draw.name),
            use_tournament_list_var=Var(True),
            engine=SimpleNamespace(
                stored_penalties=[{
                    "team": "White", "cap": "7", "duration": "120"
                }],
                clear_goal_scorers=Mock(),
            ),
            log_game_event=Mock(),
            clear_all_penalties=Mock(),
            advance_to_next_game=Mock(),
            update_team_names_display=Mock(),
            write_game_results_to_csv=lambda game, white, black, penalties:
                self.export(game),
        )

        with patch.object(
            csv_export.os, "replace",
            side_effect=PermissionError("file is in use")
        ):
            with self.assertRaisesRegex(PermissionError, "in use"):
                game_flow.export_and_reset_game_at_break(app)
        self.assertEqual(self.draw.read_bytes(), before)
        self.assertEqual(self.staged(), [])
        self.assertEqual(app.white_score_var.get(), 4)
        self.assertEqual(app.black_score_var.get(), 3)
        self.assertEqual(len(app.engine.stored_penalties), 1)
        app.engine.clear_goal_scorers.assert_not_called()
        app.log_game_event.assert_not_called()
        app.clear_all_penalties.assert_not_called()
        app.advance_to_next_game.assert_not_called()


if __name__ == "__main__":
    unittest.main()
