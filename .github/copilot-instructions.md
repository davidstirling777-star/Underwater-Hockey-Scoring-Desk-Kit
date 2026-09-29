# UWH source-contribution notes

**Read [MAINTAINERS.md](../../MAINTAINERS.md) first.** It is the current
maintainer-oriented map of modules, threading, tournament-export invariants,
and deployment. README.md is for operators/installers; ZIGBEE_SETUP.md is
for Zigbee2MQTT deployment. The original single-file/no-tests notes that were
previously in this file no longer described the repository.

## Dependencies and environments

- This is a **multi-module Python Tkinter application**. It is tested as a
  Windows packaged EXE and from source on Raspberry Pi OS Bookworm with X11.
- The tested Raspberry Pi environment uses **Python 3.11**. Use the
  repository's `requirements.txt` in a virtual environment instead of
  assuming the standard library alone is sufficient. Optional devices and
  audio use `paho-mqtt`, `pyserial`, and `pygame`.
- Build/release details live in `.github/workflows/build-exe.yml`; a new
  source commit does **not** update an already-installed EXE.
- Existing matches may contain user-edited `settings.json`, tournament CSVs,
  sounds and logs. Do not rewrite or remove them merely to test a change.

## Where to work

| Concern | Main modules |
|---|---|
| Tk root and live event handlers | `uwh.py` |
| Game period rules | `game_engine.py`, `game_flow.py` |
| Results/data | `csv_helpers.py`, `csv_export.py`, `game_logging.py` |
| Settings and backups | `settings_manager.py`, `game_settings_manager.py` |
| Screen widgets and scaling | `settings_ui.py`, `scoreboard_ui.py`, `display_ui.py`, `ui_scaling.py` |
| Sounds | `sound.py`, `sounds_ui.py` |
| Wireless MQTT | `zigbee_siren.py`, `zigbee_control.py`, `zigbee_ui.py` |
| Arduino and detected USB ports | `serial_siren_listener.py`, `zigbee_hardware_ui.py` |

**Safety boundaries:** Only the Tk thread should update widgets and read Tk
variables; the MQTT and Arduino workers enqueue UI/audio events. Zigbee2MQTT,
not UWH, owns the Zigbee coordinator COM port. Port detection is *not* a
successful serial open. An unrecognised Zigbee button/action must not activate
a siren until a referee has explicitly allowed and mapped it.

**Results boundary:** The tournament CSV must be successfully written before
the game can be reset/advanced. The writer uses `csv.reader`/`csv.writer`
for quoted names, checks unique game numbers, stages a full replacement, and
replaces the draw atomically. On failure, preserve live scores and penalties
and let the operator retry. `UWH_Game_Data.txt` is a legacy event log and
does not include a reliable tournament game-number field.

**Settings boundary:** Changes to sections belong through the central locked
unified settings writer. Normal Game Variables and Screens autosave coalesce
about once per minute; explicit save operations are immediate. Retain existing
user settings and their five most recent timestamped backups.

## Validation

Install the dependencies into the intended virtual environment. Run:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q .
```

The repository has an automated **headless GitHub Actions** regression suite.
It does not validate real USB devices, audio routing, Linux/Windows monitor
placement, or whether a coordinator is paired; test those separately on
appropriate hardware and a copy of any live tournament draw.

Keep one focused draft pull request per issue, with regression tests for
behaviour changes. Never change a production siren or tournament file as
an incidental side effect of a documentation cleanup.
