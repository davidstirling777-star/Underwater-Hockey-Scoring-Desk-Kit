"""
Sound module for Underwater Hockey Scoring Desk Kit.
"""

import subprocess
import os
import sys
import platform
import threading
from tkinter import messagebox

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


try:
    import pygame.mixer

    PYGAME_AVAILABLE = True

    try:
        pygame.mixer.init(
            frequency=22050,
            size=-16,
            channels=2,
            buffer=512
        )
        PYGAME_INITIALIZED = True

    except Exception as e:
        print(f"Warning: pygame.mixer initialization failed: {e}")
        PYGAME_INITIALIZED = False

except ImportError:
    PYGAME_AVAILABLE = False
    PYGAME_INITIALIZED = False
    print("Warning: pygame not available. Falling back to subprocess sound playback.")


if IS_WINDOWS:
    try:
        import winsound
        WINSOUND_AVAILABLE = True
    except ImportError:
        WINSOUND_AVAILABLE = False
else:
    WINSOUND_AVAILABLE = False


_preloaded_sounds = {}


def _get_value(value):
    return value.get() if hasattr(value, "get") else value


def _normalise_volume(volume):
    """Convert a 0-100 value to pygame's 0.0-1.0 range."""
    try:
        numeric_volume = float(_get_value(volume))
    except (TypeError, ValueError):
        numeric_volume = 0.0

    return max(0.0, min(100.0, numeric_volume)) / 100.0


def _normalise_filename(filename):
    """Return a stripped filename string, or an empty string."""
    return str(filename).strip() if filename is not None else ""


def _is_valid_sound_selection(filename):
    """
    Return True only for an actual selected sound filename.

    An empty selection means "do not play". "Default" is still ignored
    for compatibility with older saved settings.
    """
    filename = _normalise_filename(filename)

    return (
        bool(filename)
        and filename.lower()
        not in {"default", "no sound files found"}
    )


def check_audio_device_available(enable_sound):
    sound_enabled = _get_value(enable_sound)

    if not sound_enabled:
        return True

    if IS_WINDOWS:
        return WINSOUND_AVAILABLE or PYGAME_INITIALIZED

    if IS_LINUX:
        try:
            result = subprocess.run(
                ["aplay", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                return True

        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError
        ):
            pass

        try:
            result = subprocess.run(
                ["amixer", "scontrols"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout.strip():
                return True

        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError
        ):
            pass

    return False


def handle_no_audio_device_warning(
    sound_var,
    sound_type,
    enable_sound,
    audio_device_warning_shown
):
    """Warn once when no audio device is available and clear selection."""
    sound_enabled = (
        enable_sound.get()
        if hasattr(enable_sound, "get")
        else enable_sound
    )

    if not sound_enabled:
        return audio_device_warning_shown

    if not audio_device_warning_shown:
        messagebox.showwarning(
            "Audio Device Warning",
            f"No audio device detected. Cannot play "
            f"{sound_type} sounds.\n\n"
            f"The sound selection has been cleared."
        )
        audio_device_warning_shown = True

    sound_var.set("")
    return audio_device_warning_shown

def get_sound_files():
    sound_files = []
    supported_extensions = [".wav", ".mp3"]

    try:
        assets_dir = resource_path("assets")

        if os.path.exists(assets_dir):
            for filename in os.listdir(assets_dir):
                file_path = os.path.join(assets_dir, filename)

                if (
                    os.path.isfile(file_path)
                    and any(
                        filename.lower().endswith(ext)
                        for ext in supported_extensions
                    )
                ):
                    sound_files.append(filename)

    except Exception as e:
        print(f"Error scanning for sound files: {e}")

    return sorted(sound_files) if sound_files else ["No sound files found"]


def preload_sounds():
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
            file_path = resource_path(os.path.join("assets", filename))

            if os.path.exists(file_path):
                sound_obj = pygame.mixer.Sound(file_path)
                _preloaded_sounds[filename] = sound_obj
                loaded_count += 1
                print(f"Preloaded sound: {filename}")

        except Exception as e:
            print(f"Warning: Failed to preload {filename}: {e}")

    print(f"Successfully preloaded {loaded_count} sound files")
    return loaded_count


def _play_sound_sync(filename, enable_sound):
    """Play a sound once without changing volume."""
    if not enable_sound:
        return

    filename = _normalise_filename(filename)

    if not _is_valid_sound_selection(filename):
        print(f"Sound Test: Cannot play '{filename}' - not a valid sound file")
        return

    try:
        file_path = resource_path(os.path.join("assets", filename))

        if not os.path.exists(file_path):
            print(
                f"Sound Error: Sound file '{filename}' "
                f"not found at {file_path}"
            )
            return

        if PYGAME_INITIALIZED and filename in _preloaded_sounds:
            _preloaded_sounds[filename].play()
            return

        if IS_WINDOWS:
            if filename.lower().endswith(".wav") and WINSOUND_AVAILABLE:
                winsound.PlaySound(
                    file_path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )
            elif filename.lower().endswith(".mp3"):
                print("Error: Windows requires pygame to play MP3 files.")

        elif IS_LINUX:
            if filename.lower().endswith(".wav"):
                subprocess.Popen(["aplay", "-q", file_path])
            elif filename.lower().endswith(".mp3"):
                subprocess.Popen(
                    ["omxplayer", "-o", "local", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

    except Exception as e:
        print(f"Unexpected error executing sound sync: {e}")

def play_sound(filename, enable_sound):
    """Play a sound once in a background thread."""
    sound_enabled = _get_value(enable_sound)
    filename = _normalise_filename(filename)

    if not sound_enabled or not _is_valid_sound_selection(filename):
        return

    sound_thread = threading.Thread(
        target=_play_sound_sync,
        args=(filename, sound_enabled),
        daemon=True
    )
    sound_thread.start()

def play_sound_with_volume(
    filename,
    sound_type,
    enable_sound,
    pips_volume,
    siren_volume,
    air_volume,
    water_volume,
    siren_duration
):
    """Play a selected pip or siren sound in a background thread."""
    sound_enabled = _get_value(enable_sound)
    filename = _normalise_filename(filename)

    if not sound_enabled or not _is_valid_sound_selection(filename):
        return

    if sound_type == "pips":
        volume = _get_value(pips_volume)
    else:
        volume = _get_value(siren_volume)

    normalized_volume = _normalise_volume(volume)

    sound_thread = threading.Thread(
        target=_play_sound_with_volume_sync,
        args=(
            filename,
            sound_type,
            sound_enabled,
            normalized_volume,
            air_volume,
            water_volume,
            siren_duration
        ),
        daemon=True
    )
    sound_thread.start()

def _play_sound_with_volume_sync(
    filename,
    sound_type,
    enable_sound,
    normalized_volume,
    air_volume,
    water_volume,
    siren_duration
):
    """Play a pip once or a siren for the configured duration."""
    if not enable_sound:
        return

    filename = _normalise_filename(filename)

    if not _is_valid_sound_selection(filename):
        return

    try:
        file_path = resource_path(os.path.join("assets", filename))

        if not os.path.exists(file_path):
            print(
                f"Sound Error: Sound file '{filename}' "
                f"not found at {file_path}"
            )
            return

        try:
            duration_seconds = float(_get_value(siren_duration))
        except (TypeError, ValueError):
            duration_seconds = 0.0

        if PYGAME_INITIALIZED and filename in _preloaded_sounds:
            sound_obj = _preloaded_sounds[filename]
            sound_obj.set_volume(normalized_volume)

            if sound_type == "siren" and duration_seconds > 0:
                sound_length_ms = int(sound_obj.get_length() * 1000)

                if sound_length_ms > 0:
                    duration_ms = int(duration_seconds * 1000)
                    loops = max(0, (duration_ms // sound_length_ms) - 1)
                    sound_obj.play(loops=loops)
                else:
                    sound_obj.play()
            else:
                sound_obj.play()

            return

        if IS_WINDOWS:
            if filename.lower().endswith(".wav") and WINSOUND_AVAILABLE:
                winsound.PlaySound(
                    file_path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )
            elif filename.lower().endswith(".mp3"):
                print("Error: Windows requires pygame to play MP3 files.")

        elif IS_LINUX:
            if filename.lower().endswith(".wav"):
                subprocess.Popen(["aplay", "-q", file_path])
            elif filename.lower().endswith(".mp3"):
                subprocess.Popen(
                    ["omxplayer", "-o", "local", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

    except Exception as e:
        print(f"Error in sound playback with volume: {e}")

def start_looping_sound_with_volume(
    filename,
    sound_type,
    enable_sound,
    pips_volume,
    siren_volume
):
    """
    Start a looping sound and return the pygame Channel object.

    Used for Arduino press-and-hold siren playback.
    The caller is responsible for storing the returned channel and
    stopping it with stop_looping_sound().
    """
    sound_enabled = _get_value(enable_sound)
    filename = _normalise_filename(filename)

    if not sound_enabled or not _is_valid_sound_selection(filename):
        return None

    if sound_type == "pips":
        volume = _get_value(pips_volume)
    else:
        volume = _get_value(siren_volume)

    normalized_volume = _normalise_volume(volume)

    try:
        file_path = resource_path(os.path.join("assets", filename))

        if not os.path.exists(file_path):
            print(
                f"Sound Error: Sound file '{filename}' "
                f"not found at {file_path}"
            )
            return None

        if PYGAME_INITIALIZED and filename in _preloaded_sounds:
            sound_obj = _preloaded_sounds[filename]
            sound_obj.set_volume(normalized_volume)

            channel = sound_obj.play(loops=-1)

            if channel:
                channel.set_volume(normalized_volume)

            return channel

        print("Looping sound requires pygame.mixer and a preloaded sound.")
        return None

    except Exception as e:
        print(f"Error starting looping sound: {e}")
        return None

def stop_looping_sound(channel):
    """
    Stop a previously started looping sound channel.
    """
    try:
        if channel:
            channel.stop()

    except Exception as e:
        print(f"Error stopping looping sound: {e}")
