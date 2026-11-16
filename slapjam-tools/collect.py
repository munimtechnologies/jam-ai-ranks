# SPDX-License-Identifier: Apache-2.0
# slapjam-tools: collect the public results and the optional public "tools checklist" answers of
# itch.io's Slapjam AI jams (AI use is REQUIRED there), to see which tools entrants report and
# whether reporting relates to judged rank. Made with AI agents for MV2 of Munim, Inc.
# Stdlib only. Polite: one request every --delay seconds, generic user agent, public pages only.
# Author names are NOT written to the CSV (titles and itch entry ids only).
import argparse
import csv
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; jam-results-census/0.1)"
QUESTION = "Which of these did your game use?"
CRITERIA = ["Overall", "Fun", "Visual Appeal", "Theme Following"]


def fetch(url, delay):
    time.sleep(delay)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, ""
            if e.code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            return e.code, ""
        except Exception:
            time.sleep(10 * (attempt + 1))
    return -1, ""


def to_lines(page):
    page = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?i)<br\s*/?>", "\n", page)
    page = re.sub(r"<[^>]+>", "\n", page)
    page = html.unescape(page)
    out = []
    for ln in page.split("\n"):
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln:
            out.append(ln)
    return out


def rate_ids(page, slug):
    seen = []
    for m in re.finditer(r"/jam/%s/rate/(\d+)" % re.escape(slug), page):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def parse_entry(page):
    """Return dict with title, ratings, per-criterion rank/score/raw and the checklist answer lines."""
    rec = {}
    m = re.search(r"(?is)<title>(.*?)</title>", page)
    t = html.unescape(m.group(1)).strip() if m else ""
    m2 = re.match(r"(.*) by .* for .*$", t)
    rec["title"] = (m2.group(1) if m2 else t).strip()
    lines = to_lines(page)
    text = "\n".join(lines)
    m = re.search(r"Ranked from (\d+) ratings?", text)
    rec["ratings"] = int(m.group(1)) if m else ""
    for c in CRITERIA:
        rec[c] = ("", "", "")
        for i, ln in enumerate(lines):
            if ln == c and i + 3 < len(lines) and re.fullmatch(r"#\d+", lines[i + 1]):
                rec[c] = (lines[i + 1][1:], lines[i + 2], lines[i + 3])
                break
    ans = []
    for i, ln in enumerate(lines):
        if ln == QUESTION:
            for nxt in lines[i + 1:i + 9]:
                if (nxt.endswith("?") or nxt in CRITERIA or nxt.startswith("Ranked")
                        or nxt in ("Leave a comment", "Comments", "Results", "Criteria", "Submitted")):
                    break
                ans.append(nxt)
            break
    rec["answer_lines"] = ans
    rec["question_present"] = QUESTION in lines
    return rec


def run(slug, out, delay, max_pages):
    os.makedirs(os.path.join(out, slug, "pages"), exist_ok=True)
    ids = []
    for p in range(1, max_pages + 1):
        st, page = fetch("https://itch.io/jam/%s/results?page=%d" % (slug, p), delay)
        print(slug, "results page", p, "status", st, flush=True)
        if st != 200:
            break
        new = [i for i in rate_ids(page, slug) if i not in ids]
        if not new:
            break
        ids.extend(new)
    print(slug, "entries found", len(ids), flush=True)
    rows = []
    for n, rid in enumerate(ids, 1):
        st, page = fetch("https://itch.io/jam/%s/rate/%s" % (slug, rid), delay)
        rec = parse_entry(page) if st == 200 else {"title": "", "answer_lines": [], "question_present": False}
        lines = to_lines(page) if page else []
        with open(os.path.join(out, slug, "pages", rid + ".txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        row = {"jam": slug, "rate_id": rid, "status": st, "results_order": n, "title": rec.get("title", ""),
               "ratings": rec.get("ratings", ""), "question_present": int(rec.get("question_present", False)),
               "answer": " | ".join(rec.get("answer_lines", []))}
        for c in CRITERIA:
            r = rec.get(c, ("", "", ""))
            key = c.lower().replace(" ", "_")
            row[key + "_rank"], row[key + "_score"], row[key + "_raw"] = r
        rows.append(row)
        if n % 25 == 0:
            print(slug, "entries fetched", n, flush=True)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--slugs", default="slapjam-ai-2,slapjam-ai-1,slapjam-ai")
    ap.add_argument("--delay", type=float, default=2.5)
    ap.add_argument("--max-pages", type=int, default=30)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    allrows = []
    for slug in a.slugs.split(","):
        allrows.extend(run(slug.strip(), a.out, a.delay, a.max_pages))
    if not allrows:
        print("NO_ROWS")
        return 1
    keys = list(allrows[0].keys())
    with open(os.path.join(a.out, "entries.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(allrows)
    print("COLLECT_OK rows=%d" % len(allrows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
