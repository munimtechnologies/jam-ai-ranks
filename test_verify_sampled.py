# Tests for verify_sampled.py, on the hand-worked fixture of test_check_results.py.
# By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
import copy
import csv
import json
import os
import tempfile
import unittest

import verify_sampled as vs
from test_check_results import ROWS, SUMMARY

SAMPLED = [r for r in ROWS if r["page_status"] != "not_sampled"]   # 7 rows


def summary():
    s = copy.deepcopy(SUMMARY)
    for j, n in zip(s["jams"], (3, 2, 2)):   # j1, j2, b1 sampled rows
        j["sampled"] = n
    return s


COUNTS = {"ranked": {"j1": 4, "j2": 2, "b1": 3}, "not_sampled": 2}


def write_parts(d, rows, split=4):
    for i, chunk in enumerate((rows[:split], rows[split:])):
        with open(os.path.join(d, "part%d.csv" % (i + 1)), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in chunk:
                w.writerow([r[c] for c in vs.COLS])
            f.write("\r\n")   # a trailing blank line is skipped


class VerifyTest(unittest.TestCase):
    def test_consistent_copy_passes_and_whole_run_checks_are_set_aside(self):
        bad, notes = vs.verify(SAMPLED, summary(), COUNTS)
        self.assertEqual(bad, [])
        # entries 7 vs 9; j1 has 3 of 4 rows, b1 2 of 3; j2 is complete so no note
        self.assertEqual(sorted(notes), ["b1 ranked 2 != 3", "entries 7 != 9", "j1 ranked 3 != 4"])

    def test_wrong_counts_are_caught(self):
        counts = copy.deepcopy(COUNTS)
        counts["ranked"]["j1"] = 5
        bad, _ = vs.verify(SAMPLED, summary(), counts)
        # 5 + 2 + 3 = 10 rows, not 9; 10 - 7 = 3 unsampled, not 2; j1 5 != 4
        self.assertEqual(len(bad), 3)
        self.assertTrue(any("j1 counted ranked 5 != 4" in b for b in bad))

    def test_copy_typo_is_caught(self):
        rows = copy.deepcopy(SAMPLED)
        rows[0]["pct_raw"] = "0.9000"   # j1 yes was 0.8000
        bad, _ = vs.verify(rows, summary(), COUNTS)
        self.assertTrue(any("j1 mean_pct_raw_yes" in b for b in bad))
        self.assertTrue(any("yes_vs_no raw diff" in b for b in bad))

    def test_missing_row_is_caught(self):
        bad, _ = vs.verify(SAMPLED[1:], summary(), COUNTS)
        self.assertTrue(any("j1 sampled rows 2 != 3" in b for b in bad))

    def test_robustness_by_hand(self):
        rob = vs.robustness(SAMPLED)
        yn = rob["yes_vs_no"]
        # j1: 0.8 - 0.4; j2: 0.9 - 0.5; pooled 0.85 - 0.45
        self.assertEqual(yn["per_jam"]["j1"]["diff"], 0.4)
        self.assertEqual(yn["per_jam"]["j2"]["diff"], 0.4)
        self.assertEqual(yn["pooled"], {"diff": 0.4, "n_a": 2, "n_b": 2})
        self.assertEqual(yn["leave_one_out_range"], [0.4, 0.4])
        nu = rob["no_vs_unanswered"]
        # only j1 has an unanswered entry: 0.4 - 0.2; leaving j1 out leaves nothing
        self.assertEqual(nu["per_jam"]["j1"]["diff"], 0.2)
        self.assertEqual(nu["per_jam"]["j2"], {"diff": None, "n_a": 0, "n_b": 0})
        self.assertEqual(nu["leave_one_jam_out"]["j1"]["diff"], None)
        self.assertEqual(nu["leave_one_out_range"], [0.2, 0.2])
        self.assertNotIn("b1", yn["per_jam"])   # the AI-banned jam is not in this group

    def test_load_parts_and_main(self):
        with tempfile.TemporaryDirectory() as d:
            parts = os.path.join(d, "parts")
            run = os.path.join(d, "run")
            os.makedirs(parts)
            os.makedirs(run)
            write_parts(parts, SAMPLED)
            self.assertEqual(vs.load_parts(parts), SAMPLED)
            with open(os.path.join(run, "summary.json"), "w", encoding="utf-8") as f:
                json.dump(summary(), f)
            with open(os.path.join(run, "ranked_counts.json"), "w", encoding="utf-8") as f:
                json.dump(COUNTS, f)
            out = os.path.join(d, "out")
            self.assertEqual(vs.main(["--parts", parts, "--run", run, "--out", out]), 0)
            with open(os.path.join(out, "verify.json"), encoding="utf-8") as f:
                res = json.load(f)
            self.assertEqual((res["ok"], res["sampled_rows"]), (True, 7))

    def test_short_line_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "part1.csv"), "w", encoding="utf-8") as f:
                f.write("j1,x,ai_not_banned,1\n")
            with self.assertRaises(ValueError):
                vs.load_parts(d)


if __name__ == "__main__":
    unittest.main()
