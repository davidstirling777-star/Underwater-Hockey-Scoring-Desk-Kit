"""
Sound module for Underwater Hockey Scoring Desk Kit.

This module contains all sound-related functions for audio playback,
device checking, and sound file management.

Cross-platform support:
- Preferred: Uses pygame.mixer for instant preloaded sound playback (all platforms)
- Fallback Linux/Raspberry Pi: Uses aplay for .wav, omxplayer for .mp3, amixer for volume
- Fallback Windows: Uses winsound for .wav, playsound for other formats if available

Note: Sound playback functions use threading to prevent blocking the UI timer.
"""

import subprocess
import os
import platform
import threading
from tkinter import messagebox

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Try to import pygame.mixer for preloaded sound playback
try:
    import pygame.mixer
    PYGAME_AVAILABLE = True
    # Initialize pygame.mixer with appropriate settings
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        PYGAME_INITIALIZED = True
    except Exception as e:
        print(f"Warning: pygame.mixer initialization failed: {e}")
        PYGAME_INITIALIZED = False
except ImportError:
    PYGAME_AVAILABLE = False
    PYGAME_INITIALIZED = False
    print("Warning: pygame not available. Falling back to subprocess-based sound playback.")

# Optional imports for Windows
if IS_WINDOWS:
    try:
        import winsound
        WINSOUND_AVAILABLE = True
    except ImportError:
        WINSOUND_AVAILABLE = False
    
    try:
        from playsound import playsound
        PLAYSOUND_AVAILABLE = True
    except ImportError:
        PLAYSOUND_AVAILABLE = False
else:
    WINSOUND_AVAILABLE = False
    PLAYSOUND_AVAILABLE = False

# Global dictionary to store preloaded sounds
_preloaded_sounds = {}


def check_audio_device_available(enable_sound):
    """
    Check if audio devices are available for playback.
    Returns True if audio devices are available, False otherwise.
    If sound is disabled, always returns True to prevent warnings.
    
    Cross-platform support:
    - Windows: Assumes audio device available if winsound module is available
    - Linux: Checks using aplay and amixer commands
    
    Args:
        enable_sound: BooleanVar or bool indicating if sound is enabled
    
    Returns:
        bool: True if audio devices available or sound disabled, False otherwise
    """
    # If sound is disabled, don't check for audio devices
    sound_enabled = enable_sound.get() if hasattr(enable_sound, 'get') else enable_sound
    if not sound_enabled:
        return True
    
    # Windows: Assume audio device is available if winsound is available
    if IS_WINDOWS:
        return WINSOUND_AVAILABLE
    
    # Linux: Check for audio devices using aplay and amixer
    if IS_LINUX:
        try:
            # Try to check for audio devices using aplay (Linux/Raspberry Pi)
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Alternative check using amixer
            result = subprocess.run(['amixer', 'scontrols'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    return False


def handle_no_audio_device_warning(sound_var, sound_type, enable_sound, audio_device_warning_shown):
    """
    Handle the case when no audio device is available.
    Shows warning once per session and resets sound selection to "Default".
    If sound is disabled, skip the warning.
    
    Args:
        sound_var: StringVar for sound selection
        sound_type: str describing the type of sound
        enable_sound: BooleanVar or bool indicating if sound is enabled
        audio_device_warning_shown: bool flag to track if warning shown
    
    Returns:
        bool: Updated audio_device_warning_shown flag
    """
    # If sound is disabled, don't show audio device warnings
    sound_enabled = enable_sound.get() if hasattr(enable_sound, 'get') else enable_sound
    if not sound_enabled:
        return audio_device_warning_shown
        
    if not audio_device_warning_shown:
        messagebox.showwarning(
            "Audio Device Warning", 
            f"No audio device detected. Cannot play {sound_type} sounds.\n"
            f"Sound selection will be reset to 'Default'."
        )
        audio_device_warning_shown = True
    
    # Reset sound selection to "Default" to prevent loop
    sound_var.set("Default")
    
    return audio_device_warning_shown


def get_sound_files():
    """
    Scan the current directory for supported sound files (.wav, .mp3).
    Returns a list of sound files found.
    
    Returns:
        list: Sorted list of sound files, or ["No sound files found"] if none
    """
    sound_files = []
    supported_extensions = ['.wav', '.mp3']
    
    try:
        current_dir = os.getcwd()
        for filename in os.listdir(current_dir):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                sound_files.append(filename)
    except Exception as e:
        print(f"Error scanning for sound files: {e}")
    
    return sorted(sound_files) if sound_files else ["No sound files found"]


def preload_sounds():
    """
    Preload all available sound files into memory using pygame.mixer.
    This enables instant sound playback without delay.
    
    Should be called once during application startup.
    Only works if pygame is available and initialized.
    
    Returns:
        int: Number of sounds successfully preloaded
    """
    global _preloaded_sounds
    
    if not PYGAME_AVAILABLE or not PYGAME_INITIALIZED:
        print("pygame.mixer not available - sounds will not be preloaded")
        return 0
    
    sound_files = get_sound_files()
    if sound_files == ["No sound files found"]:
        print("No sound files found to preload")
        return 0
    
    loaded_count = 0
    for filename in sound_files:
        try:
            file_path = os.path.join(os.getcwd(), filename)
            if os.path.exists(file_path):
                # Load the sound into memory
                sound = pygame.mixer.Sound(file_path)
                _preloaded_sounds[filename] = sound
                loaded_count += 1
                print(f"Preloaded sound: {filename}")
        except Exception as e:
            print(f"Warning: Failed to preload {filename}: {e}")
    
    print(f"Successfully preloaded {loaded_count} sound files")
    return loaded_count


def _play_sound_sync(filename, enable_sound):
    """
    Internal synchronous sound playback function.
    Called by play_sound() in a separate thread to prevent UI blocking.
    
    Cross-platform support:
    - Linux: Uses aplay for WAV files and omxplayer for MP3 files (Raspberry Pi compatible)
    - Windows: Uses winsound for WAV files, playsound for other formats if available
    
    Args:
        filename: str path to sound file
        enable_sound: bool indicating if sound is enabled
    """
    # Check if sound is enabled
    if not enable_sound:
        return
        
    if filename == "No sound files found" or filename == "Default":
        print(f"Sound Test: Cannot play '{filename}' - not a valid sound file")
        return
        
    try:
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            print(f"Sound Error: Sound file '{filename}' not found")
            return
        
        # Windows playback with improved reliability
        if IS_WINDOWS:
            if filename.lower().endswith('.wav'):
                if WINSOUND_AVAILABLE:
                    try:
                        # Use SND_ASYNC for non-blocking playback
                        winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                        print(f"Sound Test: Successfully played: {filename}")
                    except Exception as e:
                        # Try synchronous fallback
                        try:
                            winsound.PlaySound(file_path, winsound.SND_FILENAME)
                            print(f"Sound Test: Successfully played (sync): {filename}")
                        except Exception as e2:
                            print(f"Sound Error: Failed to play WAV: {e2}")
                else:
                    print("Sound Error: winsound module not available")
            else:
                # Try playsound for non-WAV files
                if PLAYSOUND_AVAILABLE:
                    try:
                        playsound(file_path)
                        print(f"Sound Test: Successfully played: {filename}")
                    except Exception as e:
                        print(f"Sound Error: Failed to play {filename}: {e}")
                else:
                    print("Sound Warning: playsound module not available. Install with: pip install playsound")
            return
            
        # Linux playback
        if IS_LINUX:
            # Determine command based on file extension
            if filename.lower().endswith('.wav'):
                # Use aplay for WAV files (works well on Raspberry Pi with DigiAMP+ HAT)
                subprocess.Popen(['aplay', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif filename.lower().endswith('.mp3'):
                # Use omxplayer for MP3 files (Raspberry Pi optimized)
                subprocess.Popen(['omxplayer', '--no-osd', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                print(f"Sound Error: Unsupported file format: {filename}")
                return
                
            # Show success feedback via console (avoid messagebox from thread)
            print(f"Sound Test: Successfully started playing: {filename}")
            return
        
        # Unsupported platform
        print(f"Sound Error: Unsupported platform: {platform.system()}")
        
    except FileNotFoundError:
        # Fallback for development environments without aplay/omxplayer
        print(f"Sound Warning: Audio player not found. Would play: {filename}")
    except Exception as e:
        print(f"Sound Error: Unexpected error playing {filename}: {e}")


def play_sound(filename, enable_sound):
    """
    Play a sound file asynchronously using threading to prevent UI blocking.
    
    This function immediately returns after spawning a background thread,
    ensuring the timer and UI remain responsive during sound playback.
    
    Cross-platform support:
    - Linux: Uses aplay for WAV files and omxplayer for MP3 files (Raspberry Pi compatible)
    - Windows: Uses winsound for WAV files, playsound for other formats if available
    
    Args:
        filename: str path to sound file
        enable_sound: BooleanVar or bool indicating if sound is enabled
    """
    # Extract value in main thread to avoid tkinter threading issues
    enable_sound_val = enable_sound.get() if hasattr(enable_sound, 'get') else enable_sound
    
    # Create and start a daemon thread for sound playback
    # Daemon thread ensures the thread doesn't prevent application exit
    sound_thread = threading.Thread(
        target=_play_sound_sync,
        args=(filename, enable_sound_val),
        daemon=True
    )
    sound_thread.start()


def _play_sound_with_volume_sync(filename, sound_type, enable_sound, pips_volume, siren_volume, 
                                 air_volume, water_volume, siren_duration=1.5):
    """
    Internal synchronous sound playback function with volume control.
    Called by play_sound_with_volume() in a separate thread to prevent UI blocking.
    
    Cross-platform support:
    - Preferred: Uses pygame.mixer for instant preloaded sound playback (all platforms)
    - Fallback Linux/Raspberry Pi: Uses aplay for .wav, omxplayer for .mp3, amixer for volume
    - Fallback Windows: Uses winsound for .wav, playsound for other formats if available
    
    Siren Duration Requirement:
    - Siren sounds play for a configurable duration (default 1.5 seconds)
    - If the sound file is shorter than the configured duration, it will be looped/replayed
    - This ensures sirens are always audible for officials and players
    - Pips and other sound types are NOT looped (play once only)
    
    Args:
        filename: str path to sound file
        sound_type: str type of sound ("pips" or "siren")
        enable_sound: bool indicating if sound is enabled
        pips_volume: int/float for pips volume (0-100)
        siren_volume: int/float for siren volume (0-100)
        air_volume: int/float for air channel volume (0-100)
        water_volume: int/float for water channel volume (0-100)
        siren_duration: float for siren duration in seconds (default 1.5)
    """
    # Check if sound is enabled
    if not enable_sound:
        return
        
    if filename == "No sound files found" or filename == "Default":
        print(f"Cannot play '{filename}' - not a valid sound file")
        return
    
    # Get sound-specific volume (already extracted as plain values)
    if sound_type == "pips":
        sound_vol = pips_volume / 100.0
    elif sound_type == "siren":
        sound_vol = siren_volume / 100.0
    else:
        sound_vol = 0.5  # Default 50%
    
    # Use configured siren duration (in seconds)
    MINIMUM_SIREN_DURATION = siren_duration
    
    # Try pygame.mixer first (instant playback from preloaded sounds)
    if PYGAME_AVAILABLE and PYGAME_INITIALIZED and filename in _preloaded_sounds:
        try:
            sound = _preloaded_sounds[filename]
            # Set volume (0.0 to 1.0 range)
            sound.set_volume(sound_vol)
            
            # For siren sounds: ensure minimum 2-second duration by looping if needed
            if sound_type == "siren":
                # Get the actual duration of the sound file
                sound_duration = sound.get_length()
                
                if sound_duration < MINIMUM_SIREN_DURATION:
                    # Calculate how many times to loop to reach minimum duration
                    # Round up to ensure we meet or exceed the minimum
                    import math
                    loop_count = math.ceil(MINIMUM_SIREN_DURATION / sound_duration)
                    
                    # Play the sound with looping (loops parameter is additional plays after first)
                    # So loops=1 means play twice total, loops=2 means play 3 times total
                    sound.play(loops=loop_count - 1)
                    print(f"Played (pygame, looped {loop_count}x): {filename} "
                          f"(Duration: {sound_duration:.2f}s -> {sound_duration * loop_count:.2f}s, "
                          f"{sound_type.title()} Volume: {int(sound_vol*100)}%)")
                else:
                    # Sound is already long enough, play once
                    sound.play()
                    print(f"Played (pygame): {filename} (Duration: {sound_duration:.2f}s, "
                          f"{sound_type.title()} Volume: {int(sound_vol*100)}%)")
            else:
                # For non-siren sounds (pips, etc.), play once only
                sound.play()
                print(f"Played (pygame): {filename} ({sound_type.title()} Volume: {int(sound_vol*100)}%)")
            return
        except Exception as e:
            print(f"pygame playback failed, falling back to subprocess: {e}")
            # Continue to fallback methods below
    
    # Fallback to subprocess-based playback
    try:
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            print(f"Sound Error: Sound file '{filename}' not found")
            return
        
        # Get volume values for Linux channel control (already extracted as plain values)
        air_vol = int(air_volume)
        water_vol = int(water_volume)
        
        # Use configured siren duration (in seconds)
        MINIMUM_SIREN_DURATION = siren_duration
        
        # For fallback systems without duration detection:
        # Estimate short siren files are typically 0.2-0.6 seconds
        # Calculate loop count to reach desired duration
        # (e.g., for 1.5s duration and 0.5s average file: 3 plays × 0.5s = 1.5s)
        siren_loop_count = max(1, int(siren_duration / 0.5)) if sound_type == "siren" else 1
        
        # Windows playback with improved reliability
        if IS_WINDOWS:
            if filename.lower().endswith('.wav'):
                if WINSOUND_AVAILABLE:
                    try:
                        # For siren sounds: loop to ensure configured duration
                        for i in range(siren_loop_count):
                            if i == 0:
                                # First play: Use SND_ASYNC flag for non-blocking
                                winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                            else:
                                # Subsequent plays: Use synchronous to ensure sequential playback
                                # Small delay to ensure previous sound starts
                                import time
                                time.sleep(0.1)
                                winsound.PlaySound(file_path, winsound.SND_FILENAME)
                        
                        loop_msg = f" (looped {siren_loop_count}x for min 2s)" if siren_loop_count > 1 else ""
                        print(f"Successfully played: {filename} ({sound_type.title()} Volume: {int(sound_vol*100)}%){loop_msg}")
                    except Exception as e:
                        print(f"Sound Error: Failed to play WAV file: {e}")
                        # Try synchronous fallback
                        try:
                            for i in range(siren_loop_count):
                                winsound.PlaySound(file_path, winsound.SND_FILENAME)
                                if i < siren_loop_count - 1:
                                    import time
                                    time.sleep(0.1)
                            print(f"Successfully played (sync fallback): {filename}")
                        except Exception as e2:
                            print(f"Sound Error: WAV playback failed completely: {e2}")
                else:
                    print("Sound Error: winsound module not available")
            else:
                # Try playsound for non-WAV files
                if PLAYSOUND_AVAILABLE:
                    try:
                        # For siren sounds: loop to ensure minimum 2-second duration
                        for i in range(siren_loop_count):
                            playsound(file_path)
                        
                        loop_msg = f" (looped {siren_loop_count}x for min 2s)" if siren_loop_count > 1 else ""
                        print(f"Successfully played: {filename} ({sound_type.title()} Volume: {int(sound_vol*100)}%){loop_msg}")
                    except Exception as e:
                        print(f"Sound Error: Failed to play {filename}: {e}")
                else:
                    print("Sound Warning: playsound module not available. Install with: pip install playsound")
            return
        
        # Linux playback with volume control
        if IS_LINUX:
            # Set AIR channel volume (typically left channel - card 0, control 0)
            try:
                subprocess.run(['amixer', '-c', '0', 'sset', 'Left', f'{air_vol}%'], 
                             check=False, capture_output=True)
            except:
                # Fallback - try different control names
                try:
                    subprocess.run(['amixer', 'sset', 'PCM', f'{air_vol}%'], 
                                 check=False, capture_output=True)
                except:
                    pass  # Ignore amixer errors in development environments
            
            # Set WATER channel volume (typically right channel - card 0, control 1)  
            try:
                subprocess.run(['amixer', '-c', '0', 'sset', 'Right', f'{water_vol}%'], 
                             check=False, capture_output=True)
            except:
                # Fallback - try different control names
                try:
                    subprocess.run(['amixer', 'sset', 'Speaker', f'{water_vol}%'], 
                                 check=False, capture_output=True)
                except:
                    pass  # Ignore amixer errors in development environments
                
            # Determine command based on file extension
            # For siren sounds: loop multiple times to ensure configured duration
            if filename.lower().endswith('.wav'):
                # Use aplay for WAV files with volume control if available
                for i in range(siren_loop_count):
                    try:
                        # Try to use aplay with volume control
                        subprocess.Popen(['aplay', '--volume', str(int(sound_vol * 65536)), file_path], 
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except:
                        # Fallback to regular aplay if volume control not supported
                        subprocess.Popen(['aplay', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Add small delay between loops to prevent overlap (only for sirens)
                    if i < siren_loop_count - 1 and siren_loop_count > 1:
                        import time
                        time.sleep(0.5)  # Wait for sound to start/finish before next loop
                        
            elif filename.lower().endswith('.mp3'):
                # Use omxplayer for MP3 files with volume control
                vol_arg = str(int((sound_vol - 1.0) * 2000))  # omxplayer volume range
                for i in range(siren_loop_count):
                    try:
                        subprocess.Popen(['omxplayer', '--no-osd', '--vol', vol_arg, file_path], 
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except:
                        # Fallback to regular omxplayer if volume control not supported
                        subprocess.Popen(['omxplayer', '--no-osd', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    # Add small delay between loops to prevent overlap (only for sirens)
                    if i < siren_loop_count - 1 and siren_loop_count > 1:
                        import time
                        time.sleep(0.5)  # Wait for sound to start/finish before next loop
            else:
                print(f"Sound Error: Unsupported file format: {filename}")
                return
                
            # Show success feedback with volume info
            loop_msg = f" (looped {siren_loop_count}x for min 2s)" if siren_loop_count > 1 else ""
            print(f"Successfully played: {filename} ({sound_type.title()} Volume: {int(sound_vol*100)}%, AIR: {air_vol}%, WATER: {water_vol}%){loop_msg}")
            return
        
        # Unsupported platform
        print(f"Sound Error: Unsupported platform: {platform.system()}")
        
    except subprocess.CalledProcessError as e:
        print(f"Sound Error: Failed to play {filename}. Command failed: {e}")
    except FileNotFoundError:
        # Fallback for development environments without aplay/omxplayer
        loop_msg = f" (looped {siren_loop_count}x for min 2s)" if 'siren_loop_count' in locals() and siren_loop_count > 1 else ""
        print(f"Sound Warning: Audio player not found. Would play: {filename} (With {sound_type} volume: {int(sound_vol*100) if 'sound_vol' in locals() else 50}%, AIR: {air_vol if 'air_vol' in locals() else 50}%, WATER: {water_vol if 'water_vol' in locals() else 50}%){loop_msg}")
    except Exception as e:
        print(f"Sound Error: Unexpected error playing {filename}: {e}")


def play_sound_with_volume(filename, sound_type, enable_sound, pips_volume, siren_volume, 
                           air_volume, water_volume, siren_duration=1.5):
    """
    Play a sound file asynchronously with volume control using threading to prevent UI blocking.
    
    This function immediately returns after spawning a background thread,
    ensuring the timer and UI remain responsive during sound playback.
    
    Cross-platform support:
    - Preferred: Uses pygame.mixer for instant preloaded sound playback (all platforms)
    - Fallback Linux/Raspberry Pi: Uses aplay for .wav, omxplayer for .mp3, amixer for volume
    - Fallback Windows: Uses winsound for .wav, playsound for other formats if available
    
    Args:
        filename: str path to sound file
        sound_type: str type of sound ("pips" or "siren")
        enable_sound: BooleanVar or bool indicating if sound is enabled
        pips_volume: IntVar or int for pips volume (0-100)
        siren_volume: IntVar or int for siren volume (0-100)
        air_volume: IntVar or int for air channel volume (0-100)
        water_volume: IntVar or int for water channel volume (0-100)
        siren_duration: DoubleVar or float for siren duration in seconds (default 1.5)
    """
    # Extract values in main thread to avoid tkinter threading issues
    enable_sound_val = enable_sound.get() if hasattr(enable_sound, 'get') else enable_sound
    pips_volume_val = pips_volume.get() if hasattr(pips_volume, 'get') else pips_volume
    siren_volume_val = siren_volume.get() if hasattr(siren_volume, 'get') else siren_volume
    air_volume_val = air_volume.get() if hasattr(air_volume, 'get') else air_volume
    water_volume_val = water_volume.get() if hasattr(water_volume, 'get') else water_volume
    siren_duration_val = siren_duration.get() if hasattr(siren_duration, 'get') else siren_duration
    
    # Create and start a daemon thread for sound playback
    # Daemon thread ensures the thread doesn't prevent application exit
    sound_thread = threading.Thread(
        target=_play_sound_with_volume_sync,
        args=(filename, sound_type, enable_sound_val, pips_volume_val, siren_volume_val, 
              air_volume_val, water_volume_val, siren_duration_val),
        daemon=True
    )
    sound_thread.start()
