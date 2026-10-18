"""Regression checks for CMAS preset clock policy and local sound offsets.

Run with: python -m unittest tests.test_cmas_clock_timing
These tests deliberately document the EXISTING referee and timeout controls;
they do not implement a new two-minute stop policy or change restart sounds.
"""
import unittest
from clock_timing import OneSecondDeadline
from game_engine import GameEngine


class CMASClockTests(unittest.TestCase):
    def test_tk_delay_does_not_accumulate(self):
        now = [100.0]
        scheduler = OneSecondDeadline(clock=lambda: now[0])
        self.assertEqual(scheduler.next_delay_ms(), 1000)
        now[0] = 101.12  # sound/UI work finished 120 ms late
        self.assertEqual(scheduler.next_delay_ms(), 880)
        now[0] = 102.20
        self.assertEqual(scheduler.next_delay_ms(), 800)
        now[0] = 102.99
        self.assertEqual(scheduler.next_delay_ms(), 1010)

    def test_reset_starts_new_second_after_referee_pause(self):
        now = [10.0]
        scheduler = OneSecondDeadline(clock=lambda: now[0])
        self.assertEqual(scheduler.next_delay_ms(), 1000)
        now[0] = 50.0
        scheduler.reset()
        self.assertEqual(scheduler.next_delay_ms(), 1000)

    def test_break_warning_uses_existing_one_second_offset(self):
        game = GameEngine()
        period = {"name": "Half Time", "type": "break"}
        game.timer_seconds = 31
        self.assertTrue(game.should_play_break_countdown_pip(period))
        game.timer_seconds = 30
        self.assertFalse(game.should_play_break_countdown_pip(period))
        for secs in range(2, 12):
            game.timer_seconds = secs
            self.assertTrue(game.should_play_break_countdown_pip(period))

    def test_period_end_siren_uses_existing_offset(self):
        game = GameEngine()
        for period in (
            {"name": "First Half", "type": "regular"},
            {"name": "Overtime Second Half", "type": "overtime"},
            {"name": "Between Game Break", "type": "break"},
        ):
            game.timer_seconds = 2
            self.assertFalse(game.should_play_period_end_siren(period))
            game.timer_seconds = 1
            self.assertTrue(game.should_play_period_end_siren(period))

    def test_draw_proceeds_to_overtime_but_win_skips_it(self):
        periods = [
            {"name": "First Half", "type": "regular"},
            {"name": "Second Half", "type": "regular"},
            {"name": "Overtime Game Break", "type": "break"},
            {"name": "Overtime First Half", "type": "overtime"},
            {"name": "Overtime Second Half", "type": "overtime"},
            {"name": "Sudden Death Game Break", "type": "break"},
            {"name": "Sudden Death", "type": "sudden_death"},
            {"name": "Between Game Break", "type": "break"},
        ]
        game = GameEngine()
        game.set_sequence(periods)
        game.go_to_period("Second Half")
        game.advance_period(1, 1)
        self.assertEqual(game.get_current_period()["name"], "Overtime Game Break")
        game.go_to_period("Second Half")
        game.advance_period(2, 1)
        self.assertEqual(game.get_current_period()["name"], "Between Game Break")
        game.go_to_period("Overtime Second Half")
        game.advance_period(1, 1)
        self.assertEqual(game.get_current_period()["name"], "Sudden Death Game Break")

    def test_timeout_allowances_and_referee_pause_state(self):
        game = GameEngine()
        game.start_timeout("White")
        self.assertEqual(game.white_timeouts_this_half, 1)
        game.end_timeout()
        self.assertIsNone(game.active_timeout_team)
        game.reset_half_timeouts()
        self.assertEqual(game.white_timeouts_this_half, 0)
        self.assertTrue(game.is_referee_timeout("Referee Time-Out"))
        self.assertIn("Sudden Death", game.timeouts_disabled_periods())


if __name__ == "__main__":
    unittest.main()
