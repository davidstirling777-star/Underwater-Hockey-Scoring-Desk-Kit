class GameEngine:

    def __init__(self):
        self.white_goal_scorers = {}
        self.black_goal_scorers = {}

        self.stored_penalties = []
        self.active_penalties = []

        self.white_timeouts_this_half = 0
        self.black_timeouts_this_half = 0
        self.active_timeout_team = None

        self.sudden_death_goal_scored = False
        self.sudden_death_restore_time = None
        self.sudden_death_restore_active = False

        self.saved_state = {}
        
        self.full_sequence = []
        self.current_index = 0

        self.timer_running = True
        self.timer_seconds = 0

        self.saved_timer_running = False
        self.saved_timer_seconds = 0

    def record_goal_scorer(self, team, cap_number):

        if cap_number is None:
            return

        if team == "White":
            self.white_goal_scorers[cap_number] = (
                self.white_goal_scorers.get(cap_number, 0) + 1
            )

        elif team == "Black":
            self.black_goal_scorers[cap_number] = (
                self.black_goal_scorers.get(cap_number, 0) + 1
            )

    def clear_goal_scorers(self):
        self.white_goal_scorers.clear()
        self.black_goal_scorers.clear()

    def clear_penalties(self):
        self.stored_penalties.clear()
        self.active_penalties.clear()

    def reset_timeouts(self):
        self.white_timeouts_this_half = 0
        self.black_timeouts_this_half = 0
        self.active_timeout_team = None

    def reset_half_timeouts(self):
        self.white_timeouts_this_half = 0
        self.black_timeouts_this_half = 0

    def start_timeout(self, team):
    
        if team == "White":
            self.active_timeout_team = "white"
            self.white_timeouts_this_half += 1
    
        elif team == "Black":
            self.active_timeout_team = "black"
            self.black_timeouts_this_half += 1

    def end_timeout(self):
        self.active_timeout_team = None

    def mark_sudden_death_goal(self, remaining_time):
        self.sudden_death_restore_time = remaining_time
        self.sudden_death_restore_active = True
        self.sudden_death_goal_scored = True

    def clear_sudden_death_goal(self):
        self.sudden_death_restore_time = None
        self.sudden_death_restore_active = False
        self.sudden_death_goal_scored = False

    def find_period_index(self, name):
    
        for idx, period in enumerate(self.full_sequence):
    
            if period["name"] == name:
                return idx
    
        return len(self.full_sequence) - 1

    def advance_period(self, white_score, black_score):
    
        if self.current_index >= len(self.full_sequence):
            self.current_index = self.find_period_index(
                "Between Game Break"
            )
            return True
    
        cur_period = self.full_sequence[self.current_index]
        period_name = cur_period["name"]
    
        if period_name == "Second Half":
            if white_score != black_score:
                self.current_index = self.find_period_index(
                    "Between Game Break"
                )
                return True
    
        if period_name == "Overtime Second Half":
            if white_score != black_score:
                self.current_index = self.find_period_index(
                    "Between Game Break"
                )
                return True
    
        if (
            period_name == "Sudden Death"
            and self.sudden_death_goal_scored
        ):
            self.current_index = self.find_period_index(
                "Between Game Break"
            )
            return True
    
        self.current_index += 1
    
        if self.current_index >= len(self.full_sequence):
            self.current_index = self.find_period_index(
                "First Half"
            )
    
        return True

    def get_current_period(self):
    
        if not self.full_sequence:
            return None
    
        if self.current_index >= len(self.full_sequence):
            return None
    
        return self.full_sequence[self.current_index]
    
    
    def save_timer_state(self, timer_running, timer_seconds):
    
        self.saved_timer_running = timer_running
        self.saved_timer_seconds = timer_seconds
    
    
    def restore_timer_state(self):
    
        return (
            self.saved_timer_running,
            self.saved_timer_seconds
        )

    def clear_timer_state(self):
    
        self.saved_timer_running = False
        self.saved_timer_seconds = 0

    def set_current_period(self, index):
        self.current_index = index
    
    def next_period_index(self):
        self.current_index += 1
    
    def reset_to_first_half(self):
        self.current_index = self.find_period_index("First Half")
    
    def reset_to_between_game_break(self):
        self.current_index = self.find_period_index(
            "Between Game Break"
        )

    def reset_to_first_period(self):
        self.current_index = 0

    def go_to_period(self, period_name):
        self.current_index = self.find_period_index(period_name)

    def set_sequence(self, sequence):
        self.full_sequence = sequence
        self.current_index = 0
