"""Tournament draw CSV regression tests: quoted fields must not shift columns."""
import csv
from pathlib import Path
import tempfile
import unittest

import csv_export
import csv_helpers


class TournamentCSVParsingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = self.temp.name
        self.file = Path(self.directory) / "Draw.csv"

    def write(self, header, *records, encoding="utf-8-sig"):
        with self.file.open("w", encoding=encoding, newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(records)

    def games(self):
        return csv_helpers.parse_csv_game_numbers(
            self.file.name, self.directory
        )

    def names(self, game):
        return csv_helpers.parse_csv_team_names(
            self.file.name, game, self.directory
        )

    def test_quoted_comma_in_column_before_number(self):
        self.write(
            ["Venue, Pool", "#", "White", "Black"],
            ["Deep, west", "2", "Wellington", "Auckland"],
            ["Shallow, east", "1", "Christchurch", "Hamilton"],
        )
        self.assertEqual(self.games(), ["1", "2"])
        self.assertEqual(self.names("2"), ("Wellington", "Auckland"))

    def test_quoted_commas_and_escaped_quotes_in_team_names(self):
        self.write(
            ["date", "#", "White", "Black", "Referees"],
            ["2026-09-29", "4", 'United, "A" Team',
             'Black, "B" Team', "Sam, Jo"],
        )
        self.assertEqual(self.games(), ["4"])
        self.assertEqual(
            self.names("4"),
            ('United, "A" Team', 'Black, "B" Team'),
        )

    def test_quoted_line_breaks_are_one_record_not_two(self):
        white = "United, North\nReserves"
        self.write(
            ["date", "#", "White", "Black"],
            ["2026-09-29", "5", white, "Coastal"],
            ["2026-09-29", "9", "South", "East"],
        )
        self.assertEqual(self.games(), ["5", "9"])
        self.assertEqual(self.names("5"), (white, "Coastal"))
        self.assertEqual(self.names("9"), ("South", "East"))

    def test_bom_and_case_insensitive_headers(self):
        self.write(
            ["Game_Number", " WHITE ", "BLACK"],
            ["007", " Pool A ", " Pool B "],
        )
        self.assertEqual(self.games(), ["7"])
        self.assertEqual(self.names("7"), ("Pool A", "Pool B"))

    def test_header_aliases_game_number_and_sort_order(self):
        self.write(
            ["game#", "white", "black"],
            ["10", "Tenth", "Team"],
            ["2", "Second", "Team"],
            ["2", "Duplicate", "Team"],
            ["not-a-number", "Invalid", "Team"],
        )
        self.assertEqual(self.games(), ["2", "10"])
        self.assertEqual(self.names("2"), ("Second", "Team"))

    def test_blank_and_short_rows_are_skipped(self):
        self.write(
            ["date", "#", "White", "Black"],
            [],
            ["2026-09-29"],
            ["2026-09-29", "x", "Invalid", "Entry"],
            ["2026-09-29", "3", "Valid", "Entry"],
        )
        self.assertEqual(self.games(), ["3"])
        self.assertEqual(self.names("3"), ("Valid", "Entry"))
        self.assertEqual(self.names("8"), (None, None))

    def test_missing_file_and_placeholder_are_safe(self):
        self.assertEqual(self.games(), [])
        self.assertEqual(self.names("1"), (None, None))
        self.assertEqual(csv_helpers.parse_csv_game_numbers(
            "No CSV files found", self.directory
        ), [])
        self.assertEqual(csv_helpers.parse_csv_team_names(
            "No CSV files found", "1", self.directory
        ), (None, None))

    def test_missing_required_headers_do_not_guess_positions(self):
        self.write(
            ["date", "#", "White", "Referees"],
            ["2026-09-29", "1", "Team A", "Ref"],
        )
        self.assertEqual(self.games(), ["1"])
        self.assertEqual(self.names("1"), (None, None))
        self.write(
            ["date", "Round", "White", "Black"],
            ["2026-09-29", "1", "Team A", "Team B"],
        )
        self.assertEqual(self.games(), [])
        self.assertEqual(self.names("1"), (None, None))

    def test_round_trip_through_live_results_writer_retains_team_columns(self):
        self.write(
            ["Venue, Pool", "#", "White", "WScore", "Black",
             "BScore", "Penalties", "Comments"],
            ["Pool 1, east", "6", 'Wellington, "A"', "",
             "Auckland, B", "", "", ""],
        )
        self.assertEqual(self.games(), ["6"])
        self.assertEqual(
            self.names("6"), ('Wellington, "A"', "Auckland, B")
        )

        saved = csv_export.write_game_results_to_csv(
            self.file.name, self.directory, "6",
            4, 3,
            [{"team": "White", "cap": "7", "duration": "120"}],
            True, {"3": 2, "8": 1}, {"10": 1},
        )
        self.assertTrue(saved)
        self.assertEqual(self.games(), ["6"])
        self.assertEqual(
            self.names("6"), ('Wellington, "A"', "Auckland, B")
        )
        # The original draw retains its empty score columns.
        with self.file.open("r", newline="", encoding="utf-8-sig") as source:
            self.assertEqual(list(csv.reader(source))[1][3], "")
        result_file = Path(self.directory) / "Draw_Results.csv"
        with result_file.open("r", newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.reader(stream))
        self.assertEqual(rows[1][3], "4")
        self.assertEqual(rows[1][5], "3")
        self.assertEqual(rows[1][6], "W#7(120)")
        self.assertEqual(rows[1][7], "W#3(2), W#8(1), B#10(1)")


if __name__ == "__main__":
    unittest.main()
