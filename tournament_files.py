"""Separate the operator's tournament DRAW from its mutable RESULTS file.

The draw is a source document: never write scores into it. Every draw gets one
sibling results file, which is created only if absent and thereafter preserved.
These helpers are shared by the Python source build and Windows executable.
"""

import csv
import os


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


def seed_sample_draw(base_dir):
    """Place the distributed sample beside the application once.

    Source distributions keep their template under assets/. PyInstaller may
    have copied it from _internal/ already. Do not overwrite an operator's
    existing root-level draw or touch any results file.
    """
    destination = os.path.join(base_dir, "Tournament_Draw.csv")
    if os.path.lexists(destination):
        return False

    for source in (
        os.path.join(base_dir, "assets", "Tournament_Draw.csv"),
        os.path.join(base_dir, "_internal", "Tournament_Draw.csv"),
    ):
        if os.path.isfile(source):
            return _copy_if_absent(source, destination)
    return False


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
