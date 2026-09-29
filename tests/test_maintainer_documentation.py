"""Guard the maintainer notes and operator-facing explanations from drifting.

These tests read source/docs without creating Tk windows, opening COM ports or
using a live tournament CSV. They intentionally assert labels and invariants,
not the incidental line numbers or widget geometry.
"""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class MaintenanceDocumentationTests(unittest.TestCase):
    def test_every_runtime_python_module_has_a_maintainer_docstring(self):
        modules = (
            "uwh.py", "game_engine.py", "game_flow.py", "game_logging.py",
            "csv_helpers.py", "csv_export.py", "csv_ui.py",
            "tournament_files.py", "tournament_sync.py",
            "tournament_results_server.py",
            "game_settings_manager.py", "settings_manager.py",
            "settings_ui.py", "scoreboard_ui.py", "display_ui.py",
            "display_manager.py", "ui_scaling.py", "penalties_ui.py",
            "preset_manager.py", "sounds_ui.py", "sound.py",
            "startup_selftest.py", "zigbee_siren.py", "zigbee_ui.py",
            "zigbee_control.py", "zigbee_hardware_ui.py",
            "serial_siren_listener.py", "hardware_detection.py",
        )
        for module in modules:
            with self.subTest(module=module):
                self.assertIsNotNone(
                    ast.get_docstring(ast.parse(source(module))),
                    f"Missing maintainer module docstring: {module}",
                )

    def test_module_map_names_current_critical_files(self):
        guide = source("MAINTAINERS.md")
        for filename in (
            "uwh.py", "game_engine.py", "game_flow.py", "csv_export.py",
            "settings_manager.py", "display_ui.py", "zigbee_siren.py",
            "serial_siren_listener.py", "startup_selftest.py",
        ):
            with self.subTest(filename=filename):
                self.assertIn(filename, guide)

    def test_maintainer_guide_preserves_three_key_safety_distinctions(self):
        guide = source("MAINTAINERS.md")
        self.assertIn("export-before-reset", guide)
        self.assertIn("Port detection", guide)
        self.assertIn("Auto-add From Log", guide)
        self.assertIn("five most recent", guide)

    def test_readme_reports_up_to_three_tested_working_buttons(self):
        readme = source("README.md")
        self.assertIn("**up to three working Zigbee buttons**", readme)
        self.assertIn(
            "siren_button, siren_button_2, siren_button_3",
            readme,
        )
        self.assertIn("not universal button behaviours", readme)
        self.assertNotIn("### Two paired buttons", readme)

    def test_zigbee_guide_reports_up_to_three_tested_working_buttons(self):
        guide = source("ZIGBEE_SETUP.md")
        self.assertIn("**up to three working Zigbee buttons**", guide)
        self.assertIn(
            '"siren_button_2", "siren_button_3"',
            guide,
        )
        self.assertIn("individual buttons may publish different actions", guide)

    def test_readme_settings_and_preset_instructions_match_current_code(self):
        readme = source("README.md")
        self.assertIn("for **three seconds**", readme)
        self.assertIn("in **seconds**", readme)
        self.assertIn("queues the closed state", readme)
        self.assertIn("or on normal program exit", readme)
        self.assertIn("Maximum Siren Duration (seconds)", readme)
        self.assertIn("both `9:36` and `09:36` mean 09:36", readme)
        self.assertNotIn("use the two-digit form until", readme)

    def test_zigbee_guide_explains_mapping_and_auto_add_safety(self):
        guide = source("ZIGBEE_SETUP.md")
        self.assertIn("**Auto-add From Log**", guide)
        self.assertIn("**Ignore**", guide)
        self.assertIn("**Save Action Mappings**", guide)
        self.assertIn("**Save Configuration**", guide)
        self.assertIn("up to five recent", guide)
        self.assertIn("**Detected** ports", guide)
        self.assertIn("`emergency`", guide)

    def test_tournament_help_names_the_actual_required_score_columns(self):
        text = source("settings_ui.py")
        self.assertIn(
            "Expected CSV headers: date,#,White,WScore,Black,BScore,",
            text,
        )
        self.assertNotIn(
            "date,#,White,Score,Black,Score,",
            text,
        )

    def test_preset_help_matches_the_three_second_editor_threshold(self):
        self.assertIn(
            "Press and hold a preset for 3 seconds",
            source("settings_ui.py"),
        )
        self.assertIn(
            "3000,",
            source("preset_manager.py"),
        )

    def test_one_platform_independent_zigbee_frontend_button(self):
        text = source("zigbee_ui.py")
        self.assertEqual(
            text.count('webbrowser.open("http://localhost:8080")'),
            1,
        )
        self.assertIn('"Open Zigbee2MQTT Frontend"', text)
        self.assertNotIn('"Linux Open Zigbee2MQTT Frontend"', text)
        self.assertNotIn('"Windows Open Zigbee2MQTT Frontend"', text)

    def test_hardware_presence_does_not_claim_a_successful_connection(self):
        labels = source("zigbee_hardware_ui.py")
        self.assertIn('text=f"Detected ({arduino_port})"', labels)
        self.assertIn('text=f"Detected ({zigbee_port})"', labels)
        self.assertIn('text="Not detected"', labels)
        self.assertNotIn('text=f"Connected ({arduino_port})"', labels)
        # MQTT connection is a different, actual broker connection state.
        self.assertIn(
            'status_text = "Connected"',
            source("zigbee_control.py"),
        )

    def test_critical_game_export_and_serial_handlers_are_explained(self):
        tree = ast.parse(source("uwh.py"))
        klass = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "GameManagementApp"
        )
        methods = {
            node.name: node for node in klass.body
            if isinstance(node, ast.FunctionDef)
        }
        for name in ("countdown_timer", "run_next_game_transition",
                     "next_period", "_process_hardware_siren_event"):
            with self.subTest(name=name):
                self.assertTrue(ast.get_docstring(methods[name]))

        serial = ast.parse(source("serial_siren_listener.py"))
        listener = next(
            node for node in serial.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "serial_listener_thread"
        )
        self.assertIn("OFF", ast.get_docstring(listener))


if __name__ == "__main__":
    unittest.main()
