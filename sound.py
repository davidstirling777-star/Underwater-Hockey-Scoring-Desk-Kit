"""Audio loading, channel playback and the siren's independent safety cutoff.

Ordinary game cues use the configured timed duration, looping short clips
rather than cutting them off at the end of their first sample. Timed wireless
playback also uses pygame's maxtime so an unresponsive Tk event loop cannot
leave it sounding. The Arduino hold-to-sound channel is stopped on release,
not by the timed Zigbee mapping; never conflate these paths. Tk variables
must be read on the UI thread before calling playback from background work.
"""

import subprocess
import os
import sys
import platform
import threading
import math
from tkinter import messagebox

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"


def _describe_linux_audio_properties(properties):
    """Turn PipeWire/ALSA properties into an operator-friendly device name."""
    identifiers = " ".join(
        str(properties.get(key, ""))
        for key in (
            "api.alsa.card.name",
            "api.alsa.card.longname",
            "node.name",
            "node.description",
            "device.description",
        )
    ).lower()
    card_index = str(properties.get("api.alsa.card", "")).strip()
    card_suffix = f" (ALSA card {card_index})" if card_index else ""

    if "hifiberry" in identifiers or "pcm512" in identifiers:
        return f"HiFiBerry DAC+ / compatible I2S DAC{card_suffix}"

    if "hdmi" in identifiers:
        return f"HDMI audio{card_suffix}"

    description = (
        properties.get("node.description")
        or properties.get("device.description")
        or properties.get("api.alsa.card.name")
    )
    if description:
        return f"{description}{card_suffix}"

    return "Linux system default audio output"


def _linux_default_audio_output_description():
    """Report the PipeWire default sink without changing the OS selection."""
    try:
        result = subprocess.run(
            ["wpctl", "inspect", "@DEFAULT_AUDIO_SINK@"],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        OSError,
    ):
        return "Linux system default audio output"

    if result.returncode != 0:
        return "Linux system default audio output"

    properties = {}
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if " = " not in line:
            continue
        key, value = line.split(" = ", 1)
        properties[key.strip()] = value.strip().strip('"')

    return _describe_linux_audio_properties(properties)


def get_audio_output_description():
    """Return the system-default output that pygame selected at startup."""
    if IS_LINUX:
        return _linux_default_audio_output_description()
    if IS_WINDOWS:
        return "Windows system default audio output"
    return f"{platform.system()} system default audio output"


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


# pygame.mixer selects the operating system's default output when it starts.
# Capture the description once so the UI reports the device actually selected
# for this UWH session rather than a default that may be changed afterwards.
AUDIO_OUTPUT_AT_STARTUP = get_audio_output_description()
print(f"Audio output selected at UWH startup: {AUDIO_OUTPUT_AT_STARTUP}")


_preloaded_sounds = {}


def _get_value(value):
    return value.get() if hasattr(value, "get") else value


def normalise_max_siren_duration(value):
    """Return a safe timed-siren cutoff (default 10 s; allowed 1-30 s).

    An invalid or missing saved value must never remove the safety limit.
    Call on the GUI thread if value is a Tkinter variable.
    """
    try:
        seconds = float(str(_get_value(value)).strip().replace(",", "."))
        if math.isfinite(seconds) and 1.0 <= seconds <= 30.0:
            return seconds
    except (TypeError, ValueError, OverflowError):
        pass
    return 10.0


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

def play_timed_sound(
    filename,
    sound_type,
    enable_sound,
    siren_duration,
    max_siren_duration=10.0
):
    """Play a selected pip once or a siren for its configured duration."""
    sound_enabled = _get_value(enable_sound)
    filename = _normalise_filename(filename)

    if not sound_enabled or not _is_valid_sound_selection(filename):
        return

    # Snapshot Tk variables on the UI thread before background playback.
    if sound_type == "siren":
        try:
            duration_seconds = float(_get_value(siren_duration))
        except (TypeError, ValueError):
            duration_seconds = 0.0
        max_duration_seconds = normalise_max_siren_duration(max_siren_duration)
    else:
        duration_seconds = 0.0
        max_duration_seconds = 10.0

    sound_thread = threading.Thread(
        target=_play_timed_sound_sync,
        args=(
            filename,
            sound_type,
            sound_enabled,
            duration_seconds,
            max_duration_seconds,
        ),
        daemon=True,
    )
    sound_thread.start()


def _play_timed_sound_sync(
    filename,
    sound_type,
    enable_sound,
    siren_duration,
    max_siren_duration=10.0
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

        if sound_type == "siren":
            try:
                duration_seconds = float(siren_duration)
            except (TypeError, ValueError):
                duration_seconds = 0.0

            if not math.isfinite(duration_seconds) or duration_seconds <= 0:
                print("Siren playback skipped: duration must be positive.")
                return

            max_duration = normalise_max_siren_duration(max_siren_duration)
            duration_ms = max(
                1, min(30_000, int(min(duration_seconds, max_duration) * 1000))
            )

        if PYGAME_INITIALIZED and filename in _preloaded_sounds:
            sound_obj = _preloaded_sounds[filename]
            # UWH no longer applies its own volume scaling. The operating
            # system / amplifier owns volume, so every app path uses unity.
            sound_obj.set_volume(1.0)

            if sound_type == "siren":
                channel = sound_obj.play(loops=-1, maxtime=duration_ms)
            else:
                channel = sound_obj.play()

            if channel is not None:
                channel.set_volume(1.0)
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
        print(f"Error in timed sound playback: {e}")


def stop_looping_sound(channel):
    """
    Stop a previously started looping sound channel.
    """
    try:
        if channel:
            channel.stop()

    except Exception as e:
        print(f"Error stopping looping sound: {e}")


def start_timed_siren(
    filename, enable_sound, duration_seconds,
    max_siren_duration=10.0
):
    """Play one wireless siren for at most the selected duration.

    Must be called from the Tkinter/UI thread when passed Tk variables.
    Returns the pygame channel so UWH can also stop it immediately.
    The operator-set 10-second default and hard 30-second upper bound
    prevent malformed settings from leaving a siren on indefinitely.
    The Arduino press-and-hold helper is intentionally unchanged.
    """
    import math

    if not _get_value(enable_sound):
        return None

    filename = _normalise_filename(filename)
    if not _is_valid_sound_selection(filename):
        return None

    try:
        seconds = float(_get_value(duration_seconds))
        if not math.isfinite(seconds) or seconds <= 0:
            print("Wireless siren not started: duration must be a positive number.")
            return None
        duration_ms = max(
            1, min(30_000, int(min(
                seconds, normalise_max_siren_duration(max_siren_duration)
            ) * 1000))
        )

        if not PYGAME_INITIALIZED or filename not in _preloaded_sounds:
            print("Wireless siren requires pygame.mixer and a preloaded sound.")
            return None

        sound_obj = _preloaded_sounds[filename]
        sound_obj.set_volume(1.0)
        # maxtime independently stops this sound even if Tk's event loop stalls.
        channel = sound_obj.play(loops=-1, maxtime=duration_ms)
        if channel is not None:
            channel.set_volume(1.0)
        return channel
    except Exception as e:
        print(f"Error starting timed wireless siren: {e}")
        return None
