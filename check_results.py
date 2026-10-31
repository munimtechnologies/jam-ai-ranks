#!/usr/bin/env python3
# jam-ai-ranks: independent re-check of a finished run, and the redacted public file.
# By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
"""Re-derive a run's per-jam counts, mean places and pooled differences from its
entries_public.csv alone (no code shared with study.py) and compare them with its
summary.json. Then write entries_public_redacted.csv, the file meant for
publishing: in jams that ban AI, a row's rank, ratings, scores and engines are
removed, places are rounded to one decimal and the rows are re-sorted, so no
entry that discloses AI in a jam that bans it can be found from the data.

    python check_results.py --run-dir out --out check
"""

import argparse
import csv
import json
import os
import sys

CLASSES = ("yes", "no", "unanswered", "both")
SIDES = {"yes_vs_rest": (("yes",), ("no", "unanswered")),
         "yes_vs_no": (("yes",), ("no",)),
         "no_vs_unanswered": (("no",), ("unanswered",))}
REDACT = ("rank", "ratings", "score", "raw", "engines")
PCTS = ("pct_rank", "pct_raw", "pct_graphics", "pct_audio")
MEAN_TOL = 0.0006   # summary means are rounded to 3 places, the csv to 4
DIFF_TOL = 0.0002   # summary diffs are rounded to 4 places


def num(v):
    return float(v) if v != "" else None


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pooled_diff(rows, a, b, key):
    """Mean of `key` over classes `a` minus over classes `b`, both taken only from jams
    that have at least one row of each side with a value."""
    jams = {}
    for r in rows:
        v = num(r[key])
        if v is None:
            continue
        side = 0 if r["ai_class"] in a else 1 if r["ai_class"] in b else None
        if side is not None:
            jams.setdefault(r["jam"], ([], []))[side].append(v)
    xs = [v for s in jams.values() if s[0] and s[1] for v in s[0]]
    ys = [v for s in jams.values() if s[0] and s[1] for v in s[1]]
    if not xs or not ys:
        return None, len(xs), len(ys)
    return sum(xs) / len(xs) - sum(ys) / len(ys), len(xs), len(ys)


def check(rows, summary):
    """List of human-readable mismatches between the csv and summary.json."""
    bad = []
    classified = [r for r in rows if r["ai_class"]]
    if len(rows) != summary["entries"]:
        bad.append("entries %d != %d" % (len(rows), summary["entries"]))
    if len(classified) != summary["classified"]:
        bad.append("classified %d != %d" % (len(classified), summary["classified"]))
    for j in summary["jams"]:
        js = [r for r in rows if r["jam"] == j["jam"]]
        if len(js) != j["ranked"]:
            bad.append("%s ranked %d != %d" % (j["jam"], len(js), j["ranked"]))
        for c in CLASSES:
            vs = [float(r["pct_raw"]) for r in js if r["ai_class"] == c]
            if len(vs) != j[c]:
                bad.append("%s %s %d != %d" % (j["jam"], c, len(vs), j[c]))
            want = j["mean_pct_raw_" + c]
            got = sum(vs) / len(vs) if vs else None
            if (got is None) != (want is None) or (got is not None and abs(got - want) > MEAN_TOL):
                bad.append("%s mean_pct_raw_%s %s != %s" % (j["jam"], c, got, want))
    for group, g in summary["groups"].items():
        gs = [r for r in classified if r["group"] == group]
        for name, (a, b) in SIDES.items():
            for kind, key in (("raw", "pct_raw"), ("rank", "pct_rank")):
                got, na, nb = pooled_diff(gs, a, b, key)
                want = g[name][kind]
                if (na, nb) != (want["n_a"], want["n_b"]):
                    bad.append("%s %s %s n %s != %s" % (group, name, kind, (na, nb), (want["n_a"], want["n_b"])))
                if (got is None) != (want["diff"] is None) or (got is not None and abs(got - want["diff"]) > DIFF_TOL):
                    bad.append("%s %s %s diff %s != %s" % (group, name, kind, got, want["diff"]))
        for part in ("graphics", "audio"):
            marked = [dict(r, ai_class="yes_" + part)
                      if r["ai_class"] == "yes" and part in r["ai_parts"].split(";") else r for r in gs]
            got, na, nb = pooled_diff(marked, ("yes_" + part,), ("no", "unanswered"), "pct_" + part)
            want = g["yes_%s_vs_rest_on_%s" % (part, part)]
            if (na, nb) != (want["n_a"], want["n_b"]):
                bad.append("%s %s n %s != %s" % (group, part, (na, nb), (want["n_a"], want["n_b"])))
            if (got is None) != (want["diff"] is None) or (got is not None and abs(got - want["diff"]) > DIFF_TOL):
                bad.append("%s %s diff %s != %s" % (group, part, got, want["diff"]))
    return bad


def redact(rows):
    """Rows of jams that allow AI are kept as they are. Rows of jams that ban AI keep
    only sampled pages, lose rank, ratings, scores and engines, get places rounded to
    one decimal, and are sorted so their order says nothing about rank."""
    kept, banned = [], []
    for r in rows:
        if r["group"] != "ai_banned":
            kept.append(dict(r))
            continue
        if r["page_status"] == "not_sampled":
            continue
        r = dict(r)
        for k in REDACT:
            r[k] = ""
        for k in PCTS:
            if r[k] != "":
                r[k] = "%.1f" % round(float(r[k]), 1)
        banned.append(r)
    banned.sort(key=lambda r: (r["jam"], r["ai_class"], -float(r["pct_raw"] or 0), r["ai_parts"], r["web"]))
    return kept + banned


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run-dir", required=True, help="folder with entries_public.csv and summary.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    rows = load(os.path.join(a.run_dir, "entries_public.csv"))
    with open(os.path.join(a.run_dir, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    bad = check(rows, summary)
    os.makedirs(a.out, exist_ok=True)
    out_rows = redact(rows)
    with open(os.path.join(a.out, "entries_public_redacted.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    result = {"ok": not bad, "mismatches": bad, "rows_in": len(rows), "rows_out": len(out_rows)}
    with open(os.path.join(a.out, "check.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
    print(json.dumps(result, indent=1))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
