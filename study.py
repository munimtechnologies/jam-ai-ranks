#!/usr/bin/env python3
# jam-ai-ranks: do itch.io jam entries that disclose generative AI rank differently?
# By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
"""Read each jam's public results pages, then each ranked entry's game page, and
sort the entry by the page's own Generative AI disclosure (itch.io, since
November 2024): "yes" (an AI Disclosure row: AI Assisted, plus Code / Graphics /
Sounds / Text), "no" ("No generative AI was used") or "unanswered" (neither).
Then compare where each group ranks inside its own jam.

One request at a time, at least --delay seconds apart, public pages only. No
names, usernames or game addresses are written to the public outputs.

    python study.py --jams jams.csv --out out --delay 1.0 --deadline-minutes 300
"""

import argparse
import csv
import html
import json
import os
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.request

VERSION = "0.1.0"
UA = ("MV2-jam-study/%s (Munim, Inc.; munimversion2@gmail.com; "
      "public pages only, one request at a time)" % VERSION)

ANCHOR = re.compile(r'<a\b[^>]*?\bhref\s*=\s*(["\'])(.*?)\1[^>]*>', re.I | re.S)
ROW = re.compile(r'</?tr\b[^>]*>', re.I)
TAG = re.compile(r'<[^>]+>', re.S)
DROP = re.compile(r'<(script|style)\b.*?</\1\s*>', re.I | re.S)
LINK = re.compile(r'\[\[(.*?)\]\]')
RANKED = re.compile(r'Ranked\s+(\d+)\s*(?:st|nd|rd|th)\s+with\s+([\d,]+)\s+ratings?'
                    r'\s*\(\s*Score:\s*(\d+(?:\.\d+)?)\s*\)', re.I)
GAME = re.compile(r'^https?://([a-z0-9_-]+)\.itch\.io/([A-Za-z0-9_-]+)/?$', re.I)
CRIT = re.compile(r'^(?:\[\[[^\]]*\]\]\s*)?(.+?)\s+#\s*(\d+)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$')
PAGES = re.compile(r'Page\s+\d+\s+of\s+(\d+)', re.I)
BROWSE = re.compile(r'^(?:https?://itch\.io)?/games/([a-z0-9-]+)/?$', re.I)

AI_PART = {
    "ai-code": "code", "ai-graphics": "graphics", "ai-audio": "audio", "ai-text": "text",
    "tag-ai-generated-code": "code", "tag-ai-generated-graphics": "graphics",
    "tag-ai-generated-audio": "audio", "tag-ai-generated-text": "text",
}
NOT_A_GAME_HOST = {"www", "static", "img", "itch"}
GRAPHICS = re.compile(r"graphic|visual|art\b|aesthetic", re.I)
AUDIO = re.compile(r"audio|sound|music", re.I)


def flatten(page):
    """HTML -> one line of text: links become [[href]], table rows are cut by a broken bar."""
    page = DROP.sub(" ", page)
    page = ROW.sub(" ¦ ", page)
    page = ANCHOR.sub(lambda m: " [[%s]] " % html.unescape(m.group(2)).strip(), page)
    page = TAG.sub(" ", page)
    page = html.unescape(page)
    return re.sub(r"\s+", " ", page).strip()


def results_url(slug, page_no):
    base = "https://itch.io/jam/%s/results" % slug
    return base if page_no == 1 else "%s?page=%d" % (base, page_no)


def page_count(page):
    m = PAGES.search(flatten(page))
    return int(m.group(1)) if m else 1


def game_links(text):
    out = []
    for m in LINK.finditer(text):
        g = GAME.match(m.group(1))
        if g and g.group(1).lower() not in NOT_A_GAME_HOST:
            out.append((m.start(), m.group(1).rstrip("/")))
    return out


def parse_results(page, slug):
    """Ranked entries on one results page. The title link sits just before the
    'Ranked ...' line and the criteria table just after it."""
    text = flatten(page)
    ranks = list(RANKED.finditer(text))
    games = game_links(text)
    rate = re.compile(r"\[\[[^\]]*/jam/%s/rate/(\d+)[^\]]*\]\]" % re.escape(slug))
    rates = [(m.start(), m.group(1)) for m in rate.finditer(text)]
    entries = []
    for i, r in enumerate(ranks):
        lo = ranks[i - 1].end() if i else 0
        hi = ranks[i + 1].start() if i + 1 < len(ranks) else len(text)
        before = [u for p, u in games if lo <= p < r.start()]
        near = [(abs(p - r.start()), rid) for p, rid in rates if lo <= p < hi]
        criteria = {}
        for seg in text[r.end():hi].split("¦"):
            m = CRIT.match(seg.strip())
            if m:
                name = LINK.sub("", m.group(1)).strip()
                if name and name not in criteria:
                    criteria[name] = {"rank": int(m.group(2)), "score": float(m.group(3)),
                                      "raw": float(m.group(4))}
        overall = criteria.get("Overall")
        entries.append({
            "rank": int(r.group(1)),
            "ratings": int(r.group(2).replace(",", "")),
            "score": float(r.group(3)),
            "raw": overall["raw"] if overall else float(r.group(3)),
            "game": before[-1] if before else "",
            "rate_id": min(near)[1] if near else "",
            "criteria": criteria,
        })
    return entries


def classify(page):
    """The game page's own Generative AI disclosure: (class, parts, engines, web)."""
    slugs = []
    for m in ANCHOR.finditer(page):
        b = BROWSE.match(html.unescape(m.group(2)).strip())
        if b:
            slugs.append(b.group(1).lower())
    yes = any(s == "ai-assisted" or s in AI_PART or s.startswith("tag-ai-generated") for s in slugs)
    no = "tag-no-ai" in slugs or "no generative ai was used" in flatten(page).lower()
    cls = "both" if yes and no else "yes" if yes else "no" if no else "unanswered"
    parts = sorted({AI_PART[s] for s in slugs if s in AI_PART})
    engines = sorted({s[len("made-with-"):] for s in slugs if s.startswith("made-with-")})
    web = "html_embed" in page or "html5" in slugs or "platform-web" in slugs
    return cls, parts, engines, web


class Fetcher:
    """GET with a fixed gap between requests; backs off and slows down on 429 and 5xx."""

    def __init__(self, delay=1.0, log=print):
        self.delay, self.log, self.last, self.count = delay, log, 0.0, 0

    def __call__(self, url):
        for attempt in range(4):
            wait = self.last + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            self.count += 1
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return r.status, r.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                    if e.code == 429:
                        self.delay = min(self.delay * 2, 10.0)
                    after = e.headers.get("Retry-After", "") if e.headers else ""
                    pause = float(after) if after.isdigit() else 10 * 3 ** attempt
                    self.log("  %d on %s, waiting %.0f s" % (e.code, url, pause))
                    time.sleep(min(pause, 300))
                    continue
                return e.code, ""
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if attempt < 3:
                    self.log("  %s on %s, retrying" % (type(e).__name__, url))
                    time.sleep(10 * 3 ** attempt)
                    continue
                return 0, ""
        return 0, ""


def collect(jams, fetch, deadline, log=print, samples=None, max_pages=200):
    """All ranked entries of every jam, each with its game page's disclosure."""
    rows = []
    for jam in jams:
        slug = jam["slug"]
        entries, seen, page_no, total = [], set(), 1, 1
        while page_no <= min(total, max_pages) and time.monotonic() < deadline:
            status, page = fetch(results_url(slug, page_no))
            if status != 200:
                log("%s: results page %d returned %s" % (slug, page_no, status))
                break
            if page_no == 1:
                total = page_count(page)
                if samples:
                    save(os.path.join(samples, "results-%s.html" % slug), page)
            got = parse_results(page, slug)
            if not got:
                log("%s: no ranked entries on page %d" % (slug, page_no))
                break
            for e in got:
                key = e["game"] or ("rate:" + e["rate_id"])
                if key not in seen:
                    seen.add(key)
                    entries.append(e)
            page_no += 1
        log("%s: %d ranked entries from %d of %d results pages, %d without a game link"
            % (slug, len(entries), page_no - 1, total, sum(1 for e in entries if not e["game"])))
        for n, e in enumerate(entries):
            e.update({"jam": slug, "policy": jam["policy"], "group": jam["group"],
                      "ai_class": "", "ai_parts": [], "engines": [], "web": "", "page_status": ""})
            if not e["game"]:
                e["page_status"] = "no_link"
            elif time.monotonic() >= deadline:
                e["page_status"] = "not_fetched"
            else:
                status, page = fetch(e["game"])
                e["page_status"] = str(status)
                if status == 200:
                    e["ai_class"], e["ai_parts"], e["engines"], e["web"] = classify(page)
                    if samples and n < 2 and jam is jams[0]:
                        save(os.path.join(samples, "game-%s-%d.html" % (slug, n)), page)
            if n % 100 == 99:
                log("  %s: %d of %d game pages" % (slug, n + 1, len(entries)))
        add_percentiles(entries)
        rows.extend(entries)
    return rows


def save(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def mid_percentiles(values):
    """1.0 = best (highest value), 0.0 = worst; ties share the mean of their places."""
    n = len(values)
    if n < 2:
        return [0.5] * n
    out = []
    for v in values:
        lower = sum(1 for w in values if w < v)
        equal = sum(1 for w in values if w == v) - 1
        out.append((lower + 0.5 * equal) / (n - 1))
    return out


def add_percentiles(entries):
    """pct_rank from itch's own rank (ratings-adjusted); pct_raw from the raw overall score;
    pct_graphics / pct_audio from the raw score of a matching criterion, if the jam has one."""
    if not entries:
        return
    for e, p in zip(entries, mid_percentiles([-e["rank"] for e in entries])):
        e["pct_rank"] = p
    for e, p in zip(entries, mid_percentiles([e["raw"] for e in entries])):
        e["pct_raw"] = p
    for key, pattern in (("pct_graphics", GRAPHICS), ("pct_audio", AUDIO)):
        have = []
        for e in entries:
            name = next((c for c in e["criteria"] if pattern.search(c)), None)
            if name is not None:
                have.append((e, e["criteria"][name]["raw"]))
            else:
                e[key] = None
        for (e, _), p in zip(have, mid_percentiles([v for _, v in have])):
            e[key] = p


def compare(rows, a, b, key="pct_raw", iters=5000, seed=1):
    """Pooled mean of `key` for classes `a` minus classes `b`, using only jams that have
    both; a permutation test that shuffles labels inside each jam, and a bootstrap that
    resamples each class inside each jam."""
    jams = {}
    for r in rows:
        if r.get(key) is None:
            continue
        side = 0 if r["ai_class"] in a else 1 if r["ai_class"] in b else None
        if side is not None:
            jams.setdefault(r["jam"], ([], []))[side].append(r[key])
    jams = {j: s for j, s in jams.items() if s[0] and s[1]}
    na = sum(len(s[0]) for s in jams.values())
    nb = sum(len(s[1]) for s in jams.values())
    if not na or not nb:
        return {"n_a": na, "n_b": nb, "jams": len(jams), "diff": None, "p": None, "ci95": None}

    def stat(groups):
        return (sum(sum(x) for x, _ in groups) / na) - (sum(sum(y) for _, y in groups) / nb)

    groups = list(jams.values())
    diff = stat(groups)
    rng = random.Random(seed)
    extreme = 0
    for _ in range(iters):
        shuffled = []
        for x, y in groups:
            pool = x + y
            rng.shuffle(pool)
            shuffled.append((pool[:len(x)], pool[len(x):]))
        if abs(stat(shuffled)) >= abs(diff) - 1e-12:
            extreme += 1
    boots = []
    for _ in range(max(iters // 2, 200)):
        boots.append(stat([([rng.choice(x) for _ in x], [rng.choice(y) for _ in y]) for x, y in groups]))
    boots.sort()
    lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]
    return {"n_a": na, "n_b": nb, "jams": len(jams), "diff": round(diff, 4),
            "p": round((extreme + 1) / (iters + 1), 4), "ci95": [round(lo, 4), round(hi, 4)]}


def analyse(rows, iters=5000):
    fetched = [r for r in rows if r["ai_class"]]
    out = {"version": VERSION, "entries": len(rows), "classified": len(fetched), "jams": [], "groups": {}}
    for slug in dict.fromkeys(r["jam"] for r in rows):
        js = [r for r in rows if r["jam"] == slug]
        fs = [r for r in js if r["ai_class"]]
        row = {"jam": slug, "policy": js[0]["policy"], "group": js[0]["group"], "ranked": len(js),
               "classified": len(fs)}
        for c in ("yes", "no", "unanswered", "both"):
            cs = [r for r in fs if r["ai_class"] == c]
            row[c] = len(cs)
            row["mean_pct_raw_" + c] = round(statistics.mean(r["pct_raw"] for r in cs), 3) if cs else None
        row["yes_share"] = round(row["yes"] / len(fs), 4) if fs else None
        out["jams"].append(row)
    sides = {"yes_vs_rest": (("yes",), ("no", "unanswered")),
             "yes_vs_no": (("yes",), ("no",)),
             "no_vs_unanswered": (("no",), ("unanswered",))}
    for group in dict.fromkeys(r["group"] for r in rows):
        gs = [r for r in fetched if r["group"] == group]
        g = {"classified": len(gs)}
        for c in ("yes", "no", "unanswered", "both"):
            cs = [r for r in gs if r["ai_class"] == c]
            g[c] = len(cs)
            g["median_ratings_" + c] = statistics.median(r["ratings"] for r in cs) if cs else None
        for name, (a, b) in sides.items():
            g[name] = {"raw": compare(gs, a, b, "pct_raw", iters),
                       "rank": compare(gs, a, b, "pct_rank", iters)}
        part = {"graphics": "pct_graphics", "audio": "pct_audio"}
        for p, key in part.items():
            marked = [dict(r, ai_class="yes_" + p) if r["ai_class"] == "yes" and p in r["ai_parts"] else r
                      for r in gs]
            g["yes_%s_vs_rest_on_%s" % (p, p)] = compare(marked, ("yes_" + p,), ("no", "unanswered"), key, iters)
        out["groups"][group] = g
    return out


PUBLIC = ["jam", "policy", "group", "rank", "ratings", "score", "raw", "pct_rank", "pct_raw",
          "pct_graphics", "pct_audio", "ai_class", "ai_parts", "engines", "web", "page_status"]


def write_outputs(rows, summary, out):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "entries_public.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(PUBLIC)
        for r in rows:
            w.writerow([fmt(r.get(k)) for k in PUBLIC])
    # Kept on the machine for re-checks only; never published: it holds itch submission ids.
    with open(os.path.join(out, "entries_private.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rate_id"] + PUBLIC + ["criteria"])
        for r in rows:
            w.writerow([r.get("rate_id", "")] + [fmt(r.get(k)) for k in PUBLIC] + [json.dumps(r["criteria"])])
    with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as f:
        f.write(report(summary))


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return "%.4f" % v
    if isinstance(v, list):
        return ";".join(v)
    return str(v)


def report(s):
    lines = ["# Generative AI disclosure and jam rank (jam-ai-ranks %s)" % s["version"], "",
             "%d ranked entries, %d game pages classified." % (s["entries"], s["classified"]), "",
             "| jam | policy | ranked | classified | yes | no | unanswered | yes share | mean pct (yes / no / unanswered) |",
             "|---|---|---|---|---|---|---|---|---|"]
    for j in s["jams"]:
        lines.append("| %s | %s | %d | %d | %d | %d | %d | %s | %s / %s / %s |" % (
            j["jam"], j["policy"], j["ranked"], j["classified"], j["yes"], j["no"], j["unanswered"],
            j["yes_share"], j["mean_pct_raw_yes"], j["mean_pct_raw_no"], j["mean_pct_raw_unanswered"]))
    for name, g in s["groups"].items():
        lines += ["", "## %s" % name, "", "```", json.dumps(g, indent=1), "```"]
    lines += ["", "pct = place inside the entry's own jam, 1 = best, 0 = worst; raw = raw overall score,",
              "rank = itch's ratings-adjusted rank. diff = mean pct of the first classes minus the second,",
              "pooled over jams that have both; p from shuffling labels inside each jam.", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jams", default="jams.csv")
    ap.add_argument("--out", default="out")
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--deadline-minutes", type=float, default=300)
    ap.add_argument("--iters", type=int, default=5000)
    a = ap.parse_args(argv)
    with open(a.jams, newline="", encoding="utf-8") as f:
        jams = list(csv.DictReader(f))
    start = time.monotonic()

    def log(msg):
        print("[%6.0f s] %s" % (time.monotonic() - start, msg), flush=True)

    fetch = Fetcher(a.delay, log)
    rows = collect(jams, fetch, start + a.deadline_minutes * 60, log, os.path.join(a.out, "samples"))
    summary = analyse(rows, a.iters)
    summary["requests"] = fetch.count
    summary["read_at_utc"] = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
    write_outputs(rows, summary, a.out)
    log("done: %d entries, %d requests" % (len(rows), fetch.count))
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
