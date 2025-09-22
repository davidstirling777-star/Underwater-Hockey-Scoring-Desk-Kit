# Underwater Hockey Scoring Desk Kit
Underwater Hockey Scoring Desk Kit is a Python Tkinter GUI application for managing Underwater Hockey games. It provides scoreboard functionality, timing, penalties, and game management specifically designed for New Zealand Underwater Hockey operations.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Bootstrap and Dependencies
- Install Python 3.12+ and tkinter:
  - `sudo apt-get update`
  - `sudo apt-get install -y python3-tk`
- For GUI testing in headless environments:
  - `sudo apt-get install -y xvfb imagemagick`
  - `export DISPLAY=:99 && Xvfb :99 -screen 0 1024x768x24 &`

### Build and Test
- **NO BUILD PROCESS REQUIRED** - This is a pure Python application using only standard libraries
- Validate syntax: `python3 -m py_compile uwh.py` -- takes < 1 second
- Import test: `python3 -c "import uwh; print('Module loads successfully')"` -- takes < 1 second  
- AST validation: `python3 -m ast uwh.py` -- takes < 1 second
- **NEVER CANCEL**: All validation commands complete in under 3 seconds

### Run the Application
- **ALWAYS install dependencies first** using the bootstrap steps above
- GUI mode: `python3 uwh.py`
- Headless testing: `export DISPLAY=:99 && python3 uwh.py`
- Application starts immediately (< 1 second startup time)
- **NEVER CANCEL**: Application startup is instant - no extended timeouts needed

### Validation
- **MANUAL TESTING SCENARIOS**: Always test these complete user workflows after making changes:
  1. **Scoreboard Test**: Start app → Add goals to White/Black teams → Verify score display updates
  2. **Timer Test**: Start app → Go to settings → Change half period to 1 minute → Start timer → Verify countdown works
  3. **Penalties Test**: Start app → Click Penalties button → Add penalty for White team, Cap 5, 2 minutes → Verify penalty appears in stored penalties
  4. **Settings Test**: Start app → Go to Game Variables tab → Toggle overtime enabled checkbox → Verify setting persists
  5. **Referee Timeout Test**: Start app → Click "Referee Time-Out" button → Verify timer pauses and label changes
- Take screenshots when testing GUI: `export DISPLAY=:99 && import -window root /tmp/screenshot.png`
- **NO AUTOMATED TESTS EXIST** - All validation is manual through GUI interaction
- Application has two main tabs: "Scoreboard" (main game interface) and "Game Variables" (settings)

## Common Tasks

### Repository Structure
```
.
├── README.md               # Project description and hardware goals
├── LICENSE                 # MIT License
├── uwh.py                  # Main application file (1163 lines)
├── ui_simulation.txt       # Detailed UI mockup and functionality description
└── __pycache__/           # Python cache (auto-generated, ignore)
```

### Key Application Features
The main file `uwh.py` contains:
- **GameManagementApp class**: Complete game management system
- **Scoreboard**: Live score display for White vs Black teams
- **Timer System**: Countdown timers for periods, breaks, overtime, sudden death
- **Penalty Management**: Track player penalties with duration and automatic removal
- **Settings Configuration**: Runtime adjustment of all game timing variables
- **Display Window**: Separate display window for external monitors
- **Team Timeouts**: One timeout per team per half with proper tracking

### Frequently Used Commands
```bash
# Start application (most common)
python3 uwh.py

# Validate code changes
python3 -m py_compile uwh.py

# Headless testing setup
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
python3 uwh.py

# Take GUI screenshot for verification  
import -window root /tmp/app_screenshot.png
```

### Application Dependencies
- **Python 3.12+** (tested version)
- **tkinter** (GUI framework - install with python3-tk package)
- **datetime** (standard library)
- **Standard Python libraries only** - no external pip packages required

### Critical Code Areas
When making changes, always review these key components:
- **Timer logic**: Lines 800-900 in uwh.py handle all timing functionality
- **Score management**: Lines 400-500 handle goal addition/subtraction with confirmations  
- **Settings system**: Lines 600-700 manage game variable configuration
- **Penalty system**: Lines 1000-1100 track active penalties and timeouts
- **Display synchronization**: Lines 1050+ keep external display in sync with main window

## Hardware Context
This application is designed to run on **Raspberry Pi 5** with:
- DigiAMP+ HAT for audio amplification
- NVMe Base for robust data storage
- Zigbee communications for wireless controls
- TOA SC610 speaker (above water) and Lubell Labs LL916 (underwater)
- Mouse-driven interface (no keyboard required during games)

## Troubleshooting
- **"no display name" error**: Set up virtual display with Xvfb (see bootstrap section)
- **Import errors**: Ensure python3-tk is installed via apt-get
- **GUI not responding**: Application requires active display connection
- **Timer issues**: Check datetime module imports and system clock
- **Settings not saving**: Settings are stored in memory only (no persistence between sessions)

## Development Notes
- **No CI/CD configured** - manual testing required
- **No linting tools configured** - basic syntax validation only
- **Single-file application** - all logic contained in uwh.py
- **Tkinter-based** - modern cross-platform GUI framework
- **Thread-safe timers** - uses tkinter's after() method for all timing operations
- **Scalable fonts** - automatically adjusts font sizes based on window resizing