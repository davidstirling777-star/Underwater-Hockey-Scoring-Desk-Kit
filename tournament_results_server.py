"""Single-writer tournament results receiver for a trusted local network.

Run ONE copy on the results computer. Both courts POST a single finished game;
a process-wide lock serialises read/check/write of the shared results CSV.
The server never allows callers to choose a filesystem path or edit the draw.

Start:
    UWH_SYNC_TOKEN=<long-random-secret> python tournament_results_server.py \
      --draw /path/to/Tournament_Draw.csv --bind 0.0.0.0

Use a firewall/private LAN or a VPN. HTTP is NOT encrypted: do not expose the
listener to the internet or carry sensitive credentials over untrusted Wi-Fi.
"""

import argparse
import csv
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hmac
import json
import os
import re
import threading

import csv_export
import tournament_files


RESULT_FIELDS = ("wscore", "bscore", "penalties", "comments")
GAME_HEADERS = tournament_files.GAME_HEADERS


class ResultConflict(ValueError):
    """Another court or operator has already supplied different values."""


def _game_key(value):
    """Treat numeric identifiers such as 007 and 7 as the same game."""
    stripped = str(value).strip()
    if not stripped:
        raise ValueError("Missing game number")
    try:
        return ("number", int(stripped))
    except ValueError:
        return ("text", stripped)


def apply_submission(draw_path, submission):
    """Validate then merge ONE game's results without touching the source draw.

    Only this function may replace the server's results CSV. The HTTP handler
    serialises calls to it with a lock. It is also independently testable.
    """
    if not isinstance(submission, dict):
        raise ValueError("Submission must be a JSON object")
    if set(submission) != {"draw_sha256", "game_number", "results"}:
        raise ValueError("Unexpected or missing submission fields")

    with open(draw_path, "rb") as stream:
        expected_digest = hashlib.sha256(stream.read()).hexdigest()
    if not hmac.compare_digest(str(submission["draw_sha256"]), expected_digest):
        raise ResultConflict("The courts and results server use different draw files")

    values = submission["results"]
    if not isinstance(values, dict) or set(values) != set(RESULT_FIELDS):
        raise ValueError("Incomplete result data")
    if any(not isinstance(value, str) or len(value) > 2000
           for value in values.values()):
        raise ValueError("Result fields must be reasonably sized text")
    if not re.fullmatch(r"[0-9]{1,3}", values["wscore"]) or not re.fullmatch(
        r"[0-9]{1,3}", values["bscore"]
    ):
        raise ValueError("Both scores must be whole numbers")

    game_key = _game_key(submission["game_number"])

    # This refuses a changed schedule, unmatched team or corrupt results
    # before modifying anything. The initial seed is only created if absent.
    results_path = tournament_files.ensure_results_file(draw_path)
    draw_rows = tournament_files._read_rows(draw_path)
    results_rows = tournament_files._read_rows(results_path)
    keys = [part.strip().casefold() for part in draw_rows[0]]
    game_column = next(i for i, name in enumerate(keys) if name in GAME_HEADERS)
    result_columns = {name: keys.index(name) for name in RESULT_FIELDS}
    matches = [
        index for index, row in enumerate(draw_rows[1:], start=1)
        if len(row) > game_column
        and row[game_column].strip()
        and _game_key(row[game_column]) == game_key
    ]
    if len(matches) != 1:
        raise ValueError("Game number missing or ambiguous in the tournament draw")

    index = matches[0]
    source_row = draw_rows[index]
    target_row = results_rows[index]
    target_row.extend([""] * (len(keys) - len(target_row)))
    source_row = source_row + [""] * (len(keys) - len(source_row))
    existing = {
        field: target_row[col] for field, col in result_columns.items()
    }
    initial = {
        field: source_row[col] for field, col in result_columns.items()
    }

    # The same submission may be retried after an ACK is lost. A duplicate
    # must not be treated as a conflict, nor rewrite the file.
    if existing == values:
        return "already_saved"

    # Never clobber a result from the other court, or a score already present
    # in the original draw. A correction requires human reconciliation.
    if existing != initial or any(initial.values()):
        raise ResultConflict(
            "Different results already exist for this game; "
            "resolve the conflict before retrying"
        )

    for field, column in result_columns.items():
        target_row[column] = values[field]
    csv_export._write_csv_atomically(results_path, results_rows)
    return "saved"


def make_handler(draw_path, secret, write_lock):
    """Bind a fixed draw and token to the request handler; no arbitrary paths."""
    class Handler(BaseHTTPRequestHandler):
        def _authenticated(self):
            actual = self.headers.get("X-UWH-Sync-Token", "")
            return hmac.compare_digest(actual, secret)

        def _json(self, code, body):
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path != "/health":
                return self._json(404, {"error": "Not found"})
            if not self._authenticated():
                return self._json(401, {"error": "Unauthorised"})
            try:
                with open(draw_path, "rb") as stream:
                    digest = hashlib.sha256(stream.read()).hexdigest()
            except OSError:
                return self._json(503, {"error": "Source draw is unavailable"})
            # Clients validate this even when they have no pending games.
            return self._json(200, {
                "status": "ready", "draw_sha256": digest
            })

        def do_POST(self):
            if self.path != "/submit":
                return self._json(404, {"error": "Not found"})
            if not self._authenticated():
                return self._json(401, {"error": "Unauthorised"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self._json(400, {"error": "Invalid body size"})
            if not (0 < size <= 16_384):
                return self._json(413, {"error": "Submission size is invalid"})
            try:
                body = json.loads(self.rfile.read(size).decode("utf-8"))
                with write_lock:
                    outcome = apply_submission(draw_path, body)
            except ResultConflict as error:
                return self._json(409, {"error": str(error)})
            except (ValueError, UnicodeError, json.JSONDecodeError) as error:
                return self._json(400, {"error": str(error)})
            except OSError as error:
                print(f"Server write failure: {error}")
                return self._json(503, {"error": "Results file unavailable; retry"})
            return self._json(200, {"status": outcome})

        def log_message(self, fmt, *args):
            # Standard HTTP logging includes no authentication header or body.
            print("RESULTS SERVER: " + fmt % args)

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="One-writer UWH results service")
    parser.add_argument("--draw", required=True, help="Full path to server's original draw")
    parser.add_argument("--bind", default="127.0.0.1",
                        help="Bind address (use 0.0.0.0 only on a protected LAN)")
    parser.add_argument("--port", type=int, default=8765)
    arguments = parser.parse_args(argv)
    secret = os.environ.get("UWH_SYNC_TOKEN", "")
    if len(secret) < 16:
        parser.error("Set UWH_SYNC_TOKEN to an unpredictable secret of 16+ characters")
    draw_path = os.path.abspath(arguments.draw)
    # Require a valid draw/results pair BEFORE accepting network traffic.
    tournament_files.ensure_results_file(draw_path)
    handler = make_handler(draw_path, secret, threading.Lock())
    server = ThreadingHTTPServer((arguments.bind, arguments.port), handler)
    print(f"UWH results server listening on {arguments.bind}:{arguments.port}")
    print(f"Source draw: {draw_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
