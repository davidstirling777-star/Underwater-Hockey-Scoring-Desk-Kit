"""
Sound module for Underwater Hockey Scoring Desk Kit.

This module contains all sound-related functions for audio playback,
device checking, and sound file management.

Cross-platform support:
- Linux/Raspberry Pi: Uses aplay for .wav, omxplayer for .mp3, amixer for volume
- Windows: Uses winsound for .wav, playsound for other formats if available
"""

import subprocess
import os
import platform
import threading
from tkinter import messagebox

# Platform detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

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


def play_sound(filename, enable_sound):
    """
    Play a sound file using the appropriate system command.
    
    Cross-platform support:
    - Linux: Uses aplay for WAV files and omxplayer for MP3 files (Raspberry Pi compatible)
    - Windows: Uses winsound for WAV files, playsound for other formats if available
    
    Args:
        filename: str path to sound file
        enable_sound: BooleanVar or bool indicating if sound is enabled
    """
    # Check if sound is enabled
    sound_enabled = enable_sound.get() if hasattr(enable_sound, 'get') else enable_sound
    if not sound_enabled:
        return
        
    if filename == "No sound files found" or filename == "Default":
        messagebox.showinfo("Sound Test", f"Cannot play '{filename}' - not a valid sound file")
        return
        
    try:
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            messagebox.showerror("Sound Error", f"Sound file '{filename}' not found")
            return
        
        # Windows playback
        if IS_WINDOWS:
            if filename.lower().endswith('.wav'):
                if WINSOUND_AVAILABLE:
                    winsound.PlaySound(file_path, winsound.SND_FILENAME)
                    messagebox.showinfo("Sound Test", f"Successfully played: {filename}")
                else:
                    messagebox.showerror("Sound Error", "winsound module not available")
            else:
                # Try playsound for non-WAV files
                if PLAYSOUND_AVAILABLE:
                    playsound(file_path)
                    messagebox.showinfo("Sound Test", f"Successfully played: {filename}")
                else:
                    messagebox.showwarning("Sound Warning", 
                        f"playsound module not available. Install with: pip install playsound")
            return
            
        # Linux playback
        if IS_LINUX:
            # Determine command based on file extension
            if filename.lower().endswith('.wav'):
                # Use aplay for WAV files (works well on Raspberry Pi with DigiAMP+ HAT)
                subprocess.run(['aplay', file_path], check=True, capture_output=True)
            elif filename.lower().endswith('.mp3'):
                # Use omxplayer for MP3 files (Raspberry Pi optimized)
                subprocess.run(['omxplayer', '--no-osd', file_path], check=True, capture_output=True)
            else:
                messagebox.showerror("Sound Error", f"Unsupported file format: {filename}")
                return
                
            # Show success feedback
            messagebox.showinfo("Sound Test", f"Successfully played: {filename}")
            return
        
        # Unsupported platform
        messagebox.showerror("Sound Error", f"Unsupported platform: {platform.system()}")
        
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Sound Error", f"Failed to play {filename}. Command failed: {e}")
    except FileNotFoundError:
        # Fallback for development environments without aplay/omxplayer
        messagebox.showwarning("Sound Warning", f"Audio player not found. Would play: {filename}")
    except Exception as e:
        messagebox.showerror("Sound Error", f"Unexpected error playing {filename}: {e}")


def _play_sound_thread(file_path, filename, sound_type, sound_vol):
    """
    Internal function to play sound in a background thread on Windows.
    This ensures reliable playback and prevents UI blocking.
    
    Args:
        file_path: str absolute path to sound file
        filename: str filename for logging
        sound_type: str type of sound ("pips" or "siren")
        sound_vol: float sound volume (0.0-1.0)
    """
    try:
        if filename.lower().endswith('.wav'):
            if WINSOUND_AVAILABLE:
                # Use SND_ASYNC flag for non-blocking playback
                winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                print(f"Successfully played: {filename} ({sound_type.title()} Volume: {int(sound_vol*100)}%)")
            else:
                print("Sound Error: winsound module not available")
        else:
            # Try playsound for non-WAV files
            if PLAYSOUND_AVAILABLE:
                playsound(file_path)
                print(f"Successfully played: {filename} ({sound_type.title()} Volume: {int(sound_vol*100)}%)")
            else:
                print("Sound Warning: playsound module not available. Install with: pip install playsound")
    except Exception as e:
        print(f"Sound Error in playback thread: {e}")


def play_sound_with_volume(filename, sound_type, enable_sound, pips_volume, siren_volume, 
                           air_volume, water_volume):
    """
    Play a sound file with volume control using amixer for channel volumes and sound-specific volume.
    
    Cross-platform support:
    - Linux: Uses aplay for WAV files and omxplayer for MP3 files (Raspberry Pi compatible)
      with amixer for volume control
    - Windows: Uses winsound for WAV files with threading for reliable playback,
      playsound for other formats if available
    
    Args:
        filename: str path to sound file
        sound_type: str type of sound ("pips" or "siren")
        enable_sound: BooleanVar or bool indicating if sound is enabled
        pips_volume: IntVar or int for pips volume (0-100)
        siren_volume: IntVar or int for siren volume (0-100)
        air_volume: IntVar or int for air channel volume (0-100)
        water_volume: IntVar or int for water channel volume (0-100)
    """
    # Check if sound is enabled
    sound_enabled = enable_sound.get() if hasattr(enable_sound, 'get') else enable_sound
    if not sound_enabled:
        return
        
    if filename == "No sound files found" or filename == "Default":
        print(f"Cannot play '{filename}' - not a valid sound file")
        return
        
    try:
        file_path = os.path.join(os.getcwd(), filename)
        if not os.path.exists(file_path):
            print(f"Sound Error: Sound file '{filename}' not found")
            return
        
        # Get volume values
        air_vol = int(air_volume.get() if hasattr(air_volume, 'get') else air_volume)
        water_vol = int(water_volume.get() if hasattr(water_volume, 'get') else water_volume)
        
        # Get sound-specific volume
        if sound_type == "pips":
            sound_vol = (pips_volume.get() if hasattr(pips_volume, 'get') else pips_volume) / 100.0
        elif sound_type == "siren":
            sound_vol = (siren_volume.get() if hasattr(siren_volume, 'get') else siren_volume) / 100.0
        else:
            sound_vol = 0.5  # Default 50%
        
        # Windows playback with threading for reliability
        if IS_WINDOWS:
            # Run sound playback in background thread to prevent blocking and ensure reliability
            playback_thread = threading.Thread(
                target=_play_sound_thread,
                args=(file_path, filename, sound_type, sound_vol),
                daemon=True
            )
            playback_thread.start()
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
            if filename.lower().endswith('.wav'):
                # Use aplay for WAV files with volume control if available
                try:
                    # Try to use aplay with volume control
                    subprocess.run(['aplay', '--volume', str(int(sound_vol * 65536)), file_path], 
                                 check=True, capture_output=True)
                except:
                    # Fallback to regular aplay if volume control not supported
                    subprocess.run(['aplay', file_path], check=True, capture_output=True)
            elif filename.lower().endswith('.mp3'):
                # Use omxplayer for MP3 files with volume control
                vol_arg = str(int((sound_vol - 1.0) * 2000))  # omxplayer volume range
                try:
                    subprocess.run(['omxplayer', '--no-osd', '--vol', vol_arg, file_path], 
                                 check=True, capture_output=True)
                except:
                    # Fallback to regular omxplayer if volume control not supported
                    subprocess.run(['omxplayer', '--no-osd', file_path], check=True, capture_output=True)
            else:
                print(f"Sound Error: Unsupported file format: {filename}")
                return
                
            # Show success feedback with volume info
            print(f"Successfully played: {filename} ({sound_type.title()} Volume: {int(sound_vol*100)}%, AIR: {air_vol}%, WATER: {water_vol}%)")
            return
        
        # Unsupported platform
        print(f"Sound Error: Unsupported platform: {platform.system()}")
        
    except subprocess.CalledProcessError as e:
        print(f"Sound Error: Failed to play {filename}. Command failed: {e}")
    except FileNotFoundError:
        # Fallback for development environments without aplay/omxplayer
        print(f"Sound Warning: Audio player not found. Would play: {filename} (With {sound_type} volume: {int(sound_vol*100) if 'sound_vol' in locals() else 50}%, AIR: {air_vol}%, WATER: {water_vol}%)")
    except Exception as e:
        print(f"Sound Error: Unexpected error playing {filename}: {e}")
