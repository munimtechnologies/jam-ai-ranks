# SPDX-License-Identifier: Apache-2.0
# slapjam-tools: summarise entries.csv (tools checklist vs judged Overall score). Stdlib only.
# Made with AI agents for MV2 of Munim, Inc.
import csv
import math
import sys
from collections import Counter


def split_answer(a):
    parts = []
    for chunk in a.split(" | "):
        for p in chunk.split(", "):
            p = p.strip()
            if p:
                parts.append(p)
    return parts


def mann_whitney(x, y):
    """Two-sided normal-approximation Mann-Whitney U with tie correction. Returns (U, z, p)."""
    allv = sorted([(v, 0) for v in x] + [(v, 1) for v in y])
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return None, None, None
    ranks = [0.0] * len(allv)
    i = 0
    ties = 0.0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        r = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[k] = r
        t = j - i + 1
        ties += t ** 3 - t
        i = j + 1
    r1 = sum(r for r, (v, g) in zip(ranks, allv) if g == 0)
    u1 = r1 - n1 * (n1 + 1) / 2.0
    n = n1 + n2
    mu = n1 * n2 / 2.0
    var = n1 * n2 / 12.0 * ((n + 1) - ties / (n * (n - 1)))
    if var <= 0:
        return u1, 0.0, 1.0
    z = (u1 - mu) / math.sqrt(var)
    p = math.erfc(abs(z) / math.sqrt(2))
    return u1, z, p


def median(v):
    v = sorted(v)
    if not v:
        return None
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2.0


def group(row):
    tools = split_answer(row["answer"])
    if not tools:
        return "blank", tools
    if tools == ["None of these"]:
        return "none", tools
    return "tools", tools


def main(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    for jam in sorted({r["jam"] for r in rows}):
        rs = [r for r in rows if r["jam"] == jam and r["status"] == "200"]
        print("== %s: %d entries fetched OK" % (jam, len(rs)))
        if not rs:
            continue
        print("question_present: %d" % sum(int(r["question_present"]) for r in rs))
        g = Counter(group(r)[0] for r in rs)
        print("groups: %s" % dict(g))
        tc = Counter()
        for r in rs:
            kind, tools = group(r)
            if kind == "tools":
                tc.update(tools)
        print("tool counts (entries ticking each):")
        for t, c in tc.most_common():
            print("  %3d  %s" % (c, t))
        scored = [r for r in rs if r["overall_score"]]
        def sc(r):
            return float(r["overall_score"])
        by = {k: [sc(r) for r in scored if group(r)[0] == k] for k in ("tools", "none", "blank")}
        for k, v in by.items():
            print("overall %s: n=%d median=%s" % (k, len(v), median(v)))
        u, z, p = mann_whitney(by["tools"], by["none"] + by["blank"])
        print("MWU tools vs (none+blank): U=%s z=%s p=%s" % (u, z, p))
        u, z, p = mann_whitney(by["tools"], by["none"])
        print("MWU tools vs none: U=%s z=%s p=%s" % (u, z, p))
        ranked = sorted(scored, key=lambda r: int(r["overall_rank"] or 9999))
        top = ranked[:10]
        print("top10 groups: %s" % dict(Counter(group(r)[0] for r in top)))
        for r in top:
            print("  #%s %s | %s | %s" % (r["overall_rank"], r["overall_score"], r["title"], r["answer"]))
        rat = [int(r["ratings"]) for r in rs if r["ratings"]]
        print("ratings: n=%d median=%s min=%s max=%s" % (len(rat), median(rat), min(rat) if rat else None,
                                                          max(rat) if rat else None))
        print("ANALYZE_OK %s" % jam)


if __name__ == "__main__":
    main(sys.argv[1])
