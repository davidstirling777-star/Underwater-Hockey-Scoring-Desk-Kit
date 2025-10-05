# Cap Number Dialog - Visual State Persistence Fix

## Problem Statement
The cap number dialog needed to ensure that when a user clicks a cap number button (1-15), Unknown, or Penalty Goal button, the button remains visually depressed (highlighted/selected) until the OK button is pushed, even if the user interacts with other parts of the dialog.

## Root Cause
Tkinter buttons have built-in event handlers that automatically manage the button's relief (visual appearance):
- On `<ButtonPress-1>`: The button's relief changes to `SUNKEN`
- On `<ButtonRelease-1>`: The button's relief changes back to `RAISED`

Even though our `select_*` functions were setting the button to `SUNKEN` and `lightblue`, the button's built-in event handler would reset it back to `RAISED` immediately after the mouse button was released, potentially losing the visual indication of selection.

## Solution
The fix uses tkinter's `after()` method to schedule the visual state update to run 1 millisecond after the button click completes. This ensures the visual state is applied AFTER the button's built-in event handlers have completed, making it the final state that persists.

### Implementation Details

Each selection function (`select_cap`, `select_unknown`, `select_penalty_goal`) now:

1. **Moves the highlighting logic into a nested `apply_highlight()` function**
   - This allows the same logic to be called twice

2. **Calls `apply_highlight()` immediately**
   - Applies the visual state right away

3. **Schedules `apply_highlight()` to run again after 1ms**
   - Uses `dialog.after(1, apply_highlight)`
   - This ensures the visual state persists even if tkinter's event handlers try to reset it

### Code Changes

#### `select_cap(cap)` function:
```python
# Before:
def select_cap(cap):
    selected_cap["value"] = str(cap)
    # Highlight the selected button temporarily
    for widget in matrix_frame.winfo_children():
        if hasattr(widget, 'cap_value') and widget.cap_value == cap:
            widget.config(relief=tk.SUNKEN, bg="lightblue")
        elif isinstance(widget, tk.Button) and hasattr(widget, 'original_bg'):
            widget.config(relief=tk.RAISED, bg=widget.original_bg)
    # ... more code ...

# After:
def select_cap(cap):
    selected_cap["value"] = str(cap)
    # Highlight the selected button and keep it highlighted
    def apply_highlight():
        for widget in matrix_frame.winfo_children():
            if hasattr(widget, 'cap_value') and widget.cap_value == cap:
                widget.config(relief=tk.SUNKEN, bg="lightblue")
            elif isinstance(widget, tk.Button) and hasattr(widget, 'original_bg'):
                widget.config(relief=tk.RAISED, bg=widget.original_bg)
        # ... more code ...
    # Apply immediately and schedule again to override button's default behavior
    apply_highlight()
    cap_number_dialog.after(1, apply_highlight)
```

The same pattern was applied to `select_unknown()` and `select_penalty_goal()` functions.

## Testing

### Automated Tests
An automated test suite was created and run successfully, verifying:
- ✓ Cap 5 button becomes SUNKEN and lightblue after click
- ✓ Cap 12 button becomes SUNKEN and lightblue after click
- ✓ Cap 5 button returns to RAISED after clicking cap 12
- ✓ Unknown button becomes SUNKEN and lightblue after click
- ✓ Cap 12 button returns to RAISED after clicking Unknown
- ✓ Penalty Goal button becomes SUNKEN and lightblue after click
- ✓ Unknown button returns to RAISED after clicking Penalty Goal

**Result: 7/7 tests passed ✓**

### Manual Testing
To manually verify the fix:
1. Run the application: `python3 uwh.py`
2. Click "Add Goal" for either team
3. In the cap number dialog:
   - Click any cap number (e.g., 5)
   - **Observe**: Button 5 remains SUNKEN with light blue background
   - Click another cap number (e.g., 12)
   - **Observe**: Button 12 is now SUNKEN, button 5 returns to normal
   - Click "Unknown"
   - **Observe**: Unknown button is SUNKEN, all cap buttons normal
   - Click "Penalty Goal"
   - **Observe**: Penalty Goal button is SUNKEN, others normal
   - Click "OK" to confirm selection

## Visual Examples

See the screenshots in the repository:
- `cap_dialog_button7_selected.png` - Shows cap number 7 selected
- `cap_dialog_unknown_selected.png` - Shows "Unknown" button selected
- `cap_dialog_penalty_selected.png` - Shows "Penalty Goal" button selected

## Impact
- **No functional changes** - The selection logic remains exactly the same
- **Visual improvement only** - Buttons now reliably maintain their highlighted state
- **User experience** - Users can clearly see which button was selected before clicking OK
- **Minimal performance impact** - The 1ms delay is imperceptible to users
- **No breaking changes** - All existing functionality preserved

## Files Modified
- `uwh.py` - Updated `select_cap()`, `select_unknown()`, and `select_penalty_goal()` functions
- `.gitignore` - Added `cap_dialog_*.png` to exclude test screenshots

## Validation
- ✓ Syntax validation: `python3 -m py_compile uwh.py` - Success
- ✓ Module import: `python3 -c "import uwh"` - Success
- ✓ Automated tests: 7/7 tests passed
- ✓ No breaking changes to existing functionality
