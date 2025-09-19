# GitHub Copilot Quick Reference - UWH Scoring App

## 🚀 Quick Start Prompts

### Understanding the Codebase
```
Analyze the UWH GameManagementApp in uwh.py. Show me the main UI components, game logic flow, and data structures used for scoring and timing.
```

### Adding Features
```
Add a [feature name] to the UWH scoring app that [description]. Follow the existing patterns for UI layout, confirmation dialogs, and settings integration.
```

### Debugging Issues
```
Debug this UWH app issue: [describe problem]. Check the timer system, UI event handlers, and game state management.
```

## 🎯 Context Keywords

Use these terms in your prompts for better Copilot understanding:

**App-Specific Terms:**
- `GameManagementApp` - Main application class
- `uwh.py` - Primary source file
- Scoreboard tab, Game Variables tab
- White team, Black team scoring
- Game phases: First Half, Half Time, Overtime, Sudden Death
- Court Time, Timer, Referee timeout

**Technical Terms:**
- Tkinter notebook tabs, grid layout
- Font scaling system, responsive design
- Variable configuration dictionary
- Confirmation dialogs, messagebox
- Timer jobs, after() callbacks

## 🛠️ Common Tasks

### Add New Button
```python
# Prompt: "Add a [button name] button to the UWH scoreboard"
self.new_button = tk.Button(
    tab, text="Button Text", font=self.fonts["button"],
    bg="light grey", fg="black",
    command=self.button_action
)
self.new_button.grid(row=X, column=Y, padx=1, pady=1, sticky="nsew")
```

### Add Game Setting
```python
# Prompt: "Add a configurable [setting name] to UWH game variables"
"setting_name": {"default": value, "checkbox": False, "unit": "minutes"},
```

### Add Confirmation Dialog
```python
# Prompt: "Add confirmation dialog for [action] in UWH app"
result = messagebox.askyesno("Action Title", "Confirmation message?")
if result:
    # Perform action
```

## 🔧 Modification Patterns

### UI Layout (Grid System)
- Row 0: Court time (spans 6 columns)
- Row 1: Game phase display (spans 6 columns)  
- Row 2: Team labels (White: 0-1, Game info: 2-3, Black: 4-5)
- Rows 3-8: Scores and timer display
- Rows 9-10: Action buttons

### Font System
All UI elements use `self.fonts["type"]` references that auto-scale with window size.

### Color Scheme
- White team: `bg="white", fg="black"`
- Black team: `bg="black", fg="white"`
- Neutral: `bg="light grey", fg="black"`
- Active states: `bg="red"` for alerts

## 📋 Testing Checklist

When making changes, verify:
- [ ] Window resizing works (font scaling)
- [ ] Both team scoring functions
- [ ] Timer progression through game phases
- [ ] Settings tab configuration
- [ ] Confirmation dialogs appear
- [ ] No Python errors in console

## 🚨 Safety Patterns

Always use confirmation dialogs for:
- Score modifications (especially subtractions)
- Game state changes (reset, phase jumps)
- Settings that affect active games

Always validate:
- Time inputs (positive numbers, reasonable ranges)
- Score inputs (non-negative integers)
- Settings dependencies (overtime requires settings)

## 💡 Pro Tips

1. **Context Loading**: Start prompts with "In the UWH scoring app..." for better context
2. **Method Naming**: Use descriptive snake_case following existing patterns
3. **UI Consistency**: Reference existing UI elements for styling patterns
4. **Error Handling**: Wrap user actions in try-catch with messagebox feedback
5. **Font Usage**: Always use `self.fonts[type]` for scalable UI

---
*Keep this reference open alongside the full instructions document for efficient development*