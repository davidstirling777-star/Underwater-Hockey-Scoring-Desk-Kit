import os
import datetime


def format_court_time(court_time_seconds):
    if court_time_seconds is None:
        return "00:00:00"

    hours, remainder = divmod(court_time_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def log_game_event(
    base_dir,
    court_time_seconds,
    event_type,
    team=None,
    cap_number=None,
    duration=None,
    break_status=None,
    debug_mode=False
):
    now = datetime.datetime.now()
    local_time = now.strftime("%Y-%m-%d %H:%M:%S")

    court_time = format_court_time(court_time_seconds)

    fields = [
        local_time,
        court_time,
        event_type,
        team if team else "",
        cap_number if cap_number else "",
        duration if duration else "",
        break_status if break_status else ""
    ]

    event_line = "|".join(str(field) for field in fields)
    txt_file = os.path.join(base_dir, "UWH_Game_Data.txt")

    try:
        with open(txt_file, "a", encoding="utf-8") as f:
            f.write(event_line + "\n")
        return True

    except Exception as e:
        if debug_mode:
            print(f"Error logging game event: {e}")
        return False
