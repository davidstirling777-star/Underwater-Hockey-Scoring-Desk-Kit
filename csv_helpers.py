import csv
import os


def _read_tournament_rows(csv_path):
    """Read actual CSV records, preserving commas, quotes and newlines in cells.

    The tournament writer uses utf-8-sig, so accept its optional BOM too.
    Both game-number and team-name lookups must see identical columns.
    """
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as source:
        return list(csv.reader(source))


def parse_csv_game_numbers(csv_filename, base_dir):
    """
    Parse CSV file and extract game numbers from the '#' column.
    Expected header:
    date,#,White,Score,Black,Score,Referees,Penalties
    """
    game_numbers = []

    if csv_filename == "No CSV files found" or not csv_filename:
        return game_numbers

    try:
        csv_path = os.path.join(base_dir, csv_filename)

        if not os.path.exists(csv_path):
            return game_numbers

        rows = _read_tournament_rows(csv_path)
        if len(rows) < 2:
            return game_numbers

        header_cols = [col.strip().lower() for col in rows[0]]
        game_num_col_idx = -1

        for i, col in enumerate(header_cols):
            if col in ["#", "game", "game#", "game_number"]:
                game_num_col_idx = i
                break

        if game_num_col_idx == -1:
            print(
                f"Warning: Could not find game number "
                f"column in CSV {csv_filename}"
            )
            return game_numbers

        for row in rows[1:]:
            if not row:
                continue

            if len(row) <= game_num_col_idx:
                continue

            try:
                game_num = int(row[game_num_col_idx].strip())
                game_numbers.append(str(game_num))
            except ValueError:
                pass

    except Exception as e:
        print(f"Error parsing CSV file {csv_filename}: {e}")

    return (
        sorted(set(game_numbers), key=int)
        if game_numbers
        else []
    )


def parse_csv_team_names(csv_filename, game_number, base_dir):
    """
    Parse CSV file and extract team names for a specific game number.
    Returns: (white_team_name, black_team_name)
    """
    if (
        csv_filename == "No CSV files found"
        or not csv_filename
        or not game_number
    ):
        return (None, None)

    try:
        csv_path = os.path.join(base_dir, csv_filename)

        if not os.path.exists(csv_path):
            return (None, None)

        rows = _read_tournament_rows(csv_path)
        if len(rows) < 2:
            return (None, None)

        header_cols = [col.strip().lower() for col in rows[0]]

        game_num_col_idx = -1
        white_team_col_idx = -1
        black_team_col_idx = -1

        for i, col in enumerate(header_cols):
            if col in ["#", "game", "game#", "game_number"]:
                game_num_col_idx = i
            elif col == "white":
                white_team_col_idx = i
            elif col == "black":
                black_team_col_idx = i

        if (
            game_num_col_idx == -1
            or white_team_col_idx == -1
            or black_team_col_idx == -1
        ):
            return (None, None)

        for row in rows[1:]:
            if not row:
                continue

            if len(row) <= max(
                game_num_col_idx,
                white_team_col_idx,
                black_team_col_idx
            ):
                continue

            try:
                if (
                    str(int(row[game_num_col_idx].strip()))
                    == str(game_number)
                ):
                    return (
                        row[white_team_col_idx].strip(),
                        row[black_team_col_idx].strip()
                    )

            except (ValueError, IndexError):
                pass

    except Exception as e:
        print(
            f"Error parsing team names from CSV "
            f"file {csv_filename}: {e}"
        )

    return (None, None)


def get_csv_files(base_dir):
    """
    Scan the application folder for CSV files.
    Returns a sorted list of CSV files found.
    """

    csv_files = []

    try:
        for filename in os.listdir(base_dir):
            if filename.lower().endswith(".csv"):
                csv_files.append(filename)

    except Exception as e:
        print(f"Error scanning for CSV files: {e}")

    return sorted(csv_files) if csv_files else ["No CSV files found"]

