#!/usr/bin/env python3
import importlib.machinery
import importlib.util
import os
import tempfile
import tomllib
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
TOOL = os.path.join(ROOT, "src", "omarchy-touchbar-settings")
loader = importlib.machinery.SourceFileLoader("touchbar_settings", TOOL)
spec = importlib.util.spec_from_loader("touchbar_settings", loader)
ts = importlib.util.module_from_spec(spec)
loader.exec_module(ts)


class ConfigEditor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "touchbar.toml")
        with open(os.path.join(ROOT, "config", "touchbar.toml")) as handle:
            self.original = handle.read()
        with open(self.path, "w") as handle:
            handle.write(self.original)
        self.cfg = ts.ConfigFile(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_settings_edits_keep_comments_and_parse(self):
        self.cfg.set_setting("corner_radius", 9)
        self.cfg.set_setting("clock", "%H:%M")
        self.cfg.set_setting("dictation", False)
        self.cfg.set_setting("brand_new_key", "x")
        data = self.cfg.save()
        self.assertEqual(data["settings"]["corner_radius"], 9)
        self.assertEqual(data["settings"]["clock"], "%H:%M")
        self.assertFalse(data["settings"]["dictation"])
        self.assertEqual(data["settings"]["brand_new_key"], "x")
        with open(self.path) as handle:
            text = handle.read()
        self.assertIn("# buttons besides the esc key", text)      # comments survive
        self.assertIn("corner_radius = 9", text)
        self.assertEqual(text.count("[settings]"), 1)

    def test_football_and_profile_edits(self):
        self.cfg.set_football("team", "ARS")
        self.cfg.set_profile("Terminal", "enabled", False)
        self.cfg.set_profile("Obsidian", "icon", "X")
        self.cfg.set_profile_buttons("Spotify", [
            {"label": "A", "keys": "CTRL+A", "color": "green"},
            {"label": "B", "keys": "PlayPause"},
        ])
        data = self.cfg.save()
        self.assertEqual(data["football"]["team"], "ARS")
        by_name = {p["name"]: p for p in data["profiles"]}
        self.assertFalse(by_name["Terminal"]["enabled"])
        self.assertEqual(by_name["Obsidian"]["icon"], "X")
        self.assertEqual([b["keys"] for b in by_name["Spotify"]["buttons"]],
                         ["CTRL+A", "PlayPause"])
        self.assertEqual(by_name["Spotify"]["buttons"][0]["color"], "green")
        # Untouched profiles are byte-for-byte the same.
        self.assertEqual(by_name["Discord"], tomllib.loads(self.original)["profiles"][
            [p["name"] for p in tomllib.loads(self.original)["profiles"]].index("Discord")])

    def test_missing_football_table_is_created_outside_profiles(self):
        import re
        stripped = re.sub(r"\[football\]\n(?:[^\[\n][^\n]*\n|\n)*", "", self.original)
        with open(self.path, "w") as handle:
            handle.write(stripped)
        cfg = ts.ConfigFile(self.path)
        self.assertNotIn("football", cfg.data)
        cfg.set_football("team", "LIV")
        data = cfg.save()
        self.assertEqual(data["football"]["team"], "LIV")
        self.assertEqual(len(data["profiles"]), len(tomllib.loads(self.original)["profiles"]))

    def test_bad_edit_is_refused(self):
        self.cfg.text += "\n[[profiles]]\nname = \"broken\n"
        with self.assertRaises(tomllib.TOMLDecodeError):
            self.cfg.save()


if __name__ == "__main__":
    unittest.main(verbosity=2)
