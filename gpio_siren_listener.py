"""Pi 5 wired siren input; worker events are queued, never sent to Tk/audio.

The motherboard supplies the 3.3 V pull-up (R13). Claim only GPIO17 with
bias disabled; locate RP1 by chip label instead of assuming gpiochip0/4.
"""

import os
from pathlib import Path
import sys
import threading
import time

GPIO_PIN = 17  # BCM numbering, physical header pin 11
DEBOUNCE_SECONDS = 0.050
POLL_SECONDS = 0.005


class DebouncedButton:
    """Accept a level only after 50 ms without a sampled change, on both edges."""

    def __init__(self):
        self.pressed = False
        self._candidate = None
        self._since = 0.0

    def update(self, level, now):
        pressed = level == 0
        if pressed != self._candidate:
            self._candidate = pressed
            self._since = now
        if pressed != self.pressed and now - self._since >= DEBOUNCE_SECONDS:
            self.pressed = pressed
            return "GPIO_ON" if pressed else "GPIO_OFF"
        return None


def is_pi5():
    """Do not import GPIO libraries or claim pins on Windows/other computers."""
    if not sys.platform.startswith("linux"):
        return False
    try:
        return Path("/proc/device-tree/model").read_bytes().startswith(b"Raspberry Pi 5")
    except OSError:
        return False


def open_rp1(gpio):
    """Find the header controller across old and new Pi OS chip numbering."""
    failures = []
    for device in sorted(Path("/dev").glob("gpiochip[0-9]*")):
        handle = None
        selected = False
        try:
            handle = gpio.gpiochip_open(int(device.name.removeprefix("gpiochip")))
            status, lines, name, label = gpio.gpio_get_chip_info(handle)
            if status == 0 and label == "pinctrl-rp1" and lines > GPIO_PIN:
                selected = True
                return handle
        except Exception as error:
            failures.append(f"{device}: {error}")
        finally:
            if handle is not None and not selected:
                gpio.gpiochip_close(handle)
    detail = "; ".join(failures) or "no pinctrl-rp1 GPIO chip found"
    raise RuntimeError(detail)


class GPIOSirenListener:
    def __init__(self, callback):
        self.callback = callback
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, daemon=True,
                                            name="gpio17-siren")
            self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self):
        handle = None
        gpio = None
        button = DebouncedButton()
        try:
            # Optional Linux dependency: never required for Windows/USB use.
            import lgpio as gpio
            handle = open_rp1(gpio)
            gpio.gpio_claim_input(handle, GPIO_PIN, gpio.SET_PULL_NONE)
            self.callback("GPIO_STATUS:GPIO17 (physical pin 11) ready; external pull-up, active LOW, 50 ms debounce")
            while not self._stop.is_set():
                level = gpio.gpio_read(handle, GPIO_PIN)
                if level not in (0, 1):
                    raise RuntimeError(f"invalid GPIO level: {level}")
                event = button.update(level, time.monotonic())
                if event is not None:
                    self.callback(event)
                self._stop.wait(POLL_SECONDS)
        except Exception as error:
            self.callback(f"GPIO_STATUS:GPIO17 unavailable: {error}. USB Arduino input remains available.")
        finally:
            # Release only this source, never an Arduino press still in progress.
            self.callback("GPIO_OFF")
            if handle is not None:
                try:
                    gpio.gpiochip_close(handle)
                except Exception as error:
                    self.callback(f"GPIO_STATUS:GPIO17 cleanup failed: {error}")


def start_gpio_listener(app):
    """Start once per app on Pi 5; allow unwired installations to opt out."""
    if not is_pi5() or os.environ.get("UWH_GPIO_SIREN", "1") == "0":
        return None
    listener = getattr(app, "gpio_siren_listener", None)
    if listener is None:
        listener = GPIOSirenListener(app.handle_hardware_siren_event)
        app.gpio_siren_listener = listener
        listener.start()
    return listener
