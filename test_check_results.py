# Tests for check_results.py. Expected values are worked out by hand in the comments.
# By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
import copy
import csv
import json
import os
import tempfile
import unittest

import check_results as cr

COLS = ["jam", "policy", "group", "rank", "ratings", "score", "raw", "pct_rank", "pct_raw",
        "pct_graphics", "pct_audio", "ai_class", "ai_parts", "engines", "web", "page_status"]


def row(jam, group, rank, pct, cls, parts="", graphics="", status="200"):
    return {"jam": jam, "policy": "x", "group": group, "rank": str(rank), "ratings": "10",
            "score": "3.0000", "raw": "3.0000", "pct_rank": pct, "pct_raw": pct,
            "pct_graphics": graphics, "pct_audio": "", "ai_class": cls, "ai_parts": parts,
            "engines": "godot", "web": "1", "page_status": status}


ROWS = [
    row("j1", "ai_not_banned", 1, "0.8000", "yes"),
    row("j1", "ai_not_banned", 2, "0.6000", "", status="not_sampled"),
    row("j1", "ai_not_banned", 3, "0.4000", "no"),
    row("j1", "ai_not_banned", 4, "0.2000", "unanswered"),
    row("j2", "ai_not_banned", 1, "0.9000", "yes", parts="code;graphics", graphics="0.9000"),
    row("j2", "ai_not_banned", 2, "0.5000", "no", graphics="0.3000"),
    row("b1", "ai_banned", 5, "0.7300", "yes", parts="audio"),
    row("b1", "ai_banned", 6, "0.5000", "", status="not_sampled"),
    row("b1", "ai_banned", 9, "0.2000", "no"),
]


def side(na, nb, diff):
    d = {"n_a": na, "n_b": nb, "jams": 0, "diff": diff, "p": None, "ci95": None}
    return {"raw": d, "rank": dict(d)}


def jam(name, ranked, yes, no, un):
    out = {"jam": name, "ranked": ranked, "both": 0, "mean_pct_raw_both": None}
    for c, v in (("yes", yes), ("no", no), ("unanswered", un)):
        out[c] = 1 if v is not None else 0
        out["mean_pct_raw_" + c] = v
    return out


SUMMARY = {
    "entries": 9, "classified": 7,
    "jams": [jam("j1", 4, 0.8, 0.4, 0.2), jam("j2", 2, 0.9, 0.5, None), jam("b1", 3, 0.73, 0.2, None)],
    "groups": {
        "ai_not_banned": {
            # yes (0.8 + 0.9) / 2 = 0.85; rest (0.4 + 0.2 + 0.5) / 3 = 0.36667; diff 0.48333
            "yes_vs_rest": side(2, 3, 0.4833),
            # yes 0.85; no (0.4 + 0.5) / 2 = 0.45; diff 0.4
            "yes_vs_no": side(2, 2, 0.4),
            # only j1 has both: 0.4 - 0.2
            "no_vs_unanswered": side(1, 1, 0.2),
            # j2 only: AI graphics 0.9 against the "no" entry's 0.3
            "yes_graphics_vs_rest_on_graphics": {"n_a": 1, "n_b": 1, "diff": 0.6},
            "yes_audio_vs_rest_on_audio": {"n_a": 0, "n_b": 0, "diff": None},
        },
        "ai_banned": {
            "yes_vs_rest": side(1, 1, 0.53),
            "yes_vs_no": side(1, 1, 0.53),
            "no_vs_unanswered": side(0, 0, None),
            "yes_graphics_vs_rest_on_graphics": {"n_a": 0, "n_b": 0, "diff": None},
            # one AI-audio entry but no audio places at all, so no comparison
            "yes_audio_vs_rest_on_audio": {"n_a": 0, "n_b": 0, "diff": None},
        },
    },
}


class CheckTest(unittest.TestCase):
    def test_pooled_diff_by_hand(self):
        got, na, nb = cr.pooled_diff(ROWS[:6], ("yes",), ("no", "unanswered"), "pct_raw")
        self.assertAlmostEqual(got, 0.85 - 1.1 / 3, places=9)
        self.assertEqual((na, nb), (2, 3))
        got, na, nb = cr.pooled_diff(ROWS[:6], ("no",), ("unanswered",), "pct_raw")
        self.assertAlmostEqual(got, 0.2, places=9)
        self.assertEqual((na, nb), (1, 1))

    def test_consistent_summary_passes(self):
        self.assertEqual(cr.check(ROWS, SUMMARY), [])

    def test_changed_count_and_diff_are_caught(self):
        s = copy.deepcopy(SUMMARY)
        s["jams"][0]["yes"] = 2
        s["groups"]["ai_not_banned"]["yes_vs_no"]["raw"]["diff"] = 0.41
        bad = cr.check(ROWS, s)
        self.assertEqual(len(bad), 2)
        self.assertTrue(any("j1 yes 1 != 2" in b for b in bad))
        self.assertTrue(any("yes_vs_no raw diff" in b for b in bad))

    def test_redact(self):
        out = cr.redact(ROWS)
        self.assertEqual(len(out), 8)   # the unsampled b1 row is dropped
        self.assertEqual(out[:6], ROWS[:6])   # jams that allow AI are untouched
        banned = out[6:]
        self.assertEqual([r["ai_class"] for r in banned], ["no", "yes"])
        yes = banned[1]
        for k in ("rank", "ratings", "score", "raw", "engines"):
            self.assertEqual(yes[k], "")
        self.assertEqual(yes["pct_raw"], "0.7")
        self.assertEqual(yes["pct_rank"], "0.7")
        self.assertEqual(yes["pct_graphics"], "")
        self.assertEqual(yes["ai_parts"], "audio")
        self.assertEqual(ROWS[6]["rank"], "5")   # input not changed in place

    def test_main_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            run = os.path.join(d, "run")
            os.makedirs(run)
            with open(os.path.join(run, "entries_public.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=COLS)
                w.writeheader()
                w.writerows(ROWS)
            with open(os.path.join(run, "summary.json"), "w", encoding="utf-8") as f:
                json.dump(SUMMARY, f)
            out = os.path.join(d, "out")
            self.assertEqual(cr.main(["--run-dir", run, "--out", out]), 0)
            with open(os.path.join(out, "check.json"), encoding="utf-8") as f:
                res = json.load(f)
            self.assertEqual((res["ok"], res["rows_in"], res["rows_out"]), (True, 9, 8))
            with open(os.path.join(out, "entries_public_redacted.csv"), newline="", encoding="utf-8") as f:
                red = list(csv.DictReader(f))
            self.assertEqual(list(red[0].keys()), COLS)
            self.assertFalse(any(r["rank"] for r in red if r["group"] == "ai_banned"))


if __name__ == "__main__":
    unittest.main()
