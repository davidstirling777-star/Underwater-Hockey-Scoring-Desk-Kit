"""Two-court local-first result sync: safety, retry and shared-writer tests."""

import csv
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import queue
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

import csv_export
import tournament_results_server as server
import tournament_sync


HEADER = ["Venue", "#", "White", "WScore", "Black", "BScore", "Penalties", "Comments"]
SECRET = "a-long-unpredictable-test-token"


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.reader(stream))


class TwoCourtTournamentSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.server_folder = self.root / "server"
        self.server_folder.mkdir()
        self.courts = [self.root / "even", self.root / "odd"]
        for folder in self.courts:
            folder.mkdir()

        self.draw = self.server_folder / "Tournament_Draw.csv"
        with self.draw.open("w", encoding="utf-8-sig", newline="") as stream:
            csv.writer(stream).writerows([
                HEADER,
                ["Pool A", "1", "Odd, A", "", "Odd B", "", "", ""],
                ["Pool A", "2", "Even A", "", "Even B", "", "", ""],
                ["Pool A", "3", "Odd C", "", "Odd D", "", "", ""],
            ])
        self.original = self.draw.read_bytes()
        for folder in self.courts:
            (folder / self.draw.name).write_bytes(self.original)

        self.handler = server.make_handler(
            str(self.draw), SECRET, threading.Lock()
        )
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), self.handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True
        )
        self.server_thread.start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def export(self, court, game, white, black, penalties=()):
        return csv_export.write_game_results_to_csv(
            self.draw.name, str(self.courts[court]), str(game),
            white, black, penalties, True, {"7": 1}, {},
        )

    def worker(self, court):
        worker = tournament_sync.TournamentSyncWorker(queue.Queue())
        path = self.courts[court] / self.draw.name
        return worker, str(path)

    def sync(self, court, url=None, token=SECRET):
        worker, path = self.worker(court)
        worker._sync_once(path, True, url or self.url, token)
        return worker

    def results(self):
        return read_rows(self.server_folder / "Tournament_Results.csv")

    def test_each_court_keeps_local_results_and_server_merges_by_game(self):
        self.assertTrue(self.export(0, 2, 4, 3))
        self.assertTrue(self.export(1, 1, 1, 0))
        self.assertFalse((self.server_folder / "Tournament_Results.csv").exists())
        self.sync(0)
        self.sync(1)
        self.assertEqual(self.results()[1][3:6], ["1", "Odd B", "0"])
        self.assertEqual(self.results()[2][3:6], ["4", "Even B", "3"])
        self.assertEqual(self.draw.read_bytes(), self.original)
        for court in self.courts:
            self.assertEqual((court / self.draw.name).read_bytes(), self.original)

    def test_simultaneous_submissions_do_not_lose_either_result(self):
        self.export(0, 2, 2, 1)
        self.export(1, 1, 3, 4)
        failures = []
        def submit(index):
            try:
                self.sync(index)
            except Exception as error:
                failures.append(error)
        threads = [threading.Thread(target=submit, args=(i,)) for i in (0, 1)]
        for worker in threads:
            worker.start()
        for worker in threads:
            worker.join()
        self.assertEqual(failures, [])
        self.assertEqual(self.results()[1][3], "3")
        self.assertEqual(self.results()[2][3], "2")

    def test_zero_zero_is_an_actual_finished_game(self):
        self.export(1, 1, 0, 0)
        self.sync(1)
        self.assertEqual(self.results()[1][3], "0")
        self.assertEqual(self.results()[1][5], "0")

    def test_reboot_without_receipt_is_idempotent_and_no_reset(self):
        self.export(0, 2, 4, 3)
        self.sync(0)
        first = (self.server_folder / "Tournament_Results.csv").read_bytes()
        receipt = tournament_sync._receipt_path(
            self.courts[0] / self.draw.name
        )
        Path(receipt).unlink()
        worker = self.sync(0)
        self.assertEqual(self.results()[2][3], "4")
        self.assertEqual(
            (self.server_folder / "Tournament_Results.csv").read_bytes(),
            first
        )
        self.assertIn("all completed games synced", worker._last_status)

    def test_two_games_then_restart_preserves_both_results(self):
        self.export(1, 1, 1, 0)
        self.sync(1)
        self.export(1, 3, 4, 5)
        self.sync(1)
        saved = (self.server_folder / "Tournament_Results.csv").read_bytes()
        self.sync(1)  # a new worker, like app restart
        self.assertEqual(
            (self.server_folder / "Tournament_Results.csv").read_bytes(),
            saved,
        )
        self.assertEqual(self.results()[1][3], "1")
        self.assertEqual(self.results()[3][3], "4")

    def test_one_court_cannot_silently_overwrite_others_game(self):
        self.export(0, 2, 5, 1)
        self.export(1, 2, 9, 9)
        self.sync(0)
        prior = (self.server_folder / "Tournament_Results.csv").read_bytes()
        conflicted = self.sync(1)
        self.assertIn("CONFLICT game 2:", conflicted._last_status)
        self.assertEqual(
            (self.server_folder / "Tournament_Results.csv").read_bytes(),
            prior
        )
        # The local court keeps its conflicting score for manual resolution.
        self.assertEqual(
            read_rows(self.courts[1] / "Tournament_Results.csv")[2][3],
            "9"
        )

    def test_court_keeps_results_after_network_fails_then_retries(self):
        self.export(0, 2, 7, 2)
        self.httpd.shutdown()
        self.httpd.server_close()
        offline = self.sync(0)
        self.assertIn("Network unavailable:", offline._last_status)
        self.assertEqual(
            read_rows(self.courts[0] / "Tournament_Results.csv")[2][3],
            "7"
        )
        # A new server on the same endpoint allows the pending game to retry.
        self.httpd = ThreadingHTTPServer(
            ("127.0.0.1", int(self.url.rsplit(":", 1)[1])),
            self.handler,
        )
        self.server_thread = threading.Thread(
            target=self.httpd.serve_forever, daemon=True
        )
        self.server_thread.start()
        resumed = self.sync(0)
        self.assertIn("all completed games synced", resumed._last_status)
        self.assertEqual(self.results()[2][3], "7")

    def test_server_failure_does_not_ack_or_damage_local_files(self):
        self.export(0, 2, 3, 4)
        with patch.object(
            server.csv_export.os, "replace",
            side_effect=OSError("simulated disk full"),
        ):
            pending = self.sync(0)
        self.assertIn("Sync blocked (HTTP 503)", pending._last_status)
        self.assertEqual(self.draw.read_bytes(), self.original)
        self.assertEqual(
            read_rows(self.courts[0] / "Tournament_Results.csv")[2][3],
            "3",
        )
        success = self.sync(0)
        self.assertIn("all completed games synced", success._last_status)
        self.assertEqual(self.results()[2][3], "3")

    def test_different_draw_is_rejected_before_writing_results(self):
        self.export(0, 2, 4, 3)
        changed = self.courts[0] / self.draw.name
        changed.write_bytes(self.original.replace(b"Even A", b"EVEN B"))
        with self.assertRaisesRegex(ValueError, "does not match"):
            self.sync(0)
        self.assertFalse((self.server_folder / "Tournament_Results.csv").exists())
        # A valid, but different, source draw still fails the server hash check.
        with (self.courts[0] / "Tournament_Results.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as stream:
            rows = list(csv.reader(stream))
        rows[2][2] = "EVEN B"
        with (self.courts[0] / "Tournament_Results.csv").open(
            "w", encoding="utf-8-sig", newline=""
        ) as stream:
            csv.writer(stream).writerows(rows)
        rejected = self.sync(0)
        self.assertIn("CONFLICT", rejected._last_status)
        self.assertFalse((self.server_folder / "Tournament_Results.csv").exists())

    def test_authentication_is_required_even_for_health_check(self):
        self.export(0, 2, 1, 1)
        unauthorised = self.sync(0, token="wrong-but-long-enough")
        self.assertIn("Sync blocked (HTTP 401)", unauthorised._last_status)
        self.assertFalse((self.server_folder / "Tournament_Results.csv").exists())
        request = urllib.request.Request(self.url + "/health")
        with self.assertRaises(urllib.error.HTTPError) as captured:
            urllib.request.urlopen(request, timeout=3)
        self.assertEqual(captured.exception.code, 401)

    def test_server_rejects_arbitrary_filename_in_submission(self):
        digest, updates = tournament_sync.completed_game_records(
            self.courts[0] / self.draw.name
        )
        self.assertEqual(updates, [])
        record = {
            "draw_sha256": digest,
            "game_number": "1",
            "results": {
                "wscore": "1", "bscore": "0",
                "penalties": "", "comments": ""
            },
            "file": "../elsewhere.csv",
        }
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            server.apply_submission(str(self.draw), record)

    def test_health_check_detects_different_draw_before_first_game(self):
        # Merely configuring a court must detect a mismatched server draw,
        # even while the court has no completed results to POST.
        ready = self.sync(0)
        self.assertIn("all completed games synced", ready._last_status)
        self.draw.write_bytes(self.original.replace(b"Odd B", b"OTHER"))
        mismatch = self.sync(0)
        self.assertIn("different original tournament draw", mismatch._last_status)
        self.assertFalse((self.server_folder / "Tournament_Results.csv").exists())

    def test_local_only_mode_never_contacts_the_server(self):
        self.export(0, 2, 2, 3)
        worker, path = self.worker(0)
        worker._sync_once(path, False, "http://unreachable.invalid:8765", "")
        self.assertIn("network sync off", worker._last_status)
        self.assertFalse((self.server_folder / "Tournament_Results.csv").exists())
        self.assertEqual(
            read_rows(self.courts[0] / "Tournament_Results.csv")[2][3], "2"
        )

    def test_invalid_server_url_rejected_before_io(self):
        for invalid in (
            "", "\\\\server\\share", "file:///tmp/results", "http://user:p@host",
            "http://host/folder", "http://host/?path=../x",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    tournament_sync.normalise_url(invalid)

    def test_worker_can_be_stopped_without_a_network_connection(self):
        self.export(0, 2, 5, 5)
        worker, path = self.worker(0)
        worker.configure(path, True, self.url, SECRET)
        worker.start()
        worker.stop()
        worker._thread.join(timeout=5)
        self.assertFalse(worker._thread.is_alive())

    def test_results_server_rejects_duplicate_game_numbers(self):
        self.draw.write_bytes(self.original.replace(b"Pool A,2,", b"Pool A,1,"))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            # The result isn't created until the server's guarded first write.
            digest = __import__("hashlib").sha256(
                self.draw.read_bytes()
            ).hexdigest()
            server.apply_submission(str(self.draw), {
                "draw_sha256": digest,
                "game_number": "1",
                "results": {
                    "wscore": "2", "bscore": "2",
                    "penalties": "", "comments": ""
                },
            })


if __name__ == "__main__":
    unittest.main()
