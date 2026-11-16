# SPDX-License-Identifier: Apache-2.0
# Unit tests for collect.py / analyze.py (stdlib only). Made with AI agents for MV2 of Munim, Inc.
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import analyze  # noqa: E402
import collect  # noqa: E402

PAGE = """<html><head><title>Demo Game by someone for Slapjam #2 - itch.io</title>
<script>var x = "Overall";</script></head><body>
<a href="/jam/slapjam-ai-2/rate/111">View</a><a href="/jam/slapjam-ai-2/rate/111">again</a>
<a href="/jam/slapjam-ai-2/rate/222">b</a>
<div class="field_responses"><p><strong>Which of these did your game use?</strong><br>Tool A, Tool B</p></div>
<p>Ranked from 4 ratings. Score is adjusted from raw score by the median number of ratings per game in the jam.</p>
<table><tr><th>Criteria</th><th>Rank</th><th>Score*</th><th>Raw Score</th></tr>
<tr><td><a href="#">Fun</a></td><td>#1</td><td>4.500</td><td>4.500</td></tr>
<tr><td><a href="#">Overall</a></td><td>#3</td><td>4.000</td><td>4.250</td></tr></table>
<h2>Leave a comment</h2></body></html>"""


class T(unittest.TestCase):
    def test_ids_dedup_in_order(self):
        self.assertEqual(collect.rate_ids(PAGE, "slapjam-ai-2"), ["111", "222"])

    def test_parse(self):
        r = collect.parse_entry(PAGE)
        self.assertEqual(r["title"], "Demo Game")
        self.assertEqual(r["ratings"], 4)
        self.assertEqual(r["Overall"], ("3", "4.000", "4.250"))
        self.assertEqual(r["Fun"], ("1", "4.500", "4.500"))
        self.assertEqual(r["Visual Appeal"], ("", "", ""))
        self.assertTrue(r["question_present"])
        self.assertEqual(r["answer_lines"], ["Tool A, Tool B"])

    def test_groups(self):
        self.assertEqual(analyze.group({"answer": ""})[0], "blank")
        self.assertEqual(analyze.group({"answer": "None of these"})[0], "none")
        self.assertEqual(analyze.group({"answer": "Tool A, Tool B"}), ("tools", ["Tool A", "Tool B"]))
        self.assertEqual(analyze.split_answer("A | B, C"), ["A", "B", "C"])

    def test_mwu_hand_checked(self):
        # x=[1,2], y=[3,4]: ranks of x = 1,2 -> R1=3, U1 = 3 - 3 = 0; mu = 2; var = 4/12*5 = 5/3
        u, z, p = analyze.mann_whitney([1, 2], [3, 4])
        self.assertEqual(u, 0.0)
        self.assertAlmostEqual(z, -2 / (5 / 3) ** 0.5, places=9)
        self.assertTrue(0.12 < p < 0.13)  # 2*(1-Phi(1.549)) = 0.1213

    def test_median(self):
        self.assertEqual(analyze.median([3, 1, 2]), 2)
        self.assertEqual(analyze.median([4, 1, 2, 3]), 2.5)


if __name__ == "__main__":
    unittest.main()
