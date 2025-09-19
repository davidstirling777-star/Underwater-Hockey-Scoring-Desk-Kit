# GitHub Copilot Instructions for Underwater Hockey Scoring Desk Kit (UWH)

## Application Overview

The Underwater Hockey Game Management App is a Python Tkinter-based scoring system designed for underwater hockey tournaments. This application provides real-time scorekeeping, game timing, and tournament management functionality.

### Key Components
- **Main Class**: `GameManagementApp` - The primary application controller
- **UI Framework**: Tkinter with ttk components
- **Architecture**: Single-file application with modular methods
- **File**: `uwh.py` (723 lines of Python code)

### Core Features
- Dual-team scoreboard with configurable game phases
- Real-time timer with multiple period types (regular, overtime, sudden death)
- Team timeout management with visual indicators
- Configurable game variables through settings interface
- Goal addition/subtraction with confirmation dialogs
- Referee timeout functionality
- Dynamic font scaling based on window size

## Application-Specific Context and Terminology

### Underwater Hockey Terms
- **Court Time**: Real-world clock time displayed during games
- **Half Period**: Standard game period (typically 15 minutes)
- **Overtime**: Extended play periods when games are tied
- **Sudden Death**: Unlimited time period where first goal wins
- **Crib Time**: Player substitution timeout period
- **Chief Ref**: Head referee with special controls
- **Time-Out**: Team or referee-called pause in play

### Technical Architecture
```python
# Main application structure
class GameManagementApp:
    def __init__(self, master):
        # Initialize UI components, variables, fonts
    
    # Core UI creation methods
    def create_scoreboard_tab(self)     # Main game display
    def create_settings_tab(self)       # Game configuration
    
    # Game logic methods
    def build_game_sequence(self)       # Configure game phases
    def start_current_period(self)      # Period management
    def update_timer_display(self)      # Timer updates
    
    # Scoring methods
    def add_goal_with_confirmation(self, score_var, team_name)
    def adjust_score_with_confirm(self, score_var, team_name)
```

### Key Variables and Data Structures
```python
# Game configuration dictionary
self.variables = {
    "team_timeouts_allowed": {"default": True, "checkbox": True},
    "half_period": {"default": 1, "checkbox": False, "unit": "minutes"},
    "overtime_allowed": {"default": True, "checkbox": True},
    # ... more game settings
}

# Font system for responsive UI
self.fonts = {
    "court_time": font.Font(family="Arial", size=36),
    "score": font.Font(family="Arial", size=200, weight="bold"),
    "timer": font.Font(family="Arial", size=90, weight="bold"),
    # ... more font definitions
}
```

## Development Workflow Prompts

### Starting Development Session
```
# Copilot Prompt
I'm working on the Underwater Hockey Scoring Desk Kit application. This is a Python Tkinter app for tournament scoring. The main class is GameManagementApp in uwh.py. Please help me understand the current codebase structure and suggest improvements for [specific functionality].

Key context:
- Single-file Tkinter application (uwh.py)
- Dual-team scoring with configurable game periods
- Real-time timer with multiple game phases
- Settings tab for runtime configuration
```

### Code Analysis and Understanding
```
# Copilot Prompt
Analyze the GameManagementApp class structure in uwh.py and explain:
1. How the game sequence/phases are managed
2. The timer system architecture (regular vs sudden death)
3. The relationship between UI components and game state
4. How font scaling works for responsive design

Focus on the methods: build_game_sequence(), start_current_period(), and update_timer_display().
```

### Adding New Features
```
# Copilot Prompt
Help me add a new feature to the UWH scoring app:
[Feature description]

Context:
- Application uses Tkinter with notebook tabs (Scoreboard, Game Variables)
- Settings are stored in self.variables dictionary with default values and units
- UI uses grid layout with responsive font scaling
- All user actions should have confirmation dialogs for safety
- Follow existing naming patterns: snake_case for methods, descriptive button text

Please provide:
1. Method implementation
2. UI integration code
3. Settings integration if needed
4. Confirmation dialog if user-facing action
```

## Code Generation Examples

### Adding New Game Setting
```python
# Copilot Prompt: Add a new configurable game setting for "warm_up_period"

# Add to self.variables in __init__:
"warm_up_period": {"default": 5, "checkbox": False, "unit": "minutes"},

# The settings tab will automatically display this new variable
# Access the value using: self.get_minutes('warm_up_period')
```

### Creating New UI Button
```python
# Copilot Prompt: Create a new button for "Reset Scores Only"

def reset_scores_only(self):
    """Reset team scores without affecting timer or game state"""
    result = messagebox.askyesno(
        "Reset Scores",
        "Are you sure you want to reset both team scores to zero?"
    )
    if result:
        self.white_score_var.set(0)
        self.black_score_var.set(0)

# Add button to scoreboard tab in create_scoreboard_tab():
self.reset_scores_button = tk.Button(
    tab, text="Reset Scores", font=self.fonts["button"],
    bg="light grey", fg="black",
    command=self.reset_scores_only
)
self.reset_scores_button.grid(row=11, column=2, columnspan=2, padx=1, pady=1, sticky="nsew")
```

### Adding Confirmation Dialog Pattern
```python
# Copilot Prompt: Create a confirmation dialog for critical actions

def action_with_confirmation(self, action_name, confirmation_message, action_callback):
    """Generic confirmation dialog pattern used throughout the app"""
    result = messagebox.askyesno(action_name, confirmation_message)
    if result:
        action_callback()

# Usage example:
self.action_with_confirmation(
    "End Game Early",
    "Are you sure you want to end the current game?",
    lambda: self.goto_between_game_break()
)
```

### Extending Timer Functionality
```python
# Copilot Prompt: Add a new timer state for "Pre-Game Warm-up"

def start_warmup_period(self):
    """Start the pre-game warm-up timer"""
    warmup_seconds = self.get_minutes('warm_up_period')
    self.timer_seconds = warmup_seconds
    self.half_label.config(text="Warm-up Period")
    self.update_half_label_background("Warm-up Period")
    self.timer_running = True
    self.update_timer_display()
    self.start_timer()

# Add to build_game_sequence() at the beginning:
seq.insert(0, {'name': 'Warm-up Period', 'type': 'warmup', 'duration': self.get_minutes('warm_up_period')})
```

## UI Modification and Layout Patterns

### Grid Layout System
```python
# Copilot Prompt: Understanding the grid layout in UWH scoreboard

# Scoreboard tab uses 11 rows x 6 columns grid:
# Row 0: Court time display (spans all columns)
# Row 1: Game phase/half display (spans all columns) 
# Row 2: Team labels (White: cols 0-1, Black: cols 4-5, Game info: cols 2-3)
# Rows 3-8: Scores (White: cols 0-1, Timer: cols 2-3, Black: cols 4-5)
# Rows 9-10: Action buttons and team timeouts

# When adding new UI elements, follow this pattern:
for i in range(11):  # Configure rows
    tab.grid_rowconfigure(i, weight=1)
for i in range(6):   # Configure columns
    tab.grid_columnconfigure(i, weight=1)
```

### Font Scaling System
```python
# Copilot Prompt: Add a new scalable font type

# Add to fonts dict in __init__:
"new_element": font.Font(family="Arial", size=24, weight="bold"),

# Add to base_sizes in scale_fonts():
"new_element": 24,

# Font will automatically scale with window resize
```

### Color Scheme and Theming
```python
# Copilot Prompt: Understanding UWH app color scheme

# Team colors:
# White team: bg="white", fg="black"
# Black team: bg="black", fg="white"
# Neutral elements: bg="light grey", fg="black"
# Timer/display: bg="lightgrey", fg="black"
# Phase backgrounds: bg="lightblue" (regular), bg="lightcoral" (breaks)

# Referee timeout states:
self.referee_timeout_default_bg = "light grey"
self.referee_timeout_active_bg = "red"
```

## Debugging and Troubleshooting

### Common Issues and Solutions
```python
# Copilot Prompt: Debug timer synchronization issues in UWH app

# Timer not updating:
# 1. Check if self.timer_running is True
# 2. Verify timer_job is not None
# 3. Check if after() callback is properly scheduled

def debug_timer_state(self):
    """Debug helper to check timer state"""
    print(f"Timer running: {self.timer_running}")
    print(f"Timer job: {self.timer_job}")
    print(f"Current seconds: {self.timer_seconds}")
    print(f"Current period: {self.full_sequence[self.current_index]['name'] if self.full_sequence else 'None'}")
```

### UI Responsiveness Issues
```python
# Copilot Prompt: Fix font scaling problems

# Font not scaling properly:
# 1. Check if scale_fonts() is bound to <Configure> event
# 2. Verify base_sizes dictionary includes all font keys
# 3. Ensure new UI elements use self.fonts references

# Force font refresh:
def refresh_fonts(self):
    """Force refresh of all font scaling"""
    self.scale_fonts(None)
    self.master.update_idletasks()
```

### Data Validation Issues
```python
# Copilot Prompt: Add input validation for game settings

def validate_time_input(self, value, setting_name):
    """Validate time-based setting inputs"""
    try:
        minutes = int(float(value))
        if minutes < 0:
            raise ValueError("Time cannot be negative")
        if minutes > 60 and setting_name.endswith('_period'):
            raise ValueError("Game periods should be reasonable (≤60 minutes)")
        return minutes
    except (ValueError, TypeError) as e:
        messagebox.showerror("Invalid Input", f"Invalid time value for {setting_name}: {str(e)}")
        return None
```

## Feature Extension Patterns

### Adding New Game Phases
```python
# Copilot Prompt: Add a "Penalty Shootout" phase to the game sequence

def add_penalty_shootout_phase(self):
    """Add penalty shootout to game sequence after sudden death"""
    # Add to variables dict:
    "penalty_shootout_enabled": {"default": False, "checkbox": True, "label": "Penalty Shootout enabled?"},
    
    # Add to build_game_sequence():
    if self.is_penalty_shootout_enabled():
        seq.append({'name': 'Penalty Shootout', 'type': 'penalty', 'duration': None})

def is_penalty_shootout_enabled(self):
    """Check if penalty shootout is enabled"""
    return self.variables.get("penalty_shootout_enabled", {}).get("value", False)
```

### Extending Team Management
```python
# Copilot Prompt: Add team name customization

def setup_team_names(self):
    """Allow customization of team names beyond White/Black"""
    # Add to __init__:
    self.team_names = {"white": "White", "black": "Black"}
    
def update_team_display(self, team_color, new_name):
    """Update team name display"""
    if team_color == "white":
        self.white_label.config(text=new_name)
        self.team_names["white"] = new_name
    elif team_color == "black":
        self.black_label.config(text=new_name)
        self.team_names["black"] = new_name
```

### Adding Data Export/Import
```python
# Copilot Prompt: Add game data export functionality

import json
from tkinter import filedialog

def export_game_data(self):
    """Export current game state to JSON file"""
    game_data = {
        "white_score": self.white_score_var.get(),
        "black_score": self.black_score_var.get(),
        "current_period": self.full_sequence[self.current_index]["name"] if self.full_sequence else "",
        "timer_seconds": self.timer_seconds,
        "settings": {name: var.get("value", var["default"]) for name, var in self.variables.items()}
    }
    
    filename = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    
    if filename:
        with open(filename, 'w') as f:
            json.dump(game_data, f, indent=2)
        messagebox.showinfo("Export Complete", f"Game data exported to {filename}")
```

## Testing and Validation

### Manual Testing Checklist
```
# Copilot Prompt: Create a testing checklist for UWH app changes

## UI Testing:
- [ ] Window resizes properly and fonts scale correctly
- [ ] All buttons are clickable and responsive
- [ ] Tab navigation works between Scoreboard and Game Variables
- [ ] Colors and themes display correctly for both teams

## Timer Testing:
- [ ] Timer counts down properly in each game phase
- [ ] Sudden death timer counts up correctly
- [ ] Referee timeout functions independently
- [ ] Court time displays real-world time accurately

## Scoring Testing:
- [ ] Goal addition works for both teams
- [ ] Goal subtraction shows confirmation dialog
- [ ] Scores persist across timer periods
- [ ] Reset functionality works correctly

## Settings Testing:
- [ ] All game variables can be modified
- [ ] Checkbox settings enable/disable related options
- [ ] Invalid inputs are handled gracefully
- [ ] Settings changes affect game behavior immediately
```

### Automated Testing Approach
```python
# Copilot Prompt: Create unit tests for UWH app core functions

import unittest
from unittest.mock import Mock, patch

class TestGameManagementApp(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.root = Mock()
        self.app = GameManagementApp(self.root)
    
    def test_get_minutes_conversion(self):
        """Test minutes to seconds conversion"""
        self.app.variables["test_var"] = {"default": 5}
        result = self.app.get_minutes("test_var")
        self.assertEqual(result, 300)  # 5 minutes = 300 seconds
    
    def test_score_validation(self):
        """Test score addition and subtraction"""
        initial_score = self.app.white_score_var.get()
        # Test goal addition logic
        # Test goal subtraction confirmation
        pass

if __name__ == "__main__":
    unittest.main()
```

## Repository-Specific Best Practices

### Code Style Guidelines
```python
# Copilot Prompt: Follow UWH app coding conventions

# Method naming: snake_case with descriptive names
def create_new_game_feature(self):          # ✓ Good
def createFeature(self):                    # ✗ Inconsistent

# UI element naming: descriptive with component type suffix
self.white_goal_button = tk.Button(...)     # ✓ Good
self.btn1 = tk.Button(...)                  # ✗ Not descriptive

# Comment style: Docstrings for methods, inline for complex logic
def complex_calculation(self):
    """Calculate game phase timing based on settings"""
    # Convert minutes to seconds for internal timer
    return self.get_minutes(variable_name) * multiplier

# Font references: Always use self.fonts dictionary
font=self.fonts["button"]                   # ✓ Good
font=("Arial", 20, "bold")                  # ✗ Hard-coded, won't scale
```

### Error Handling Patterns
```python
# Copilot Prompt: Implement robust error handling for UWH app

def safe_setting_update(self, setting_name, new_value):
    """Safely update a game setting with validation"""
    try:
        # Validate input
        if not self.validate_setting_value(setting_name, new_value):
            return False
        
        # Update setting
        self.variables[setting_name]["value"] = new_value
        
        # Refresh dependent UI elements
        self.refresh_dependent_settings(setting_name)
        
        return True
        
    except Exception as e:
        messagebox.showerror(
            "Setting Update Error",
            f"Failed to update {setting_name}: {str(e)}"
        )
        return False
```

### Performance Considerations
```python
# Copilot Prompt: Optimize UWH app performance

# Timer efficiency: Use single timer job, not multiple
def efficient_timer_update(self):
    """Centralized timer update to avoid multiple after() calls"""
    if not self.timer_running:
        return
    
    # Update all time-based displays in one method
    self.update_game_timer()
    self.update_court_time()
    self.update_timeout_timers()
    
    # Schedule next update
    self.timer_job = self.master.after(1000, self.efficient_timer_update)

# Font scaling: Debounce resize events
def debounced_font_scaling(self, event):
    """Prevent excessive font scaling during window resize"""
    if hasattr(self, '_resize_timer'):
        self.master.after_cancel(self._resize_timer)
    
    self._resize_timer = self.master.after(100, lambda: self.scale_fonts(event))
```

## Integration and Deployment

### Hardware Integration Prompts
```
# Copilot Prompt: Integrate UWH app with Raspberry Pi hardware

The UWH app is designed to run on Raspberry Pi 5 with specific hardware:
- DigiAMP+ HAT for audio amplification
- Zigbee USB dongle for wireless controls
- NVMe storage for data persistence
- Multiple display outputs for scoreboard and control interface

Help me add hardware integration code for:
1. Audio output control for game signals
2. Zigbee communication for referee controls
3. Multi-display support for scoreboard projection
4. Data persistence and backup systems
```

### Packaging and Distribution
```python
# Copilot Prompt: Create deployment package for UWH app

# Create requirements.txt:
# tkinter (usually included with Python)
# No external dependencies currently

# Create startup script (uwh_launcher.py):
#!/usr/bin/env python3
import sys
import os
import tkinter as tk
from uwh import GameManagementApp

def main():
    """Launch UWH application with error handling"""
    try:
        root = tk.Tk()
        app = GameManagementApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Support and Documentation

### User Manual Integration
```
# Copilot Prompt: Add embedded help system to UWH app

Create a help system that explains:
1. Basic scoring operations (add goal, subtract goal)
2. Timer management (start, pause, reset)
3. Game phase progression (regular time, overtime, sudden death)
4. Settings configuration (game variables, timeouts)
5. Troubleshooting common issues

The help should be accessible from the main interface and context-sensitive.
```

### Maintenance and Updates
```python
# Copilot Prompt: Add version control and update checking

VERSION = "2.1.0"
BUILD_DATE = "2025-01-27"

def check_for_updates(self):
    """Check for application updates (placeholder for future implementation)"""
    about_text = f"""
Underwater Hockey Scoring Desk Kit
Version: {VERSION}
Build Date: {BUILD_DATE}

Designed for New Zealand Underwater Hockey tournaments.
Open source project available on GitHub.
"""
    messagebox.showinfo("About UWH Scoring Kit", about_text)
```

## Quick Reference Commands

### Essential Copilot Prompts for UWH Development
```
# Application Analysis
"Explain the UWH GameManagementApp class structure and main components"

# Feature Development  
"Add a new [feature] to the UWH scoring app following existing patterns"

# UI Modifications
"Modify the UWH scoreboard layout to add [element] while maintaining responsive design"

# Bug Fixes
"Debug the UWH timer synchronization issue where [describe problem]"

# Settings Extension
"Add a new configurable game setting for [setting] with proper validation"

# Hardware Integration
"Integrate UWH app with [hardware component] for Raspberry Pi deployment"

# Testing
"Create test cases for UWH app [functionality] with proper error handling"

# Performance
"Optimize UWH app [component] for better performance and user experience"
```

---

*This document provides comprehensive guidance for using GitHub Copilot effectively with the Underwater Hockey Scoring Desk Kit application. Keep this reference handy during development sessions for context-aware assistance and best practices.*