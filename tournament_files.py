"""Separate the operator's tournament DRAW from its mutable RESULTS file.

The draw is a source document: never write scores into it. Every draw gets one
sibling results file, which is created only if absent and thereafter preserved.
These helpers are shared by the Python source build and Windows executable.
"""

import csv
import os
import re


TOURNAMENT_DATA_FOLDER = "Tournament data"
MANUAL_DRAW_HEADER = [
    "date", "#", "White", "WScore", "Black", "BScore",
    "Referees", "Penalties", "Comments",
]
GAME_HEADERS = {"#", "game", "game#", "game_number"}
RESULT_HEADERS = {"wscore", "bscore", "penalties", "comments"}


def results_path_for_draw(draw_path):
    """Return a deterministic sibling path; never accept a results file as a draw.

    Tournament_Draw.csv -> Tournament_Results.csv
    Other_Draw.csv      -> Other_Results.csv
    MySchedule.csv      -> MySchedule_Results.csv
    """
    absolute = os.path.abspath(os.fspath(draw_path))
    stem, extension = os.path.splitext(absolute)
    if extension.casefold() != ".csv":
        raise ValueError("The tournament draw must be a CSV file.")
    if stem.casefold().endswith("_results"):
        raise ValueError("Select the original draw, not a results file.")
    if stem.casefold().endswith("_draw"):
        stem = stem[:-5]
    return stem + "_Results.csv"


def _copy_if_absent(source_path, destination_path):
    """Copy bytes once, preserving CSV encoding; exclusive create prevents clobbering.

    The results file can be an existing live tournament, so NEVER use
    shutil.copy2(...), open(..., 'wb'), or os.replace here.
    """
    created = False
    try:
        with open(source_path, "rb") as source:
            try:
                with open(destination_path, "xb") as destination:
                    created = True
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        destination.write(chunk)
                    destination.flush()
                    os.fsync(destination.fileno())
            except FileExistsError:
                return False
    except BaseException:
        # A disk-full error during initial creation must not leave a
        # half-written results file that a later launch would treat as valid.
        if created:
            try:
                os.unlink(destination_path)
            except OSError:
                pass
        raise
    return created


def tournament_data_directory(base_dir):
    """Return/create the operator-visible Tournament data folder."""
    path = os.path.join(os.path.abspath(os.fspath(base_dir)), TOURNAMENT_DATA_FOLDER)
    os.makedirs(path, exist_ok=True)
    return path


def migrate_legacy_tournament_csvs(base_dir, destination_dir=None):
    """Copy old root-level tournament CSVs into Tournament data once.

    Older UWH versions scanned the application folder directly.  Keep those
    files intact, but copy every root-level CSV into the new visible folder
    when no file of the same name exists there.
    """
    base_dir = os.path.abspath(os.fspath(base_dir))
    destination_dir = (
        tournament_data_directory(base_dir)
        if destination_dir is None
        else os.path.abspath(os.fspath(destination_dir))
    )
    os.makedirs(destination_dir, exist_ok=True)

    copied = []
    try:
        names = os.listdir(base_dir)
    except OSError:
        return copied

    for filename in names:
        if not filename.lower().endswith(".csv"):
            continue
        source = os.path.join(base_dir, filename)
        destination = os.path.join(destination_dir, filename)
        if not os.path.isfile(source) or os.path.lexists(destination):
            continue
        if _copy_if_absent(source, destination):
            copied.append(filename)
    return copied


def seed_sample_draw(base_dir):
    """Place the distributed demo draw/results in Tournament data once.

    Source distributions keep the template under assets/. PyInstaller may
    bundle it under _internal/. Existing operator files are never overwritten.
    """
    base_dir = os.path.abspath(os.fspath(base_dir))
    destination_dir = tournament_data_directory(base_dir)
    destination = os.path.join(destination_dir, "Tournament_Draw.csv")

    if not os.path.lexists(destination):
        for source in (
            os.path.join(base_dir, "assets", "Tournament_Draw.csv"),
            os.path.join(base_dir, "_internal", "Tournament_Draw.csv"),
            os.path.join(base_dir, "_internal", "assets", "Tournament_Draw.csv"),
            os.path.join(base_dir, "_internal", TOURNAMENT_DATA_FOLDER, "Tournament_Draw.csv"),
        ):
            if os.path.isfile(source):
                _copy_if_absent(source, destination)
                break

    if os.path.isfile(destination):
        # The demo results file starts as an exact copy of the demo draw.
        # ensure_results_file never overwrites an existing result.
        ensure_results_file(destination)

    return destination if os.path.isfile(destination) else ""


def prepare_tournament_data(base_dir):
    """Create the visible folder, migrate old CSVs, then ensure the demo pair."""
    destination_dir = tournament_data_directory(base_dir)
    migrate_legacy_tournament_csvs(base_dir, destination_dir)
    seed_sample_draw(base_dir)
    return destination_dir


def _safe_draw_filename(draw_name):
    """Return a Windows/Linux-safe draw filename derived from operator text."""
    name = str(draw_name).strip()
    if not name:
        raise ValueError("Enter a Draw Name before saving.")

    if name.lower().endswith(".csv"):
        name = name[:-4].rstrip()

    name = re.sub(r'[<>:"/\\|?*]+', "_", name).strip(" .")
    if not name:
        raise ValueError("The Draw Name does not contain a usable filename.")

    if not name.casefold().endswith("_draw"):
        name += "_Draw"

    return name + ".csv"


def save_manual_draw(tournament_dir, draw_name, rows):
    """Create a new draw/results pair from editable manual-entry rows.

    Each row is (game number, white team, black team). Completely empty team
    rows are ignored, so the UI may pre-number spare rows. Partly completed
    rows are rejected. Game numbers and team names are capped at 16 characters.
    Existing draw/results files are never overwritten.
    """
    tournament_dir = os.path.abspath(os.fspath(tournament_dir))
    os.makedirs(tournament_dir, exist_ok=True)

    cleaned = []
    seen_games = set()

    for index, row in enumerate(rows, start=1):
        game, white, black = (str(value).strip() for value in row)

        # A pre-numbered unused row is still empty for saving purposes.
        if not white and not black:
            continue

        if not game or not white or not black:
            raise ValueError(
                f"Manual draw row {index} is incomplete. "
                "Enter Game number, White and Black, or clear both team names."
            )

        for label, value in (("Game number", game), ("White", white), ("Black", black)):
            if len(value) > 16:
                raise ValueError(
                    f"{label} on row {index} is longer than 16 characters."
                )

        key = game.casefold()
        if key in seen_games:
            raise ValueError(f"Game number '{game}' is duplicated.")
        seen_games.add(key)
        cleaned.append((game, white, black))

    if not cleaned:
        raise ValueError("Enter at least one complete game before saving.")

    filename = _safe_draw_filename(draw_name)
    draw_path = os.path.join(tournament_dir, filename)

    if os.path.lexists(draw_path):
        raise FileExistsError(
            f"{filename} already exists. Use a different Draw Name."
        )

    try:
        with open(
            draw_path,
            "x",
            newline="",
            encoding="utf-8-sig",
        ) as stream:
            writer = csv.writer(stream)
            writer.writerow(MANUAL_DRAW_HEADER)
            for game, white, black in cleaned:
                writer.writerow([
                    "", game, white, "", black, "", "", "", "",
                ])
            stream.flush()
            os.fsync(stream.fileno())

        results_path = ensure_results_file(draw_path)
    except BaseException:
        # Never leave a partial brand-new draw behind after a failed save.
        try:
            if os.path.isfile(draw_path) and not os.path.lexists(
                results_path_for_draw(draw_path)
            ):
                os.unlink(draw_path)
        except OSError:
            pass
        raise

    return draw_path, results_path

def _read_rows(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as stream:
        return list(csv.reader(stream))


def _validate_headers(rows):
    if not rows:
        raise ValueError("The tournament draw is empty.")
    header = [cell.strip().casefold() for cell in rows[0]]
    if not GAME_HEADERS.intersection(header):
        raise ValueError("The tournament draw has no game-number column.")
    missing = RESULT_HEADERS.difference(header)
    if missing:
        raise ValueError(
            "The tournament draw is missing results column(s): "
            + ", ".join(sorted(missing))
        )
    return {index for index, name in enumerate(header) if name in RESULT_HEADERS}


def _validate_existing_results(draw_rows, result_rows, result_columns):
    """Refuse to write results against a different or subsequently edited draw.

    Scores, penalties and comments may differ as games finish. All remaining
    fields (including game numbers, teams and schedule) must still match.
    """
    if len(draw_rows) != len(result_rows) or draw_rows[0] != result_rows[0]:
        raise ValueError(
            "The results file does not match the selected draw (rows/header). "
            "Back up both files and resolve the difference before exporting."
        )

    for row_number, (draw_row, result_row) in enumerate(
        zip(draw_rows[1:], result_rows[1:]), start=2
    ):
        for column in range(max(len(draw_row), len(result_row))):
            if column in result_columns:
                continue
            from_draw = draw_row[column] if column < len(draw_row) else ""
            from_results = result_row[column] if column < len(result_row) else ""
            if from_draw != from_results:
                raise ValueError(
                    "The results file does not match the selected draw "
                    f"(CSV row {row_number}). Back up both files before editing."
                )


def ensure_results_file(draw_path):
    """Create the results file from the draw only once; validate on every use.

    An existing results file is NEVER overwritten or reset, including after
    an application restart. Invalid/mismatched results stop exporting rather
    than endangering previously saved scores.
    """
    draw_path = os.path.abspath(os.fspath(draw_path))
    results_path = results_path_for_draw(draw_path)
    draw_rows = _read_rows(draw_path)
    result_columns = _validate_headers(draw_rows)

    if not os.path.lexists(results_path):
        _copy_if_absent(draw_path, results_path)

    # A pre-existing symlink or hard link must not cause an output write to
    # target the original draw. Check after exclusive creation as well.
    if os.path.samefile(draw_path, results_path):
        raise ValueError("The results file must not be the original draw.")

    results_rows = _read_rows(results_path)
    _validate_existing_results(draw_rows, results_rows, result_columns)
    return results_path
