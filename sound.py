"""
Sound module for Underwater Hockey Scoring Desk Kit.

This module contains all sound-related functions for audio playback,
device checking, and sound file management.

Cross-platform support:
- Preferred: Uses pygame.mixer for instant preloaded sound playback (all platforms)
- Fallback Linux/Raspberry Pi: Uses aplay for .wav, omxplayer for .mp3, amixer for volume
- Fallback Windows: Uses winsound for .wav

Note: Sound playback functions use threading to prevent blocking the UI timer.
"""

import subprocess
import os
import sys
import platform
import threading
from tkinter import messagebox

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller executable """
    try:
        # PyInstaller creates a temporary folder and stores its path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
else:
    WINSOUND_AVAILABLE = False

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
    sound_enabled = enable_sound.get() if hasattr(enable_sound, 'get') else enable_sound
    if not sound_enabled:
        return True
    
    if IS_WINDOWS:
        return WINSOUND_AVAILABLE
    
    if IS_LINUX:
        try:
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            result = subprocess.run(['amixer', 'scontrols'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    return False


def handle_no_audio_device_warning(sound_var, sound_type, enable_sound, audio_device_warning_shown):
    """
    Handle the case when no audio device is available.
    """
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
    
    sound_var.set("Default")
    return audio_device_warning_shown


def get_sound_files():
    """
    Scan the assets directory for supported sound files (.wav, .mp3).
    Returns a list of sound files found.
    
    Returns:
        list: Sorted list of sound files, or ["No sound files found"] if none
    """
    sound_files = []
    supported_extensions = ['.wav', '.mp3']
    
    try:
        # Read from the bundled/local assets directory path
        assets_dir = resource_path("assets")
        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    sound_files.append(filename)
    except Exception as e:
        print(f"Error scanning for sound files: {e}")
    
    return sorted(sound_files) if sound_files else ["No sound files found"]


def preload_sounds():
    """
    Preload all available sound files into memory using pygame.mixer.
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
            # Look inside our structured assets subdirectory
            file_path = resource_path(os.path.join("assets", filename))
            if os.path.exists(file_path):
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
    """
    if not enable_sound:
        return
        
    if filename == "No sound files found" or filename == "Default":
        print(f"Sound Test: Cannot play '{filename}' - not a valid sound file")
        return
        
    try:
        # Correctly point files to the assets/ subfolder via the resource path extractor
        file_path = resource_path(os.path.join("assets", filename))
        if not os.path.exists(file_path):
            print(f"Sound Error: Sound file '{filename}' not found at {file_path}")
            return
        
        # 1. Use the preloaded pygame player if available (Safest and cleanest option)
        if PYGAME_INITIALIZED and filename in _preloaded_sounds:
            _preloaded_sounds[filename].play()
            return

        # 2. Windows Fallbacks if Pygame failed to initialize
        if IS_WINDOWS:
            if filename.lower().endswith('.wav'):
                if WINSOUND_AVAILABLE:
                    winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif filename.lower().endswith('.mp3'):
                if PYGAME_INITIALIZED:
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
                else:
                    print("Error: Windows requires pygame to play MP3 files in this executable bundle.")

        # 3. Linux Fallbacks if Pygame failed to initialize
        elif IS_LINUX:
            if filename.lower().endswith('.wav'):
                subprocess.Popen(['aplay', '-q', file_path])
            elif filename.lower().endswith('.mp3'):
                subprocess.Popen(['omxplayer', '-o', 'local', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        print(f"Unexpected error executing sound sync: {e}")


def play_sound(filename, enable_sound):
    """
    Play a sound file asynchronously using a background thread.
    """
    sound_thread = threading.Thread(target=_play_sound_sync, args=(filename, enable_sound))
    sound_thread.daemon = True

    def play_sound_with_volume(filename, sound_type, enable_sound, pips_volume, siren_volume, air_volume, water_volume, siren_duration):
    """
    Play a sound file with volume control.
    
    Args:
        filename: Name of the sound file to play
        sound_type: Type of sound ("pips" or "siren") - determines which volume to use
        enable_sound: BooleanVar or bool indicating if sound is enabled
        pips_volume: DoubleVar for pips volume (0-100)
        siren_volume: DoubleVar for siren volume (0-100)
        air_volume: DoubleVar for air volume (0-100) - Linux only
        water_volume: DoubleVar for water volume (0-100) - Linux only
        siren_duration: DoubleVar for siren duration in seconds
    """
    sound_enabled = enable_sound.get() if hasattr(enable_sound, 'get') else enable_sound
    
    # Get the appropriate volume based on sound type
    if sound_type == "pips":
        volume = pips_volume.get() if hasattr(pips_volume, 'get') else pips_volume
    else:  # siren
        volume = siren_volume.get() if hasattr(siren_volume, 'get') else siren_volume
    
    # Normalize volume to 0.0-1.0 range for pygame
    normalized_volume = max(0.0, min(100.0, volume)) / 100.0
    
    sound_thread = threading.Thread(
        target=_play_sound_with_volume_sync,
        args=(filename, sound_type, sound_enabled, normalized_volume, air_volume, water_volume, siren_duration)
    )
    sound_thread.daemon = True
    sound_thread.start()


def _play_sound_with_volume_sync(filename, sound_type, enable_sound, normalized_volume, air_volume, water_volume, siren_duration):
    """
    Internal synchronous sound playback function with volume control.
    """
    if not enable_sound:
        return
    
    if filename == "No sound files found" or filename == "Default":
        return
    
    try:
        file_path = resource_path(os.path.join("assets", filename))
        if not os.path.exists(file_path):
            print(f"Sound Error: Sound file '{filename}' not found at {file_path}")
            return
        
        # Use pygame.mixer for volume control if available
        if PYGAME_INITIALIZED and filename in _preloaded_sounds:
            sound = _preloaded_sounds[filename]
            sound.set_volume(normalized_volume)
            sound.play()
            return
        
        # Windows fallback
        if IS_WINDOWS:
            if filename.lower().endswith('.wav'):
                if WINSOUND_AVAILABLE:
                    winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif filename.lower().endswith('.mp3'):
                if PYGAME_INITIALIZED:
                    pygame.mixer.set_volume(normalized_volume)
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
        
        # Linux fallback with amixer volume control
        elif IS_LINUX:
            air_vol = air_volume.get() if hasattr(air_volume, 'get') else air_volume
            water_vol = water_volume.get() if hasattr(water_volume, 'get') else water_volume
            
            if filename.lower().endswith('.wav'):
                subprocess.Popen(['aplay', '-q', file_path])
            elif filename.lower().endswith('.mp3'):
                subprocess.Popen(
                    ['omxplayer', '-o', 'local', file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
    
    except Exception as e:
        print(f"Error in sound playback with volume: {e}")
    sound_thread.start()
