"""Regression tests: explain silent Zigbee button actions without activating them."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]


def controller_class():
    path = ROOT / "zigbee_siren.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in module.body if isinstance(n, ast.ClassDef)
               and n.name == "ZigbeeSirenController")
    wanted = {"_on_message", "_process_button_event"}
    functions = [n for n in cls.body if isinstance(n, ast.FunctionDef)
                 and n.name in wanted]
    assert {n.name for n in functions} == wanted
    isolated = ast.ClassDef(name="Controller", bases=[], keywords=[],
                            body=functions, decorator_list=[])
    top = ast.fix_missing_locations(ast.Module(body=[isolated], type_ignores=[]))
    namespace = {"json": json, "Dict": dict, "Any": object,
                 "ACTION_TO_EVENT": {
        "one_cycle": "PULSE", "two_cycles": "DOUBLE_PULSE"
    }, "queue": __import__("queue")}
    exec(compile(top, str(path), "exec"), namespace)
    return namespace["Controller"]


class UnrecognisedZigbeeButtonTests(unittest.TestCase):
    def setUp(self):
        self.app = controller_class()()
        self.app.config = {
            "siren_button_devices": ["siren_button"],
            "siren_button_device": "siren_button",
            "action_mappings": [
                {"device": "siren_button", "action": "single",
                 "uwh_action": "one_cycle"},
                {"device": "siren_button", "action": "emergency",
                 "uwh_action": "ignore"},
            ],
        }
        self.app.logger = Mock()
        self.app.gui_log_callback = Mock()
        self.app._trigger_siren = Mock()
        self.app.unmapped_actions = __import__("queue").Queue()

    def send(self, device, data):
        self.app._on_message(None, None, SimpleNamespace(
            topic=f"zigbee2mqtt/{device}",
            payload=json.dumps(data).encode("utf-8"),
        ))

    def test_unlisted_button_three_is_logged_but_not_triggered(self):
        self.send("siren_button_3", {"action": "emergency", "linkquality": 123})
        self.app.gui_log_callback.assert_called_once_with(
            "Ignored Zigbee button 'siren_button_3' action 'emergency': "
            "device is not in Button Device Names."
        )
        self.app._trigger_siren.assert_not_called()
        self.assertEqual(
            self.app.unmapped_actions.get_nowait(),
            ("siren_button_3", "emergency"),
        )

    def test_unlisted_sensor_telemetry_does_not_spam_log(self):
        self.send("temperature", {"temperature": 20})
        self.app.gui_log_callback.assert_not_called()

    def test_existing_allowed_button_still_triggers(self):
        self.send("siren_button", {"action": "single"})
        self.app._trigger_siren.assert_called_once_with("PULSE")

    def test_existing_ignored_action_explains_no_sound(self):
        self.send("siren_button", {"action": "emergency"})
        self.app._trigger_siren.assert_not_called()
        self.assertIn("mapped to Ignore", self.app.gui_log_callback.call_args.args[0])

    def test_listed_button_three_with_explicit_mapping_triggers(self):
        self.app.config["siren_button_devices"].append("siren_button_3")
        self.app.config["action_mappings"].append({
            "device": "siren_button_3", "action": "emergency",
            "uwh_action": "one_cycle",
        })
        self.send("siren_button_3", {"action": "emergency"})
        self.app._trigger_siren.assert_called_once_with("PULSE")

    def test_listed_but_unmapped_action_stays_silent(self):
        self.app.config["siren_button_devices"].append("siren_button_3")
        self.send("siren_button_3", {"action": "emergency"})
        self.app._trigger_siren.assert_not_called()
        logs = [x.args[0] for x in self.app.gui_log_callback.call_args_list]
        self.assertTrue(any("Unmapped action" in x for x in logs))


if __name__ == "__main__":
    unittest.main()
