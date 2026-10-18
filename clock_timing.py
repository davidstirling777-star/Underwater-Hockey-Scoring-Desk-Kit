"""Drift-resistant scheduling for the scoring-desk's one-second callbacks.

Tk.after() schedules a *minimum* delay; scheduling every callback 1000 ms
after the previous one makes UI and audio handling delays accumulate.
This helper anchors successive callbacks to monotonic one-second deadlines.
A long interruption (such as a referee pause) can explicitly reset it.
"""
import time


class OneSecondDeadline:
    def __init__(self, clock=None):
        self.clock = clock or time.monotonic
        self.deadline = None

    def reset(self):
        self.deadline = None

    def next_delay_ms(self):
        now = self.clock()
        if self.deadline is None:
            self.deadline = now + 1.0
        else:
            self.deadline += 1.0
        # Catch up if a short GUI callback was late; don't carry that delay
        # into every later second. Long manual pauses must call reset().
        return max(1, round((self.deadline - now) * 1000))
