# Checks that RESULTS.md says what data/summary-2026-10-16.json and data/verify-2026-10-16.json hold.
# By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
import json
import os
import unittest
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
SUMMARY = os.path.join(HERE, "data", "summary-2026-10-16.json")
VERIFY = os.path.join(HERE, "data", "verify-2026-10-16.json")
DOC = os.path.join(HERE, "RESULTS.md")


def pts(x):
    """A share difference as signed percentile points, one decimal, halves rounded up (0.2015 -> +20.2)."""
    return format((Decimal(repr(x)) * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP), "+.1f")


class ResultsDoc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SUMMARY, encoding="utf-8") as f:
            cls.s = json.load(f)
        with open(VERIFY, encoding="utf-8") as f:
            cls.v = json.load(f)
        with open(DOC, encoding="utf-8") as f:
            cls.doc = f.read()

    def test_totals(self):
        self.assertEqual(self.s["entries"], 5125)
        self.assertEqual(self.s["classified"], 609)
        self.assertEqual(sum(j["classified"] for j in self.s["jams"]), 609)
        self.assertIn("(5,125 ranked entries)", self.doc)
        self.assertIn("(609 pages classified)", self.doc)

    def test_jam_table(self):
        for j in self.s["jams"]:
            share = (Decimal(j["yes"]) * 100 / Decimal(j["classified"])).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            cells = "| %s | %d | %d | %d | %d | %s%% |" % (format(j["ranked"], ","), j["classified"], j["yes"], j["no"],
                                                          j["unanswered"], share)
            self.assertIn(cells, self.doc, j["jam"])

    def test_pooled_differences(self):
        g = self.s["groups"]["ai_not_banned"]
        for key in ("yes_vs_rest", "yes_vs_no", "no_vs_unanswered"):
            raw = g[key]["raw"]
            lo, hi = raw["ci95"]
            self.assertIn("%s to %s" % (pts(lo), pts(hi)), self.doc, key)
            self.assertIn(pts(raw["diff"]), self.doc, key)
        self.assertEqual(pts(g["yes_vs_no"]["raw"]["diff"]), "-1.4")
        self.assertEqual(pts(g["no_vs_unanswered"]["raw"]["diff"]), "+17.5")
        self.assertIn("| says No AI vs unanswered | 240 vs 39 (4 jams) | **+17.5** | **+8.7 to +26.4** | **0.001** |", self.doc)

    def test_independent_check_and_leave_one_out(self):
        self.assertTrue(self.v["ok"])
        self.assertEqual(self.v["mismatches"], [])
        self.assertEqual(self.v["sampled_rows"], 625)
        rob = self.v["robustness_ai_not_banned"]
        g = self.s["groups"]["ai_not_banned"]
        for key in ("yes_vs_rest", "yes_vs_no", "no_vs_unanswered"):
            self.assertEqual(rob[key]["pooled"]["diff"], g[key]["raw"]["diff"], key)
            lo, hi = rob[key]["leave_one_out_range"]
            self.assertIn("**%s to %s**" % (pts(lo), pts(hi)), self.doc, key)
        self.assertIn("**+13.3 to +20.2**", self.doc)

    def test_privacy_and_licence(self):
        data = open(SUMMARY, encoding="utf-8").read() + open(VERIFY, encoding="utf-8").read()
        self.assertNotIn(".itch.io", data)
        self.assertNotIn("http", data)
        self.assertIn("CC BY 4.0", self.doc)
        self.assertIn("Apache-2.0", self.doc)
        self.assertNotIn("MIT", self.doc)


if __name__ == "__main__":
    unittest.main()
