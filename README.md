A project to use modern computers, languages and hardware to make a scoring system for Underwater Hockey.

Open software is desirable, as is a redesigned user interface (from the system currently used in New Zealand) that is accessible, logical and easily understood by novices and is not reliant on secret buttons. 

A modern version of hardware taking advantage of newer technology is desired.

The people helping with UWH are always churning over so a User Manual, possibly online or embedded in the software is essential. 

The inital idea is to use a Raspberry Pi5 computer, tiny amplifier (Raspberry DigiAMP+), Bluetooth or Wi-Fi remote control to minimise connections.  Hardware button backup for wireless remote control.  Using a Compute Module CM5 on a custom board with built in amplifier is probably beyond where we think we want to go.  The reason for gravitating to a Raspberry Pi is the HATs that are available, such as a dual channel amplifier, will drastically reduces wires and connections (hopefully leading to a more robust system that what we currently have). It may be that a RPi5 is not grunty enough, but we will see.

The goal is to make a solution for UWH scoring that anyone can use, based on easy to obtain hardware, hence the desire to use a Raspberry Pi 5.  Aiming to use a DigiAMP+ HAT, NVMe Base for Raspberry Pi 5 for robustness of data storage, Wi-Fi buttons or Zigbee communications between Zigbee USB dongle and Zigbee buttons for Chief Ref ability to signal, TOA SC610 8 Ohm 10W IP65 Horn Speaker for above water siren and a Lubell Labs Underwater loudspeaker (why? Because that is what we already use) LL916 is the modern version of the ones NZUWH already uses.  Can also be run on Windows.

## Sound Timing Table

The system automatically plays audio cues during different periods:

| Period Type | Period Name | 30s Remaining | 10s-1s Remaining | 0s (End) |
|-------------|-------------|---------------|------------------|----------|
| **Break Periods** | First Game Starts In | 1 Pip | 1 Pip per second | Siren |
| | Between Game Break | 1 Pip | 1 Pip per second | Siren |
| | Half Time | 1 Pip | 1 Pip per second | Siren |
| | Overtime Game Break | 1 Pip | 1 Pip per second | Siren |
| | Overtime Half Time | 1 Pip | 1 Pip per second | Siren |
| | Sudden Death Game Break | 1 Pip | 1 Pip per second | Siren |
| **Game Periods** | First Half | - | - | Siren |
| | Second Half | - | - | Siren |
| | Overtime First Half | - | - | Siren |
| | Overtime Second Half | - | - | Siren |
| | Sudden Death | - | - | - |

**Notes:**
- Pip sounds use the "Pips" sound file and volume settings from the Sounds tab
- Siren sounds use the "Siren" sound file and volume settings from the Sounds tab
- Audio channels (Air/Water) use their respective volume settings
- Game periods (halves) only play siren at the end, no countdown pips
- Sudden Death periods have no automatic audio cues

## New Features

### Zigbee2MQTT Wireless Siren Control
The system now includes full Zigbee2MQTT integration for wireless siren control:
- **Wireless Chief Referee Controls**: Use Zigbee buttons to trigger sirens remotely
- **MQTT Integration**: Full Zigbee2MQTT compatibility with automatic reconnection
- **Configuration UI**: Dedicated "Zigbee Siren" tab for easy setup and monitoring  
- **Seamless Integration**: Uses existing sound files, volume controls, and audio channels
- **Robust Error Handling**: Graceful fallback when wireless is unavailable
- **Real-time Logging**: Activity monitoring and troubleshooting tools

See `ZIGBEE_SETUP.md` for complete installation and configuration instructions.

Some Features


Coping with Errors (like when a goal is scored right on the buzzer!)
Summary of what happens when goals are added during the three "break" periods:

In Between Game Break
Scores After Goal	is added: What Happens
Even	Progress to Overtime Game Break (if Overtime allowed)<br>OR Sudden Death Game Break (if Sudden Death allowed and Overtime not allowed)
Uneven	Remain in Between Game Break. No progression; continue as normal.

In Overtime Game Break
Scores After Goal	is added: What Happens
Even	Remain in Overtime Game Break. Proceed to overtime periods according to schedule.
Uneven	Skip Overtime! Progress directly to Between Game Break.

Sudden Death Game Break
Scores After Goal	is added: What Happens
Even	Remain in Sudden Death Game Break. Proceed to Sudden Death period as scheduled.
Uneven	Progress directly to Between Game Break. (Skips Sudden Death period.)

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

