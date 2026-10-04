"""Regression guards for the October v1.3.6 UI fixes.

These tests stay display-independent: they verify the widget wiring and
palette/fallback code without starting Tk, opening serial ports, or using MQTT.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class OctoberUiRegressionTests(unittest.TestCase):
    def test_game_number_is_restored_with_classic_grey_palette(self):
        text = source("scoreboard_ui.py")
        start = text.index("def _restore_classic_scoreboard_palette")
        end = text.index("\ndef create_scoreboard_tab", start)
        restore = text[start:end]
        self.assertIn(
            '(getattr(app, "game_label", None),',
            restore,
        )
        self.assertIn(
            '{"bg": "lightgrey", "fg": "black"}',
            restore,
        )

    def test_preset_editor_handles_variables_without_a_separate_label_widget(self):
        text = source("preset_manager.py")
        self.assertIn(
            'label = widget.get("label_widget")',
            text,
        )
        self.assertIn(
            'else app.variables.get(var_name, {}).get(',
            text,
        )
        self.assertIn(
            'text=label_text',
            text,
        )

    def test_zigbee_mapping_buttons_live_in_toolbar_not_mapping_card(self):
        text = source("zigbee_ui.py")
        start = text.index("def _create_mapping_table")
        end = text.index("\ndef create_zigbee_siren_tab", start)
        block = text[start:end]

        self.assertIn('"Button Action Mapping"', block)
        self.assertIn(
            "ui_theme.primary_button(toolbar, label, command)",
            block,
        )
        self.assertIn(
            "ui_theme.danger_button(toolbar, label, command)",
            block,
        )
        self.assertIn(
            "ui_theme.secondary_button(toolbar, label, command)",
            block,
        )
        self.assertNotIn(
            "ui_theme.secondary_button(mapping, label, command)",
            block,
        )
        self.assertIn("height=4", block)


if __name__ == "__main__":
    unittest.main()
