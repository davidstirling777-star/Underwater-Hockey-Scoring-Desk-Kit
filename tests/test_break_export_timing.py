"""Tests for saving results immediately before the break's 30-second pip."""
import ast
from pathlib import Path
import unittest
from unittest.mock import Mock

import game_flow


def load_uwh_methods(*names):
    """Extract actual UWH methods without importing Tk/pygame or starting UWH."""
    path = Path(__file__).resolve().parents[1] / "uwh.py"
    parsed = ast.parse(path.read_text(encoding="utf-8"))
    methods = [item for cls in parsed.body if isinstance(cls, ast.ClassDef)
               for item in cls.body
               if isinstance(item, ast.FunctionDef) and item.name in names]
    if {item.name for item in methods} != set(names):
        raise AssertionError("Requested UWH method missing")
    cls = ast.ClassDef(name="CountdownCode", bases=[], keywords=[],
                       body=methods, decorator_list=[])
    compiled = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    namespace = {"game_flow": game_flow,
                 "play_timed_sound": lambda *args: SOUNDS.append(args[1])}
    exec(compile(compiled, str(path), "exec"), namespace)
    return namespace["CountdownCode"]


SOUNDS = []
CountdownCode = load_uwh_methods("countdown_timer",
                                 "run_next_game_transition",
                                 "next_period")


class Var:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class FakeEngine:
    def __init__(self, seconds):
        self.timer_seconds = seconds
        self.timer_running = True
        self.stored_penalties = [{"team": "White", "cap": "7", "duration": 120}]
        self.clear_goal_scorers = Mock()
        self.advance_period = Mock()
        self.period_end_event_name = Mock(return_value=None)

    def get_current_period(self):
        return {"name": "Between Game Break", "type": "break"}

    def should_play_period_end_siren(self, period):
        return self.timer_seconds == 1

    def should_play_break_countdown_pip(self, period):
        return self.timer_seconds == 31 or 2 <= self.timer_seconds <= 11

    def decrement_timer(self):
        self.timer_seconds -= 1

    def clear_sudden_death_goal(self):
        pass

    def stop_timer(self):
        self.timer_running = False

    def start_timer(self):
        self.timer_running = True


class FakeClock:
    def __init__(self):
        self.after = Mock(return_value="next_tick")
        self.after_cancel = Mock()


class Harness(CountdownCode):
    def __init__(self, seconds=31, succeeds=True):
        self.engine = FakeEngine(seconds)
        self.master = FakeClock()
        self.timer_job = None
        self.next_game_transition_job = "old_job"
        self.next_game_transition_done = False
        self._game_export_pending = False
        self._pending_export_game_number = None
        self._game_export_timer_was_running = False
        self._game_export_dialog = None
        self._game_export_error_label = None
        self.next_game_preview_active = True
        self.next_game_preview_number = "2"
        self.next_game_notice_active = False
        self.csv_success = succeeds
        self.events = []
        self.csv_var = Var("Draw.csv")
        self.use_tournament_list_var = Var(True)
        self.white_score_var = Var(4)
        self.black_score_var = Var(3)
        self.game_numbers = ["1", "2"]
        self.current_game_index = 0
        self.starting_game_var = Var("1")
        self.siren_var = Var("siren.mp3")
        self.pips_var = Var("pip.mp3")
        self.enable_sound = Var(True)
        self.sound_trims = {"pip.mp3": 50, "siren.mp3": 60}
        self.siren_duration = Var(1.5)
        self.max_siren_duration = Var("10")
        self.update_timer_display = Mock()
        self.log_game_event = Mock()
        self.update_team_names_display = Mock()
        self.update_game_number_display = Mock()
        self.update_penalty_display = Mock()
        self.clear_all_penalties = Mock()
        self.start_current_period = Mock()

    def get_sound_trim(self, filename):
        return self.sound_trims.get(filename, 100)

    def get_current_game_number(self):
        return self.starting_game_var.get()

    def write_game_results_to_csv(self, *args):
        self.events.append("export")
        return self.csv_success

    def advance_to_next_game(self):
        self.events.append("advance")

    def _show_game_export_error(self, reason):
        self.events.append("warning")
        self._game_export_timer_was_running |= self.engine.timer_running
        self.engine.stop_timer()


class BreakExportTimingTests(unittest.TestCase):
    def setUp(self):
        SOUNDS.clear()

    def test_export_not_run_at_break_start_or_with_32_seconds_left(self):
        for seconds in (300, 32):
            with self.subTest(seconds=seconds):
                app = Harness(seconds)
                app.countdown_timer()
                self.assertNotIn("export", app.events)
                self.assertFalse(app.next_game_transition_done)
                self.assertEqual(app.engine.timer_seconds, seconds - 1)

    def test_save_precedes_warning_pip_at_30_second_boundary(self):
        app = Harness(31)
        app.countdown_timer()
        self.assertEqual(app.events, ["export", "advance"])
        self.assertEqual(SOUNDS, ["pips"])
        self.assertEqual(app.engine.timer_seconds, 30)
        self.assertTrue(app.next_game_transition_done)

    def test_excel_lock_pauses_at_31_without_warning_pip_or_reset(self):
        app = Harness(31, succeeds=False)
        app.countdown_timer()
        self.assertEqual(app.events, ["export", "warning"])
        self.assertEqual(SOUNDS, [])
        self.assertEqual(app.engine.timer_seconds, 31)
        self.assertFalse(app.engine.timer_running)
        self.assertEqual(app.white_score_var.get(), 4)
        self.assertEqual(app.black_score_var.get(), 3)
        self.assertEqual(len(app.engine.stored_penalties), 1)

    def test_retry_saves_before_pip_and_resumes_break(self):
        app = Harness(31, succeeds=False)
        app.countdown_timer()
        app.csv_success = True
        app.run_next_game_transition()
        self.assertTrue(app.engine.timer_running)
        self.assertEqual(app.engine.timer_seconds, 31)
        self.assertEqual(SOUNDS, [])
        app.countdown_timer()
        self.assertEqual(SOUNDS, ["pips"])
        self.assertEqual(app.engine.timer_seconds, 30)
        self.assertEqual(app.events.count("export"), 2)
        self.assertEqual(app.events.count("advance"), 1)

    def test_short_break_exports_at_first_tick(self):
        app = Harness(25)
        app.countdown_timer()
        self.assertEqual(app.events[:2], ["export", "advance"])
        self.assertEqual(app.engine.timer_seconds, 24)

    def test_manual_next_period_cannot_bypass_export_failure(self):
        app = Harness(90, succeeds=False)
        app.next_period()
        self.assertEqual(app.events, ["export", "warning"])
        app.engine.advance_period.assert_not_called()
        self.assertEqual(app.white_score_var.get(), 4)

    def test_manual_next_period_exports_before_advancing(self):
        app = Harness(90)
        app.next_period()
        self.assertEqual(app.events, ["export", "advance"])
        app.engine.advance_period.assert_called_once_with(0, 0)
        app.start_current_period.assert_called_once_with()

    def test_export_is_not_duplicated_on_subsequent_pips(self):
        app = Harness(31)
        app.countdown_timer()
        app.countdown_timer()
        self.assertEqual(app.events.count("export"), 1)
        self.assertEqual(SOUNDS, ["pips"])


if __name__ == "__main__":
    unittest.main()
