"""Headless regression tests for precise, bounded ordinary siren duration.

Import only the relevant sound.py functions: no mixer, audio device or Tk
window is needed to exercise the actual playback decisions.
"""
import ast
import math
import os
from pathlib import Path
import types
import unittest


class FakeChannel:
    def __init__(self):
        self.volume = None

    def set_volume(self, volume):
        self.volume = volume


class FakeSound:
    def __init__(self, length):
        self.length = length
        self.calls = []
        self.volume = None
        self.channels = []

    def get_length(self):
        return self.length

    def set_volume(self, volume):
        self.volume = volume

    def play(self, **kwargs):
        self.calls.append(kwargs)
        channel = FakeChannel()
        self.channels.append(channel)
        return channel


class DeferredThread:
    created = []

    def __init__(self, target, args, daemon):
        self.target = target
        self.args = args
        self.daemon = daemon
        self.created.append(self)

    def start(self):
        pass

    def run(self):
        self.target(*self.args)


def _load_sound_functions(sound_object):
    path = Path(__file__).resolve().parents[1] / "sound.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    names = {"play_sound_with_volume", "_play_sound_with_volume_sync"}
    funcs = [
        node for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    if {node.name for node in funcs} != names:
        raise AssertionError("Expected sound.py helpers not found")
    selected = ast.fix_missing_locations(
        ast.Module(body=funcs, type_ignores=[])
    )
    fake_os = types.SimpleNamespace(path=types.SimpleNamespace(
        join=os.path.join, exists=lambda path: True
    ))
    namespace = {
        "_get_value": lambda value: value.get() if hasattr(value, "get") else value,
        "_normalise_filename": lambda name: str(name or "").strip(),
        "_is_valid_sound_selection": lambda name: bool(str(name or "").strip()),
        "_normalise_volume": lambda value: float(value) / 100,
        "_preloaded_sounds": {"siren.mp3": sound_object, "pip.mp3": sound_object},
        "PYGAME_INITIALIZED": True,
        "IS_WINDOWS": False,
        "IS_LINUX": False,
        "resource_path": lambda path: path,
        "threading": types.SimpleNamespace(Thread=DeferredThread),
        "os": fake_os,
        "math": math,
    }
    exec(compile(selected, str(path), "exec"), namespace)
    return namespace


class TkDuration:
    """Fail if a worker tries reading a Tk value after the UI snapshot."""
    def __init__(self, value):
        self.value = value
        self.calls = 0

    def get(self):
        self.calls += 1
        if self.calls > 1:
            raise RuntimeError("Tk duration accessed from playback thread")
        return self.value


class TimedSoundTests(unittest.TestCase):
    def setUp(self):
        DeferredThread.created.clear()
        self.sound = FakeSound(length=0.7)
        self.api = _load_sound_functions(self.sound)

    def play(self, kind="siren", duration=1.5, filename=None, enabled=True):
        self.api["play_sound_with_volume"](
            filename or ("pip.mp3" if kind == "pips" else "siren.mp3"),
            kind,
            enabled,
            40,
            65,
            60,
            60,
            duration,
        )
        if DeferredThread.created:
            DeferredThread.created[-1].run()

    def test_short_siren_loops_until_exact_time_limit(self):
        self.play(duration=1.5)
        self.assertEqual(self.sound.calls, [{"loops": -1, "maxtime": 1500}])
        self.assertEqual(self.sound.volume, 0.65)
        self.assertEqual(self.sound.channels[0].volume, 1.0)

    def test_long_siren_is_cut_off_at_configured_time(self):
        self.sound.length = 4.5
        self.play(duration=1.5)
        self.assertEqual(self.sound.calls, [{"loops": -1, "maxtime": 1500}])

    def test_duration_shorter_than_one_sample_uses_positive_maxtime(self):
        self.play(duration=0.0001)
        self.assertEqual(self.sound.calls, [{"loops": -1, "maxtime": 1}])

    def test_configured_zero_negative_nan_inf_do_not_play(self):
        for invalid in (0, -1, float("nan"), float("inf"), "invalid"):
            with self.subTest(invalid=invalid):
                self.sound.calls.clear()
                DeferredThread.created.clear()
                self.play(duration=invalid)
                self.assertEqual(self.sound.calls, [])

    def test_duration_is_bounded_to_wireless_safety_limit(self):
        self.play(duration=100)
        self.assertEqual(self.sound.calls, [{"loops": -1, "maxtime": 30_000}])

    def test_pips_remain_one_full_sound(self):
        self.play(kind="pips", duration=100)
        self.assertEqual(self.sound.calls, [{}])
        self.assertEqual(self.sound.volume, 0.4)
        self.assertEqual(self.sound.channels[0].volume, 1.0)

    def test_pips_do_not_access_siren_duration_at_all(self):
        tk_value = TkDuration(1.5)
        self.play(kind="pips", duration=tk_value)
        self.assertEqual(tk_value.calls, 0)
        self.assertEqual(self.sound.calls, [{}])

    def test_ui_snapshots_duration_before_background_thread_starts(self):
        tk_value = TkDuration(1.5)
        self.api["play_sound_with_volume"](
            "siren.mp3", "siren", True, 40, 65, 60, 60, tk_value
        )
        self.assertEqual(tk_value.calls, 1)
        self.assertEqual(len(DeferredThread.created), 1)
        self.assertEqual(DeferredThread.created[0].args[-1], 1.5)
        DeferredThread.created[0].run()
        self.assertEqual(tk_value.calls, 1)
        self.assertEqual(self.sound.calls, [{"loops": -1, "maxtime": 1500}])

    def test_muted_sound_does_not_start_worker(self):
        self.play(enabled=False)
        self.assertEqual(DeferredThread.created, [])
        self.assertEqual(self.sound.calls, [])


if __name__ == "__main__":
    unittest.main()
