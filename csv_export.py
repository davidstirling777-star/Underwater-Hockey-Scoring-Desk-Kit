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
    """Stage a complete RESULTS file before replacing the prior results."""
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


def sort_cap_key(cap_number):
    """Sort numeric caps first, followed by the two special goal labels."""
    if cap_number == "Penalty Goal":
        return (1, 100)
    if cap_number == "Unknown":
        return (1, 101)

    try:
        return (0, int(cap_number))
    except (TypeError, ValueError):
        return (2, 0)


def build_penalties_text(penalties):
    penalty_entries = []

    for penalty in penalties:
        team_prefix = "W" if penalty["team"] == "White" else "B"
        penalty_entries.append(
            f"{team_prefix}#{penalty['cap']}({penalty['duration']})"
        )

    return ", ".join(penalty_entries)


def format_goal_scorers_comment(scorers):
    """Return the established scorer-comment notation without spaces."""
    comment_parts = []
    labels = {"Penalty Goal": "PG", "Unknown": "UNK"}

    for team, prefix in (("White", "W"), ("Black", "B")):
        team_scorers = scorers.get(team, {})
        for cap_number, count in sorted(
            team_scorers.items(), key=lambda item: sort_cap_key(item[0])
        ):
            label = labels.get(cap_number, cap_number)
            comment_parts.append(f"{prefix}#{label}({count})")

    return ",".join(comment_parts)


def build_scorer_comments(
    record_scorers,
    white_goal_scorers,
    black_goal_scorers,
):
    """Build CSV scorer comments using the same notation as the display."""
    if not record_scorers:
        return ""

    formatted = format_goal_scorers_comment({
        "White": white_goal_scorers,
        "Black": black_goal_scorers,
    })
    return formatted.replace(",", ", ")


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
    debug_mode=False,
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

    try:
        results_file = tournament_files.ensure_results_file(csv_file)
    except ValueError as error:
        print(f"CSV UPDATE: Cannot use tournament results: {error}")
        return False

    penalties_text = build_penalties_text(penalties)
    comments_text = build_scorer_comments(
        record_scorers,
        white_goal_scorers,
        black_goal_scorers,
    )

    with open(results_file, "r", newline="", encoding="utf-8-sig") as source:
        rows = list(csv.reader(source))

    if not rows:
        if debug_mode:
            print("CSV UPDATE: CSV file is empty")
        return False

    header = [str(value).strip() for value in rows[0]]
    header_keys = [name.casefold() for name in header]

    game_col = next(
        (
            index
            for index, name in enumerate(header_keys)
            if name in ("#", "game", "game#", "game_number")
        ),
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
    except ValueError as error:
        if debug_mode:
            print(f"CSV UPDATE: Missing required column: {error}")
        return False

    target = str(game_number).strip()
    if not target:
        if debug_mode:
            print("CSV UPDATE: No game number supplied")
        return False

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


def aggregate_goal_scorers(goal_events):
    scorers = {"White": {}, "Black": {}}

    for event in goal_events:
        team = event.get("team", "")
        cap_number = event.get("cap_number", "")

        if team in scorers and cap_number:
            scorers[team][cap_number] = scorers[team].get(cap_number, 0) + 1

    return scorers


def get_goal_events_for_game(base_dir, game_number):
    """Read legacy goal events; the legacy file has no game-number field."""
    txt_file = os.path.join(base_dir, "UWH_Game_Data.txt")
    goal_events = []

    if not os.path.exists(txt_file):
        return goal_events

    try:
        with open(txt_file, "r", encoding="utf-8") as source:
            for line in source:
                line = line.strip()
                if not line:
                    continue

                fields = line.split("|")
                if len(fields) < 5 or fields[2].strip() != "Goal":
                    continue

                goal_events.append({
                    "team": fields[3].strip(),
                    "cap_number": fields[4].strip(),
                })
    except Exception as error:
        print(f"Error reading goal events from {txt_file}: {error}")

    return goal_events
