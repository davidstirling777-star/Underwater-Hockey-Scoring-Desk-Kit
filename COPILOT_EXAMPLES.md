# GitHub Copilot Examples for UWH Scoring App

## Real-World Development Scenarios

### Example 1: Adding a "Penalty Time" Feature

**Prompt:**
```
Add a penalty time tracking feature to the UWH scoring app. Teams should be able to track when players are in the penalty box. Add:
1. A new game setting for penalty duration (default 2 minutes)
2. Buttons to start/stop penalty timers for each team
3. Visual indicator when penalties are active
4. Automatic penalty expiration

Follow the existing UI patterns and confirmation dialog standards.
```

**Expected Output:**
```python
# Add to variables dictionary
"penalty_duration": {"default": 2, "checkbox": False, "unit": "minutes"},

# Add penalty tracking variables to __init__
self.white_penalty_active = False
self.black_penalty_active = False
self.white_penalty_seconds = 0
self.black_penalty_seconds = 0
self.white_penalty_job = None
self.black_penalty_job = None

# Add penalty timer methods
def start_penalty_timer(self, team_color):
    """Start penalty timer for specified team"""
    if team_color == "white":
        self.white_penalty_active = True
        self.white_penalty_seconds = self.get_minutes('penalty_duration')
        self.update_penalty_display("white")
        self.white_penalty_job = self.master.after(1000, lambda: self.countdown_penalty("white"))
    elif team_color == "black":
        self.black_penalty_active = True
        self.black_penalty_seconds = self.get_minutes('penalty_duration')
        self.update_penalty_display("black")
        self.black_penalty_job = self.master.after(1000, lambda: self.countdown_penalty("black"))

def countdown_penalty(self, team_color):
    """Countdown penalty timer"""
    if team_color == "white" and self.white_penalty_active:
        self.white_penalty_seconds -= 1
        if self.white_penalty_seconds <= 0:
            self.end_penalty("white")
        else:
            self.update_penalty_display("white")
            self.white_penalty_job = self.master.after(1000, lambda: self.countdown_penalty("white"))
    elif team_color == "black" and self.black_penalty_active:
        self.black_penalty_seconds -= 1
        if self.black_penalty_seconds <= 0:
            self.end_penalty("black")
        else:
            self.update_penalty_display("black")
            self.black_penalty_job = self.master.after(1000, lambda: self.countdown_penalty("black"))

# Add penalty buttons to create_scoreboard_tab()
self.white_penalty_button = tk.Button(
    tab, text="White\nPenalty", font=self.fonts["timeout_button"],
    bg="white", fg="red", command=lambda: self.toggle_penalty("white")
)
self.white_penalty_button.grid(row=11, column=0, padx=1, pady=1, sticky="nsew")
```

### Example 2: Adding Game Statistics Tracking

**Prompt:**
```
Add comprehensive game statistics tracking to the UWH app. Track:
- Goals per period for each team
- Total game time played
- Number of timeouts used by each team
- Penalty counts

Add a new "Statistics" tab and export functionality to save stats as JSON.
```

**Expected Output:**
```python
# Add statistics tracking to __init__
self.game_stats = {
    "white_goals_by_period": {},
    "black_goals_by_period": {},
    "white_timeouts_used": 0,
    "black_timeouts_used": 0,
    "white_penalties": 0,
    "black_penalties": 0,
    "game_start_time": None,
    "total_game_time": 0
}

def create_statistics_tab(self):
    """Create statistics display and export tab"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text="Statistics")
    
    # Statistics display
    stats_frame = ttk.LabelFrame(tab, text="Game Statistics", padding=10)
    stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # White team stats
    white_frame = ttk.LabelFrame(stats_frame, text="White Team", padding=5)
    white_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    self.white_stats_label = tk.Label(white_frame, text="", justify="left")
    self.white_stats_label.pack()
    
    # Black team stats  
    black_frame = ttk.LabelFrame(stats_frame, text="Black Team", padding=5)
    black_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    
    self.black_stats_label = tk.Label(black_frame, text="", justify="left")
    self.black_stats_label.pack()
    
    # Export button
    export_button = tk.Button(
        tab, text="Export Statistics", font=self.fonts["button"],
        command=self.export_statistics
    )
    export_button.pack(pady=10)

def update_statistics_display(self):
    """Update the statistics display"""
    white_stats = f"""Goals: {self.white_score_var.get()}
Timeouts Used: {self.game_stats['white_timeouts_used']}
Penalties: {self.game_stats['white_penalties']}"""
    
    black_stats = f"""Goals: {self.black_score_var.get()}
Timeouts Used: {self.game_stats['black_timeouts_used']}  
Penalties: {self.game_stats['black_penalties']}"""
    
    self.white_stats_label.config(text=white_stats)
    self.black_stats_label.config(text=black_stats)
```

### Example 3: Adding Sound/Audio Alerts

**Prompt:**
```
Add audio alert functionality to the UWH scoring app for:
- Period end warnings (30 seconds, 10 seconds)
- Goal scoring confirmation
- Game phase transitions
- Emergency stop signal

Include volume control in settings and different sound types for different events.
```

**Expected Output:**
```python
import pygame.mixer  # Add to imports

# Add to __init__
pygame.mixer.init()
self.sounds_enabled = True
self.alert_volume = 0.7

# Load sound files (placeholder paths)
try:
    self.sounds = {
        "period_warning": pygame.mixer.Sound("sounds/warning.wav"),
        "goal_scored": pygame.mixer.Sound("sounds/goal.wav"),
        "phase_change": pygame.mixer.Sound("sounds/phase.wav"),
        "emergency": pygame.mixer.Sound("sounds/emergency.wav")
    }
except:
    self.sounds = {}
    self.sounds_enabled = False

# Add to variables dictionary
"audio_alerts_enabled": {"default": True, "checkbox": True, "label": "Audio alerts enabled?"},
"alert_volume": {"default": 70, "checkbox": False, "unit": "percent"},

def play_sound(self, sound_type):
    """Play audio alert if enabled"""
    if not self.sounds_enabled or sound_type not in self.sounds:
        return
    
    try:
        volume = self.variables.get("alert_volume", {}).get("value", 70) / 100.0
        self.sounds[sound_type].set_volume(volume)
        self.sounds[sound_type].play()
    except Exception as e:
        print(f"Audio error: {e}")

def check_period_warnings(self):
    """Check if period warning sounds should play"""
    if self.timer_seconds == 30:
        self.play_sound("period_warning")
    elif self.timer_seconds == 10:
        self.play_sound("period_warning")

# Modify add_goal_with_confirmation to include sound
def add_goal_with_confirmation(self, score_var, team_name):
    # ... existing confirmation logic ...
    if result:
        score_var.set(score_var.get() + 1)
        self.play_sound("goal_scored")  # Add this line
        # ... rest of existing code ...
```

### Example 4: Adding Network/Remote Control Support

**Prompt:**
```
Add basic network support to the UWH scoring app to allow remote control from mobile devices. Create:
1. Simple HTTP server for remote commands
2. Web interface for basic scoring operations
3. Network settings in the app
4. Security with basic authentication

Keep it simple and lightweight for Raspberry Pi deployment.
```

**Expected Output:**
```python
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import base64

# Add to variables dictionary
"enable_remote_control": {"default": False, "checkbox": True, "label": "Enable remote control?"},
"remote_port": {"default": 8080, "checkbox": False, "unit": "port"},
"remote_password": {"default": "uwh2025", "checkbox": False, "unit": "text"},

class UWHRemoteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, uwh_app=None, **kwargs):
        self.uwh_app = uwh_app
        super().__init__(*args, **kwargs)
    
    def do_POST(self):
        """Handle remote control commands"""
        if not self.check_auth():
            self.send_auth_required()
            return
            
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            command = json.loads(post_data.decode('utf-8'))
            response = self.process_command(command)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(400, str(e))
    
    def process_command(self, command):
        """Process remote control commands"""
        action = command.get('action')
        team = command.get('team')
        
        if action == 'add_goal' and team in ['white', 'black']:
            score_var = self.uwh_app.white_score_var if team == 'white' else self.uwh_app.black_score_var
            self.uwh_app.master.after(0, lambda: score_var.set(score_var.get() + 1))
            return {"status": "success", "message": f"Goal added for {team}"}
        
        elif action == 'get_status':
            return {
                "white_score": self.uwh_app.white_score_var.get(),
                "black_score": self.uwh_app.black_score_var.get(),
                "timer": self.uwh_app.timer_label.cget("text"),
                "phase": self.uwh_app.half_label.cget("text")
            }
        
        return {"status": "error", "message": "Unknown command"}

def start_remote_server(self):
    """Start the remote control server"""
    if not self.variables.get("enable_remote_control", {}).get("value", False):
        return
        
    port = int(self.variables.get("remote_port", {}).get("value", 8080))
    
    def run_server():
        handler = lambda *args, **kwargs: UWHRemoteHandler(*args, uwh_app=self, **kwargs)
        httpd = HTTPServer(('', port), handler)
        httpd.serve_forever()
    
    self.server_thread = threading.Thread(target=run_server, daemon=True)
    self.server_thread.start()
    print(f"Remote control server started on port {port}")
```

### Example 5: Adding Data Persistence and Game History

**Prompt:**
```
Add game history and data persistence to the UWH scoring app. Save:
- Complete game records with scores, timing, and events
- Tournament bracket progression
- Player/team statistics across multiple games
- Settings backup and restore

Use JSON files for simple deployment and backup.
```

**Expected Output:**
```python
import json
import os
from datetime import datetime

# Add to __init__
self.data_dir = "uwh_data"
self.ensure_data_directory()
self.game_history = []
self.current_game_id = None

def ensure_data_directory(self):
    """Create data directory if it doesn't exist"""
    if not os.path.exists(self.data_dir):
        os.makedirs(self.data_dir)
        os.makedirs(os.path.join(self.data_dir, "games"))
        os.makedirs(os.path.join(self.data_dir, "settings"))
        os.makedirs(os.path.join(self.data_dir, "backups"))

def start_new_game(self):
    """Initialize a new game record"""
    self.current_game_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    game_record = {
        "game_id": self.current_game_id,
        "start_time": datetime.now().isoformat(),
        "white_team": "White",
        "black_team": "Black",
        "final_score": {"white": 0, "black": 0},
        "periods_played": [],
        "events": [],
        "settings": dict(self.variables)
    }
    
    self.save_game_record(game_record)
    return game_record

def log_game_event(self, event_type, details):
    """Log a game event"""
    if not self.current_game_id:
        return
        
    event = {
        "timestamp": datetime.now().isoformat(),
        "game_time": self.timer_label.cget("text"),
        "period": self.half_label.cget("text"),
        "type": event_type,
        "details": details
    }
    
    # Save to current game file
    game_file = os.path.join(self.data_dir, "games", f"{self.current_game_id}.json")
    if os.path.exists(game_file):
        with open(game_file, 'r') as f:
            game_data = json.load(f)
        game_data["events"].append(event)
        with open(game_file, 'w') as f:
            json.dump(game_data, f, indent=2)

def save_settings_backup(self):
    """Save current settings as backup"""
    backup_file = os.path.join(
        self.data_dir, "settings", 
        f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    
    settings_data = {
        "timestamp": datetime.now().isoformat(),
        "settings": {name: var.get("value", var["default"]) 
                    for name, var in self.variables.items()}
    }
    
    with open(backup_file, 'w') as f:
        json.dump(settings_data, f, indent=2)

# Modify goal addition to log events
def add_goal_with_confirmation(self, score_var, team_name):
    # ... existing confirmation logic ...
    if result:
        old_score = score_var.get()
        score_var.set(old_score + 1)
        
        # Log the goal event
        self.log_game_event("GOAL", {
            "team": team_name,
            "old_score": old_score,
            "new_score": score_var.get(),
            "scorer": "Unknown"  # Could be extended to track individual players
        })
```

## Usage Tips for These Examples

1. **Copy-Paste Ready**: These examples are designed to be directly usable with minimal modification
2. **Error Handling**: Add try-catch blocks around file operations and network code
3. **Testing**: Test each feature incrementally before combining multiple features
4. **Performance**: Consider the impact on the main UI thread, especially for network and file operations
5. **User Experience**: Always provide visual feedback for long-running operations

## Combining Features

You can combine multiple examples by:
1. Merging the `__init__` additions carefully
2. Adding all new methods without conflicts
3. Updating the UI creation methods to include all new elements
4. Testing thoroughly after each integration step

Remember to use descriptive variable names and follow the existing code patterns for consistency.