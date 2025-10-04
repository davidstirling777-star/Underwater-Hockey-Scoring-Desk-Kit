# Cap Number Dialog UI Update Summary

## Changes Made

### 1. Dialog Height Increased
- **Before**: 400x250 pixels
- **After**: 400x300 pixels
- **Reason**: To accommodate the new button and improve visual balance

### 2. Unknown Button Width Reduced
- **Before**: `button_width * 4 + 6 = 26` (spanning columns 0-3)
- **After**: `button_width * 2 + 3 = 13` (spanning columns 0-1)
- **Reduction**: Exactly 50% (half the original width)

### 3. New Penalty Goal Button Added
- **Width**: `button_width * 2 + 3 = 13` (same as Unknown button)
- **Position**: Columns 2-3 (between Unknown and OK)
- **Functionality**: Sets `selected_cap["value"] = "Penalty Goal"` with proper highlighting

### 4. OK Button Repositioned
- **Before**: Column 4 (was labeled as column 5 in comment)
- **After**: Column 4 (unchanged position, comment corrected)

## Button Layout

```
Bottom Frame Layout (5 columns):
┌──────────────┬──────────────┬──────────────┬──────────────┬─────┐
│   Unknown    │              │Penalty Goal  │              │ OK  │
│ (cols 0-1)   │              │ (cols 2-3)   │              │(c 4)│
└──────────────┴──────────────┴──────────────┴──────────────┴─────┘
    width=13                      width=13                   w=5
```

## Callback Functions

### `select_penalty_goal()`
New function added to handle Penalty Goal button selection:
- Sets `selected_cap["value"] = "Penalty Goal"`
- Unhighlights all matrix buttons (1-15)
- Unhighlights Unknown and OK buttons
- Highlights the Penalty Goal button (sunken with lightblue background)

### Updated `select_unknown()`
- Simplified to use consistent highlighting logic
- Now unhighlights all bottom_frame buttons with original_bg before highlighting itself

## Testing Results

All functionality tests passed:
- ✓ Selecting cap numbers 1-15 works correctly
- ✓ Selecting Unknown sets value to "Unknown"
- ✓ Selecting Penalty Goal sets value to "Penalty Goal"
- ✓ Clicking OK without selection shows warning message
- ✓ Button highlighting works correctly for all selections

## Visual Changes

See `cap_dialog_updated.png` for a screenshot of the updated dialog showing:
- The 5×3 matrix of cap number buttons (1-15)
- The three bottom buttons properly aligned
- Improved vertical spacing with the increased height
