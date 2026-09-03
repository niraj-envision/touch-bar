#!/usr/bin/env python3
import importlib.machinery
import importlib.util
import os
import tempfile
import time
import unittest

TOOL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "omarchy-touchbar")
loader = importlib.machinery.SourceFileLoader("touchbar_football", TOOL)
spec = importlib.util.spec_from_loader("touchbar_football", loader)
tb = importlib.util.module_from_spec(spec)
loader.exec_module(tb)


def event(identity, home, away, state, hs="1", as_="0", goals=(), kickoff=None):
    stamp = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime(kickoff or time.time()))
    return {
        "id": identity, "date": stamp,
        "status": {"type": {"state": state, "shortDetail": "", "completed": state == "post"},
                   "displayClock": "67'"},
        "competitions": [{
            "competitors": [
                {"homeAway": "home", "score": hs,
                 "team": {"id": "1", "abbreviation": home, "displayName": home}},
                {"homeAway": "away", "score": as_,
                 "team": {"id": "2", "abbreviation": away, "displayName": away}},
            ],
            "details": [
                {"scoringPlay": True, "team": {"id": team}, "clock": {"displayValue": clock},
                 "athletesInvolved": [{"shortName": who}]}
                for team, clock, who in goals
            ],
        }],
    }


class Football(unittest.TestCase):
    def setUp(self):
        self.pl = tb.PremierLeague()
        self.pl.configure({"football": True, "goal_celebrations": True}, {"team": "LIV"})
        self.tmp = tempfile.TemporaryDirectory()
        self.old_seen = tb.PL_SEEN
        tb.PL_SEEN = os.path.join(self.tmp.name, "seen.json")

    def tearDown(self):
        tb.PL_SEEN = self.old_seen
        self.tmp.cleanup()

    def load(self, raw_events):
        self.pl.events = [tb.pl_parse_event(e, "#7daea3") for e in raw_events]
        self.pl.events.sort(key=lambda e: e["kickoff"])

    def test_parse_event_reads_sides_scores_and_goals(self):
        match = tb.pl_parse_event(event("9", "LIV", "ARS", "in", "2", "1",
                                        goals=[("1", "12'", "M. Salah"), ("2", "40'", "B. Saka"),
                                               ("1", "67'", "C. Gakpo")]), "#000")
        self.assertEqual(tb.pl_score(match), (2, 1))
        self.assertEqual(match["home"]["color"], tb.CLUB_COLORS["LIV"])
        self.assertEqual([g["player"] for g in match["goals"]],
                         ["M. Salah", "B. Saka", "C. Gakpo"])
        self.assertTrue(self.pl.involves_club(match))

    def test_goal_detection_baselines_then_reports_new_goals_once(self):
        self.load([event("9", "LIV", "ARS", "in", "1", "0", goals=[("1", "12'", "M. Salah")])])
        self.assertEqual(self.pl.detect_goals(set()), [])          # silent baseline
        self.load([event("9", "LIV", "ARS", "in", "2", "0",
                         goals=[("1", "12'", "M. Salah"), ("1", "55'", "C. Gakpo")])])
        new = self.pl.detect_goals(set())
        self.assertEqual(len(new), 1)
        self.assertEqual(new[0]["scorer"], "C. Gakpo")
        self.assertEqual((new[0]["homeScore"], new[0]["awayScore"]), (2, 0))
        self.assertEqual(self.pl.detect_goals(set()), [])          # not twice
        # A goal the Football plugin already delivered is skipped too.
        self.load([event("9", "LIV", "ARS", "in", "3", "0",
                         goals=[("1", "12'", "M. Salah"), ("1", "55'", "C. Gakpo"),
                                ("1", "80'", "D. Nunez")])])
        key = tb.PremierLeague.goal_key(self.pl.events[0], self.pl.events[0]["goals"][2], 2)
        self.assertEqual(self.pl.detect_goals({key}), [])

    def test_old_results_are_learned_silently(self):
        self.load([event("1", "LIV", "ARS", "in", "1", "0", goals=[("1", "12'", "A")])])
        self.pl.detect_goals(set())
        stale = event("2", "CHE", "TOT", "post", "2", "0",
                      goals=[("1", "10'", "B"), ("1", "50'", "C")],
                      kickoff=time.time() - 3 * 86400)
        self.load([event("1", "LIV", "ARS", "in", "1", "0", goals=[("1", "12'", "A")]), stale])
        self.assertEqual(self.pl.detect_goals(set()), [])
        self.assertEqual(len(self.pl.seen), 3)

    def test_club_queries(self):
        now = time.time()
        self.load([
            event("1", "LIV", "NFO", "post", "2", "2", kickoff=now - 5 * 86400),
            event("2", "ARS", "LIV", "post", "0", "1", kickoff=now - 2 * 86400),
            event("3", "IPS", "LIV", "pre", kickoff=now + 86400),
            event("4", "NEW", "BOU", "pre", kickoff=now + 2 * 86400),
        ])
        self.assertEqual(self.pl.club_form(), "DW")
        self.assertEqual(self.pl.club_next()["id"], "3")
        self.assertEqual(self.pl.club_last()["id"], "2")
        self.assertEqual([e["id"] for e in self.pl.upcoming()], ["3", "4"])
        self.assertAlmostEqual(self.pl.next_kickoff_in(), 86400, delta=70)   # minute-precision stamps
        self.assertIn("1d", tb.pl_kickoff_caption(now + 86400 + 3600))

    def test_page_renders_and_pages_by_swipe(self):
        bar = tb.TouchBar()
        bar.render = lambda *a, **k: None
        bar.football = self.pl
        bar.football.table = [
            {"id": str(n), "name": "T%d" % n, "abbr": "T%02d" % n, "color": "#123456",
             "rank": n, "played": 5, "won": 3, "drawn": 1, "lost": 1, "gf": 9, "ga": 4,
             "gd": 5, "pts": 10} for n in range(1, 21)]
        bar.page = "football"
        bar.football_view = "table"
        specs = bar.specs()
        self.assertEqual(sum(max(1, int(t.get("stretch", 1) or 1)) for t in specs), 13)
        self.assertEqual(specs[0]["daemon"], "football:next-view")
        self.assertEqual([t["badge"] for t in specs[1:12]], list(range(1, 12)))
        self.assertTrue(bar.football_step("left"))
        self.assertEqual(bar.specs()[1]["badge"], 12)
        self.assertFalse(bar.football_step("left"))
        self.assertTrue(bar.football_step("right"))
        bar.handle_touch_action("football:next-view")
        self.assertEqual(bar.football_view, "fixtures")
        self.assertIn("football", bar.pages())
        bar.config["settings"]["football"] = False
        self.assertNotIn("football", bar.pages())


if __name__ == "__main__":
    unittest.main(verbosity=2)
