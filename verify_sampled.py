#!/usr/bin/env python3
# jam-ai-ranks: re-check a finished run from its sampled rows, plus leave-one-jam-out.
# By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
"""The compete sandbox cannot read an earlier run's output, so the 625 sampled rows
of run jam-ai-ranks-v2 (the only rows with an AI answer) were copied into
run/sampled/part*.csv without a header, and the per-jam row counts of all 5,125
rows were counted separately into run/ranked_counts.json. This script

1. runs check_results.check() on the sampled rows against the run's summary.json.
   The two whole-run counts (entries, ranked per jam) cannot match a sampled copy,
   so those are compared with ranked_counts.json instead;
2. checks that each jam has exactly summary["jams"][i]["sampled"] sampled rows;
3. reports, for jams that don't ban AI, each jam's own differences and the pooled
   differences with one jam left out at a time, to see whether one jam drives them.

    python verify_sampled.py --parts sampled --run run --out out
"""

import argparse
import csv
import glob
import json
import os
import sys

import check_results as cr

COLS = ["jam", "policy", "group", "rank", "ratings", "score", "raw", "pct_rank", "pct_raw",
        "pct_graphics", "pct_audio", "ai_class", "ai_parts", "engines", "web", "page_status"]
WHOLE_RUN = ("entries ",)


def load_parts(folder):
    rows = []
    for path in sorted(glob.glob(os.path.join(folder, "part*.csv"))):
        with open(path, newline="", encoding="utf-8") as f:
            for rec in csv.reader(f):
                if not rec:
                    continue
                if len(rec) != len(COLS):
                    raise ValueError("%s: %d fields in %r" % (path, len(rec), rec[:4]))
                rows.append(dict(zip(COLS, rec)))
    return rows


def is_whole_run(msg):
    return msg.startswith(WHOLE_RUN) or " ranked " in msg


def verify(rows, summary, counts):
    """(mismatches, notes): notes list the whole-run checks set aside from check()."""
    raw = cr.check(rows, summary)
    notes = [m for m in raw if is_whole_run(m)]
    bad = [m for m in raw if not is_whole_run(m)]
    ranked = counts["ranked"]
    if sum(ranked.values()) != summary["entries"]:
        bad.append("counted rows %d != entries %d" % (sum(ranked.values()), summary["entries"]))
    if sum(ranked.values()) - len(rows) != counts["not_sampled"]:
        bad.append("counted not_sampled %d != %d" % (counts["not_sampled"], sum(ranked.values()) - len(rows)))
    for j in summary["jams"]:
        if ranked.get(j["jam"]) != j["ranked"]:
            bad.append("%s counted ranked %s != %d" % (j["jam"], ranked.get(j["jam"]), j["ranked"]))
        n = sum(1 for r in rows if r["jam"] == j["jam"])
        if n != j["sampled"]:
            bad.append("%s sampled rows %d != %d" % (j["jam"], n, j["sampled"]))
    if any(r["page_status"] == "not_sampled" for r in rows):
        bad.append("a not_sampled row is in the sampled copy")
    return bad, notes


def r4(x):
    return None if x is None else round(x, 4)


def robustness(rows, group="ai_not_banned"):
    """Each jam's own difference, and the pooled difference without each jam."""
    gs = [r for r in rows if r["group"] == group and r["ai_class"]]
    jams = sorted({r["jam"] for r in gs})
    out = {}
    for name, (a, b) in cr.SIDES.items():
        per_jam, without = {}, {}
        for j in jams:
            d, na, nb = cr.pooled_diff([r for r in gs if r["jam"] == j], a, b, "pct_raw")
            per_jam[j] = {"diff": r4(d), "n_a": na, "n_b": nb}
            d, na, nb = cr.pooled_diff([r for r in gs if r["jam"] != j], a, b, "pct_raw")
            without[j] = {"diff": r4(d), "n_a": na, "n_b": nb}
        d, na, nb = cr.pooled_diff(gs, a, b, "pct_raw")
        known = [v["diff"] for v in without.values() if v["diff"] is not None]
        out[name] = {"pooled": {"diff": r4(d), "n_a": na, "n_b": nb}, "per_jam": per_jam,
                     "leave_one_jam_out": without,
                     "leave_one_out_range": [min(known), max(known)] if known else None}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--parts", required=True, help="folder with part*.csv (no header)")
    ap.add_argument("--run", required=True, help="folder with summary.json and ranked_counts.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rows = load_parts(a.parts)
    with open(os.path.join(a.run, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    with open(os.path.join(a.run, "ranked_counts.json"), encoding="utf-8") as f:
        counts = json.load(f)
    bad, notes = verify(rows, summary, counts)
    result = {"ok": not bad, "mismatches": bad, "set_aside_whole_run_checks": notes,
              "sampled_rows": len(rows), "robustness_ai_not_banned": robustness(rows)}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "verify.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result, indent=1))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
