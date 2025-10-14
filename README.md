A project to allow the use of cheap computers, modern computer languages and hardware to make a scoring system for Underwater Hockey.

The Software has a user interface that is hopefully accessible, logical and easily understood by novices.  

The initial idea was to use a Raspberry Pi5 computer, tiny amplifier (Raspberry DigiAMP+) and Bluetooth or Wi-Fi remote control to minimise connections.  A hardware button backup for wireless remote control would be nice but not yet implemented. The reason for gravitating to a Raspberry Pi is the HATs that are available, such as a dual channel amplifier, will drastically reduces wires and connections (hopefully leading to a robust system).

The App opens with two windows.  One, called the Display Window, is designed for facing towards the players so they can see the time and score.  The second, called Underwater Hockey Game Management App, opens with the tab 'Game Variables' visible. There are three other tabs, Sounds, Zigbee Siren and Scoreboard. Both windows are able to be maximised to the screen size.

**'Game Variables'** Tab
Here, you can set most of the parameters of the games, select if Team Time-Outs, Overtime and Sudden Death aspects of the game are allowed.  All value boxes accept decimal time e.g. 1.5 (or 1,5) = 1 minute and 30 seconds.

'Time to Start First Game' allows early setup of the system ensuring the first game starts at a particular time.  This is reliant on the Local Computer Time being correct.  The format is HH:mm (no leading zero and 24 hour format) there is a validation to ensure the time is correctly entered.
'First Game Starts In:' is another way to set when the first game starts, but this time in 'minutes from now'.  Entering a value in here will wipe the time from 'Time to Start First Game'.
'Team time-outs allowed?' is a check box that when selected, enables the Team Time-Out buttons in the Scoreboard tab and also makes the 'Team Timeout Period' value box able to accept a value.
'Team Time-Out Period' is the value in minutes allowed for the 'Team Time-out'
'Half Period:' The time in minutes of the first and second halves.
'Half Time Break:' The time in minutes of the half time break.
'Overtime allowed?' is a check box that when selected, enables the program to enter Overtime if the scores are tied at the end of normal play.  It also enables/disables the 'Overtime Game Break:', 'Overtime Half Period:'
'Overtime Game Break:' The time in minutes of the break between the end of the second half and the start of Overtime.
'Overtime Half Period:' The time in minutes of the Overtime halves.
'Overtime Half Time Break:' The time in minutes of the Overtime half time break.
'Sudden Death Game Break:' has both a checkbox that when selected, enables the program to enter Sudden Death if the scores are tied at the end of Overtime play, and a value box where the time in minutes of the break between the end of the Overtime and the start of Sudden Death.
'Between Game Break:'  The time in minutes of the break between the end of the game and the start of the next game.
'Record Scorers Cap Number' enables a popup dialogue box where the cap number of the player scoring the goal can be entered.  There is also the option of 'Unknown' and 'Penalty Goal'.  The cap number data are stored in the CSV file selected in the 'Tournament List' widget (section). More on that later.
'Crib Time:' has both a checkbox that when selected, enables the program to shorten the 'Between Game Break' by this value until the Court Time is aligned with the Local Computer Time, and a value box, in seconds, of the magnitude to crib (or claw back).  This value cannot make the 'Between Game Break' less than 31 seconds (more on that later).
'Reset Timer' transfers the value to the program and starts the timer again with the new values.

**Presets Widget**
Here six buttons are located where commonly used settings can be stored.  Holding down the button for >4 seconds allows the name of the button to be altered and all the settings changed.  Click the save button and these settings will be saved in the JSON file (stored in the same location as the app itself).  A single click on these presets will transfer these settings to the corresponding settings in the 'Game Variables' tab.

**Tournament List**
A sample CSV file is included with the distribution of this app
This has a dropdown list where a CSV file can be selected that contains the draw for a Tournament or a list of games. The team names listed in the 'White' and 'Black' columns will appear on the Scoreboard Tab (and not on the 'Display Window' Screen.  If the team don't know who they are, they are in trouble.
Expected CSV headers: date,#,White,Score,Black,Score,Referees,Penalties,Comments. where # is the Game Number [but this can actually also be 'game', 'game#' or 'game_number'].
THIS CSV FILE GETS MODIFIED as the games progress as the app stores the scores, what Cap Numbers were penalised (into the 'Penalties' column), and if the 'Record Scorers Cap Number' checkbox is selected the Cap Numbers goals were attributed to (into the 'Comments' column).

When the 'Between Game Break' timer reached 30 seconds, the penalties and cap numbers of the goal scorers are written to the selected CSV file.

The 'Starting Game #' will show a list of Game Numbers in the CSV file selected above. This could be useful if the app crashes and the games need to be restarted, or if multiple days games are in the CSV file.


**Game Sequence**
This is a description of how the app progresses through the various stages of the game parts.


**'Sounds Tab'**
'Save Settings' is a button that stores the user selected sound files to the JSON file (stored in the same location as the app itself).
'Pips' is a dropdown box where a sound file can be selected. Any .MP3 or .WAV file can be placed in the same location as the app itself and these will appear in the 'Pips' dropdown box.
'Siren' is a dropdown box where a sound file can be selected. Any .MP3 or .WAV file can be placed in the same location as the app itself and these will also appear in the 'Siren' dropdown box.
The volume controls are only effective in Linux systems.  Microsoft Windows apparently does not allow Python apps to control volume. The two controls Air and Water anr volume controls for the two channels.
'Pips' play at pre-determined periods
'Siren' play at pre-determined periods and also when the Chief Referee activate the button to stop or start play.
'Number of seconds to play Siren' is a value box to alter how long the Siren sounds at the pre-determined periods.  If the sound file is shorter than the value, it will automatically loop until the selected minimum is reached.

## Sound Timing Table

The system automatically plays audio cues during different periods:

| Period Type | Period Name | 30s Remaining | 10s-1s Remaining | 0s (End) |
|-------------|-------------|---------------|------------------|----------|
| **Break Periods** | First Game Starts In: | 1 Pip (at 30s) | 1 Pip per second (at 10s-1s) | Siren (at 0s) |
| | Between Game Break | 1 Pip (at 30s) | 1 Pip per second (at 10s-1s) | Siren (at 0s) |
| | Half Time | 1 Pip (at 30s) | 1 Pip per second (at (at 10s-1s) | Siren (at 0s) |
| | Overtime Game Break | 1 Pip (at 31s) | 1 Pip per second (at 10s-1s) | Siren (at 0s) |
| | Overtime Half Time | 1 Pip (at 31s) | 1 Pip per second (at 10s-1s) | Siren (at 0s) |
| | Sudden Death Game Break | 1 Pip (at 31s) | 1 Pip per second (at 10s-1s) | Siren (at 0s) |
| **Game Periods** | First Half | - | - | Siren (at 0s) |
| | Second Half | - | - | Siren (at 0s) |
| | Overtime First Half | - | - | Siren (at 0s) |
| | Overtime Second Half | - | - | Siren (at 0s) |
| | Sudden Death | - | - | - |

**Notes:**
- Pip sounds use the "Pips" sound file and volume settings from the Sounds tab
- Siren sounds use the "Siren" sound file and volume settings from the Sounds tab
- **Siren Minimum Duration**: All siren sounds play for a minimum period to ensure audibility for officials and players. If the sound file is shorter than the specified period, it will automatically loop until the minimum is reached.
- Audio channels (Air/Water) use their respective volume settings
- Game periods (halves) only play siren at the end, no countdown pips
- Sudden Death periods have no automatic audio cues

Scoreboard Tab
In this tab, which can be maximised to fit the screen, is the Court Time.  This is synchronised to the 'Local Computer Time' when the app first opens.  If the 'Crib Time' is selected, the Court Time will try and move back to the 'Local Computer Time' by shortening the 'Between Game Break'.
The next row is where the Game Sequence is announced.  Breaks are Red, Play is 'Light Coral'
Under that is the Game Number, picked up from the CSV file.
Then are the Team names, picked up from the CSV file.
The Scores, which will get written to the CSV file when the 'Between Game Break' timer reaches 30 seconds, are displayed next.
If the 'Team time-outs allowed?' check box is selected, the Team Time-Out buttons are selectable.  Only one team time-out per half, no team time-outs are permitted in Overtime or Sudden Death.
'Add Goal White' adds a goal to white and if the 'Record Scorers Cap Number' check box is ticked, a popup dialogue box where the cap number of the player scoring the goal can be entered.
'Referee Time-Out' stops Court Time and the timer of whatever period the timer is displaying.  This is a toggle button.
'Penalties' is enabled during play but greyed out for breaks (as you cannot award a Penalty when play cannot be stopped [section 17.1.1 of CMAS rules]) but if the 'Referee Time-Out' button is pushed, the 'Penalties' button is enabled.  When the 'Penalties' button is pushed, a popup dialogue box appears that enables the selection of cap colour, Cap number and penalty time period.  'YOU MUST SELECT START PENALTY' to record the penalty. These penalties are written to the CSV file when the 'Between Game Break' timer reaches 30 seconds.  The penalties are also displayed on both screens along with the time remaining to serve.  When this time reaches zero, the penalty is removed from the list.  Penalties can be removed in case the wrong details were entered.


**Some Other Features:**

Coping with Errors (like when a goal is scored right on the buzzer!)
Summary of what happens when goals are added during the three "break" periods:

## What Happens When Goals Are Added During Breaks

This table explains the results and progression rules when a goal is added during a break period:

| Break Period              | Scores After Goal is Added | What Happens                                                                                                                                      |
|---------------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Between Game Break**    | Even                      | Progress to Overtime Game Break (if Overtime allowed) OR Sudden Death Game Break (if Sudden Death allowed and Overtime not allowed).              |
|                           | Uneven                    | Remain in Between Game Break. No progression; continue as normal.                                                                                |
| **Overtime Game Break**   | Even                      | Remain in Overtime Game Break. Proceed to overtime periods according to schedule.                                                                |
|                           | Uneven                    | Skip Overtime! Progress directly to Between Game Break.                                                                                          |
| **Sudden Death Game Break** | Even                    | Remain in Sudden Death Game Break. Proceed to Sudden Death period as scheduled.                                                                  |
|                           | Uneven                    | Progress directly to Between Game Break. (Skips Sudden Death period.)                                                                            |

This logic ensures the correct flow for tournament progression based on goals scored during break periods.


## New Features  (that don't work yet!!!)

### Zigbee2MQTT Wireless Siren Control

The system includes comprehensive Zigbee integration for wireless siren control with **full Windows support**:

#### Platform Support
- **Linux (Raspberry Pi)**: Full MQTT support via Zigbee2MQTT (recommended production setup)
- **Windows**: Direct serial communication with Zigbee dongle OR MQTT support

#### Key Features
- **Wireless Chief Referee Controls**: Use Zigbee buttons to trigger sirens remotely
- **Dual Connection Methods**:
  - **MQTT Integration**: Full Zigbee2MQTT compatibility with automatic reconnection (Linux/Windows)
  - **Serial Communication**: Direct USB dongle communication on Windows (no MQTT required)
- **Auto-Detection**: Automatically detects Zigbee dongles (CC2531, CP210x, Silicon Labs, etc.) on Windows
- **Configuration UI**: Dedicated "Zigbee Siren" tab for easy setup and monitoring  
- **Seamless Integration**: Uses existing sound files, volume controls, and audio channels
- **Robust Error Handling**: Graceful fallback when wireless is unavailable with automatic reconnection
- **Real-time Logging**: Activity monitoring and troubleshooting tools
- **Fallback Logic**: Automatically switches between MQTT and Serial based on availability

#### Windows Serial Mode (Simplified Setup)
Windows users can use the **simplified serial mode** without installing Zigbee2MQTT or MQTT broker:
1. Plug in Zigbee USB dongle (auto-detected)
2. Install `pyserial`: `pip install pyserial`
3. Start application - automatically connects via serial
4. Press Zigbee button to trigger siren

**Supported Zigbee Dongles**: CC2531, CC2652, CC2538, CP210x, Silicon Labs, FTDI, CH340/CH341

**Zigbee Button Behavior**: Physical Zigbee button presses trigger a single siren playback for the duration configured in the Sounds tab ("Number of seconds to play Siren"). This duration setting affects both app-initiated sirens and Zigbee button triggers.

See `ZIGBEE_SETUP.md` for complete installation and configuration instructions.



## Installation and Running

### Running from Python Source

#### Prerequisites
- Python 3.12 or higher
- tkinter (usually comes with Python, or install via `sudo apt-get install python3-tk` on Linux)

#### Installing Dependencies
```bash
pip install -r requirements.txt
```

The requirements.txt includes:
- `paho-mqtt` - MQTT client for Zigbee2MQTT wireless siren integration
- `playsound` - Cross-platform audio playback (Windows)
- `pyserial` - Serial communication for Zigbee dongles

Note: These dependencies are optional. The application will run without them, but some features (wireless siren control, Windows audio) may be limited.

#### Running the Application
```bash
python3 uwh.py
```

### Building Standalone Executables

The application can be packaged as a standalone executable using PyInstaller. This creates a single file that can be run without installing Python or any dependencies.

#### Windows Build

1. Install PyInstaller (if not already installed):
   ```cmd
   pip install pyinstaller
   ```

2. Run the build script:
   ```cmd
   build_exe.bat
   ```

3. The executable will be created in the `dist` folder as `uwh.exe`

4. To run the executable:
   ```cmd
   dist\uwh.exe
   ```

#### Linux Build

1. Install PyInstaller (if not already installed):
   ```bash
   pip3 install pyinstaller
   ```

2. Make the build script executable (one-time setup):
   ```bash
   chmod +x build_exe.sh
   ```

3. Run the build script:
   ```bash
   ./build_exe.sh
   ```

4. The executable will be created in the `dist` folder as `uwh`

5. To run the executable:
   ```bash
   ./dist/uwh
   ```

#### Build Process Details

The build scripts use PyInstaller with the following configuration:
- **--onefile**: Packages everything into a single executable file
- **--windowed**: Runs without a console window (GUI mode)
- **--add-data**: Includes all necessary data files:
  - Sound files: `beep-cut.mp3`, `car-honk-cut.mp3`, `charging-machine-cut.mp3`, `countdown-beep-cut.mp3`, `notification-beep-cut.mp3`, `police-siren-cut.mp3`, `short-beep-tone-cut.mp3`
  - Configuration: `settings.json`
  - Tournament data: `tournament Draw.csv`
  
The included Python modules are:
- `uwh.py` - Main application
- `sound.py` - Audio playback module
- `zigbee_siren.py` - Wireless siren control module

#### Advanced Configuration

For custom build configurations, you can modify the `uwh.spec` file. This PyInstaller spec file allows you to:
- Add or remove data files
- Configure hidden imports
- Change executable name or icon
- Adjust build options

To build using the spec file directly:
```bash
pyinstaller --clean uwh.spec
```

#### Distribution

When distributing the executable to other users:
1. Share the entire `dist` folder contents (the executable may extract temporary files at runtime)
2. Or, copy just the executable file - it's standalone and contains all dependencies
3. Users do NOT need Python installed to run the executable
4. On first run, the application will create default `settings.json` if not present

#### Troubleshooting Builds

- **Build fails**: Ensure all data files exist in the repository root
- **Missing modules**: Add them to `hiddenimports` in `uwh.spec`
- **Large file size**: This is normal - the executable includes Python runtime and all dependencies
- **Antivirus warnings**: Some antivirus software may flag PyInstaller executables; this is a false positive

