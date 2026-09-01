#!/usr/bin/env python3
import importlib.machinery
import importlib.util
import os
import unittest

TOOL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "omarchy-touchbar")
loader = importlib.machinery.SourceFileLoader("touchbar_mic", TOOL)
spec = importlib.util.spec_from_loader("touchbar_mic", loader)
tb = importlib.util.module_from_spec(spec)
loader.exec_module(tb)


class MicAndSettings(unittest.TestCase):
    def setUp(self):
        self.bar = tb.TouchBar()
        self.bar.render = lambda *args, **kwargs: None

    def test_settings_is_icon_only_hardware_controls(self):
        self.bar.page = "settings"
        actions = {item.get("daemon") for item in self.bar.specs()}
        self.assertTrue({
            "sys:bright-", "sys:bright+", "sys:bright-toggle",
            "sys:kbd-", "sys:kbd+", "sys:kbd-toggle",
            "media:previous", "media:playpause", "media:next",
            "sys:mute", "sys:vol-", "sys:vol+",
        } <= actions)

    def test_fn_toggles_settings_and_restores_previous_page(self):
        self.bar.page = "auto"
        self.bar.toggle_fn_dashboard()
        self.assertEqual(self.bar.page, "settings")
        self.bar.toggle_fn_dashboard()
        self.assertEqual(self.bar.page, "auto")

    def test_voice_overlay_is_two_sided_and_full_width(self):
        self.bar.voice_state = "recording"
        recording = self.bar.specs()
        self.assertEqual(len(recording), 4)
        self.assertEqual(recording[0].get("sub"), "LIVE MIC")
        self.assertEqual(len(recording[1]["waveform"]), 61)
        self.bar.reset_voice_meter()
        self.bar.ingest_voice_level(-0.03, 0.06, -34.0)
        quiet = self.bar.voice_levels[-1]
        self.bar.ingest_voice_level(-0.60, 0.35, -10.0)
        loud = self.bar.voice_levels[-1]
        self.assertLess(quiet[0], 0)
        self.assertGreater(quiet[1], 0)
        self.assertLess(loud[0], quiet[0])
        svg = tb.build_svg(self.bar.voice_overlay()[1], 1497, 13,
                           self.bar.config["settings"]["font"], 1.0)
        self.assertIn("<polygon", svg)
        self.assertEqual(svg.count("<polyline"), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
