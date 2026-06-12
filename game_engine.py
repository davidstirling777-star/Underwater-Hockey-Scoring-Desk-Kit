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


