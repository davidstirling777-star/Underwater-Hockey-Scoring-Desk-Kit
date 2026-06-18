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

def sort_cap_key(cap_number):
    if cap_number == "Penalty Goal":
        return (1, 100)

    if cap_number == "Unknown":
        return (1, 101)

    try:
        return (0, int(cap_number))
    except ValueError:
        return (2, 0)

def format_goal_scorers_comment(scorers):
    comment_parts = []

    if "White" in scorers and scorers["White"]:
        white_parts = []

        for cap_number, count in sorted(
            scorers["White"].items(),
            key=lambda x: sort_cap_key(x[0])
        ):
            if cap_number == "Penalty Goal":
                white_parts.append(f"W#PG({count})")
            elif cap_number == "Unknown":
                white_parts.append(f"W#UNK({count})")
            else:
                white_parts.append(
                    f"W#{cap_number}({count})"
                )

        comment_parts.extend(white_parts)

    if "Black" in scorers and scorers["Black"]:
        black_parts = []

        for cap_number, count in sorted(
            scorers["Black"].items(),
            key=lambda x: sort_cap_key(x[0])
        ):
            if cap_number == "Penalty Goal":
                black_parts.append(f"B#PG({count})")
            elif cap_number == "Unknown":
                black_parts.append(f"B#UNK({count})")
            else:
                black_parts.append(
                    f"B#{cap_number}({count})"
                )

        comment_parts.extend(black_parts)

    return ",".join(comment_parts)

def aggregate_goal_scorers(goal_events):
    scorers = {
        "White": {},
        "Black": {}
    }

    for event in goal_events:
        team = event.get("team", "")
        cap_number = event.get("cap_number", "")

        if team in scorers and cap_number:
            if cap_number not in scorers[team]:
                scorers[team][cap_number] = 0

            scorers[team][cap_number] += 1

    return scorers

def get_goal_events_for_game(base_dir, game_number):
    txt_file = os.path.join(base_dir, "UWH_Game_Data.txt")
    goal_events = []

    if not os.path.exists(txt_file):
        return goal_events

    try:
        with open(txt_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                fields = line.split("|")

                if len(fields) < 5:
                    continue

                event_type = fields[2].strip()

                if event_type == "Goal":
                    team = fields[3].strip()
                    cap_number = fields[4].strip()

                    goal_events.append({
                        "team": team,
                        "cap_number": cap_number
                    })

    except Exception as e:
        print(f"Error reading goal events from {txt_file}: {e}")

    return goal_events

def get_goal_events_for_game(base_dir, game_number):
    txt_file = os.path.join(base_dir, "UWH_Game_Data.txt")
    goal_events = []

    if not os.path.exists(txt_file):
        return goal_events

    try:
        with open(txt_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line:
                    continue

                fields = line.split("|")

                if len(fields) < 5:
                    continue

                event_type = fields[2].strip()

                if event_type == "Goal":
                    goal_events.append({
                        "team": fields[3].strip(),
                        "cap_number": fields[4].strip()
                    })

    except Exception as e:
        print(f"Error reading goal events from {txt_file}: {e}")

    return goal_events
