"""Headless regressions for the Arduino serial button and its siren outputs."""
import ast
from pathlib import Path
from types import SimpleNamespace
import os
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def methods(path, names, globals_dict, owner=None):
    source = ROOT / path
    tree = ast.parse(source.read_text(encoding="utf-8"))
    if owner is None:
        candidates = tree.body
    else:
        candidates = next(n.body for n in tree.body if
                          isinstance(n, ast.ClassDef) and n.name == owner)
    selected = [n for n in candidates if isinstance(n, ast.FunctionDef)
                and n.name in names]
    if {n.name for n in selected} != set(names):
        raise AssertionError(f"Missing methods: {path} / {names}")
    if owner:
        selected = [ast.ClassDef(name=owner, bases=[], keywords=[],
                                 body=selected, decorator_list=[])]
    m = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(m, str(source), "exec"), globals_dict)
    return globals_dict[owner] if owner else globals_dict


class Variable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeChannel:
    def set_volume(self, val):
        self.volume = val


class FakeSound:
    def __init__(self):
        self.volume = None
        self.play = Mock(return_value=FakeChannel())

    def set_volume(self, val):
        self.volume = val


class ArduinoRoutingTests(unittest.TestCase):
    def setUp(self):
        self.clip = FakeSound()
        self.stop = Mock()
        self.log = Mock()
        audio = SimpleNamespace(
            _preloaded_sounds={"siren.mp3": self.clip},
            stop_looping_sound=self.stop,
            normalise_trim_percent=lambda value: max(
                0.0, min(100.0, float(value))
            ),
        )
        self.controller_type = methods(
            "zigbee_siren.py", {"handle_hardware_siren_event"}, {},
            "ZigbeeSirenController"
        )
        app_type = methods("uwh.py",
                           {"_process_hardware_siren_event",
                            "_stop_arduino_siren"},
                           {"sound": audio, "print": self.log},
                           "GameManagementApp")
        self.controller = self.controller_type()
        self.controller.start_siren_continuous = Mock()
        self.controller.stop_siren_continuous = Mock()
        self.app = app_type()
        self.app.zigbee_controller = self.controller
        self.app.siren_var = Variable("siren.mp3")
        self.app.enable_sound = Variable(True)
        self.app.get_sound_trim = lambda filename: 60
        self.app.arduino_siren_channel = None
        self.app.add_to_zigbee_log = Mock()

    def test_press_starts_local_and_mqtt_siren(self):
        self.app._process_hardware_siren_event("ON")
        self.clip.play.assert_called_once_with(loops=-1)
        self.assertEqual(self.clip.volume, 0.6)
        self.controller.start_siren_continuous.assert_called_once_with()
        self.app.add_to_zigbee_log.assert_called_with(
            "Arduino button: SIREN_ON received"
        )

    def test_release_stops_local_and_mqtt_siren(self):
        self.app._process_hardware_siren_event("ON")
        self.app._process_hardware_siren_event("OFF")
        self.assertEqual(
            [call.args for call in self.stop.call_args_list],
            [(None,), (self.clip.play.return_value,)],
        )
        self.controller.stop_siren_continuous.assert_called_once_with()
        self.app.add_to_zigbee_log.assert_called_with(
            "Arduino button: SIREN_OFF received"
        )

    def test_muting_pc_audio_does_not_block_mqtt_button(self):
        self.app.enable_sound = Variable(False)
        self.app._process_hardware_siren_event("ON")
        self.clip.play.assert_not_called()
        self.controller.start_siren_continuous.assert_called_once_with()
        self.app._process_hardware_siren_event("OFF")
        self.controller.stop_siren_continuous.assert_called_once_with()

    def test_missing_local_sound_still_triggers_mqtt(self):
        self.app.siren_var = Variable("not preloaded")
        self.app._process_hardware_siren_event("ON")
        self.controller.start_siren_continuous.assert_called_once_with()
        self.assertTrue(any("not preloaded" in str(c)
                            for c in self.log.call_args_list))

    def test_local_playback_failure_does_not_block_mqtt(self):
        self.clip.play.side_effect = RuntimeError("audio unavailable")
        self.app._process_hardware_siren_event("ON")
        self.controller.start_siren_continuous.assert_called_once_with()
        self.assertTrue(any("audio unavailable" in str(c)
                            for c in self.log.call_args_list))

    def test_mqtt_error_is_logged_and_release_still_attempts(self):
        self.controller.start_siren_continuous.side_effect = ValueError("broker down")
        self.app._process_hardware_siren_event("ON")
        self.assertTrue(any("broker down" in str(c)
                            for c in self.log.call_args_list))
        self.app._process_hardware_siren_event("OFF")
        self.controller.stop_siren_continuous.assert_called_once_with()

    def test_unknown_event_does_not_start_siren(self):
        self.app._process_hardware_siren_event("bogus")
        self.clip.play.assert_not_called()
        self.controller.start_siren_continuous.assert_not_called()

    def test_serial_open_status_reaches_gui_log(self):
        self.app._process_hardware_siren_event("ARDUINO_SERIAL_OPEN:COM3")
        self.app.add_to_zigbee_log.assert_called_once_with(
            "Arduino siren serial listener opened COM3 (9600 baud)"
        )
        self.clip.play.assert_not_called()
        self.controller.start_siren_continuous.assert_not_called()

    def test_serial_open_failure_reaches_gui_log(self):
        self.app._process_hardware_siren_event(
            "ARDUINO_SERIAL_ERROR:COM3: access denied"
        )
        self.app.add_to_zigbee_log.assert_called_once_with(
            "Arduino siren serial listener error: COM3: access denied"
        )
        self.clip.play.assert_not_called()

    def test_method_is_part_of_mqtt_controller_class(self):
        tree = ast.parse((ROOT / "zigbee_siren.py").read_text(encoding="utf-8"))
        top = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
        self.assertNotIn("handle_hardware_siren_event", top)
        self.assertTrue(callable(self.controller.handle_hardware_siren_event))


class SerialPortTests(unittest.TestCase):
    def setUp(self):
        self.fake_port = lambda device, description, hwid: SimpleNamespace(
            device=device, description=description, hwid=hwid
        )
        self.mock = SimpleNamespace()
        self.names = methods(
            "serial_siren_listener.py",
            {"_settings_path", "_is_zigbee_port", "_is_arduino_port",
             "detect_hardware_ports", "_port_exists"},
            {"os": os, "SETTINGS_FILE": "settings.json",
             "__file__": str(ROOT / "serial_siren_listener.py"),
             "sys": SimpleNamespace(frozen=False),
             "_detected_ports": {"arduino_port": None, "zigbee_port": None},
             "load_hardware_ports_from_json": lambda: (None, None),
             "save_hardware_ports_to_json": Mock(), "_debug": Mock()},
        )

    def test_zigbee_generic_usb_serial_is_not_arduino(self):
        p = self.fake_port("COM7", "Silicon Labs USB-Serial", "USB VID:PID=10C4:EA60")
        self.assertTrue(self.names["_is_zigbee_port"](p))
        self.assertFalse(self.names["_is_arduino_port"](p))

    def test_arduino_still_recognised(self):
        p = self.fake_port("COM3", "Arduino Nano Every", "USB VID:PID=2341:0058")
        self.assertTrue(self.names["_is_arduino_port"](p))
        self.assertFalse(self.names["_is_zigbee_port"](p))

    def test_serial_settings_path_is_independent_of_cwd(self):
        path = self.names["_settings_path"]()
        self.assertEqual(
            Path(path).parent,
            ROOT,
        )

    def test_port_classification_separates_arduino_and_zigbee(self):
        ports = [
            self.fake_port("COM7", "Silicon Labs USB-Serial", "10C4:EA60"),
            self.fake_port("COM3", "Arduino Nano Every", "2341:0058"),
        ]
        self.names["serial"] = SimpleNamespace(
            tools=SimpleNamespace(
                list_ports=SimpleNamespace(comports=lambda: ports)
            )
        )
        self.names["save_hardware_ports_to_json"] = Mock()
        found = self.names["detect_hardware_ports"]()
        self.assertEqual(found, ("COM3", "COM7"))
        self.names["save_hardware_ports_to_json"].assert_called_once_with(
            "COM3", "COM7"
        )


if __name__ == "__main__":
    unittest.main()
