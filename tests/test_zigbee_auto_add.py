"""Regression tests for safe Zigbee Auto-add From Log discovery."""

from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import zigbee_ui


class FakeEntry:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def delete(self, _start, _end):
        self.value = ""

    def insert(self, _index, value):
        self.value = value


class ZigbeeAutoAddTests(unittest.TestCase):
    def test_unlisted_observed_button_is_added_as_safe_ignore(self):
        entry = FakeEntry("siren_button")
        app = SimpleNamespace(
            config_widgets={"siren_button_devices": entry},
            zigbee_controller=SimpleNamespace(
                consume_unmapped_actions=lambda: [
                    ("siren_button_2", "single")
                ]
            ),
            _zigbee_action_mappings_draft=[],
            add_to_zigbee_log=Mock(),
            master=None,
        )

        with patch.object(zigbee_ui, "_draw_action_mappings") as draw, \
             patch.object(zigbee_ui, "_mark_mappings_dirty") as dirty:
            zigbee_ui._auto_add_from_log(app)

        self.assertEqual(
            entry.get(),
            "siren_button, siren_button_2",
        )
        self.assertEqual(
            app._zigbee_action_mappings_draft,
            [{
                "device": "siren_button_2",
                "action": "single",
                "uwh_action": "ignore",
                "notes": "Discovered from MQTT log",
            }],
        )
        draw.assert_called_once_with(app)
        dirty.assert_called_once_with(app)
        self.assertIn(
            "new button name",
            app.add_to_zigbee_log.call_args.args[0],
        )

    def test_save_action_mappings_persists_auto_added_device_name(self):
        entry = FakeEntry("siren_button, siren_button_2")
        settings = {
            "zigbeeSettings": {
                "mqtt_broker": "localhost",
            }
        }
        saved = {}
        controller = SimpleNamespace(config={})
        app = SimpleNamespace(
            config_widgets={"siren_button_devices": entry},
            _zigbee_action_mappings_draft=[{
                "device": "siren_button_2",
                "action": "single",
                "uwh_action": "one_cycle",
                "notes": "Discovered from MQTT log",
            }],
            load_unified_settings=lambda: settings,
            save_unified_settings=lambda value: saved.update(value),
            zigbee_controller=controller,
            _zigbee_mapping_save_btn=Mock(),
            add_to_zigbee_log=Mock(),
            master=None,
        )

        with patch.object(zigbee_ui.messagebox, "showinfo"):
            zigbee_ui.save_action_mappings(app)

        zigbee = saved["zigbeeSettings"]
        self.assertEqual(
            zigbee["siren_button_devices"],
            ["siren_button", "siren_button_2"],
        )
        self.assertEqual(
            zigbee["siren_button_device"],
            "siren_button",
        )
        self.assertEqual(
            zigbee["action_mappings"][0]["uwh_action"],
            "one_cycle",
        )
        self.assertEqual(
            controller.config["siren_button_devices"],
            ["siren_button", "siren_button_2"],
        )


if __name__ == "__main__":
    unittest.main()
