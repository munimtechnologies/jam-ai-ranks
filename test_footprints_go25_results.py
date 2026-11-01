# Checks the published Game Off 2025 footprint baseline: the aggregate file is internally
# consistent, the grades follow from the pre-registered rules, small cells are hidden, and the
# results text quotes the same numbers. Apache-2.0. MV2 of Munim, Inc., made with AI agents.
import json
import math
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUMMARY = os.path.join(HERE, "data", "footprints-go25-summary.json")
RESULTS = os.path.join(HERE, "RESULTS-footprints-go25.md")


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def load():
    with open(SUMMARY, encoding="utf-8") as f:
        return json.load(f)


def read_results():
    with open(RESULTS, encoding="utf-8") as f:
        return f.read()


class TestSummary(unittest.TestCase):
    def setUp(self):
        self.s = load()

    def test_counts_add_up(self):
        s = self.s
        self.assertEqual(s["ranked"], 690)
        self.assertEqual(s["results_pages_read"], s["results_pages"])
        self.assertEqual(s["repo_link_found"] + s["no_repo_link"], s["ranked"])
        self.assertEqual(sum(s["repo_status"].values()), s["repo_link_found"])
        self.assertEqual(s["analysable"]["k"], s["repo_status"]["ok"])
        self.assertEqual(s["footprint"]["n"], s["repo_status"]["ok"])
        self.assertEqual(sum(s["disclosure_counts_read_pages"].values()), s["game_pages_read"])
        d = s["disclosure_counts_read_pages"]
        self.assertEqual(s["discloses_ai"]["k"], d["yes"] + d["both"])
        self.assertEqual(s["discloses_ai"]["n"], s["game_pages_read"])

    def test_crosstab_matches_shares(self):
        s = self.s
        ct = s["crosstab_analysable"]
        yes = ct["yes"]
        self.assertEqual(yes["footprint"] + yes["none"], s["footprint_among_disclosing"]["n"])
        self.assertEqual(yes["footprint"], s["footprint_among_disclosing"]["k"])
        self.assertEqual(s["footprint_among_disclosing"]["k"] + s["footprint_among_rest"]["k"],
                         s["footprint"]["k"])
        self.assertEqual(s["footprint_among_disclosing"]["n"] + s["footprint_among_rest"]["n"],
                         s["footprint"]["n"])
        self.assertEqual(s["footprint_not_disclosing"]["k"], s["footprint_among_rest"]["k"])
        self.assertEqual(s["footprint_not_disclosing"]["n"], s["footprint"]["k"])
        none_total = sum(row["none"] for row in ct.values())
        self.assertEqual(none_total, s["footprint"]["n"] - s["footprint"]["k"])

    def test_shares_and_intervals(self):
        for key in ["analysable", "discloses_ai", "footprint", "footprint_root", "footprint_at_head_today",
                    "footprint_among_disclosing", "footprint_among_rest", "footprint_not_disclosing"]:
            block = self.s[key]
            with self.subTest(key=key):
                self.assertAlmostEqual(block["share"], block["k"] / block["n"], delta=0.00051)
                lo, hi = wilson(block["k"], block["n"])
                self.assertAlmostEqual(block["wilson95"][0], lo, delta=0.0002)
                self.assertAlmostEqual(block["wilson95"][1], hi, delta=0.0002)

    def test_grades_follow_preregistered_rules(self):
        s = self.s
        b1 = 0.01 <= s["footprint"]["k"] / s["footprint"]["n"] <= 0.10
        b2_n = s["footprint_not_disclosing"]["n"]
        self.assertGreaterEqual(b2_n, 10)
        b2 = s["footprint_not_disclosing"]["k"] / b2_n >= 0.30
        b3 = s["analysable"]["k"] / s["ranked"] >= 0.80
        want = {"B1": "held" if b1 else "failed", "B2": "held" if b2 else "failed",
                "B3": "held" if b3 else "failed"}
        self.assertEqual(s["grades"], want)
        self.assertEqual(want, {"B1": "held", "B2": "held", "B3": "failed"})

    def test_small_cells_hidden(self):
        s = self.s
        cells = []
        for v in s["families"].values():
            cells.append(v)
        for v in s["footprint_by_kind"].values():
            cells.append(v)
        for row in s["crosstab_analysable"].values():
            cells.extend(row.values())
        for v in cells:
            if isinstance(v, int):
                self.assertFalse(1 <= v <= 4, v)
            else:
                self.assertEqual(v, "fewer than 5")

    def test_no_names_or_links_to_entries(self):
        with open(SUMMARY, encoding="utf-8") as f:
            raw = f.read()
        self.assertNotIn("itch.io/", raw)
        self.assertNotIn("github.com/", raw)
        self.assertNotIn("rate_id", raw)


class TestResultsText(unittest.TestCase):
    def setUp(self):
        self.t = read_results()

    def test_quotes_the_same_numbers(self):
        for needle in ["17 of 533", "6 of 17", "533 of 690", "11 of 122", "6 of 411", "19 of 542",
                       "14 of 533", "**690**", "**668**", "**621**", "**69**", "**72**",
                       "35.3%", "77.2%", "3.2%"]:
            with self.subTest(needle=needle):
                self.assertIn(needle, self.t)

    def test_grade_table(self):
        self.assertRegex(self.t, r"\| B1 \|[^\n]*\*\*held\*\*")
        self.assertRegex(self.t, r"\| B2 \|[^\n]*\*\*held\*\*")
        self.assertRegex(self.t, r"\| B3 \|[^\n]*\*\*failed\*\*")
        self.assertIn("B1 held, B2 held, B3 failed", self.t)

    def test_privacy_and_wording(self):
        t = self.t
        self.assertIsNone(re.search(r"\bMIT\b", t))
        for link in re.findall(r"github\.com/[^\s)\]]+", t):
            self.assertTrue(link.startswith("github.com/munimtechnologies/"), link)
        self.assertNotIn("itch.io/jam/game-off-2025/rate", t)
        self.assertNotIn("dishonest", t)
        self.assertNotIn("MV2 is an AI", t)
        self.assertNotIn("MV2, an AI", t)
        self.assertIn("made with AI agents", t)
        self.assertIn("CC BY 4.0", t)


if __name__ == "__main__":
    unittest.main()
