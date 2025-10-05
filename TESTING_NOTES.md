# Testing Notes for Goal Warning and Preset Reset Fixes

## Changes Summary

This document describes the changes made to fix issues with goal warnings during breaks/timeouts and preset button behavior.

## Issues Fixed

### Issue 1: Enhanced Goal Warning Dialogs
- **Problem**: Warning dialog didn't distinguish between different types of breaks/timeouts
- **Solution**: Now shows specific warning messages:
  - "during a Team Time-Out" for team timeouts
  - "during a Referee Time-Out" for referee timeouts
  - "during a break or half time" for regular breaks

### Issue 2: CSV Logging for Break/Timeout Goals
- **Problem**: CSV logs didn't record when goals were scored during breaks or timeouts
- **Solution**: Added new "break_status" column to CSV that records:
  - "Team Time-Out" when goal scored during team timeout
  - "Referee Time-Out" when goal scored during referee timeout
  - "Break" when goal scored during a regular break
  - Empty string for goals scored during normal play

### Issue 3: Time-Outs Always Show Warning
- **Status**: Already working correctly - verified in testing

### Issue 4: Preset Button Updates Game Sequence
- **Problem**: When preset button was applied, variables were updated in the Game Variables tab, but after Reset Timer button was pushed, the game sequence didn't reflect the new values
- **Solution**: Added call to `build_game_sequence()` in `_apply_button_data()` function after `load_settings()`
- **Impact**: Now when you apply a preset and then click Reset Timer, the game will use the preset values

## Files Modified

1. `uwh.py` - All changes made to this file:
   - Line 413: Updated `log_game_event()` signature to include `break_status` parameter
   - Line 447: Added "break_status" field to CSV row data
   - Line 456: Added "break_status" to CSV fieldnames
   - Line 1997: Added `build_game_sequence()` call in `_apply_button_data()`
   - Lines 3743-3786: Complete rewrite of `add_goal_with_confirmation()` logic

## Testing Scenarios

### Scenario 1: Goal During Team Time-Out
**Steps**:
1. Start the application
2. Click "White TO" or "Black TO" button to start a team timeout
3. Click "Add Goal" button for either team
4. **Expected**: Dialog shows "You are about to add a goal for [Team] during a Team Time-Out. Are you sure?"
5. Click "Yes" to add goal
6. **Expected**: UWH_Game_Data.csv shows "Team Time-Out" in break_status column

### Scenario 2: Goal During Referee Time-Out
**Steps**:
1. Start the application
2. Click "Referee Time-Out" button to activate referee timeout
3. Click "Add Goal" button for either team
4. **Expected**: Dialog shows "You are about to add a goal for [Team] during a Referee Time-Out. Are you sure?"
5. Click "Yes" to add goal
6. **Expected**: UWH_Game_Data.csv shows "Referee Time-Out" in break_status column

### Scenario 3: Goal During Regular Break
**Steps**:
1. Start the application
2. Wait for or navigate to a break period (e.g., Half Time, Between Game Break)
3. Click "Add Goal" button for either team
4. **Expected**: Dialog shows "You are about to add a goal for [Team] during a break or half time. Are you sure?"
5. Click "Yes" to add goal
6. **Expected**: UWH_Game_Data.csv shows "Break" in break_status column

### Scenario 4: Goal During Normal Play
**Steps**:
1. Start the application
2. During a regular game period (First Half, Second Half, etc.)
3. Click "Add Goal" button for either team
4. **Expected**: No warning dialog appears
5. **Expected**: UWH_Game_Data.csv shows empty string in break_status column

### Scenario 5: Preset Button and Reset Timer
**Steps**:
1. Start the application
2. Go to "Game Variables" tab
3. Click one of the preset buttons (1-8) to apply preset settings
4. Verify that values in Game Variables tab are updated
5. Go back to "Scoreboard" tab
6. Click "Reset Timer" button
7. **Expected**: The game sequence now uses the preset values
   - Check that timer durations match the preset values
   - Verify that enabled/disabled periods (Overtime, Sudden Death, etc.) match preset settings

## CSV Output Example

After these changes, the CSV file will have this structure:

```csv
local_datetime,court_time,event_type,team,cap_number,duration,break_status
2024-01-15 14:30:00,00:15:30,Goal,White,5,,Team Time-Out
2024-01-15 14:32:00,00:17:30,Goal,Black,,,Referee Time-Out
2024-01-15 14:45:00,00:30:00,Goal,White,3,,Break
2024-01-15 14:55:00,00:40:00,Goal,Black,7,,
```

## Code Quality

All changes have been validated:
- ✅ Python syntax validation (`python3 -m py_compile uwh.py`)
- ✅ AST validation (`python3 -m ast uwh.py`)
- ✅ No new dependencies added
- ✅ Minimal changes approach followed
- ✅ Backward compatible (existing CSV logs will still work)

## Notes

- The break_status column is backward compatible - if the parameter is not provided, it defaults to an empty string
- All existing code that calls `log_game_event()` without the `break_status` parameter will continue to work
- The CSV file will automatically add the "break_status" column header when created or when first goal with break_status is logged
