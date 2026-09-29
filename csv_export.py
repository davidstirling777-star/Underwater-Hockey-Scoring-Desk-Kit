"""Tournament results export and legacy scorer/event-log helpers.

write_game_results_to_csv reads the selected draw but writes exclusively to
its sibling _Results.csv. It checks the game-number header, rejects ambiguous
IDs, and stages a complete results CSV before os.replace. A failed export must
leave the live match state available for retry; see game_flow.py.

The goal-event reader near the bottom is legacy: UWH_Game_Data.txt lacks a
game-number field. Do not use it to infer per-game scorers.
"""

import csv
import os
import stat
import tempfile

import tournament_files


def _write_csv_atomically(csv_file, rows):
    """Stage a complete RESULTS file before replacing the prior results.

    The selected source draw is never passed to this function. The temporary
    file lives next to the results file so os.replace is atomic on both
    Windows and Linux. A failed write leaves prior results and the live game.
    """
    directory = os.path.dirname(os.path.abspath(csv_file))
    original_mode = stat.S_IMODE(os.stat(csv_file).st_mode)
    staged_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=directory,
            prefix=".uwh_results_",
            suffix=".tmp",
            delete=False,
        ) as staged:
            staged_path = staged.name
            csv.writer(staged).writerows(rows)
            staged.flush()
            os.fsync(staged.fileno())

        # Preserve the results file's permissions on Windows and Linux.
        os.chmod(staged_path, original_mode)
        os.replace(staged_path, csv_file)
        staged_path = None
    finally:
        if staged_path is not None:
            try:
                os.unlink(staged_path)
            except FileNotFoundError:
                pass
            except OSError as error:
                print(f"CSV UPDATE: Could not remove temporary file: {error}")


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

    # The scorer dialog stores these full labels, while the established
    # scorer-comment notation uses PG and UNK (as in the display formatter).
    cap_labels = {"Penalty Goal": "PG", "Unknown": "UNK"}

    for cap, goals in sorted(white_goal_scorers.items(), key=lambda x: sort_cap_key(x[0])):
        scorer_entries.append(f"W#{cap_labels.get(cap, cap)}({goals})")

    for cap, goals in sorted(black_goal_scorers.items(), key=lambda x: sort_cap_key(x[0])):
        scorer_entries.append(f"B#{cap_labels.get(cap, cap)}({goals})")

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
            print(f"CSV UPDATE: Draw not found: {csv_file}")
        return False

    # Create a sibling results file only if it does not already exist.
    # Revalidate the schedule against the original draw on every export:
    # restarting or changing the selection must never reset recorded games.
    try:
        results_file = tournament_files.ensure_results_file(csv_file)
    except ValueError as error:
        print(f"CSV UPDATE: Cannot use tournament results: {error}")
        return False

    penalties_text = build_penalties_text(penalties)

    comments_text = build_scorer_comments(
        record_scorers,
        white_goal_scorers,
        black_goal_scorers
    )

    rows = []

    with open(results_file, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        if debug_mode:
            print("CSV UPDATE: CSV file is empty")
        return False

    header = [str(h).strip() for h in rows[0]]
    header_keys = [name.casefold() for name in header]

    # The draw reader already recognises these headers anywhere in the
    # file. Results must find the SAME game column, not assume row[1].
    game_col = next(
        (index for index, name in enumerate(header_keys)
         if name in ("#", "game", "game#", "game_number")),
        None,
    )
    if game_col is None:
        if debug_mode:
            print("CSV UPDATE: Missing game-number column")
        return False

    try:
        wscore_col = header_keys.index("wscore")
        bscore_col = header_keys.index("bscore")
        penalties_col = header_keys.index("penalties")
        comments_col = header_keys.index("comments")

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

    target = str(game_number).strip()
    if not target:
        if debug_mode:
            print("CSV UPDATE: No game number supplied")
        return False

    # Like the draw reader, allow numeric game IDs such as 007 to match 7.
    # Preserve the prior exact-match behavior for nonnumeric IDs.
    try:
        target_numeric = int(target)
    except ValueError:
        target_numeric = None

    matches = []
    for row in rows[1:]:
        if len(row) <= game_col:
            continue
        stored = row[game_col].strip()
        matched = stored == target
        if not matched and target_numeric is not None:
            try:
                matched = int(stored) == target_numeric
            except ValueError:
                pass
        if matched:
            matches.append(row)

    if not matches:
        if debug_mode:
            print(f"CSV UPDATE: Game {game_number} not found")
        return False

    # Never guess which row to overwrite when an ID appears twice, including
    # variants such as 7 and 007. Leave results and live scores
    # untouched so the operator can resolve the ambiguous draw.
    if len(matches) != 1:
        print(
            f"CSV UPDATE: Game {game_number} occurs in multiple rows; "
            "results not saved. Check the tournament draw."
        )
        return False

    row = matches[0]
    if len(row) < len(header):
        row.extend([""] * (len(header) - len(row)))
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

    _write_csv_atomically(results_file, rows)

    if debug_mode:
        print(f"CSV UPDATE: Saved to {results_file}")

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
