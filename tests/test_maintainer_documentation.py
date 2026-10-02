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
            "uwh.py", "app_version.py", "game_engine.py", "game_flow.py", "game_logging.py",
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

    def test_readme_zigbee_section_reports_up_to_three_tested_working_buttons(self):
        readme = source("README.md")
        self.assertIn("**up to three working Zigbee buttons**", readme)
        self.assertIn(
            '"siren_button_2", "siren_button_3"',
            readme,
        )
        self.assertIn("individual buttons may publish different actions", readme)

    def test_readme_settings_and_preset_instructions_match_current_code(self):
        readme = source("README.md")
        self.assertIn("for **three seconds**", readme)
        self.assertIn("in **seconds**", readme)
        self.assertIn("queues the closed state", readme)
        self.assertIn("or on normal program exit", readme)
        self.assertIn("Maximum Siren Duration (seconds)", readme)
        self.assertIn("both `9:36` and `09:36` mean 09:36", readme)
        self.assertNotIn("use the two-digit form until", readme)

    def test_readme_zigbee_section_explains_mapping_and_auto_add_safety(self):
        readme = source("README.md")
        self.assertIn("**Auto-add From Log**", readme)
        self.assertIn("**Ignore**", readme)
        self.assertIn("**Save Action Mappings**", readme)
        self.assertIn("**Save Configuration**", readme)
        self.assertIn("up to five recent", readme)
        self.assertIn("**Detected** ports", readme)
        self.assertIn("`emergency`", readme)

    def test_tournament_and_about_are_standalone_tabs(self):
        settings_ui = source("settings_ui.py")
        uwh = source("uwh.py")
        readme = source("README.md")

        self.assertIn('app.notebook.add(tab, text="Tournament List")', settings_ui)
        self.assertIn('app.notebook.add(tab, text="About")', settings_ui)
        self.assertIn("def create_tournament_tab(app):", settings_ui)
        self.assertIn("def create_about_tab(app, readme_path):", settings_ui)
        self.assertIn("rowspan=2", settings_ui)
        self.assertIn("Path(readme_path)", settings_ui)
        self.assertIn("path.resolve().as_uri()", settings_ui)
        self.assertIn(
            "https://github.com/davidstirling777-star/",
            settings_ui,
        )
        self.assertIn("davidstirling777@gmail.com", settings_ui)
        self.assertIn("self.create_tournament_tab()", uwh)
        self.assertIn("self.create_about_tab()", uwh)
        self.assertIn("## Tournament List tab", readme)
        self.assertIn("## About tab", readme)

    def test_zigbee_mapping_toolbar_keeps_all_five_operator_actions(self):
        zigbee_ui = source("zigbee_ui.py")
        for label in (
            "Add Mapping",
            "Edit Mapping",
            "Delete Mapping",
            "Auto-add From Log",
            "Save Action Mappings",
        ):
            with self.subTest(label=label):
                self.assertIn(f'("{label}"', zigbee_ui)

    def test_sounds_tab_reports_the_startup_audio_output(self):
        sound = source("sound.py")
        sounds_ui = source("sounds_ui.py")
        readme = source("README.md")
        self.assertIn('"@DEFAULT_AUDIO_SINK@"', sound)
        self.assertIn("HiFiBerry DAC+ / compatible I2S DAC", sound)
        self.assertIn("AUDIO_OUTPUT_AT_STARTUP", sound)
        self.assertIn("Audio output in use:", sounds_ui)
        self.assertIn("(selected when UWH started)", sounds_ui)
        self.assertIn("restart UWH", readme)
        self.assertIn("dtoverlay=hifiberry-dacplus-std", readme)
        self.assertIn("wpctl set-default", readme)
        self.assertIn("wpctl set-volume", readme)

    def test_sounds_tab_uses_per_file_trim_not_software_master_volume(self):
        for filename in ("uwh.py", "sound.py", "sounds_ui.py", "settings_manager.py"):
            text = source(filename)
            for obsolete in ("air_volume", "water_volume"):
                with self.subTest(filename=filename, obsolete=obsolete):
                    self.assertNotIn(obsolete, text)

        sounds_ui = source("sounds_ui.py")
        settings_manager = source("settings_manager.py")
        self.assertEqual(sounds_ui.count("tk.Scale("), 0)
        self.assertNotIn("Pips Vol", sounds_ui)
        self.assertNotIn("Siren Vol", sounds_ui)
        self.assertIn('text="Trim %"', sounds_ui)
        self.assertIn("MAX_SOUND_ROWS = 10", sounds_ui)
        self.assertIn("0 to 100", sounds_ui)
        self.assertIn('"sound_trims": {}', settings_manager)
        self.assertNotIn('"pips_volume": 50.0', settings_manager)
        self.assertNotIn('"siren_volume": 50.0', settings_manager)
        self.assertIn("Trim %", source("README.md"))
        self.assertIn("hardware", source("README.md").lower())

    def test_game_variables_shows_user_visible_app_version(self):
        settings_ui = source("settings_ui.py")
        version = source("app_version.py")
        workflow = source(".github/workflows/build-exe.yml")
        readme = source("README.md")

        self.assertIn("from app_version import APP_VERSION", settings_ui)
        self.assertIn('text=f"UWH v{APP_VERSION}"', settings_ui)
        self.assertIn('APP_VERSION = "1.2.source.', version)
        self.assertIn("Stamp application version", workflow)
        self.assertIn("github.run_number", workflow)
        self.assertIn("lower-right corner", readme)

    def test_sounds_tab_has_two_fixed_ten_row_sound_tables(self):
        sounds_ui = source("sounds_ui.py")
        self.assertIn('build_sound_table(', sounds_ui)
        self.assertIn('"Pips"', sounds_ui)
        self.assertIn('"Sirens"', sounds_ui)
        self.assertIn('text="Use"', sounds_ui)
        self.assertIn('text="Sound File"', sounds_ui)
        self.assertIn('text="Trim %"', sounds_ui)
        self.assertIn("ttk.Radiobutton(", sounds_ui)
        self.assertIn("variable=selection_var", sounds_ui)
        self.assertIn("value=filename", sounds_ui)
        self.assertIn('value=f"__unused_{sound_type}_{index}"', sounds_ui)
        self.assertIn('unused_radio.state(["disabled"])', sounds_ui)
        self.assertIn('blank_trim.state(["disabled"])', sounds_ui)
        self.assertIn("range(MAX_SOUND_ROWS)", sounds_ui)
        self.assertIn("double-click the filename to preview it", sounds_ui)
        readme = source("README.md")
        self.assertIn("Exactly **one Pip** and **one Siren**", readme)
        self.assertIn("`pips_sound` and `siren_sound`", readme)

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
