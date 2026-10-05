"""Regression guards for the restored classic 1.2 interface.

The restored branch intentionally keeps the pre-v1.3 Tk/ttk presentation while
retaining later functional fixes that are independent of the visual redesign.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ClassicUiRetainedFixesTests(unittest.TestCase):
    def test_classic_ui_does_not_import_new_v13_theme(self):
        self.assertNotIn("import ui_theme", source("uwh.py"))
        self.assertNotIn("import ui_theme", source("settings_ui.py"))
        self.assertNotIn("ttkbootstrap", source("requirements.txt"))

    def test_uwh_stick_replaces_default_tk_icon(self):
        uwh = source("uwh.py")
        icon = source("app_icon.py")
        self.assertIn("import app_icon", uwh)
        self.assertIn("app_icon.apply_app_icon(root)", uwh)
        self.assertIn("root.iconphoto(True, icon)", icon)
        self.assertIn("_uwh_app_icon = icon", icon)

    def test_about_credit_uses_sentence_break_before_conducted_by(self):
        settings = source("settings_ui.py")
        readme = source("README.md")
        expected = "by ChatGPT. Conducted by David Stirling"
        self.assertIn(expected, settings)
        self.assertIn(expected, readme)
        self.assertNotIn("by ChatGPT, conducted by David Stirling", settings)

    def test_tournament_and_about_tabs_remain_separate(self):
        text = source("settings_ui.py")
        self.assertIn("def create_tournament_tab(app):", text)
        self.assertIn("def create_about_tab(app, readme_path):", text)
        self.assertIn('app.notebook.add(tab, text="Tournament List")', text)
        self.assertIn('app.notebook.add(tab, text="About")', text)

    def test_classic_preset_bank_has_nine_buttons_and_migrates_six(self):
        ui = source("settings_ui.py")
        manager = source("settings_manager.py")
        self.assertIn("for i in range(9):", ui)
        self.assertIn("btn_row = 1 + (i // 3)", ui)
        self.assertIn("while len(migrated) < 9:", manager)
        for number in ("7", "8", "9"):
            self.assertIn(
                f'{{"text": "{number}", "values": {{}}, "checkboxes": {{}}}}',
                manager,
            )

    def test_team_timeout_switch_is_on_period_row_not_separate_row(self):
        text = source("settings_ui.py")
        self.assertIn(
            '"team_timeouts_allowed",\n        "overtime_allowed"',
            text,
        )
        self.assertNotIn('if var_name == "team_timeouts_allowed":', text)
        self.assertIn('if var_name == "team_timeout_period":', text)
        self.assertIn("check_var = app.team_timeouts_allowed_var", text)
        self.assertIn('"name": "team_timeouts_allowed"', text)

    def test_readme_matches_relocated_team_timeout_control(self):
        readme = source("README.md")
        self.assertIn(
            "checkbox beside **Team Time-Out Period**",
            readme,
        )
        self.assertNotIn("**Team time-outs allowed?**", readme)
        self.assertNotIn("'Team time-outs allowed?' check box", readme)

    def test_overtime_switch_is_on_game_break_row_not_separate_row(self):
        text = source("settings_ui.py")
        self.assertIn('"overtime_allowed",\n        "record_scorers_cap_number"', text)
        self.assertNotIn('if var_name == "overtime_allowed":', text)
        self.assertIn('if var_name == "overtime_game_break":', text)
        self.assertIn("check_var = app.overtime_allowed_var", text)
        self.assertIn('"name": "overtime_allowed"', text)
        self.assertIn('"name": var_name', text)

    def test_preset_editor_handles_shared_overtime_row(self):
        text = source("preset_manager.py")
        self.assertIn('label = widget.get("label_widget")', text)
        self.assertIn("label_text = (", text)
        self.assertIn("text=label_text", text)

    def test_post_1_2_sudden_death_fixes_are_retained(self):
        game_flow = source("game_flow.py")
        uwh = source("uwh.py")
        self.assertIn("app.engine.clear_sudden_death_goal()", game_flow)
        self.assertIn("return app.start_sudden_death_timer()", game_flow)
        self.assertIn("self.engine.clear_sudden_death_goal()", uwh)
        self.assertIn("self.engine.sudden_death_restore_active", uwh)
        self.assertIn("self.engine.sudden_death_restore_time", uwh)
        self.assertIn(
            "self.sudden_death_timer_job = self.master.after(\n"
            "            1000,\n"
            "            self.start_sudden_death_timer",
            uwh,
        )

    def test_release_returns_to_next_numeric_1_2_patch(self):
        workflow = source(".github/workflows/build-exe.yml")
        gate = source(".github/scripts/release_gate.py")
        chooser = source(".github/scripts/next_release_version.py")
        self.assertIn('RELEASE_SERIES: "1.2"', workflow)
        self.assertIn("Choose next 1.2 release", workflow)
        self.assertIn("next_release_version.py", workflow)
        self.assertIn("make_latest: true", workflow)
        self.assertIn('release_version = os.environ["RELEASE_VERSION"]', gate)
        self.assertIn('series = os.environ.get("RELEASE_SERIES", "1.2")', chooser)


if __name__ == "__main__":
    unittest.main()
