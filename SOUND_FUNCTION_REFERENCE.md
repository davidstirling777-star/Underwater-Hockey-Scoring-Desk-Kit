# play_sound_with_volume() Quick Reference

## Function Signature

```python
def play_sound_with_volume(filename, sound_type, enable_sound, pips_volume, siren_volume, 
                           air_volume, water_volume, siren_duration=1.5):
    """
    Play a sound file asynchronously with volume control using threading.
    
    Args:
        filename: str path to sound file (e.g., "beep-cut.mp3")
        sound_type: str type of sound ("pips" or "siren")
        enable_sound: BooleanVar or bool indicating if sound is enabled
        pips_volume: IntVar or int for pips volume (0-100)
        siren_volume: IntVar or int for siren volume (0-100)
        air_volume: IntVar or int for air channel volume (0-100)
        water_volume: IntVar or int for water channel volume (0-100)
        siren_duration: DoubleVar or float for siren duration in seconds (default 1.5)
    """
```

## Usage Examples

### Example 1: Play pips sound (all arguments)
```python
play_sound_with_volume(
    self.pips_var.get(),        # filename
    "pips",                      # sound_type
    self.enable_sound,           # enable_sound
    self.pips_volume,            # pips_volume
    self.siren_volume,           # siren_volume
    self.air_volume,             # air_volume
    self.water_volume,           # water_volume
    self.siren_duration          # siren_duration (optional, default 1.5)
)
```

### Example 2: Play siren sound (all arguments)
```python
play_sound_with_volume(
    self.siren_var.get(),        # filename
    "siren",                     # sound_type
    self.enable_sound,           # enable_sound
    self.pips_volume,            # pips_volume
    self.siren_volume,           # siren_volume
    self.air_volume,             # air_volume
    self.water_volume,           # water_volume
    self.siren_duration          # siren_duration (optional, default 1.5)
)
```

### Example 3: Using default siren_duration
```python
# You can omit the last parameter to use default value (1.5 seconds)
play_sound_with_volume(
    "beep-cut.mp3",              # filename
    "pips",                      # sound_type
    True,                        # enable_sound
    50,                          # pips_volume
    50,                          # siren_volume
    50,                          # air_volume
    50                           # water_volume
    # siren_duration defaults to 1.5
)
```

## Common Patterns in uwh.py

### Pattern 1: Timer-triggered sounds
```python
# From countdown_timer() method - playing pips at 30s
play_sound_with_volume(self.pips_var.get(), "pips", self.enable_sound, 
                       self.pips_volume, self.siren_volume, 
                       self.air_volume, self.water_volume,
                       self.siren_duration)
```

### Pattern 2: Siren loop
```python
# From _siren_loop_worker() method - continuous siren
siren_file = self.siren_var.get()
play_sound_with_volume(siren_file, "siren", self.enable_sound, 
                       self.pips_volume, self.siren_volume, 
                       self.air_volume, self.water_volume,
                       self.siren_duration)
```

### Pattern 3: Test buttons
```python
# From test_pips_sound() method
play_sound_with_volume(self.pips_var.get(), "pips", 
                       self.enable_sound, self.pips_volume, self.siren_volume, 
                       self.air_volume, self.water_volume, self.siren_duration)
```

## Important Notes

1. **Always pass 7 or 8 arguments**
   - 7 arguments: Uses default siren_duration (1.5 seconds)
   - 8 arguments: Explicitly sets siren_duration

2. **Argument order matters**
   - Arguments must be in the exact order shown in the signature
   - Cannot skip intermediate arguments

3. **Sound type affects volume used**
   - "pips" uses pips_volume
   - "siren" uses siren_volume
   - But both volume parameters must always be provided

4. **Siren duration behavior**
   - Only affects siren sounds (not pips)
   - If sound file is shorter than siren_duration, it will loop
   - Default is 1.5 seconds to ensure audibility

5. **Threading**
   - Function returns immediately (non-blocking)
   - Sound plays in background thread
   - Safe to call from UI event handlers

## Error Prevention

### ✅ Correct
```python
# 8 arguments - all explicit
play_sound_with_volume(file, "pips", True, 50, 50, 50, 50, 1.5)

# 7 arguments - using default
play_sound_with_volume(file, "pips", True, 50, 50, 50, 50)
```

### ❌ Wrong
```python
# Too few arguments (missing water_volume)
play_sound_with_volume(file, "pips", True, 50, 50, 50)  # ERROR!

# Too many arguments
play_sound_with_volume(file, "pips", True, 50, 50, 50, 50, 1.5, "extra")  # ERROR!

# Wrong order
play_sound_with_volume(file, True, "pips", 50, 50, 50, 50)  # ERROR!
```

## Verification

Run the test suite to verify correct usage:
```bash
python3 test_sound_signature.py
```

All tests should pass with the message:
```
✓✓✓ ALL TESTS PASSED ✓✓✓
```
