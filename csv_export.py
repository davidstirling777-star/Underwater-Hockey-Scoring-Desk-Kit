import csv
import os


def sort_cap_key(cap):
    text = str(cap)

    if text.isdigit():
        return 0, int(text)

    return 1, text


def build_penalties_text(penalties):
    penalty_entries = []

    for p in penalties:
        team_prefix = "W" if p["team"] == "White" else "B"
        penalty_entries.append(
            f"{team_prefix}#{p['cap']}({p['duration']})"
        )

    return ", ".join(penalty_entries)


def build_scorer_comments(record_scorers, white_goal_scorers, black_goal_scorers):
    if not record_scorers:
        return ""

    scorer_entries = []

    for cap, goals in sorted(white_goal_scorers.items(), key=lambda x: sort_cap_key(x[0])):
        scorer_entries.append(f"W#{cap}({goals})")

    for cap, goals in sorted(black_goal_scorers.items(), key=lambda x: sort_cap_key(x[0])):
        scorer_entries.append(f"B#{cap}({goals})")

    return ", ".join(scorer_entries)


def write_game_results_to_csv(
    csv_file,
    base_dir,
    game_number,
    white_score,
    black_score,
    penalties,
    record_scorers,
    white_goal_scorers,
    black_goal_scorers,
    debug_mode=False
):
    if debug_mode:
        print(f"CSV UPDATE: csv_file={csv_file}")

    if not csv_file:
        if debug_mode:
            print("CSV UPDATE: No tournament CSV selected")
        return False

    if not os.path.isabs(csv_file):
        csv_file = os.path.join(base_dir, csv_file)

    if not os.path.exists(csv_file):
        if debug_mode:
            print(f"CSV UPDATE: File not found: {csv_file}")
        return False

    penalties_text = build_penalties_text(penalties)

    comments_text = build_scorer_comments(
        record_scorers,
        white_goal_scorers,
        black_goal_scorers
    )

    rows = []

    with open(csv_file, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        if debug_mode:
            print("CSV UPDATE: CSV file is empty")
        return False

    header = [str(h).strip() for h in rows[0]]

    try:
        wscore_col = header.index("WScore")
        bscore_col = header.index("BScore")
        penalties_col = header.index("Penalties")
        comments_col = header.index("Comments")

        if debug_mode:
            print(
                f"CSV COLUMNS: "
                f"WScore={wscore_col} "
                f"BScore={bscore_col} "
                f"Penalties={penalties_col} "
                f"Comments={comments_col}"
            )

    except ValueError as e:
        if debug_mode:
            print(f"CSV UPDATE: Missing required column: {e}")
        return False

    game_found = False

    for row in rows[1:]:
        if len(row) < len(header):
            row.extend([""] * (len(header) - len(row)))

        game_col = row[1].strip()

        if game_col == str(game_number):
            row[wscore_col] = str(white_score)
            row[bscore_col] = str(black_score)
            row[penalties_col] = penalties_text
            row[comments_col] = comments_text

            if debug_mode:
                print("ROW AFTER:", row)
                print(
                    f"CSV UPDATE: Game {game_number} "
                    f"W:{white_score} B:{black_score}"
                )

            game_found = True
            break

    if not game_found:
        if debug_mode:
            print(f"CSV UPDATE: Game {game_number} not found")
        return False

    with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    if debug_mode:
        print("CSV UPDATE: Success")

    return True
