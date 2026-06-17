import os


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

        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) < 2:
            return game_numbers

        header = lines[0].strip().lower()
        header_cols = [
            col.strip()
            for col in header.split(",")
        ]

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

        for line in lines[1:]:
            line = line.strip()

            if not line:
                continue

            cols = [
                col.strip()
                for col in line.split(",")
            ]

            if len(cols) <= game_num_col_idx:
                continue

            try:
                game_num = int(cols[game_num_col_idx])
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
