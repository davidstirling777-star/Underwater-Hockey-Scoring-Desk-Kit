"""Scorer export regression tests for the referee's special goal labels."""
import csv
from pathlib import Path
import tempfile
import unittest

import csv_export
from game_engine import GameEngine


class ScorerExportLabelsTests(unittest.TestCase):
    def test_penalty_goal_and_unknown_use_established_short_labels(self):
        actual = csv_export.build_scorer_comments(
            True,
            {"Penalty Goal": 2, "Unknown": 1},
            {"Penalty Goal": 1, "Unknown": 3},
        )
        self.assertEqual(
            actual, "W#PG(2), W#UNK(1), B#PG(1), B#UNK(3)"
        )

    def test_cap_numbers_remain_sorted_numerically_before_special_goals(self):
        actual = csv_export.build_scorer_comments(
            True,
            {"11": 1, "Penalty Goal": 2, "2": 3, "Unknown": 1},
            {"10": 2, "1": 1, "Unknown": 4},
        )
        self.assertEqual(
            actual,
            "W#2(3), W#11(1), W#PG(2), W#UNK(1), "
            "B#1(1), B#10(2), B#UNK(4)"
        )

    def test_numeric_only_output_and_spacing_are_unchanged(self):
        self.assertEqual(
            csv_export.build_scorer_comments(
                True, {"12": 1, "3": 2}, {"7": 1},
            ),
            "W#3(2), W#12(1), B#7(1)",
        )

    def test_record_scorers_disabled_keeps_comments_blank(self):
        self.assertEqual(
            csv_export.build_scorer_comments(
                False, {"Penalty Goal": 1}, {"Unknown": 1}
            ),
            "",
        )

    def test_no_goals_keeps_comments_blank(self):
        self.assertEqual(csv_export.build_scorer_comments(True, {}, {}), "")

    def test_export_matches_existing_scorer_formatter_notation(self):
        white = {"5": 1, "Penalty Goal": 1, "Unknown": 2}
        black = {"12": 1, "Penalty Goal": 2, "Unknown": 1}
        exported = csv_export.build_scorer_comments(True, white, black)
        previously_displayed = csv_export.format_goal_scorers_comment({
            "White": white, "Black": black
        })
        # CSV comments retain the original comma+space layout.
        self.assertEqual(exported.replace(", ", ","), previously_displayed)

    def test_actual_goal_recording_exports_all_scorer_types(self):
        engine = GameEngine()
        engine.record_goal_scorer("White", "Penalty Goal")
        engine.record_goal_scorer("White", "Unknown")
        engine.record_goal_scorer("White", "8")
        engine.record_goal_scorer("Black", "Penalty Goal")
        engine.record_goal_scorer("Black", "Unknown")
        self.assertEqual(
            csv_export.build_scorer_comments(
                True, engine.white_goal_scorers, engine.black_goal_scorers
            ),
            "W#8(1), W#PG(1), W#UNK(1), B#PG(1), B#UNK(1)",
        )

    def test_tournament_writer_saves_special_labels_without_touching_other_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            draw = Path(folder) / "Draw.csv"
            with draw.open("w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.writer(stream)
                writer.writerow([
                    "Venue", "#", "White", "WScore", "Black",
                    "BScore", "Penalties", "Comments"
                ])
                writer.writerow([
                    "Pool, A", "4", "O'Brien, White", "",
                    "Black", "", "", ""
                ])
                writer.writerow([
                    "Pool, B", "5", "Other White", "",
                    "Other Black", "", "", ""
                ])

            saved = csv_export.write_game_results_to_csv(
                csv_file=draw.name,
                base_dir=folder,
                game_number="4",
                white_score=3,
                black_score=2,
                penalties=[],
                record_scorers=True,
                white_goal_scorers={
                    "Penalty Goal": 1, "Unknown": 1, "7": 1
                },
                black_goal_scorers={
                    "Penalty Goal": 1, "Unknown": 1
                },
            )
            self.assertTrue(saved)
            with draw.open("r", newline="", encoding="utf-8-sig") as source:
                self.assertEqual(list(csv.reader(source))[1][3], "")
            with (Path(folder) / "Draw_Results.csv").open(
                "r", newline="", encoding="utf-8-sig"
            ) as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(rows[1][2], "O'Brien, White")
            self.assertEqual(rows[1][3], "3")
            self.assertEqual(rows[1][5], "2")
            self.assertEqual(
                rows[1][7],
                "W#7(1), W#PG(1), W#UNK(1), B#PG(1), B#UNK(1)",
            )
            self.assertEqual(rows[2][3], "")
            self.assertEqual(rows[2][5], "")
            self.assertEqual(rows[2][7], "")


if __name__ == "__main__":
    unittest.main()
