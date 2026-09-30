"""Results export must locate its game column by header, not by position."""
import csv
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import csv_export
import csv_helpers
import game_flow


class Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class GameColumnExportTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.file = Path(self.folder.name) / "Draw.csv"
        self.results_file = Path(self.folder.name) / "Draw_Results.csv"

    def create_draw(self, header, *rows):
        # Each test/subtest represents a distinct new tournament.
        self.results_file.unlink(missing_ok=True)
        with self.file.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(rows)

    def read_draw(self):
        with self.file.open("r", encoding="utf-8-sig", newline="") as stream:
            return list(csv.reader(stream))

    def read_results(self):
        with self.results_file.open("r", encoding="utf-8-sig", newline="") as stream:
            return list(csv.reader(stream))

    def export(self, game_number, white=4, black=3, penalties=(),
               record_scorers=False):
        return csv_export.write_game_results_to_csv(
            self.file.name, self.folder.name,
            game_number, white, black, penalties,
            record_scorers, {"5": 2}, {"8": 1},
        )

    def test_game_column_first_prevents_other_row_overwrite(self):
        self.create_draw(
            ["Game", "Venue", "White", "WScore", "Black",
             "BScore", "Penalties", "Comments"],
            ["1", "2", "White One", "", "Black One", "", "", ""],
            ["2", "1", "White Two", "", "Black Two", "", "", ""],
        )
        # Old row[1] logic would silently update game 1 (Venue='2').
        self.assertTrue(self.export("2"))
        rows = self.read_results()
        self.assertEqual(rows[1][3:8], ["", "Black One", "", "", ""])
        self.assertEqual(rows[2][3], "4")
        self.assertEqual(rows[2][5], "3")
        self.assertEqual(rows[2][2], "White Two")
        self.assertEqual(rows[2][4], "Black Two")
        self.assertEqual(csv_helpers.parse_csv_game_numbers(
            self.file.name, self.folder.name
        ), ["1", "2"])

    def test_game_column_third_and_quoted_team_names_preserved(self):
        self.create_draw(
            ["Pool", "White", "#", "Black", "WScore",
             "BScore", "Penalties", "Comments"],
            ["West, north", 'Team "A", blue', "11",
             "Team B, red", "", "", "", ""],
        )
        self.assertTrue(self.export("11", penalties=(
            {"team": "White", "cap": "7", "duration": "120"},
        ), record_scorers=True))
        record = self.read_results()[1]
        self.assertEqual(record[0], "West, north")
        self.assertEqual(record[1], 'Team "A", blue')
        self.assertEqual(record[3], "Team B, red")
        self.assertEqual(record[4:8], [
            "4", "3", "W#7(120)", "W#5(2), B#8(1)"
        ])
        self.assertEqual(csv_helpers.parse_csv_team_names(
            self.file.name, "11", self.folder.name
        ), ('Team "A", blue', "Team B, red"))

    def test_all_reader_game_header_aliases_are_accepted(self):
        for alias in ("#", "game", "game#", "game_number"):
            with self.subTest(alias=alias):
                self.create_draw(
                    ["White", alias, "BScore", "Black",
                     "Comments", "WScore", "Penalties"],
                    ["White Team", "3", "", "Black Team", "", "", ""],
                )
                self.assertTrue(self.export("3"))
                row = self.read_results()[1]
                self.assertEqual(row[2], "3")
                self.assertEqual(row[5], "4")
                self.assertEqual(row[0], "White Team")
                self.assertEqual(row[3], "Black Team")

    def test_header_case_and_spaces_do_not_prevent_export(self):
        self.create_draw(
            [" wscore ", " BLACK ", " GAME_NUMBER ",
             " bscore ", " PENALTIES ", " COMMENTS "],
            ["", "Black", "9", "", "", ""],
        )
        self.assertTrue(self.export("9"))
        self.assertEqual(self.read_results()[1], [
            "4", "Black", "9", "3", "", ""
        ])

    def test_zero_padded_number_matches_game_list_number(self):
        self.create_draw(
            ["#", "White", "WScore", "Black",
             "BScore", "Penalties", "Comments"],
            ["007", "White", "", "Black", "", "", ""],
        )
        self.assertEqual(csv_helpers.parse_csv_game_numbers(
            self.file.name, self.folder.name
        ), ["7"])
        self.assertTrue(self.export("7"))
        self.assertEqual(self.read_results()[1][2], "4")

    def test_nonnumeric_game_id_remains_exact_match(self):
        self.create_draw(
            ["#", "WScore", "BScore", "Penalties", "Comments"],
            ["F1", "", "", "", ""],
        )
        self.assertTrue(self.export("F1"))
        self.assertEqual(self.read_results()[1][1:3], ["4", "3"])

    def test_duplicate_game_number_is_rejected_without_writing(self):
        self.create_draw(
            ["#", "WScore", "BScore", "Penalties", "Comments"],
            ["1", "", "", "", ""],
            ["1", "", "", "", ""],
        )
        original = self.file.read_bytes()
        with patch("builtins.print") as printed:
            self.assertFalse(self.export("1"))
        self.assertEqual(self.file.read_bytes(), original)
        self.assertIn("multiple rows", printed.call_args.args[0])

    def test_zero_padded_duplicate_is_also_rejected(self):
        self.create_draw(
            ["#", "WScore", "BScore", "Penalties", "Comments"],
            ["007", "", "", "", ""],
            ["7", "", "", "", ""],
        )
        original = self.file.read_bytes()
        self.assertFalse(self.export("7"))
        self.assertEqual(self.file.read_bytes(), original)

    def test_no_game_number_header_keeps_tournament_file_intact(self):
        self.create_draw(
            ["Venue", "White", "WScore", "Black",
             "BScore", "Penalties", "Comments"],
            ["1", "White", "", "Black", "", "", ""],
        )
        original = self.file.read_bytes()
        self.assertFalse(self.export("1"))
        self.assertEqual(self.file.read_bytes(), original)

    def test_missing_required_score_column_keeps_file_intact(self):
        self.create_draw(
            ["#", "White", "WScore", "Black",
             "BScore", "Comments"],
            ["1", "White", "", "Black", "", ""],
        )
        original = self.file.read_bytes()
        self.assertFalse(self.export("1"))
        self.assertEqual(self.file.read_bytes(), original)

    def test_unmatched_or_blank_game_does_not_modify_file(self):
        self.create_draw(
            ["#", "WScore", "BScore", "Penalties", "Comments"],
            ["2", "", "", "", ""],
        )
        original = self.file.read_bytes()
        self.assertFalse(self.export("3"))
        self.assertFalse(self.export(""))
        self.assertEqual(self.file.read_bytes(), original)

    def test_short_game_row_is_padded_only_when_it_matches(self):
        self.create_draw(
            ["#", "WScore", "BScore", "Penalties", "Comments"],
            ["2"],
        )
        self.assertTrue(self.export("2"))
        self.assertEqual(self.read_results()[1], ["2", "4", "3", "", ""])

    def test_failed_ambiguous_export_preserves_live_score_and_game(self):
        self.create_draw(
            ["#", "WScore", "BScore", "Penalties", "Comments"],
            ["2", "", "", "", ""],
            ["002", "", "", "", ""],
        )
        original = self.file.read_bytes()
        app = SimpleNamespace(
            get_current_game_number=lambda: "2",
            white_score_var=Var(4),
            black_score_var=Var(3),
            csv_var=Var(self.file.name),
            use_tournament_list_var=Var(True),
            engine=SimpleNamespace(
                stored_penalties=[{
                    "team": "White", "cap": "7", "duration": 120
                }],
                clear_goal_scorers=Mock(),
            ),
            log_game_event=Mock(),
            advance_to_next_game=Mock(),
            clear_all_penalties=Mock(),
            write_game_results_to_csv=lambda game, white, black, penalties:
                self.export(game, white, black, penalties),
        )

        self.assertFalse(game_flow.export_and_reset_game_at_break(app))
        self.assertEqual((app.white_score_var.get(),
                          app.black_score_var.get()), (4, 3))
        self.assertEqual(len(app.engine.stored_penalties), 1)
        self.assertEqual(self.file.read_bytes(), original)
        app.advance_to_next_game.assert_not_called()
        app.log_game_event.assert_not_called()


if __name__ == "__main__":
    unittest.main()
