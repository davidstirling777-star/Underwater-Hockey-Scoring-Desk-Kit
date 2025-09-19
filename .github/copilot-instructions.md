# Underwater Hockey Scoring Desk Kit

Underwater Hockey Game Management App is a Python tkinter desktop application for managing underwater hockey game scoring, timing, and game flow. It provides a tabbed interface with scoreboard display and game configuration settings.

**ALWAYS reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Working Effectively

### Bootstrap and Setup
- Install Python tkinter GUI library: `sudo apt-get update && sudo apt-get install -y python3-tk`
- No additional dependencies required - uses only Python standard library
- Application startup time: **0.2 seconds** (very fast)

### Running the Application
- **GUI Mode (normal use)**: `python3 uwh.py`
- **Headless Testing**: Set up virtual display first:
  ```bash
  sudo apt-get install -y xvfb
  Xvfb :99 -screen 0 1024x768x24 &
  export DISPLAY=:99
  python3 uwh.py
  ```

### Code Quality and Testing
- **Syntax validation**: `python3 -m py_compile uwh.py` - completes in **0.1 seconds**
- **Import test**: `python3 -c "import uwh; print('Module loads successfully')"` - completes in **0.1 seconds**
- **AST validation**: `python3 -c "import ast; ast.parse(open('uwh.py').read()); print('AST parsing successful')"` - completes in **0.1 seconds**

### Performance Expectations
- Module import: **0.01 seconds**
- GUI initialization: **0.2 seconds**  
- Game sequence building: **0.001 seconds**
- Settings loading: **0.001 seconds**
- **Total startup time: 0.21 seconds**

## Validation Scenarios

**ALWAYS manually validate changes using these complete end-to-end scenarios:**

### Scenario 1: Basic Application Startup
1. Run `python3 uwh.py` with virtual display
2. Verify application window opens with title "Underwater Hockey Game Management App"
3. Confirm two tabs are visible: "Scoreboard" and "Game Variables"
4. Check that timer displays and team score areas are visible
5. **Expected time: Application should start in under 0.5 seconds**

### Scenario 2: Game Configuration Testing
1. Start the application
2. Click on "Game Variables" tab
3. Verify settings table with columns: Use?, Variable, Value, Units
4. Test checkbox functionality for overtime and sudden death options
5. Modify a time value (e.g., change "Half Period" from default)
6. Click back to "Scoreboard" tab to verify changes take effect
7. **Expected time: Configuration changes should apply instantly**

### Scenario 3: Scoring and Timer Operations
1. Start the application on "Scoreboard" tab
2. Verify initial scores show "0" for both White and Black teams
3. Click "Add Goal" buttons to increment scores
4. Click "-ve Goal" buttons and verify confirmation dialogs appear
5. Test timer control buttons ("Start Timer", "Reset Timer")
6. **Expected time: All UI interactions should be immediate (< 0.1 seconds)**

### Scenario 4: Screenshot Validation (for UI changes)
```bash
# Always take screenshots when making UI changes
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
python3 uwh.py &
sleep 3
sudo apt-get install -y imagemagick
export DISPLAY=:99  # Critical: ensure DISPLAY is set for import command
import -window root screenshot.png
```

### Quick Validation Commands
- **Syntax check**: `python3 -m py_compile uwh.py` (completes in 0.04 seconds)
- **Import test**: `python3 -c "import uwh; print('Module loads successfully')"` (completes in 0.03 seconds)  
- **GUI startup test**: `timeout 2 python3 uwh.py` (exit code 124 = success, GUI started and was killed by timeout)

## Common Development Tasks

### Repository Structure
```
/home/runner/work/Underwater-Hockey-Scoring-Desk-Kit/Underwater-Hockey-Scoring-Desk-Kit/
├── uwh.py                    # Main application file (31KB, 684 lines)
├── README.md                 # Project documentation
├── LICENSE                   # MIT License
├── ui_simulation.txt         # UI mockup and feature specifications
└── __pycache__/             # Python bytecode cache (ignore)
```

### Key Application Components
- **Class**: `GameManagementApp` (not MultiTabApp)
- **Key Methods**: 
  - `build_game_sequence()` - Creates game flow with periods and breaks
  - `get_minutes(varname)` - Converts time settings to seconds
  - `create_scoreboard_tab()` - Main game display interface
  - `create_settings_tab()` - Game configuration interface
- **GUI Framework**: tkinter with ttk widgets
- **Imports Required**: `tkinter`, `tkinter.ttk`, `tkinter.messagebox`, `tkinter.font`, `datetime`

### Making Code Changes
1. **ALWAYS** test syntax before making changes: `python3 -m py_compile uwh.py`
2. **ALWAYS** test imports after changes: `python3 -c "import uwh"`
3. **ALWAYS** run visual validation with screenshot for UI changes
4. **NEVER** break the main application entry point: `if __name__ == "__main__":`

### Time-Critical Operations
- **Module loading**: 0.01 seconds
- **GUI rendering**: 0.2 seconds  
- **Settings updates**: Instant
- **NO LONG-RUNNING OPERATIONS** exist in this codebase
- **NO BUILD PROCESS** required - Python is interpreted

## Troubleshooting

### Common Issues
- **"No module named 'tkinter'"**: Run `sudo apt-get install -y python3-tk`
- **"couldn't connect to display"**: Set up Xvfb virtual display for headless environments
- **GUI doesn't appear**: Ensure DISPLAY variable is set correctly
- **Import errors**: Check Python path includes project directory

### Environment Requirements
- **Python Version**: 3.12+ (tested and working)
- **OS**: Linux (Ubuntu/Debian tested)
- **Display**: X11 or virtual display (Xvfb) for GUI
- **Memory**: Minimal (< 50MB runtime)
- **Disk**: Minimal (< 1MB application size)

### File Locations
- **Main application**: `/uwh.py` (single file application)
- **Documentation**: `/README.md`, `/ui_simulation.txt`
- **Generated files**: `/__pycache__/` (can be ignored/deleted)

### Validation Checklist for Changes
- [ ] Syntax check passes: `python3 -m py_compile uwh.py`
- [ ] Import test passes: `python3 -c "import uwh"`
- [ ] Application starts without errors
- [ ] GUI renders correctly (take screenshot if UI changed)  
- [ ] Core functionality works (scoring, timing, settings)
- [ ] No new dependencies introduced
- [ ] Changes are minimal and focused

**CRITICAL**: This is a lightweight, single-file Python application with no build process, no external dependencies, and very fast startup times. All operations complete in under 1 second. There are no long-running processes to wait for or cancel.