# Underwater Hockey Scoring Desk Kit

A project to allow the use of a computer, modern computer languages and readily available Arduino hardware to make a scoring and siren system for Underwater Hockey. Example hardware is described in `HARDWARE_SETUP.md`.

The software has an operator-facing Underwater Hockey Game Management App and a player-facing Display Window. The operator window opens on Game Variables, with three other tabs: Sounds, Zigbee Siren and Scoreboard.

Contents
- [Raspberry Pi 5: tested configuration](#raspberry-pi-5-tested-configuration-september-2026)
- [Download and install on a Raspberry Pi 5](#downloading-and-installing-uwh-on-a-raspberry-pi-5)
- [Game Variables tab](#game-variables-tab)
- [Sounds tab](#sounds-tab)
- [Scoreboard tab](#scoreboard-tab)
- [Zigbee2MQTT wireless siren control](#zigbee2mqtt-wireless-siren-control)
- [Other installation and packaging notes](#other-installation-and-packaging-notes)


### Known working setups:

## Windows 11: tested configuration (September 2026)

#### Windows 11
App works fine under Windows, Zigbee wireless sirens wo.

## Raspberry Pi 5: tested configuration (September 2026)

#### Raspberry Pi 5
Raspberry Pi OS Desktop based on Debian 12 Bookworm (now listed as Raspberry Pi OS Legacy), Python 3.11, and the X11 desktop session. Two maximised displays, mouse movement, game timers and score updates work well on this combination.

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
5. Enable **Show Display Screen** on the Game Variables tab to open the player-facing display, if required.

You can create a desktop shortcut by right-clicking the executable and selecting **Show more options → Send to → Desktop (create shortcut)**.

### Installing future updates
When a newer version is released, repeat the download and extraction process.

> [!IMPORTANT]
> Before replacing an existing installation, back up your `settings.json` file and tournament CSV files. These can contain your customised settings, game results and tournament information.

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
2. Open the GitHub repository containing this README. This document does not include a verified repository-owner URL, so please use the project's existing GitHub link rather than a guessed address.
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

The startup self-test should run, followed by the operator interface. Use the **Show Display Screen** checkbox in **Game Variables → Tournament List** if you need to open the player-facing window. Position both windows on their respective monitors.

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

In particular, keep copies of your own `settings.json`, tournament CSV files, sound files added under `assets/`, and game logs such as `UWH_Game_Data.txt` if present. The application writes results back to the CSV file during tournaments.

After copying a fresh version into its intended location, install that version's dependencies into its `.venv` and test it from Terminal before changing the desktop shortcut. Do not copy a `.venv` from an old installation.

### Raspberry Pi troubleshooting

| Symptom | Check |
|---------|-------|
| Jerky mouse when passing over Game Variables checkboxes | Run `echo $XDG_SESSION_TYPE`. If it shows `wayland`, test the X11 option described [above](#select-x11-on-raspberry-pi-os). |
| `ModuleNotFoundError` at startup | Check that `.venv/bin/python -m pip install -r requirements.txt` completed successfully, and that you launch with `.venv/bin/python uwh.py`. |
| `No module named tkinter` | Install `python3-tk` using APT and recreate/test the virtual environment as necessary. |
| Desktop icon appears but program does not start | Run `.venv/bin/python uwh.py` from Terminal; check the `Exec=` and `Path=` entries in the desktop shortcut. |
| Presentation Display is missing or opens on the wrong monitor | Check **Show Display Screen** and position the window on the intended display. |
| Zigbee siren unavailable | Consult `ZIGBEE_SETUP.md`; a detected USB/COM port is not proof that the Zigbee button is paired or communicating. |
| Need to check OS package updates | Run `sudo apt update` followed by `apt list --upgradable`. An empty list means no upgrades are offered by the configured repositories, not that you are on the newest version. |

## Game Variables tab

Here, you can set most of the parameters of the games and select whether Team Time-Outs, Overtime and Sudden Death aspects of the game are allowed.

All value boxes accept decimal time, e.g. `1.5` (or `1,5`) = 1 minute and 30 seconds.

**Time to Start First Game** allows early setup of the system, ensuring the first game starts at a particular time. This is reliant on the Local Computer Time being correct. The format is HH:mm (no leading zeros).

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

**Crib Time:** has both a checkbox that, when selected, enables the program to shorten the 'Between Game Break' by this value until the Court Time is aligned with the Local Computer Time, and a value box where the time in minutes can be entered.

**Reset Timer** transfers the entered values to the program and starts the timer again with the new values.

### Presets

Here, six buttons are located where commonly used settings can be stored. Holding down the button for >4 seconds allows the name of the button to be altered and all the settings changed. Click the stored button to load those settings back into the Game Variables.

## Tournament List

A sample CSV file is included with the distribution of this app. This has a dropdown list where a CSV file can be selected that contains the draw for a Tournament or a list of games. The team names listed in the 'White' and 'Black' columns will appear on the Scoreboard.

The CSV File dropdown automatically refreshes when clicked. New Tournament CSV files copied into the application folder can be selected without restarting the application.

**Expected CSV headers:** `date,#,White,WScore,Black,BScore,Referees,Penalties,Comments`

Where `#` is the Game Number (but this can also be `game`, `game#` or `game_number`).

> [!IMPORTANT]
> The selected CSV file is modified as the games progress, as the app stores the scores, what Cap Numbers were penalised (into the 'Penalties' column), and if the 'Record Scorers Cap Number' check box is ticked, the cap numbers of the goal scorers from the selected 'White' and 'Black' columns.

When the 'Between Game Break' timer reached 30 seconds after the last game, the penalties and cap numbers of the goal scorers from the previous game are written to the selected CSV file and the penalties cleared.

The 'Starting Game #' will show a list of Game Numbers in the CSV file selected above. This could be useful if the app crashes and the games need to be restarted, or if multiple days' games are in the same file.

At the completion of each game, the application automatically advances to the next game number in the selected Tournament CSV file and updates the displayed team names. There is a drop down box to select the starting game number.

### Game Sequence

This section describes how the app progresses through the various stages of the game.

## Sounds tab

**Save Settings** is a button that stores the user-selected sound files to the JSON file (stored in the same location as the app itself).

**Pips** is a dropdown box where a sound file can be selected. Any .MP3 or .WAV file can be placed in the 'assets' folder and these will appear in the 'Pips' dropdown box.

**Siren** is a dropdown box where a sound file can be selected. Any .MP3 or .WAV file can be placed in the 'assets' folder and these will also appear in the 'Siren' dropdown box.

The **Open Sounds Folder** button opens the 'assets' folder, where sound files can be added.

The **Air** and **Water** controls are intended for separate above-water and underwater audio channels. Their effectiveness depends on the operating system, audio device and playback backend; check both channels work with your hardware.

**Pips** play at pre-determined periods.

**Siren** play at pre-determined periods and also when the Chief Referee activates the button to stop or start play.

**Number of seconds to play Siren** is a value box to alter how long the Siren sounds at the pre-determined periods. If the sound file is shorter than the value, it will automatically loop until the selected duration is complete.

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

- Pip sounds use the "Pips" sound file and, if it is a Linux system, volume settings from the Sounds tab
- Siren sounds use the "Siren" sound file and, if it is a Linux system, volume settings from the Sounds tab
- **Siren Minimum Duration:** All siren sounds play for a minimum period to ensure audibility for officials and players. If the sound file is shorter than the specified period, it will automatically loop until the configured duration is reached.
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

**Add Goal White** adds a goal to white and, if the 'Record Scorers Cap Number' check box is ticked, a popup dialogue box where the cap number of the player scoring the goal can be entered. Unknown and Penalty Goal options are provided.

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

The application includes Zigbee siren integration. Raspberry Pi/Linux MQTT and Windows operation require separate setup and end-to-end testing.

## Platform support

**Linux (Raspberry Pi):** MQTT/Zigbee2MQTT integration is provided; configure and test it using `ZIGBEE_SETUP.md`.

**Windows:** Zigbee2MQTT with a Mosquitto MQTT broker is documented, but not verified here as a complete working installation.

### Features and implementation status

**Wireless Chief Referee Controls:** Use Zigbee buttons to trigger sirens remotely

**Dual Connection Methods:**
- **MQTT Integration:** Zigbee2MQTT/MQTT communication and reconnection logic are implemented; confirm reliability on the actual Linux or Windows installation.
- **Serial Communication:** The code describes a Windows serial option, but its end-to-end behaviour has not been confirmed; do not assume an arbitrary Zigbee USB radio works merely because a COM port appears.
- **Auto-Detection:** USB/COM-port detection may identify a connected adapter; confirm that the Zigbee radio actually communicates.

**Configuration UI:** Dedicated "Zigbee Siren" tab for easy setup and monitoring

**Seamless Integration:** Uses existing sound files, volume controls, and audio channels

**Robust Error Handling:** The application includes reconnect/fallback logic; verify its behaviour before relying on the wireless siren in a match.

**Real-time Logging:** Activity monitoring and troubleshooting tools

**Fallback Logic:** MQTT/serial fallback is an intended feature; check it on the target hardware.

### Windows serial mode: verification required

Plugging in a Zigbee USB dongle and installing `pyserial` may be sufficient. This is not a verified installation procedure. A visible serial port alone does not establish that the app and dongle communicate.

**Adapter compatibility:** CC2531, CC2652 and CC2538 refer to Zigbee hardware families. CP210x, FTDI and CH340/CH341 refer to USB/serial interface chips, not proof of Zigbee support. Verify the actual radio and its drivers on the target platform.

**Intended Zigbee button behaviour:** When configured and working, physical Zigbee button presses trigger a single siren playback for the duration configured in the Sounds tab ("Number of seconds to play Siren").

See `ZIGBEE_SETUP.md` for complete installation and configuration instructions.

## Other installation and packaging notes

### Running on other systems

The source is a Python/Tkinter program. Install the Python version and dependencies appropriate to your operating system, then launch `uwh.py`. The Pi 5 instructions above are the configuration actually tested; other operating systems and Python versions are not verified here.

On Raspberry Pi OS Bookworm, use the project virtual environment rather than a system-wide `pip install`. For additional Python packages, use:

```bash
.venv/bin/python -m pip install PACKAGE_NAME
```

Optional modules mentioned in earlier documentation include `paho-mqtt` (MQTT), `pyserial` (serial access) and audio backends. Their presence alone does not establish a working wireless siren or correct audio routing.

### Standalone executables (advanced)

A PyInstaller build can package the application, but builds and bundled resources must be checked for each platform. These notes describe the project's existing build approach; they have not been extensively tested.

**Windows:** If the GitHub repository offers a prepared Windows executable under Releases, download the appropriate release asset and follow its accompanying instructions. Otherwise, build from source using PyInstaller.

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

The application includes a startup diagnostic window. Earlier documentation lists MQTT broker detection, Zigbee2MQTT detection, MQTT stability checks, Arduino and Zigbee adapter detection, and serial/COM port discovery. Verify the final implementation on your platform.

### Useful references

- [Raspberry Pi OS downloads](https://www.raspberrypi.com/software/) — Bookworm-based Raspberry Pi OS Legacy desktop images.
- [Raspberry Pi OS documentation](https://www.raspberrypi.com/documentation/computers/os.html) — OS updates and Python virtual environments.
- [Raspberry Pi desktop configuration](https://www.raspberrypi.com/documentation/computers/configuration.html) — switching between X11 and Wayland using `raspi-config`.
- [GitHub: downloading files](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives-and-directories) — using Code → Download ZIP.
- `HARDWARE_SETUP.md` and `ZIGBEE_SETUP.md` in this repository, if supplied with your checkout.
