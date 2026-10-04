"""Release-order regression tests; no GitHub token or network required."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / ".github" / "scripts" / "release_gate.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "build-exe.yml"

spec = importlib.util.spec_from_file_location("release_gate", GATE_PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def release(tag, *, draft=False, prerelease=False):
    return {"tag_name": tag, "draft": draft, "prerelease": prerelease}


class ReleaseOrderTests(unittest.TestCase):
    def test_newest_main_build_is_publishable(self):
        allowed, reason = gate.release_is_current(
            "new", "new", "v1.2.740", [release("v1.2.739")]
        )
        self.assertTrue(allowed, reason)

    def test_older_main_commit_cannot_be_published_after_new_merge(self):
        allowed, reason = gate.release_is_current(
            "previous", "new", "v1.2.740", []
        )
        self.assertFalse(allowed)
        self.assertIn("newer commit", reason)

    def test_older_run_for_same_main_commit_cannot_reclaim_latest(self):
        allowed, reason = gate.release_is_current(
            "main", "main", "v1.2.740",
            [release("v1.2.741"), release("v1.2.739")],
        )
        self.assertFalse(allowed)
        self.assertIn("v1.2.741", reason)

    def test_rerunning_existing_release_cannot_reset_latest(self):
        allowed, _ = gate.release_is_current(
            "main", "main", "v1.2.741", [release("v1.2.741")]
        )
        self.assertFalse(allowed)

    def test_version_comparison_is_numeric_not_lexical(self):
        allowed, _ = gate.release_is_current(
            "main", "main", "v1.2.9", [release("v1.2.10")]
        )
        self.assertFalse(allowed)

    def test_older_published_release_does_not_block_new_build(self):
        allowed, _ = gate.release_is_current(
            "main", "main", "v1.2.741", [release("v1.2.740")]
        )
        self.assertTrue(allowed)

    def test_release_series_rollback_does_not_override_newer_series(self):
        allowed, reason = gate.release_is_current(
            "main", "main", "v1.2.742", [release("v1.3.741")]
        )
        self.assertFalse(allowed)
        self.assertIn("v1.3.741", reason)

    def test_new_release_series_can_publish(self):
        allowed, _ = gate.release_is_current(
            "main", "main", "v1.3.742", [release("v1.2.741")]
        )
        self.assertTrue(allowed)

    def test_draft_and_prerelease_do_not_suppress_stable_publish(self):
        allowed, _ = gate.release_is_current(
            "main", "main", "v1.2.741", [
                release("v1.2.800", draft=True),
                release("v1.2.799", prerelease=True),
                release("preview-build"),
            ]
        )
        self.assertTrue(allowed)

    def test_malformed_release_version_is_rejected(self):
        for tag in ("v1.2", "not-a-version", "v1.2.7.9"):
            with self.subTest(tag=tag):
                self.assertFalse(gate.release_is_current(
                    "main", "main", tag, []
                )[0])

    def test_release_listing_paginates_until_last_page(self):
        first = [release("v1.2.1")] * 100
        second = [release("v1.2.2")]
        paths = []

        def api(path, token):
            paths.append(path)
            return first if path.endswith("&page=1") else second

        with patch.object(gate, "github_get", side_effect=api):
            versions = list(gate.published_releases("owner/repo", "token"))
        self.assertEqual(len(versions), 101)
        self.assertEqual(len(paths), 2)
        self.assertTrue(paths[0].endswith("page=1"))
        self.assertTrue(paths[1].endswith("page=2"))

    def test_gate_outputs_skip_for_stale_main_without_fetching_releases(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output.txt"
            env = {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_SHA": "old-commit",
                "RELEASE_VERSION": "1.3.1",
                "GITHUB_TOKEN": "fake-test-token",
                "GITHUB_OUTPUT": str(output),
            }
            with patch.dict(os.environ, env):
                with patch.object(gate, "github_get", return_value={
                    "sha": "new-commit"
                }) as github:
                    gate.main()
            self.assertEqual(output.read_text(), "publish=false\n")
            github.assert_called_once_with(
                "repos/owner/repo/commits/main", "fake-test-token"
            )

    def test_gate_outputs_skip_after_higher_version_has_published(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output.txt"
            env = {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_SHA": "main",
                "RELEASE_VERSION": "1.3.1",
                "GITHUB_TOKEN": "fake-test-token",
                "GITHUB_OUTPUT": str(output),
            }
            with patch.dict(os.environ, env):
                with patch.object(gate, "github_get",
                                  side_effect=[{"sha": "main"},
                                               [release("v1.3.2")]]):
                    gate.main()
            self.assertEqual(output.read_text(), "publish=false\n")

    def test_api_failure_is_fail_closed_and_never_authorizes_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output.txt"
            env = {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_SHA": "main",
                "RELEASE_VERSION": "1.3.1",
                "GITHUB_TOKEN": "fake-test-token",
                "GITHUB_OUTPUT": str(output),
            }
            with patch.dict(os.environ, env):
                with patch.object(gate, "github_get",
                                  side_effect=OSError("GitHub offline")):
                    with self.assertRaisesRegex(OSError, "offline"):
                        gate.main()
            self.assertFalse(output.exists())

    def test_workflow_builds_both_platforms_and_serializes_publication(self):
        source = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("  build-windows:", source)
        self.assertIn("runs-on: windows-2022", source)
        self.assertIn("  build-rpi5:", source)
        self.assertIn("runs-on: ubuntu-22.04-arm", source)
        self.assertIn("needs: [build-windows, build-rpi5]", source)
        self.assertIn("if: github.event_name != 'pull_request'", source)
        self.assertIn("group: uwh-release-publish", source)
        self.assertIn("queue: max", source)
        self.assertIn("cancel-in-progress: false", source)
        self.assertEqual(
            source.count("uses: actions/download-artifact@v8"),
            2,
        )
        self.assertEqual(
            source.count("run: python .github/scripts/release_gate.py"),
            2,
        )
        self.assertIn("if: steps.final.outputs.publish == 'true'", source)
        self.assertIn("make_latest: true", source)
        self.assertIn('RELEASE_VERSION: "1.3.1"', source)
        self.assertNotIn("RELEASE_SERIES", source)
        self.assertIn("UnderwaterHockeyScoringDesk-v${{ env.RELEASE_VERSION }}-Windows.zip", source)
        self.assertIn("UnderwaterHockeyScoringDesk-v${{ env.RELEASE_VERSION }}-RaspberryPi5.zip", source)
        self.assertIn("tag_name: v${{ env.RELEASE_VERSION }}", source)
        self.assertIn("zip -yr", source)
        self.assertIn("Start-UWH.sh", source)


if __name__ == "__main__":
    unittest.main()
