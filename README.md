# Underwater Hockey Scoring Desk Kit

A project to allow the use of a computer, modern computer languages and readily available Arduino hardware to make a scoring and siren system for Underwater Hockey. Example hardware is described in `HARDWARE_SETUP.md`.

The software has an operator-facing Underwater Hockey Game Management App and a player-facing or spectator-facing Display Window(s). The operator window opens on the second tab, Game Variables, with four other tabs: Scoreboard, Screens, Sounds, and Zigbee Siren.

## Contents

- [Windows 11: tested configuration](#windows-11-tested-configuration-september-2026)
- [Raspberry Pi 5: tested configuration](#raspberry-pi-5-tested-configuration-september-2026)
- [Downloading and installing UWH on Windows](#downloading-and-installing-uwh-on-windows)
- [Downloading and installing UWH on a Raspberry Pi 5](#downloading-and-installing-uwh-on-a-raspberry-pi-5)
- [Game Variables tab](#game-variables-tab)
- [Tournament List](#tournament-list)
- [Screens tab](#screens-tab)
- [Sounds tab](#sounds-tab)
- [Scoreboard tab](#scoreboard-tab)
- [Zigbee2MQTT wireless siren control](#zigbee2mqtt-wireless-siren-control)
- [Other installation and packaging notes](#other-installation-and-packaging-notes)

## Known working setups

## Windows 11: tested configuration (September 2026)

The Windows 11 UWH application, wired Arduino siren, Mosquitto MQTT broker and Zigbee2MQTT have been tested together with **up to three working Zigbee buttons** on one coordinator. Observed button actions include `single`, `double`, `hold` and `emergency`; **which action each button sends depends on its model**, and UWH's per-button Action Mapping determines the siren response. Zigbee2MQTT was also confirmed to restart through PM2 and Windows Task Scheduler after a Windows reboot. See [ZIGBEE_SETUP.md](ZIGBEE_SETUP.md) for installation and button-mapping instructions. Do not re-pair a working button to a second coordinator just to share it with another UWH computer.

## Raspberry Pi 5: tested configuration (September 2026)

Raspberry Pi OS Desktop based on Debian 12 Bookworm (listed as Raspberry Pi OS Legacy), Python 3.11, and the X11 desktop session. Two maximised displays, mouse movement, game timers and score updates have been tested on this combination. A complete Raspberry Pi Zigbee2MQTT/Mosquitto installation has **not** been independently verified in the same way as the Windows setup.

Why X11 matters for this application: On the tested Pi 5, moving the pointer over Game Variables checkboxes under Wayland caused GPU utilisation to reach about 98% and the mouse became jerky. A separate note: Raspberry Pi recommends Wayland generally, but X11 was demonstrably better for this GUI.

> [!IMPORTANT]
> **Recommended Pi 5 configuration:** Stay with **Bookworm + X11** until a different combination has been tested with UWH. Raspberry Pi recommends Wayland generally, but X11 was demonstrably better for the Scoring Desk Kit's GUI performance on Bookworm.

#### Select X11 on Raspberry Pi OS
1. Open Terminal and run `sudo raspi-config`.
2. Select **6 Advanced Options** → **A7 Wayland** → **W1 X11**.
3. Select Finish and reboot when prompted.
4. After reboot, run:
   ```bash
   echo $XDG_SESSION_TYPE
   ```
   It should print `x11`. If it prints `wayland`, check the selection and reboot again. To switch back later, use **W2 Labwc** in the same menu.

## Downloading and installing UWH on Windows

### Download the program
1. Open the UWH Scoring Desk Kit repository on GitHub.
2. On the right-hand side of the repository page, find **Releases**.
3. Click Releases, then select the latest release.
4. Scroll down to the **Assets** section.
5. Click the Windows ZIP file. Its name will resemble: `UnderwaterHockeyScoringDesk-v1.2.123-Windows.zip`
   (The version and build numbers will vary.)
6. The ZIP file will download to your computer, normally into your Downloads folder.

> [!IMPORTANT]
> Do not select **Source code (zip)** or use the green **Code → Download ZIP** button. Those download the Python source code, not the ready-to-run Windows application.

### Extract the program
1. Open Windows File Explorer and navigate to Downloads.
2. Right-click the downloaded ZIP file.
3. Select **Extract All...**
4. Choose a permanent folder, such as `Documents\UWH Scoring Desk`.
5. Click Extract.

The extracted folder contains `UnderwaterHockeyScoringDesk.exe` and its supporting files. Keep these together.

### Run the application
1. Open the extracted folder.
2. Double-click `UnderwaterHockeyScoringDesk.exe`.
3. The startup self-test will run before the application opens.
4. The Game Management window will appear.
5. Use the **Screens** tab's **Display Screen Options** to open a player-facing or crowd-facing display, if required. Choose a supported Standard or Widescreen layout. Closing a Display Window with its **X** closes it and queues the closed state for the next automatic settings save (about one minute after the first change, or on normal program exit). Check your monitor assignments with **Auto Detect Screens** and **Test Displays**.

You can create a desktop shortcut by right-clicking the executable and selecting **Show more options → Send to → Desktop (create shortcut)**.

### Installing future updates

Download the newer release and extract it into a **separate folder** first. Do not overwrite a working installation without a backup.

> [!WARNING]
> **Back up `settings.json` before every update.** It includes your **Zigbee button-name list** (for example, `siren_button, siren_button_2, siren_button_3`), MQTT settings, sound preferences, screen layout and the remembered Display Window open/closed state. Back up tournament CSVs, custom sounds under `assets/`, and game logs too. Replacing UWH's settings can lose button names **or action mappings**, even though the buttons remain paired to Zigbee2MQTT.

After updating, confirm the **Zigbee Siren → Button Device Names** field and test every configured button and its action mapping before using the system at a match. Do not blindly replace a new-format `settings.json` with a very old version; compare and carry forward your customised values where the format has changed. Zigbee2MQTT has a **separate** `data/` directory that should be backed up before Zigbee2MQTT updates; see [ZIGBEE_SETUP.md](ZIGBEE_SETUP.md).

## Downloading and installing UWH on a Raspberry Pi 5

These instructions are for a new installation from the Python source, not a standalone executable. A keyboard, mouse and Raspberry Pi OS Desktop are needed; the Lite edition does not include the graphical desktop.

### 1. Prepare Raspberry Pi OS

For a new Pi 5 installation based on the tested setup, select **Raspberry Pi OS (Legacy, 64-bit) with desktop** in Raspberry Pi Imager. As of September 2026 this is the Bookworm-based image; the standard, newer Raspberry Pi OS uses Wayland by default.

After booting into the desktop, select X11 using the [instructions above](#select-x11-on-raspberry-pi-os). Open Terminal and install the prerequisites:

```bash
sudo apt update
sudo apt install python3-venv python3-tk python3-pip unzip
```

Raspberry Pi OS Bookworm includes Python 3.11. Python 3.12 is not a requirement for the configuration tested here. `python3-tk` supplies the Tkinter desktop toolkit; `python3-venv` allows dependencies to be installed in a project-specific environment.

### 2. Download the program from GitHub

1. Open Chromium (or another browser) on the Raspberry Pi.
2. Open the GitHub repository containing this README. Open the [UWH Scoring Desk Kit repository](https://github.com/davidstirling777-star/Underwater-Hockey-Scoring-Desk-Kit).
3. Above the list of files, click the green **Code** button and choose **Download ZIP**.
4. Save the ZIP into your Downloads folder. In the tested installation it was named `Underwater-Hockey-Scoring-Desk-Kit-main.zip`.
5. Open **File Manager** → **Downloads**. Right-click the ZIP and extract it into Downloads. If the Pi has no internet connection, download the ZIP on another computer and copy it to the Pi using a USB drive from another computer.

Alternatively, using Terminal after the ZIP has downloaded:

```bash
cd ~/Downloads
unzip Underwater-Hockey-Scoring-Desk-Kit-main.zip
cd Underwater-Hockey-Scoring-Desk-Kit-main
```

> [!WARNING]
> **Do not overwrite an existing installation without a backup.** It may contain your saved `settings.json`, edited tournament CSV files, custom sounds and other game records. Back it up first, or extract into a separate directory.

### 3. Install the Python dependencies

Open Terminal in the extracted project directory (or use `cd` as shown above). Run:

```bash
cd ~/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

A `.venv` is a private Python environment inside the project folder. This is important on Bookworm: do not use `sudo pip install` or `pip install --break-system-packages` to install this project's dependencies.

The contents of `requirements.txt` may change between versions; use the file in the ZIP you downloaded as the source of truth. The application includes optional audio and Zigbee features that may need additional system packages or Python modules.

### 4. Run UWH

Still in Terminal, run:

```bash
cd ~/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main
.venv/bin/python uwh.py
```

The startup self-test should run, followed by the operator interface. Use **Screens → Display Screen Options** to open player-facing or crowd-facing displays. Position each window on its intended monitor. Closing a Display Window with **X** queues its closed state for automatic saving (about one minute after the first change, or on normal exit). Use **Auto Detect Screens** and **Test Displays** to identify the monitors.

If startup fails, launch with the Terminal command above rather than a desktop shortcut. The last lines printed to Terminal are usually much more useful than the last startup self-test message.

### 5. Optional: create a desktop shortcut

Once the Terminal launch works, the following commands create a shortcut on the Pi user's desktop, using the folder shown in these instructions. Paste the complete block into Terminal:

```bash
cat > "$HOME/Desktop/UWH-Scoring-Desk.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=UWH Scoring Desk
Comment=Underwater Hockey scoring and siren application
Exec=$HOME/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main/.venv/bin/python $HOME/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main/uwh.py
Path=$HOME/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main
Terminal=false
Categories=Game;
EOF
chmod +x "$HOME/Desktop/UWH-Scoring-Desk.desktop"
```

If the desktop asks you to **Allow Launching** or **mark the shortcut as trusted**, do so. If your project was extracted anywhere other than `~/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main`, adjust both the `Exec=` and `Path=` entries to match.

### 6. Updating an existing installation safely

A GitHub Download ZIP is a snapshot: it does not update itself. To obtain newer code, download a new ZIP and extract it into a separate directory, or back up the existing directory before replacing files.

In particular, keep copies of `settings.json` (including the Zigbee `siren_button_devices` list, MQTT broker, sounds and screen visibility), tournament CSV files, sound files added under `assets/`, and game logs such as `UWH_Game_Data.txt` if present. The application writes results back to the CSV file during tournaments. A missing UWH `settings.json` does not unpair a button, but UWH can lose its name and stop responding to it.

After copying a fresh version into its intended location, install that version's dependencies into its `.venv` and test it from Terminal before changing the desktop shortcut. Do not copy a `.venv` from an old installation. Verify the **Zigbee Siren** button-name list after restoring settings; the Raspberry Pi and Windows MQTT setup instructions are in [ZIGBEE_SETUP.md](ZIGBEE_SETUP.md).

### Raspberry Pi troubleshooting

| Symptom | Check |
|---------|-------|
| Jerky mouse when passing over Game Variables checkboxes | Run `echo $XDG_SESSION_TYPE`. If it shows `wayland`, test the X11 option described [above](#select-x11-on-raspberry-pi-os). |
| `ModuleNotFoundError` at startup | Check that `.venv/bin/python -m pip install -r requirements.txt` completed successfully, and that you launch with `.venv/bin/python uwh.py`. |
| `No module named tkinter` | Install `python3-tk` using APT and recreate/test the virtual environment as necessary. |
| Desktop icon appears but program does not start | Run `.venv/bin/python uwh.py` from Terminal; check the `Exec=` and `Path=` entries in the desktop shortcut. |
| Display Window is missing or opens on the wrong monitor | Check **Screens → Display Screen Options**, run **Auto Detect Screens** and **Test Displays**, and position the window on the intended monitor. Closing the window with **X** queues its closed state for automatic saving or normal exit. |
| Zigbee siren unavailable | Consult `ZIGBEE_SETUP.md`; a detected USB/COM port is not proof that the Zigbee button is paired or communicating. |
| Need to check OS package updates | Run `sudo apt update` followed by `apt list --upgradable`. An empty list means no upgrades are offered by the configured repositories, not that you are on the newest version. |

## Game Variables tab

Here, you can set most of the parameters of the games and select whether Team Time-Outs, Overtime and Sudden Death aspects of the game are allowed.

Most period-duration boxes accept decimal **minutes**, e.g. `1.5` (or `1,5`) = 1 minute and 30 seconds. **Crib Time** is in seconds; **Time to Start First Game** is a 24-hour clock time, not a duration.

**Time to Start First Game** schedules the first game against the computer's local clock. Enter a 24-hour time as `H:MM` or `HH:MM`: both `9:36` and `09:36` mean 09:36. The minutes must have two digits (for example, `9:06`). If the selected time has already passed today, the app schedules it for tomorrow.

**First Game Starts In:** is another way to set when the first game starts, in 'minutes from now'. Entering a value here will wipe the time from 'Time to Start First Game'.

**Team time-outs allowed?** is a checkbox that, when selected, enables the Team Time-Out buttons in the Scoreboard tab and makes the 'Team Timeout Period' value box able to accept a value.

**Team Time-Out Period** is the value in minutes allowed for the 'Team Time-out'.

**Half Period:** The time in minutes of the first and second halves.

**Half Time Break:** The time in minutes of the half time break.

**Overtime allowed?** is a checkbox that, when selected, enables the program to enter Overtime if the scores are tied at the end of normal play. It also enables/disables the 'Overtime Game Break:', 'Overtime Half Period' and 'Overtime Half Time Break' value boxes.

**Overtime Game Break:** The time in minutes of the break between the end of the second half and the start of Overtime.

**Overtime Half Period:** The time in minutes of the Overtime halves.

**Overtime Half Time Break:** The time in minutes of the Overtime half time break.

**Sudden Death Game Break:** has both a checkbox that, when selected, enables the program to enter Sudden Death if the scores are tied at the end of Overtime play, and a value box where the time in minutes of the break before Sudden Death can be entered.

**Between Game Break:** The time in minutes of the break between the end of the game and the start of the next game. This time can be shortened by "Crib Time" (see below).

**Record Scorers Cap Number:** enables a popup dialogue box to appear when a goal is scored, where the cap number of the player scoring the goal can be entered. There is also the option of 'Unknown' and 'Penalty Goal'.

**Crib Time:** has both a checkbox that, when selected, enables the program to shorten the 'Between Game Break' by this value until Court Time is aligned with Local Computer Time, and a value box where the adjustment is entered in **seconds**.

**Reset Timer** transfers the entered values to the program and starts the timer again with the new values.

### Presets

Here, six buttons are located where commonly used settings can be stored. Holding a preset button for **three seconds** opens its editor, where the button name and saved settings can be changed. Click the stored button to load those settings back into the Game Variables.

### Tournament List

A sample CSV file is included with the distribution of this app. This has a dropdown list where a CSV file can be selected that contains the draw for a Tournament or a list of games. The team names listed in the 'White' and 'Black' columns will appear on the Scoreboard.

The CSV File dropdown automatically refreshes when clicked. New Tournament CSV files copied into the application folder can be selected without restarting the application.

**Expected CSV headers:** `date,#,White,WScore,Black,BScore,Referees,Penalties,Comments`

Where `#` is the Game Number (but this can also be `game`, `game#` or `game_number`).

> [!IMPORTANT]
> The selected tournament CSV is updated with scores in `WScore` and `BScore`, penalised cap numbers in `Penalties`, and (when **Record Scorers Cap Number** is enabled) scorer information in `Comments`. Scorer entries use forms such as `W#7(2)`, `W#PG(1)` (Penalty Goal) and `B#UNK(1)` (Unknown). The `White` and `Black` columns retain the team names. Team names containing commas or quotes must be properly quoted in CSV.

During **Between Game Break**, UWH attempts to export the completed game **just before the countdown reaches 00:30**. It writes a complete replacement CSV before swapping it into place. If saving fails, the game remains available for correction and retry: UWH must not discard its scores, penalties or scorer records and advance to the next game.

The 'Starting Game #' will show a list of Game Numbers in the CSV file selected above. This could be useful if the app crashes and the games need to be restarted, or if multiple days' games are in the same file.

At the completion of each game, the application automatically advances to the next game number in the selected Tournament CSV file and updates the displayed team names. There is a drop down box to select the starting game number.

### Game Sequence

This section describes how the app progresses through the various stages of the game.

## Screens tab

**Operator Screen** selects the standard or widescreen arrangement of the operator's own window. This is distinct from whether the player/crowd Display Window is currently open.

**Display Screen Options** offers Single/Dual Standard or Widescreen display layouts, subject to the monitors attached to the computer. Use these options to open the player-facing or crowd-facing window(s). **Closing a Display Window with its X** closes that window; its closed state is queued for automatic saving (about one minute after the first change, or on normal exit) and should remain closed after a normal restart. The selected layout is retained for the next time the display is opened. Do not assume changing the operator layout is an instruction to reopen a deliberately closed display.

**Show Team Names** controls whether team names are shown on the operator and display screens.

**Auto Detect Screens** refreshes the monitor information shown under **These screens were detected**. Windows uses the native monitor list; on the tested Raspberry Pi Bookworm/X11 configuration, monitor detection uses `xrandr`. If automatic detection cannot establish a layout, select the required layout manually.

**Test Displays** labels the detected screens for approximately eight seconds. Dismiss the labels by clicking or pressing **Esc**. The controls and screen placement should be tested on the actual monitors before a match.

## Sounds tab

**Save Settings** is a button that stores the user-selected sound files to the JSON file (stored in the same location as the app itself).

**Pips** is a dropdown box where a sound file can be selected. Any .MP3 or .WAV file can be placed in the 'assets' folder and these will appear in the 'Pips' dropdown box.

**Siren** is a dropdown box where a sound file can be selected. Any .MP3 or .WAV file can be placed in the 'assets' folder and these will also appear in the 'Siren' dropdown box.

The **Open Sounds Folder** button opens the 'assets' folder, where sound files can be added.

The **Air** and **Water** controls are intended for separate above-water and underwater audio channels. Channel routing depends on the operating system, audio device and playback backend; test both outputs on the actual hardware. The Windows Zigbee siren was tested using the same selected sound and matched playback volume as the application/Arduino siren, which does **not** by itself establish that independent Air/Water routing is implemented on every Windows audio device.

**Pips** play at pre-determined periods.

**Siren** plays at pre-determined periods and also when the Chief Referee activates the button to stop or start play.

**Number of seconds to play Siren** sets the requested duration of timed game and mapped wireless siren cycles. If the selected file is shorter, playback loops as needed. **Maximum Siren Duration (seconds)** independently caps each timed blast (default 10 seconds; allowed 1–30 seconds), including when the requested duration is longer.

**Hardwired button (Arduino/serial):** the siren sounds while the button is held and stops when it is released. This differs from the timed Zigbee button behaviour.

**Zigbee buttons (MQTT):** When **Button Action Mapping** assigns them accordingly, `single` sounds one timed cycle and `double` sounds two consecutive timed cycles **without a programmed pause**. On the button tested for `hold`, that action arrives on release and was mapped to one timed cycle. Another tested button publishes `emergency`, which must be mapped separately. These are **observed examples, not universal button behaviours**. See [ZIGBEE_SETUP.md](ZIGBEE_SETUP.md) for setup and Auto-add From Log.

### Sound timing table

The system automatically plays audio cues during different periods:

| Period Type | Period Name | 30s Remaining | 10s–1s Remaining | 0s (End) |
|---|---|---|---|---|
| **Break Periods** | First Game Starts In | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Between Game Break | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Half Time | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Overtime Game Break | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Overtime Half Time | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| | Sudden Death Game Break | 1 Pip (at 30s) | 1 Pip per second (at 10s–1s) | Siren (at 0s) |
| **Game Periods** | First Half | – | – | Siren (at 0s) |
| | Second Half | – | – | Siren (at 0s) |
| | Overtime First Half | – | – | Siren (at 0s) |
| | Overtime Second Half | – | – | Siren (at 0s) |
| | Sudden Death | – | – | – |

#### Notes:

- Pip sounds use the chosen **Pips** file and the playback settings supported by the installed audio backend.
- Siren sounds use the chosen **Siren** file. Matching application, Arduino and Zigbee playback levels have been tested on the Windows setup; test Air/Water channel routing separately on the target hardware.
- **Timed siren playback:** A short sound file loops until the configured duration is reached, subject to **Maximum Siren Duration**. The hardwired Arduino siren instead follows the button's physical press and release.
- Audio channels (Air/Water) use their respective volume settings
- Game periods (halves) only play siren at the end, no countdown pips
- Sudden Death periods have no automatic audio cues. The Sudden Death timer counts upwards from 00:00. A goal scored during Sudden Death immediately ends the game. Sudden Death Start and Sudden Death End messages are logged but do not trigger audio.

## Scoreboard tab

**Court Time:** In this widget is the Court Time. This is synchronised to the 'Local Computer Time' when the app first opens. If the 'Crib Time' is selected, the Court Time, which may have been extended by break periods, is progressively shortened until it aligns with the Local Computer Time.

**Game Sequence:** The next row is where the Game Sequence is announced. Breaks are 'Red', Play is 'Light Coral Blue'.

**Game Number:** Under that is the Game Number, picked up from the CSV file (if this is selected from the Tournament list).

**Team names:** Then are the Team names, picked up from the CSV file (if this is selected from the Tournament list).

**Scores:** The Scores, which will get written to the CSV file when the 'Between Game Break' timer reaches 30 seconds after a game ends, are displayed next.

If the 'Team time-outs allowed?' check box is selected, the Team Time-Out buttons are selectable. Only one team time-out per half, no team time-outs are permitted in Overtime or Sudden Death according to CMAS rules.

**Add Goal White** adds a goal to white and, if the 'Record Scorers Cap Number' checkbox is ticked, a popup dialogue box where the cap number of the player scoring the goal can be entered. Unknown and Penalty Goal options are provided.

**Referee Time-Out** pauses:
- Court Time
- The active game timer
- Team Time-Out timers
- Penalty timers

When Referee Time-Out is released, the interrupted period(s) resumes from the exact point at which it was paused, including Sudden Death periods.

**Penalties** is enabled during play but greyed out for breaks (as you cannot award a Penalty when play cannot be stopped [section 17.1.1 of CMAS rules]) but if the 'Referee Time-Out' button is pushed, the Penalties button becomes active.

## Other game behaviour

### Coping with Errors (like when a goal is scored right on the buzzer!)

Summary of what happens when goals are added during the three "break" periods:

### Goals added during breaks

This table explains the results and progression rules when a goal is added during a break period:

| Break Period | Scores After Goal is Added | What Happens |
|---|---|---|
| Between Game Break | Even | Progress to Overtime Game Break (if Overtime allowed) OR Sudden Death Game Break (if Sudden Death allowed and Overtime not allowed). |
| | Uneven | Remain in Between Game Break. No progression; continue as normal. |
| Overtime Game Break | Even | Remain in Overtime Game Break. Proceed to overtime periods according to schedule. |
| | Uneven | Skip Overtime! Progress directly to Between Game Break. |
| Sudden Death Game Break | Even | Remain in Sudden Death Game Break. Proceed to Sudden Death period as scheduled. |
| | Uneven | Progress directly to Between Game Break. (Skips Sudden Death period.) |

This logic ensures the correct flow for tournament progression based on goals scored during break periods.

## Zigbee2MQTT wireless siren control

UWH receives wireless referee-button actions via **Zigbee2MQTT → Mosquitto (MQTT) → UWH**. Windows 11 has been verified end-to-end, including automatic Zigbee2MQTT startup after reboot. Raspberry Pi 5 MQTT/Zigbee installation instructions are provided but should be tested on the actual Pi before match use.

### Tested Zigbee button actions

The following are **observed action names with example mappings**, not a claim that all three buttons publish the same actions. Only a saved mapping for the exact button and action triggers UWH:

| Observed action in MQTT | Example local UWH siren mapping |
|---|---|
| `single` | One timed cycle |
| `double` | Two consecutive timed cycles, no programmed pause |
| `hold` | One timed cycle, triggered on release for the tested button |
| `emergency` | A separately configured action, such as one timed cycle |

Timed cycles use **Sounds → Number of seconds to play Siren**, capped by **Maximum Siren Duration**. The wired Arduino button retains physical press-and-release control. Check each model's Activity Log and save its mapping.

### Up to three tested Zigbee buttons and configuration backups

The setup has been tested with **up to three working Zigbee buttons** on the **same Zigbee2MQTT coordinator**, with friendly names `siren_button`, `siren_button_2` and `siren_button_3`. Enter the names of the buttons you actually use in **Zigbee Siren → Button Device Names (comma-separated)**. For the three-button setup:

```text
siren_button, siren_button_2, siren_button_3
```

Click **Save Configuration**, then check **Button Action Mapping**. A button can be listed and appear in the Activity Log without sounding the siren if its observed action has no mapping. Press the button, use **Auto-add From Log** for a missing action, edit the new **Ignore** row to your intended UWH action, and click **Save Action Mappings**. Both the button-name list and action mappings live in `settings.json`; restoring them can restore UWH control **without re-pairing** the Zigbee device.

> [!IMPORTANT]
> **One Zigbee button cannot ordinarily be paired to two separate Zigbee coordinator networks at the same time.** To use a button with a second UWH computer, connect both UWH applications to the **existing MQTT broker**, rather than pairing the button to a second coordinator. **Both UWH installations may sound their local sirens** when receiving the same button message; choose which computer is authorised to control the live amplifier. Re-pairing to a different Zigbee network can break the original pairing.

For detailed [Raspberry Pi 5 and Windows setup](ZIGBEE_SETUP.md), native Windows PM2/Task Scheduler startup, pairing, frontend-friendly-name conventions, MQTT broker security and two-computer examples, read **[ZIGBEE_SETUP.md](ZIGBEE_SETUP.md)**. A Windows COM-port detection message by itself does not prove a button is paired; direct Windows serial operation is **not** the verified button-control path here.

## Other installation and packaging notes

### Running on other systems

The source is a Python/Tkinter program. Install the Python version and dependencies appropriate to your operating system, then launch `uwh.py`. Windows 11 has been tested end-to-end with Zigbee2MQTT; Raspberry Pi 5 has been tested as a Bookworm/X11 desktop application. The full Pi MQTT/Zigbee setup and other operating systems have not received the same end-to-end verification.

On Raspberry Pi OS Bookworm, use the project virtual environment rather than a system-wide `pip install`. For additional Python packages, use:

```bash
.venv/bin/python -m pip install PACKAGE_NAME
```

For source installations, `paho-mqtt` is the **Python MQTT client**, not the MQTT broker. Zigbee2MQTT is a separate **Node.js** program. On Bookworm, install Python dependencies inside the UWH virtual environment; a Windows release EXE normally includes its required Python dependencies. `pyserial`/COM-port discovery alone does not establish Zigbee pairing or serial-mode compatibility. See [ZIGBEE_SETUP.md](ZIGBEE_SETUP.md).

### Standalone executables (advanced)

A PyInstaller build can package the application, but builds and bundled resources must be checked for each platform. These notes describe the project's existing build approach; they have not been extensively tested.

**Windows:** Prefer the prepared Windows ZIP under GitHub **Releases → Assets**. Use a source/PyInstaller build only if you need to develop or package UWH yourself. A downloaded source-code ZIP is not the ready-to-run Windows EXE.

**Linux:** If `build_exe.sh` exists in the checkout, the earlier build workflow was:

```bash
cd ~/Downloads/Underwater-Hockey-Scoring-Desk-Kit-main
source .venv/bin/activate
python -m pip install pyinstaller
chmod +x build_exe.sh
./build_exe.sh
```

The earlier documentation expects an executable at `dist/uwh` after a successful Linux build. That path depends on the current build script; use `ls dist` to inspect the actual result. For a direct specification, consult the build script.

The earlier spec/build notes refer to `--onefile`, `--windowed`, bundled MP3 files under `assets/`, `settings.json` and tournament sample data. Check the current `.spec` or build script before relying on those features.

### Startup self-test

The application includes a startup diagnostic window and a Zigbee Siren activity log. Device/COM-port detection is a diagnostic, **not** proof of Zigbee pairing or an audible siren. The Windows MQTT path has been tested by pressing the physical buttons and hearing the local siren; use the same end-to-end test on any new computer.

### Useful references

- [Raspberry Pi OS downloads](https://www.raspberrypi.com/software/) — Bookworm-based Raspberry Pi OS Legacy desktop images.
- [Raspberry Pi OS documentation](https://www.raspberrypi.com/documentation/computers/os.html) — OS updates and Python virtual environments.
- [Raspberry Pi desktop configuration](https://www.raspberrypi.com/documentation/computers/configuration.html) — switching between X11 and Wayland using `raspi-config`.
- [GitHub: downloading files](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives-and-directories) — using Code → Download ZIP.
- [ZIGBEE_SETUP.md](ZIGBEE_SETUP.md) — Mosquitto, Python/Paho, Zigbee2MQTT, pairing, multi-computer warnings and troubleshooting.
- `HARDWARE_SETUP.md` — wired Arduino/physical hardware, where supplied.
