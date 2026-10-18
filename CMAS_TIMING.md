# CMAS match timing and local sound preferences

Reference: CMAS Underwater Hockey Rules of Play, version 13.0 (February
2025). Confirm the applicable competition regulations with organisers.

## Rules / CMAS preset

The stored CMAS preset specifies two 15-minute regulation halves and a
3-minute interval. It also includes a 3-minute pre-overtime interval, two
5-minute overtime halves with a 1-minute interval, and a 1-minute
pre-sudden-death interval. A team timeout is 60 seconds, with one allowed
per team in each regulation half. The application tracks match periods,
scores and remaining team-timeout allowances.

CMAS has special clock-stoppage rules in the final two minutes, and the
Chief Referee controls stoppage and restart signals. A sounding siren by
itself does not tell software whether it signals a stop or a restart.
**Operator procedure:** use the existing Referee Time-Out facility to
hold the clock when directed by the referee. Do not assume the scoring
desk automatically interprets a siren as a stop or restart.

## Local scoring-desk preferences (not CMAS tolerance claims)

* The selected 30-second warning is triggered on the tick that updates
  the countdown from 00:31 to 00:30.
* The final 10 countdown pips are triggered on ticks updating 00:11
  through 00:02 to 00:10 through 00:01.
* A period-ending siren is requested on the tick updating 00:01 to 00:00.
* Team-timeout warning is requested at 00:16 (one second before the
  displayed 00:15); the existing end sound is requested at 00:01.
* Sound files, trims, durations and these established audible cues are
  local operational choices. They do **not** represent a statement that
  CMAS formally allows an arbitrary +/-1-second signal tolerance.

The app uses monotonic scheduled deadlines for its one-second Tk timers,
so routine audio/UI callback latency does not accumulate across the
match. This does not guarantee zero output-device sound latency or
hard-real-time behaviour on Windows / Raspberry Pi. Verify timing with
a clock and speakers in a real pool-side setup.

## Referee review pending

Do not change the final-two-minute policy automatically, the referee
restart workflow, or the team-timeout-end sound until the proposed
operator procedures have been discussed with referees. A rapid buzz
as a *request* for the Chief Referee to sound the restart signal is a
proposal only, **not** an implemented change.

## Regression checks

Run `python -m unittest tests.test_cmas_clock_timing` and the full
`python -m unittest discover -s tests` suite after software changes.
Check live half-time, overtime, sudden death, both team timeouts in
sequence, referee pauses, operator stop/restart and actual audible pip
and siren timing before tournament use.
