"""Protect the source draw and resume a separate tournament results CSV."""

import csv
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import csv_export
import csv_helpers
import csv_ui
import tournament_files


HEADER = [
    "Venue", "#", "White", "WScore", "Black", "BScore", "Penalties", "Comments"
]


class TournamentFileSeparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.draw = self.folder / "Tournament_Draw.csv"
        self.results = self.folder / "Tournament_Results.csv"
        with self.draw.open("w", encoding="utf-8-sig", newline="") as out:
            csv.writer(out).writerows([
                HEADER,
                ["Pool, east", "1", "A, White", "", "B, Black", "", "", ""],
                ["Pool, west", "2", "C", "", "D", "", "", ""],
            ])

    @staticmethod
    def read(path):
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            return list(csv.reader(stream))

    def export(self, game, white=4, black=3):
        return csv_export.write_game_results_to_csv(
            self.draw.name, str(self.folder), str(game),
            white, black, [], False, {}, {},
        )

    def test_result_filename_for_sample_and_custom_draws(self):
        self.assertEqual(
            tournament_files.results_path_for_draw(self.draw),
            str(self.results)
        )
        self.assertEqual(
            tournament_files.results_path_for_draw(self.folder / "Court_A_Draw.csv"),
            str(self.folder / "Court_A_Results.csv")
        )
        self.assertEqual(
            tournament_files.results_path_for_draw(self.folder / "Round1.csv"),
            str(self.folder / "Round1_Results.csv")
        )
        with self.assertRaisesRegex(ValueError, "original draw"):
            tournament_files.results_path_for_draw(self.results)

    def test_selecting_draw_creates_result_file_and_restart_preserves_scores(self):
        before = self.draw.read_bytes()
        self.assertEqual(tournament_files.ensure_results_file(self.draw),
                         str(self.results))
        self.assertEqual(self.draw.read_bytes(), before)
        self.assertEqual(self.results.read_bytes(), before)

        self.assertTrue(self.export(1))
        first = self.results.read_bytes()
        self.assertEqual(self.read(self.results)[1][3], "4")
        self.assertEqual(self.draw.read_bytes(), before)

        # Restart/select the SAME draw: it must not copy the template again.
        self.assertEqual(tournament_files.ensure_results_file(self.draw),
                         str(self.results))
        self.assertEqual(self.results.read_bytes(), first)
        self.assertTrue(self.export(2, white=1, black=2))
        rows = self.read(self.results)
        self.assertEqual((rows[1][3], rows[1][5]), ("4", "3"))
        self.assertEqual((rows[2][3], rows[2][5]), ("1", "2"))
        self.assertEqual(self.draw.read_bytes(), before)
        self.assertEqual(
            csv_helpers.parse_csv_team_names(self.draw.name, "1", str(self.folder)),
            ("A, White", "B, Black")
        )

    def test_existing_results_reused_without_clobbering(self):
        self.assertTrue(self.export(1))
        saved = self.results.read_bytes()
        self.assertEqual(tournament_files.ensure_results_file(self.draw),
                         str(self.results))
        self.assertEqual(self.results.read_bytes(), saved)

    def test_mismatched_draw_refuses_write_and_retains_previous_results(self):
        self.assertTrue(self.export(1))
        before = self.results.read_bytes()
        rows = self.read(self.draw)
        rows[2][2] = "Unexpected replacement team"
        with self.draw.open("w", encoding="utf-8-sig", newline="") as stream:
            csv.writer(stream).writerows(rows)
        with self.assertRaisesRegex(ValueError, "does not match"):
            tournament_files.ensure_results_file(self.draw)
        self.assertFalse(self.export(2))
        self.assertEqual(self.results.read_bytes(), before)

    def test_changed_draw_results_columns_do_not_erase_completed_games(self):
        self.assertTrue(self.export(1))
        existing = self.results.read_bytes()
        rows = self.read(self.draw)
        rows[1][3] = "12"
        with self.draw.open("w", encoding="utf-8-sig", newline="") as stream:
            csv.writer(stream).writerows(rows)
        tournament_files.ensure_results_file(self.draw)
        self.assertEqual(self.results.read_bytes(), existing)

    def test_incomplete_results_file_is_not_silently_replaced(self):
        self.results.write_text("incomplete", encoding="utf-8")
        original = self.results.read_bytes()
        with self.assertRaisesRegex(ValueError, "does not match"):
            tournament_files.ensure_results_file(self.draw)
        self.assertEqual(self.results.read_bytes(), original)
        self.assertFalse(self.export(1))
        self.assertEqual(self.results.read_bytes(), original)

    def test_selector_shows_draws_not_generated_result_files(self):
        self.results.write_text("results", encoding="utf-8")
        (self.folder / "Other_Results.csv").write_text("results", encoding="utf-8")
        (self.folder / "Court_B_Draw.csv").write_text("draw", encoding="utf-8")
        self.assertEqual(
            csv_ui.get_csv_files(str(self.folder)),
            ["Court_B_Draw.csv", "Tournament_Draw.csv"]
        )

    def test_sample_copy_places_draw_in_app_root_once(self):
        root = self.folder / "source"
        assets = root / "assets"
        assets.mkdir(parents=True)
        template = assets / "Tournament_Draw.csv"
        template.write_bytes(self.draw.read_bytes())
        self.assertTrue(tournament_files.seed_sample_draw(str(root)))
        sample = root / "Tournament_Draw.csv"
        self.assertEqual(sample.read_bytes(), template.read_bytes())
        sample.write_bytes(b"operator-modified-draw")
        self.assertFalse(tournament_files.seed_sample_draw(str(root)))
        self.assertEqual(sample.read_bytes(), b"operator-modified-draw")
        self.assertEqual(template.read_bytes(), self.draw.read_bytes())

    def test_failed_results_update_preserves_draw_and_prior_results(self):
        self.assertTrue(self.export(1))
        draw_bytes, results_bytes = self.draw.read_bytes(), self.results.read_bytes()
        with patch.object(csv_export.os, "replace",
                          side_effect=PermissionError("results locked")):
            with self.assertRaisesRegex(PermissionError, "results locked"):
                self.export(2)
        self.assertEqual(self.draw.read_bytes(), draw_bytes)
        self.assertEqual(self.results.read_bytes(), results_bytes)
        self.assertEqual(list(self.folder.glob(".uwh_results_*.tmp")), [])

    def test_invalid_draw_does_not_create_results(self):
        self.draw.write_text("wrong,headers\n1,A\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "game-number"):
            tournament_files.ensure_results_file(self.draw)
        self.assertFalse(self.results.exists())

    def test_results_collision_from_other_draw_does_not_overwrite(self):
        self.assertTrue(self.export(1))
        before = self.results.read_bytes()
        collision = self.folder / "Tournament.csv"
        collision.write_text("Venue,#,White,WScore,Black,BScore,Penalties,Comments\n"
                             "Other,1,X,,Y,,,\n", encoding="utf-8")
        # 'Tournament.csv' derives the same output name as 'Tournament_Draw.csv'.
        with self.assertRaisesRegex(ValueError, "does not match"):
            tournament_files.ensure_results_file(collision)
        self.assertEqual(self.results.read_bytes(), before)

    @unittest.skipIf(os.name == "nt", "Creating symlinks may require Windows privileges")
    def test_results_symlink_to_draw_is_rejected(self):
        self.results.symlink_to(self.draw)
        before = self.draw.read_bytes()
        with self.assertRaisesRegex(ValueError, "must not"):
            tournament_files.ensure_results_file(self.draw)
        self.assertEqual(self.draw.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
