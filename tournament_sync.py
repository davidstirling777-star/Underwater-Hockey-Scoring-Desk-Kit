"""Local-first tournament results synchronisation without Tk calls on workers.

The court always writes its own _Results.csv first. This worker reconstructs
unsynchronised *finished games* from that durable file after every restart,
submits one game at a time to the single-writer results server, and records
acknowledgements atomically. Transient failures retry every ten seconds.

No entire-CSV uploads: an out-of-date local copy must never wipe another
court's completed games. Conflicts are reported, never auto-resolved.
"""

import hashlib
import json
import os
import queue
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request

import tournament_files


RETRY_SECONDS = 10
RESULT_FIELDS = ("wscore", "bscore", "penalties", "comments")
GAME_HEADERS = tournament_files.GAME_HEADERS


def normalise_url(value):
    """Restrict the destination to a fixed HTTP(S) server root."""
    address = str(value).strip().rstrip("/")
    parsed = urllib.parse.urlsplit(address)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname
            or parsed.username or parsed.password or parsed.query
            or parsed.fragment or parsed.path not in ("", "/")):
        raise ValueError("Enter a server URL such as http://RESULTS-PC:8765")
    if not parsed.port and parsed.netloc.endswith(":"):
        raise ValueError("Invalid server port")
    return address


def _game_key(value):
    text = str(value).strip()
    if not text:
        raise ValueError("Tournament game number is blank")
    try:
        return str(int(text))
    except ValueError:
        return text


def _digest_record(record):
    serialised = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


def _receipt_path(draw_path):
    """Never put court sync metadata in the results CSV itself."""
    path = os.path.abspath(draw_path)
    return os.path.join(
        os.path.dirname(path),
        ".uwh_sync_" + hashlib.sha256(path.encode("utf-8")).hexdigest()[:16] + ".json",
    )


def _load_receipts(path, draw_digest, url):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as stream:
        doc = json.load(stream)
    if not isinstance(doc, dict) or not isinstance(doc.get("acked"), dict):
        raise ValueError("Invalid local sync receipt file; back it up before retrying")
    # A different server or changed draw needs its own complete sync pass.
    if doc.get("draw_sha256") != draw_digest or doc.get("server_url") != url:
        return {}
    return doc["acked"]


def _save_receipts(path, draw_digest, url, receipts):
    """A lost receipt only causes an idempotent retry, never data loss."""
    directory = os.path.dirname(path)
    payload = {
        "draw_sha256": draw_digest,
        "server_url": url,
        "acked": receipts,
    }
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=directory,
            prefix=".uwh_sync_write_", suffix=".tmp", delete=False
        ) as stream:
            temporary = stream.name
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def completed_game_records(draw_path):
    """Find durable finished games rather than trusting a transient queue.

    A finished game is identifiable even when both scores are zero: the local
    exporter writes "0" to both score fields. Incomplete games have at least
    one blank score. The draw itself is always read separately for row IDs.
    """
    path = os.path.abspath(draw_path)
    results_path = tournament_files.ensure_results_file(path)
    with open(path, "rb") as stream:
        draw_digest = hashlib.sha256(stream.read()).hexdigest()

    draw_rows = tournament_files._read_rows(path)
    result_rows = tournament_files._read_rows(results_path)
    keys = [cell.strip().casefold() for cell in draw_rows[0]]
    game_col = next(index for index, key in enumerate(keys) if key in GAME_HEADERS)
    columns = {field: keys.index(field) for field in RESULT_FIELDS}
    updates = []
    seen = set()

    for draw_row, result_row in zip(draw_rows[1:], result_rows[1:]):
        if len(draw_row) <= game_col or not draw_row[game_col].strip():
            continue
        identifier = _game_key(draw_row[game_col])
        # Duplicate game IDs, including 007 versus 7, cannot be safely synced.
        if identifier in seen:
            raise ValueError(f"Duplicate tournament game number: {identifier}")
        seen.add(identifier)
        fields = {
            field: result_row[index] if index < len(result_row) else ""
            for field, index in columns.items()
        }
        if not (fields["wscore"].strip() and fields["bscore"].strip()):
            continue
        record = {
            "draw_sha256": draw_digest,
            "game_number": draw_row[game_col].strip(),
            "results": fields,
        }
        updates.append((identifier, record, _digest_record(record)))
    return draw_digest, updates


def _send(url, token, record):
    """The server's positive acknowledgement is the ONLY sync success signal."""
    request = urllib.request.Request(
        url + "/submit",
        data=json.dumps(record, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-UWH-Sync-Token": token,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3) as reply:
        response = json.loads(reply.read(16_384).decode("utf-8"))
    if response.get("status") not in ("saved", "already_saved"):
        raise ValueError("Results server did not confirm the game was saved")


def _health(url, token, expected_draw_digest):
    request = urllib.request.Request(
        url + "/health",
        headers={"X-UWH-Sync-Token": token},
    )
    with urllib.request.urlopen(request, timeout=3) as reply:
        response = json.loads(reply.read(16_384).decode("utf-8"))
    if response.get("status") != "ready":
        raise ValueError("Results server did not confirm readiness")
    if response.get("draw_sha256") != expected_draw_digest:
        raise ValueError("The server has a different original tournament draw")


class TournamentSyncWorker:
    """A daemon that ONLY touches files/network; Tk polls a status queue.

    The stored settings and draw path are copied on the Tk thread. No widget,
    Tk variable or after() call is accessed from the networking thread.
    """

    def __init__(self, status_queue):
        self.status_queue = status_queue
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._configuration = ("", False, "", "")
        self._last_status = None
        self._thread = threading.Thread(
            target=self._run, name="Tournament results sync", daemon=True
        )

    def start(self):
        self._thread.start()

    def configure(self, draw_path, enabled, server_url, token):
        with self._lock:
            self._configuration = (
                str(draw_path), bool(enabled), str(server_url), str(token)
            )
        self.wake()

    def wake(self):
        self._wake.set()

    def stop(self):
        """Stop future retries; any in-flight network call times out promptly."""
        self._stop.set()
        self.wake()

    def _status(self, message):
        if message != self._last_status:
            self._last_status = message
            self.status_queue.put(message)

    def _run(self):
        while not self._stop.is_set():
            with self._lock:
                config = self._configuration
            try:
                self._sync_once(*config)
            except Exception as error:
                self._status(f"Sync error: {error} · retry in 10 s")
            self._wake.wait(RETRY_SECONDS)
            self._wake.clear()

    def _sync_once(self, draw_path, enabled, server_url, token):
        if not enabled:
            self._status("Local results saved on this computer · network sync off")
            return
        if not draw_path or not os.path.isfile(draw_path):
            self._status("Select a tournament draw before synchronising")
            return
        url = normalise_url(server_url)
        if len(token) < 16:
            self._status("Enter the results server token and Save & Sync")
            return

        draw_digest, records = completed_game_records(draw_path)
        receipt_path = _receipt_path(draw_path)
        acked = _load_receipts(receipt_path, draw_digest, url)
        pending = [
            (key, record, checksum) for key, record, checksum in records
            if acked.get(key) != checksum
        ]

        if not pending:
            # Distinguish "nothing to send" from an unavailable server.
            try:
                _health(url, token, draw_digest)
            except Exception as error:
                self._status(f"Server check failed: {error} · retry in 10 s")
                return
            self._status("Local results saved · all completed games synced")
            return

        self._status(f"Local results saved · {len(pending)} game(s) pending sync")
        for position, (key, record, checksum) in enumerate(pending):
            if self._stop.is_set():
                return
            # Switching to Local only or a different draw/server cancels
            # further submissions from an already-running sync pass.
            with self._lock:
                if self._configuration != (
                    draw_path, enabled, server_url, token
                ) and self._thread.is_alive():
                    return
            try:
                _send(url, token, record)
            except urllib.error.HTTPError as error:
                # 409 means a genuine conflicting score: never silently
                # overwrite another court's results or discard the local copy.
                details = ""
                try:
                    details = json.loads(error.read(2048)).get("error", "")
                except (ValueError, UnicodeError):
                    pass
                if error.code == 409:
                    self._status(
                        f"CONFLICT game {key}: {details or 'different remote result'}"
                    )
                else:
                    self._status(
                        f"Sync blocked (HTTP {error.code}): {details} · retry in 10 s"
                    )
                return
            except (OSError, ValueError, urllib.error.URLError) as error:
                self._status(f"Network unavailable: {error} · retry in 10 s")
                return

            # Mark as delivered only after server confirms that this specific
            # game has reached its durable results file.
            acked[key] = checksum
            _save_receipts(receipt_path, draw_digest, url, acked)
            self._status(
                f"Game {key} synced · {len(pending) - position - 1} pending"
            )
        self._status("Local results saved · all completed games synced")
