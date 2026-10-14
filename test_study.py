# Tests for jam-ai-ranks. By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
import csv
import os
import tempfile
import time
import unittest

import study

ENTRY = """
<div class="game_rank">
 <div class="game_thumb"><a href="https://{user}.itch.io/{game}" class="thumb_link"><img src="https://img.itch.zone/x.png"></a></div>
 <div class="game_summary">
  <h2><a href="https://{user}.itch.io/{game}">{title}</a></h2>
  <h3>by <a href="https://{user}.itch.io">{user}</a>, <a href="https://helper.itch.io">helper</a></h3>
  <h3>Ranked <strong>{place}</strong> with {ratings} ratings (Score:&nbsp;{score})</h3>
  <a href="/jam/test-jam/rate/{rid}" class="button">View submission</a>
  <table class="ranking_results_table">
   <tr><th>Criteria</th><th>Rank</th><th>Score*</th><th>Raw Score</th></tr>
   <tr><td>Overall</td><td>#{rank}</td><td>{score}</td><td>{raw}</td></tr>
   <tr><td><a href="/jam/test-jam/results/graphics">Graphics</a></td><td>#{grank}</td><td>{graw}</td><td>{graw}</td></tr>
   <tr><td><a href="/jam/test-jam/results/audio">Audio</a></td><td>#1</td><td>3.000</td><td>3.000</td></tr>
  </table>
 </div>
</div>"""


def entry(user, game, title, place, rank, ratings, score, raw, rid, grank, graw):
    return ENTRY.format(user=user, game=game, title=title, place=place, rank=rank, ratings=ratings,
                        score=score, raw=raw, rid=rid, grank=grank, graw=graw)


def results_page(entries, page_no, pages):
    return ("<html><head><script>var x = '<a href=\"https://evil.itch.io/script-game\">';</script></head>"
            "<body><h1>Results</h1><a href=\"https://host.itch.io\">host</a>"
            "<div class=\"pager\">Page %d of %d</div>%s</body></html>" % (page_no, pages, "".join(entries)))


PAGE1 = results_page([
    entry("alpha", "rain-game", "Rain Game", "1st", 1, 16, "4.150", "4.150", 111, 2, "4.375"),
    entry("bravo", "fog", "Fog &amp; Co", "2nd", 2, 2, "2.121", "4.200", 222, 1, "4.500"),
], 1, 2)
PAGE2 = results_page([
    entry("charlie", "snow", "Snow", "3rd", 3, 7, "2.000", "2.000", 333, 3, "1.500"),
    entry("delta", "dust", "Dust", "3rd", 3, 5, "2.000", "2.000", 444, 4, "1.000"),
], 2, 2)

YES = """<table><tr><td>AI Disclosure</td><td><a href="https://itch.io/games/ai-assisted">AI Assisted</a>,
<a href="https://itch.io/games/ai-code">Code</a>, <a href="https://itch.io/games/ai-graphics">Graphics</a></td></tr>
<tr><td>Made with</td><td><a href="https://itch.io/games/made-with-godot">Godot</a></td></tr></table>
<div id="html_embed_123" class="iframe_placeholder"></div>"""
NO = """<table><tr><td>Platforms</td><td><a href="https://itch.io/games/html5">HTML5</a></td></tr>
<tr><td>Content</td><td><a href="https://itch.io/games/tag-no-ai">No generative AI was used</a></td></tr></table>"""
UNANSWERED = """<table><tr><td>Tags</td><td><a href="https://itch.io/games/tag-horror">Horror</a></td></tr>
<tr><td>Made with</td><td><a href="https://itch.io/games/made-with-unity">Unity</a></td></tr></table>"""
BOTH = YES + NO


class Parse(unittest.TestCase):
    def test_flatten(self):
        t = study.flatten('<p>Ranked <b>1st</b>&nbsp;with</p><a href="/x?a=1&amp;b=2">y</a><script>z<a href="q"></script>')
        self.assertIn("Ranked 1st with", t)
        self.assertIn("[[/x?a=1&b=2]]", t)
        self.assertNotIn("[[q]]", t)

    def test_results_page(self):
        got = study.parse_results(PAGE1, "test-jam")
        self.assertEqual(len(got), 2)
        a, b = got
        self.assertEqual((a["rank"], a["ratings"], a["score"], a["raw"]), (1, 16, 4.15, 4.15))
        self.assertEqual(a["game"], "https://alpha.itch.io/rain-game")
        self.assertEqual(a["rate_id"], "111")
        self.assertEqual(a["criteria"]["Graphics"], {"rank": 2, "score": 4.375, "raw": 4.375})
        self.assertEqual(set(a["criteria"]), {"Overall", "Graphics", "Audio"})
        self.assertEqual((b["rank"], b["ratings"], b["score"], b["raw"]), (2, 2, 2.121, 4.2))
        self.assertEqual(b["game"], "https://bravo.itch.io/fog")
        self.assertEqual(b["rate_id"], "222")
        self.assertEqual(study.page_count(PAGE1), 2)
        self.assertEqual(study.page_count("<p>no pager</p>"), 1)

    def test_no_entries(self):
        self.assertEqual(study.parse_results("<p>Results are not ready</p>", "test-jam"), [])

    def test_classify(self):
        self.assertEqual(study.classify(YES), ("yes", ["code", "graphics"], ["godot"], True))
        self.assertEqual(study.classify(NO), ("no", [], [], True))
        self.assertEqual(study.classify(UNANSWERED), ("unanswered", [], ["unity"], False))
        self.assertEqual(study.classify(BOTH)[0], "both")
        old = '<a href="https://itch.io/games/tag-ai-generated">AI Generated</a>'
        self.assertEqual(study.classify(old)[0], "yes")


class Stats(unittest.TestCase):
    def test_mid_percentiles(self):
        self.assertEqual(study.mid_percentiles([3, 1, 2, 2]), [1.0, 0.0, 0.5, 0.5])
        self.assertEqual(study.mid_percentiles([7]), [0.5])

    def test_compare_finds_a_clear_gap(self):
        rows = []
        for jam in ("j1", "j2"):
            rows += [{"jam": jam, "ai_class": "yes", "pct_raw": v} for v in (0.9, 0.8, 0.95, 0.85)]
            rows += [{"jam": jam, "ai_class": "unanswered", "pct_raw": v} for v in (0.1, 0.2, 0.3, 0.15)]
        rows.append({"jam": "j3", "ai_class": "yes", "pct_raw": 0.0})  # no other class there: left out
        r = study.compare(rows, ("yes",), ("no", "unanswered"), iters=999)
        self.assertEqual((r["n_a"], r["n_b"], r["jams"]), (8, 8, 2))
        self.assertAlmostEqual(r["diff"], 0.6875, places=4)
        self.assertLess(r["p"], 0.01)
        self.assertGreater(r["ci95"][0], 0.4)
        self.assertEqual(r, study.compare(rows, ("yes",), ("no", "unanswered"), iters=999))

    def test_compare_without_both_sides(self):
        rows = [{"jam": "j", "ai_class": "no", "pct_raw": 0.5}]
        self.assertIsNone(study.compare(rows, ("yes",), ("no",), iters=10)["diff"])


class EndToEnd(unittest.TestCase):
    def test_collect_analyse_write(self):
        pages = {
            study.results_url("test-jam", 1): PAGE1,
            study.results_url("test-jam", 2): PAGE2,
            "https://alpha.itch.io/rain-game": YES,
            "https://bravo.itch.io/fog": NO,
            "https://charlie.itch.io/snow": UNANSWERED,
        }
        asked = []

        def fetch(url):
            asked.append(url)
            return (200, pages[url]) if url in pages else (404, "")

        jams = [{"slug": "test-jam", "policy": "allowed", "group": "ai_not_banned"}]
        with tempfile.TemporaryDirectory() as tmp:
            rows = study.collect(jams, fetch, time.monotonic() + 60, log=lambda m: None,
                                 samples=os.path.join(tmp, "samples"))
            self.assertEqual(len(rows), 4)
            self.assertEqual([r["ai_class"] for r in rows], ["yes", "no", "unanswered", ""])
            self.assertEqual(rows[3]["page_status"], "404")
            self.assertEqual(asked[0], "https://itch.io/jam/test-jam/results")
            self.assertEqual(asked[1], "https://itch.io/jam/test-jam/results?page=2")
            # raw scores 4.15, 4.2, 2.0, 2.0: the 2-rating entry is best on raw score
            self.assertEqual([r["pct_raw"] for r in rows], [2 / 3, 1.0, 1 / 6, 1 / 6])
            self.assertEqual(rows[0]["pct_rank"], 1.0)
            self.assertEqual(rows[2]["pct_rank"], rows[3]["pct_rank"])
            self.assertEqual([r["pct_graphics"] for r in rows], [2 / 3, 1.0, 1 / 3, 0.0])
            summary = study.analyse(rows, iters=50)
            self.assertEqual(summary["entries"], 4)
            self.assertEqual(summary["classified"], 3)
            j = summary["jams"][0]
            self.assertEqual((j["yes"], j["no"], j["unanswered"]), (1, 1, 1))
            g = summary["groups"]["ai_not_banned"]
            self.assertEqual(g["yes_vs_rest"]["raw"]["n_a"], 1)
            self.assertEqual(g["yes_graphics_vs_rest_on_graphics"]["n_a"], 1)
            out = os.path.join(tmp, "out")
            study.write_outputs(rows, summary, out)
            public = open(os.path.join(out, "entries_public.csv"), encoding="utf-8").read()
            self.assertNotIn("itch.io", public)
            self.assertNotIn("alpha", public)
            self.assertNotIn("111", public)
            with open(os.path.join(out, "entries_public.csv"), newline="", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 4)
            self.assertIn("rate_id", open(os.path.join(out, "entries_private.csv"), encoding="utf-8").read())
            self.assertTrue(os.path.exists(os.path.join(out, "report.md")))
            self.assertTrue(os.path.exists(os.path.join(tmp, "samples", "results-test-jam.html")))

    def test_deadline_stops_fetching(self):
        def fetch(url):
            return (200, PAGE1) if "results" in url else (200, YES)

        jams = [{"slug": "test-jam", "policy": "allowed", "group": "g"}]
        rows = study.collect(jams, fetch, time.monotonic() - 1, log=lambda m: None)
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
