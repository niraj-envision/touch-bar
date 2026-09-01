#!/usr/bin/env python3
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
from collections import deque

TOOL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "omarchy-touchbar")
loader = importlib.machinery.SourceFileLoader("touchbar", TOOL)
spec = importlib.util.spec_from_loader("touchbar", loader)
tb = importlib.util.module_from_spec(spec)
loader.exec_module(tb)


def goal(identity, scorer):
    return {"id": identity, "kind": "goal", "homeAbbr": "LIV", "homeScore": 2,
            "awayScore": 1, "awayAbbr": "MNC", "scorer": scorer,
            "team": "Liverpool", "clock": "89'"}


class GoalScene(unittest.TestCase):
    def test_scene_uses_all_thirteen_stable_cells(self):
        bar = tb.TouchBar()
        rows = bar.goal_specs(goal("g1", "M. Salah"), .5)
        self.assertEqual(len(rows), 13)
        self.assertEqual(len({r["scene_x"] for r in rows}), 13)
        self.assertTrue(all(r.get("goal_scene") for r in rows))
        svg = tb.build_goal_svg(dict(rows[6], fill="#111", fg="#eee",
                                     bar="#fc0", goal_red="#f44"), 150,
                                "JetBrainsMono Nerd Font")
        self.assertIn("M. Salah", svg)
        self.assertIn("LIV  2 - 1  MNC", svg)
        self.assertIn("viewBox=", svg)

    def test_fifo_is_serial_and_acknowledged_after_each_display(self):
        bar = tb.TouchBar()
        bar.goal_queue = deque([goal("g1", "First"), goal("g2", "Second")])
        bar.goal_animating = True
        shown = []
        bar.to_toml = lambda specs: "frame"
        bar.queue = lambda *a, **k: shown.append(bar.goal_active["id"])
        bar.render = lambda *a, **k: None

        class Clock:
            now = 0.0
            @classmethod
            def monotonic(cls):
                cls.now += .02
                return cls.now
            @classmethod
            def sleep(cls, amount):
                cls.now += max(0, amount)

        old_time, old_acks = tb.time, tb.GOAL_ACKS
        with tempfile.TemporaryDirectory() as tmp:
            try:
                tb.time = Clock
                tb.GOAL_ACKS = os.path.join(tmp, "acks")
                bar._goal_worker()
                with open(tb.GOAL_ACKS) as handle:
                    acked = [line.strip() for line in handle]
            finally:
                tb.time, tb.GOAL_ACKS = old_time, old_acks
        order = []
        for identity in shown:
            if not order or order[-1] != identity:
                order.append(identity)
        self.assertEqual(order, ["g1", "g2"])
        self.assertEqual(acked, ["g1", "g2"])
        self.assertFalse(bar.goal_animating)


if __name__ == "__main__":
    unittest.main(verbosity=2)
