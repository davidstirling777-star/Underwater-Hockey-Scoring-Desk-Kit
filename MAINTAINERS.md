# UWH maintainer guide

This is the technical companion to [README.md](README.md), which is the single
operator, installation, tournament-sync and Zigbee deployment manual.
[HARDWARE_SETUP.md](HARDWARE_SETUP.md) remains a separate working hardware note
while the production hardware is still being developed. This maintainer guide
is intended for someone modifying the **Python source**, not for a referee
operating a match.

## Start here

- **Program entry point:** `uwh.py`, especially `GameManagementApp`.
  It owns the Tk root, the mutable operator-facing variables, and the
  `after()` callbacks. It delegates business rules and widget creation to
  the modules below. Avoid adding new 1,000-line handlers to this file.
- **Match rules and state:** `game_engine.py` stores the current period,
  scores-related scorer counts, penalty data, and timer values.
  `game_flow.py` advances games and protects the completed game during export.
- **Test without changing a live draw:** use a copy of a tournament CSV and
  a separate installation/settings directory. The headless tests in `tests/`
  cover several important failure cases but do not test physical speakers,
  button pairing, actual COM-port ownership, or every Tk window placement.
- **Prefer a small, separately reviewed pull request.** Behavioural changes
  to sirens, match progression, and results should have tests and a physical
  acceptance check. Comments and docstrings should explain *why* a rule exists,
  not simply restate its Python syntax.

## Source map

| File | Responsibility and place to begin |
|---|---|
| `uwh.py` | Composition root; Tk event handlers, audio dispatch, timers, screen state and serial/MQTT queues. |
| `app_icon.py` | Embedded UWH stick badge applied to the Tk window and taskbar without reintroducing the v1.3 visual theme. |
| `app_version.py` | User-visible application version. Windows release builds stamp this to the GitHub Actions release number before PyInstaller runs. |
| `game_engine.py` | Period list, period transitions and runtime timer/penalty state. |
| `game_flow.py` | Tournament selection, advancing games and export-before-reset rule. |
| `game_logging.py` | Appends the older pipe-delimited `UWH_Game_Data.txt` event log. |
| `settings_ui.py` | Game Variables, standalone Tournament List, About, Screens-tab widgets and their explanatory labels/links. |
| `scoreboard_ui.py` | Referee-facing scoreboard widgets and commands. |
| `display_ui.py` | External display window creation, monitor selection and mirrored scoreboard widgets. |
| `display_manager.py` | Penalty display label/sorting helpers. |
| `ui_scaling.py` | Operator and external-window font resizing; avoids child-widget Configure storms. |
| `penalties_ui.py` | Penalty-entry dialog and its refresh/removal handlers. |
| `preset_manager.py` | Nine Game Variables preset buttons and long-hold editor; older six-slot settings are migrated without renaming existing presets. |
| `csv_ui.py` | Draw-file dropdown refresh. |
| `tournament_files.py` | Protect input draw, create/resume results CSV, manage the visible `Tournament data` folder, migrate legacy root CSVs, and write manual draws. |
| `tournament_sync.py` | Worker: completed local game discovery, 10 s retries, receipts, HTTP client; never touch Tk from worker. |
| `tournament_results_server.py` | Standalone authenticated third-computer writer, serialised result merges and conflict detection. |
| `csv_helpers.py` | CSV draw game-number list and team-name retrieval; handles quoted fields. |
| `csv_export.py` | Tournament result writer, scorer formatting and legacy goal-event helpers. |
| `game_settings_manager.py` | Translate between Game Variables widgets and the persisted gameSettings section. |
| `settings_manager.py` | The unified settings.json reader, locked merge and atomic replacement/backups. |
| `sounds_ui.py` | Sounds-tab file-selection/preview tables, per-file Trim % editing and siren timing controls. |
| `sound.py` | Audio resource loading from the visible app-level `Sounds` folder, pygame/subprocess backends, loop control and timed cutoff. |
| `zigbee_ui.py` | MQTT connection widgets, device-name field and per-button action mapping table. |
| `zigbee_siren.py` | Paho MQTT connection/subscription, message filtering and optional siren-device publishes. |
| `zigbee_control.py` | Operator's Connect/Test/Disconnect buttons and connection watchdog. |
| `zigbee_hardware_ui.py` | Display-only reporting of enumerated Arduino and coordinator ports. |
| `serial_siren_listener.py` | COM-port detection/cache and the Arduino serial listener. |
| `hardware_detection.py` | Hardware enumeration and saved detection metadata. |
| `startup_selftest.py` | Diagnostic MQTT probe, not the live connection. |
| `.github/scripts/release_gate.py` | Suppress stale multi-platform release publishing after the Windows and Raspberry Pi 5 builds. |

## The three different siren pathways

Do not assume that a visible USB dongle, a working MQTT session and an audible
siren are the same condition. Port detection is not the same as a
successful serial open, and a broker connection is not a mapped button press.

1. **Wired Arduino button:** `serial_siren_listener.py` enumerates and opens
   the *Arduino* serial port at 9600 baud; it puts ON/OFF events into the
   application's queue. `uwh.py` consumes those events on Tk's main thread.
   A held button plays local audio until release and may also send an MQTT
   ON/OFF command to the separately configured siren output device. Hardware
   enumeration alone does not mean the serial listener successfully opened
   the port. An “Access is denied” COM-port error is distinct from Zigbee.
2. **Wireless Zigbee buttons:** Zigbee2MQTT owns the *single coordinator* serial
   port and publishes button `action` messages to Mosquitto. The Paho client in
   `zigbee_siren.py` subscribes and filters by the exact UWH **Button Device
   Names**. Its separate **Button Action Mapping** table resolves
   (device name, received action) to a UWH event. Unknown devices/actions
   fail closed and are logged. **Auto-add From Log** may copy an observed new
   device into Button Device Names and imports its action as **Ignore**; an
   operator must edit and save it before it can produce audio. The MQTT worker
   queues the observation/event; it must not manipulate Tk
   widgets or pygame audio directly.
3. **Automatic game siren/pips:** `uwh.py`'s countdown checks period policy
   in `game_engine.py` and calls `sound.py`. Timed sirens loop short sound
   clips as needed, with a separate configurable maximum duration. Continuous
   wireless sound has a second bounded hold limit and an audio-level cutoff.
   These limits are **not** substitutes for the wired Arduino release.

The Windows setup has been tested with up to three working buttons on one
coordinator. Do not
pair a live button to a second coordinator just to support another UWH client.
A second UWH client can instead subscribe to the existing MQTT broker, but
two active clients may both play audible local sirens.

## Tournament draw and recovery rules

The typical header is
`date,#,White,WScore,Black,BScore,Referees,Penalties,Comments`.
The game column may be `#`, `game`, `game#` or `game_number`; the
results writer needs **WScore, BScore, Penalties, Comments**. Read records
with `csv.reader`, never `line.split(',')`: quoted team names can contain
commas, apostrophes, quotes and embedded newlines. A duplicated numeric game
ID, including `7` and `007`, must not be guessed or overwritten.

`tournament_files.py` owns the draw/output boundary. Tournament CSVs live in
the app-level `Tournament data` folder. Startup copies legacy root-level CSVs
there only when the same filename is absent, and seeds the demo draw/results
pair without overwriting operator data. `results_path_for_draw` derives the
sibling `_Results.csv`, and
`ensure_results_file` copies the source *only on first selection*. It checks
that non-result columns still match the draw on every subsequent access.
Never replace an existing results file from the sample or the selected draw:
doing so could erase a completed tournament. `csv_ui.get_csv_files` excludes
generated `_Results.csv` files from the draw picker.

`csv_export.write_game_results_to_csv` reads the selected draw indirectly
through this guard but stages and atomically replaces **only the results CSV**.
The draw remains unmodified; duplicate game numbers still fail closed. An
export failure must retain both prior results and the operator's live game.
`game_flow.export_and_reset_game_at_break` remains the protection gate: only
after a successful write does it log Game End, clear scores/penalties/scorers
and advance. Keep the two-file contract intact on Windows and Linux.
The countdown checks export before its 30-second warning pip; an operator can
retry instead of losing match data. Do not reorder these operations casually.

Scorer comments use `W#7(2)`, `W#PG(1)`, `B#UNK(1)`, etc. The legacy
`UWH_Game_Data.txt` event format has **no tournament game number**; its
`get_goal_events_for_game(..., game_number)` helper must not be used as
reliable per-game attribution without extending and migrating that format.

## Two-court, local-first results sync

The [README two-court synchronisation section](README.md#two-court-tournament-results-synchronisation) explains setup,
the private LAN boundary and RP5/Windows acceptance testing. The draw must
have identical bytes on the results server and both scoring computers.
`tournament_sync.completed_game_records` reconstructs every locally
completed game's fields from the durable court _Results.csv; a missing
acknowledgement file causes safe idempotent replay, not loss of a game.
`TournamentSyncWorker` uses its own daemon thread, wake Event and 10-second
retry; Tk is touched only by polling its status queue. It must never delay
`game_flow.export_and_reset_game_at_break`: the remote network is not part
of the local export success gate.

`tournament_results_server.apply_submission` accepts only game-number and
four result fields plus the full source-draw SHA-256. The HTTP handler
authenticates and holds one process lock around validation, merge and atomic
results replacement. All non-result columns are checked against the source
draw; a different result for an already-saved game is HTTP 409, never a
last-writer-wins overwrite. The server cannot accept filesystem paths from
clients, and production clients must authenticate over a protected LAN/VPN.
Do not use SMB to let two clients overwrite the whole results CSV.

The masked sync token and server URL live in the `tournamentSync` section
of settings.json, **not** in the draw or receipt file. A masked GUI field
does not encrypt settings.json: protect filesystem permissions. Default
mode is Local only; there are no network calls until Save & Sync explicitly
enables the shared server.

## Settings and update safety

`settings.json` is a single unified document with named sections.
`settings_manager.py` serializes and stages changes, replaces files
atomically, and keeps up to the five most recent timestamped `settings_old_*.json`
backups. The UI coalesces *automatic* Game Variables and screen edits into
roughly one write per minute; explicit Sounds, Zigbee and preset Save actions
remain immediate. Normal program exit flushes pending edits.

Do not overwrite the full settings file using a stale snapshot of one section,
and never silently reset a damaged existing settings file to defaults.
PyInstaller releases place editable files beside the EXE; back up the
operator's settings, tournament CSVs and custom audio **before** replacing an
installation. A new `.py` commit does not update an already-installed Windows
EXE: the release needs rebuilding and installation. Zigbee2MQTT's own
`data/` directory is a **separate** backup.

## Screens, threads and operating systems

The operator layout and visible external Display Screen are independent.
Closing a Display Window leaves the selected layout remembered but marks the
external display *closed*. Changing the operator's aspect ratio must not
reopen it. The screen setting joins the coalesced settings save. On Windows,
display enumeration uses native monitor APIs; the tested Raspberry Pi 5
configuration is Raspberry Pi OS Bookworm with X11, where xrandr provides
monitor geometry. Test the actual monitor arrangement before a match.

Tk widgets and Tk variables belong to the **main event-loop thread**.
Serial and MQTT background threads send work through queues; do not call Tk
or pygame on those worker threads. A status saying a port is *detected* is
not the same as a successful `serial.Serial(...)` open. The broker startup
probe in `startup_selftest.py` may fail while the actual controller later
connects successfully, so it should remain diagnostic rather than fatal.

## Check a change before proposing it

From the repository root, use the Python environment described in README:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q .
```

The GitHub Actions headless regression workflow covers scoring and settings
code but does not reproduce Windows COM-port locks, physical audio output,
the Raspberry Pi window manager, or an actual tournament draw on disk.
Test these manually on a **copy** of live files. Inspect the current
`.github/workflows/build-exe.yml` for the Windows packaging and release
procedure. Versioned Windows releases should only be published from current
`main` using the workflow's release gate.

For the exact operating instructions and any platform-specific deployment
qualification, use README.md rather than treating this architectural guide as
a setup script.
