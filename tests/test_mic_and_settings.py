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

    def test_settings_is_sliders_and_transport(self):
        self.bar.page = "settings"
        specs = self.bar.specs()
        actions = {item.get("daemon") for item in specs}
        self.assertTrue({
            "slider:bright", "slider:kbd", "slider:vol",
            "media:previous", "media:playpause", "media:next", "sys:mute",
            "page:next",
        } <= actions)
        # Sliders are wide; the page still fills exactly the stable 13 cells.
        units = sum(max(1, int(item.get("stretch", 1) or 1)) for item in specs)
        self.assertEqual(units, 13)
        self.assertFalse(any(item.get("spacer") for item in specs))

    def test_slider_drag_maps_track_position_to_level(self):
        self.bar.page = "settings"
        applied = []
        self.bar.set_level = lambda kind, level: applied.append((kind, level))
        specs = self.bar.specs()
        actions = [None] + [item.get("daemon") for item in specs]
        self.bar.touch_regions = self.bar.hit_regions(specs, actions)
        region = next(r for r in self.bar.touch_regions
                      if r["action"] == "slider:vol")
        left = region["left"] + tb.BUTTON_SPACING / 2.0
        width = region["right"] - tb.BUTTON_SPACING / 2.0 - left
        x0, x1 = tb.slider_track(width)
        self.assertTrue(self.bar.begin_drag(left + x0 + (x1 - x0) * 0.5))
        self.assertEqual(self.bar.drag_level, 50)
        self.bar.move_drag(left + x1 + 50)          # past the end clamps
        self.assertEqual(self.bar.drag_level, 100)
        self.bar.move_drag(left + x0 - 50)
        self.assertEqual(self.bar.drag_level, 0)
        self.bar.level_worker.join(2)
        # The worker applies the newest level for each control; intermediate
        # positions may be skipped but the last one always lands.
        self.assertEqual(applied[-1], ("vol", 0))
        self.bar.end_drag()
        self.assertIsNone(self.bar.drag)
        # A tap that lands off every slider is not claimed.
        self.assertFalse(self.bar.begin_drag(left + 10))

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
