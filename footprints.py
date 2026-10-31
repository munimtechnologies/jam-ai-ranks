#!/usr/bin/env python3
# jam-ai-ranks footprints: AI coding-agent traces in a jam's required GitHub repositories,
# next to each game page's own generative-AI disclosure.
# By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
"""GitHub Game Off asks every entry for a public GitHub repository. This script reads every
ranked entry of one jam (all results pages and every game page, with study.py's own parsers),
takes the repository URL from each entry's submission page, and reads each repository's git
history without downloading any file contents (a blob-less bare clone). It then looks for
AI coding-agent traces in the last commit made before the submission deadline:

  path traces    files such as CLAUDE.md, AGENTS.md, GEMINI.md, .cursorrules, .cursor/,
                 .claude/, .github/copilot-instructions.md, .aider*, .windsurf/, .clinerules
  commit traces  Co-authored-by trailers and author addresses that coding agents write
                 (Claude Code, Copilot, Cursor, Codex, Gemini, aider, Windsurf, OpenHands, Devin)

Markers under vendored folders (addons/, Packages/, Plugins/, node_modules/ ...) are counted
apart, since they come with someone else's code.

Only counts are published. Repository names, game addresses and submission ids stay in
out/private/ and are never published; no entry is ever named.

    python footprints.py --jam game-off-2025 --cutoff 2025-12-01T21:37:00Z --out out
"""

import argparse
import csv
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

import study

VERSION = "0.1.0"

GITHUB = re.compile(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9._-]+)', re.I)
NOT_OWNER = {"about", "apps", "collections", "contact", "customer-stories", "enterprise", "events", "explore",
             "features", "github", "join", "login", "marketplace", "notifications", "orgs", "pricing",
             "readme", "security", "settings", "signup", "site", "sponsors", "team", "topics", "trending"}

VENDOR = {"node_modules", "vendor", "third_party", "thirdparty", "external", "addons", "packages",
          "library", "plugins"}
DIR_FAMILY = {".claude": "claude", ".cursor": "cursor", ".windsurf": "windsurf", ".clinerules": "cline",
              ".roo": "cline", ".gemini": "gemini", ".codex": "codex", ".kiro": "kiro", ".junie": "junie",
              ".continue": "continue", ".augment": "augment", ".trae": "trae", ".qwen": "qwen",
              ".opencode": "opencode", ".specstory": "specstory", ".amazonq": "amazonq"}
FILE_FAMILY = {"claude.md": "claude", "claude.local.md": "claude", "agents.md": "agents_md",
               "agent.md": "agents_md", "gemini.md": "gemini", "qwen.md": "qwen", ".cursorrules": "cursor",
               ".windsurfrules": "windsurf", ".clinerules": "cline", ".roomodes": "cline",
               "opencode.json": "opencode", ".augment-guidelines": "augment"}

TRAILER = re.compile(r'^\s*co-authored-by:\s*(.+)$', re.I | re.M)
# Words that mark a coding agent inside a Co-authored-by trailer. Human first names (Claude,
# Devin, Jules, Kiro) are not enough on their own: the agent's own address or product is needed.
TRAILER_FAMILY = [("anthropic", "claude"), ("cursor.com", "cursor"), ("cursoragent", "cursor"),
                  ("copilot", "copilot"), ("openai.com", "codex"), ("codex", "codex"), ("gemini", "gemini"),
                  ("google-labs-jules", "gemini"), ("codeium", "windsurf"), ("windsurf", "windsurf"),
                  ("openhands", "openhands"), ("all-hands.dev", "openhands"), ("devin-ai", "devin")]
EMAIL_FAMILY = [("noreply@anthropic.com", "claude"), ("cursoragent@cursor.com", "cursor"),
                ("+copilot@users.noreply.github.com", "copilot"), ("copilot-swe-agent", "copilot"),
                ("google-labs-jules", "gemini"), ("devin-ai-integration", "devin"), ("openhands", "openhands"),
                ("noreply@aider.chat", "aider")]
GENERATED = re.compile(r'generated with \[?claude code\]?', re.I)


def parse_repo(owner, name):
    """'owner/name' for a GitHub repository link, or '' for GitHub's own pages."""
    name = name.rstrip(".")
    if name.lower().endswith(".git"):
        name = name[:-4]
    if owner.lower() in NOT_OWNER or name in ("", ".", ".."):
        return ""
    return "%s/%s" % (owner, name)


def repo_from_rate_page(page):
    """The repository named on a jam submission page: the first GitHub repository link after the
    'GitHub repository URL' answer, else the first anywhere on the page, else ''."""
    text = study.flatten(page)
    at = text.lower().find("github repository url")
    for segment in ((text[at:],) if at >= 0 else ()) + (text,):
        for m in GITHUB.finditer(segment):
            repo = parse_repo(m.group(1), m.group(2))
            if repo:
                return repo
    return ""


def path_hits(path):
    """[(family, depth, vendored)] for the agent markers in one repository path; depth is the index
    of the path part that carries the marker (0 = the repository root), and vendored is true when
    a folder above it is one of VENDOR."""
    low = [p.lower() for p in path.split("/")]
    hits = []
    for i, part in enumerate(low[:-1]):
        if part in DIR_FAMILY:
            hits.append((DIR_FAMILY[part], i))
            break
    name = low[-1]
    if name in FILE_FAMILY:
        hits.append((FILE_FAMILY[name], len(low) - 1))
    elif name.startswith(".aider"):
        hits.append(("aider", len(low) - 1))
    joined = "/".join(low)
    if (joined == ".github/copilot-instructions.md"
            or (joined.startswith(".github/instructions/") and joined.endswith(".instructions.md"))
            or (joined.startswith(".github/prompts/") and joined.endswith(".prompt.md"))
            or joined.startswith(".github/chatmodes/")):
        hits.append(("copilot", 0))
    return [(fam, depth, any(p in VENDOR for p in low[:depth])) for fam, depth in hits]


def path_signals(paths):
    """Agent families found in a list of repository paths: 'families' leaves out markers under
    vendored folders, 'families_any' keeps them; 'root' is true if a counted marker is at the root."""
    fams, fams_any, root = set(), set(), False
    for p in paths:
        for fam, depth, vendored in path_hits(p):
            fams_any.add(fam)
            if not vendored:
                fams.add(fam)
                root = root or depth == 0
    return {"families": sorted(fams), "families_any": sorted(fams_any), "root": root}


def commit_signals(commits):
    """Agent families named by commits: (author name, author email, committer email, message)."""
    fams = set()
    for name, author, committer, message in commits:
        emails = ("%s %s %s" % (name, author, committer)).lower()
        for word, fam in EMAIL_FAMILY:
            if word in emails:
                fams.add(fam)
        for t in TRAILER.findall(message or ""):
            t = t.lower()
            if "aider" in t:
                fams.add("aider")
                continue
            for word, fam in TRAILER_FAMILY:
                if word in t:
                    fams.add(fam)
        if GENERATED.search(message or ""):
            fams.add("claude")
    return sorted(fams)


LOG_FORMAT = "--format=%an%x1f%ae%x1f%ce%x1f%B%x1e"


def parse_log(text):
    """git log output in LOG_FORMAT -> [(author name, author email, committer email, message)]."""
    out = []
    for rec in text.split("\x1e"):
        rec = rec.lstrip("\n")
        if not rec.strip():
            continue
        parts = rec.split("\x1f", 3)
        if len(parts) == 4:
            out.append(tuple(parts))
    return out


def git(args, cwd=None, timeout=300):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_LFS_SKIP_SMUDGE="1", GIT_ASKPASS="true")
    p = subprocess.run(["git"] + args, cwd=cwd, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return p.returncode, p.stdout


def git_date(cutoff):
    """'2025-12-01T21:37:00Z' -> '2025-12-01 21:37:00 +0000', a form every git version reads."""
    return cutoff.replace("T", " ").replace("Z", " +0000")


def read_repo(repo, cutoff, workroot, timeout=300, url=None):
    """Blob-less bare clone of one public repository; traces at the last commit before the
    cutoff (and, for the sensitivity check, at today's default branch)."""
    d = tempfile.mkdtemp(dir=workroot)
    g = os.path.join(d, "r.git")
    try:
        try:
            rc, _ = git(["-c", "credential.helper=", "clone", "--bare", "--quiet", "--filter=blob:none",
                         url or "https://github.com/%s.git" % repo, g], timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"status": "clone_timeout"}
        if rc != 0:
            return {"status": "clone_failed"}
        rc, head = git(["rev-list", "-1", "HEAD"], cwd=g)
        if rc != 0 or not head.strip():
            return {"status": "empty"}
        rc, sha = git(["rev-list", "-1", "--before=" + git_date(cutoff), "HEAD"], cwd=g)
        out = {"status": "ok" if sha.strip() else "late"}
        for label, ref in (("cut", sha.strip()), ("head", head.strip())):
            if not ref:
                continue
            _, tree = git(["ls-tree", "-r", "--name-only", "-z", ref], cwd=g)
            _, log = git(["log", LOG_FORMAT, ref], cwd=g)
            paths = [p for p in tree.split("\0") if p]
            commits = parse_log(log)
            ps = path_signals(paths)
            cs = commit_signals(commits)
            out[label] = {"paths": len(paths), "commits": len(commits), "path_families": ps["families"],
                          "path_families_any": ps["families_any"], "root": ps["root"],
                          "commit_families": cs}
        return out
    except subprocess.TimeoutExpired:
        return {"status": "git_timeout"}
    finally:
        shutil.rmtree(d, ignore_errors=True)


def footprint(side):
    """(counted families, families including vendored markers) for one read of a repository."""
    if not side:
        return [], []
    fams = sorted(set(side["path_families"]) | set(side["commit_families"]))
    fams_any = sorted(set(side["path_families_any"]) | set(side["commit_families"]))
    return fams, fams_any


def _wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def wilson(k, n):
    """95% Wilson score interval for k of n, or None when n is 0."""
    if not n:
        return None
    lo, hi = _wilson(k, n)
    return [round(lo, 4), round(hi, 4)]


def newcombe(k1, n1, k2, n2):
    """Difference k1/n1 - k2/n2 with Newcombe's 95% hybrid score interval."""
    if not n1 or not n2:
        return None
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = _wilson(k1, n1)
    l2, u2 = _wilson(k2, n2)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return {"diff": round(d, 4), "ci95": [round(lo, 4), round(hi, 4)]}


def share(k, n):
    return {"k": k, "n": n, "share": round(k / n, 4) if n else None, "wilson95": wilson(k, n)}


CLASSES = ("yes", "no", "unanswered", "both")


def analyse(rows, jam, cutoff, iters=2000):
    """Counts only: no repository, game or entry is named."""
    s = {"version": VERSION, "jam": jam, "cutoff": cutoff, "ranked": len(rows)}
    s["game_pages_read"] = sum(1 for r in rows if r["page_status"] == "200")
    s["disclosure_counts"] = {c: sum(1 for r in rows if r["ai_class"] == c) for c in CLASSES}
    classified = [r for r in rows if r["ai_class"] in CLASSES]
    s["discloses_ai"] = share(sum(1 for r in classified if r["ai_class"] in ("yes", "both")), len(classified))
    s["repo_found"] = sum(1 for r in rows if r["repo"])
    s["repo_status"] = {}
    for r in rows:
        if r["repo"]:
            s["repo_status"][r["repo_status"]] = s["repo_status"].get(r["repo_status"], 0) + 1
    ok = [r for r in rows if r["repo_status"] == "ok"]
    fp = [r for r in ok if r["fp"]]
    s["footprint"] = share(len(fp), len(ok))
    s["footprint_incl_vendored"] = share(sum(1 for r in ok if r["fp_any"]), len(ok))
    s["footprint_root"] = share(sum(1 for r in ok if r["fp_root"]), len(ok))
    s["footprint_path_only"] = sum(1 for r in fp if r["fp_path"] and not r["fp_commit"])
    s["footprint_commit_only"] = sum(1 for r in fp if r["fp_commit"] and not r["fp_path"])
    s["footprint_path_and_commit"] = sum(1 for r in fp if r["fp_path"] and r["fp_commit"])
    head = [r for r in rows if r["repo_status"] in ("ok", "late")]
    s["footprint_at_head_today"] = share(sum(1 for r in head if r["fp_head"]), len(head))
    fams = {}
    for r in fp:
        for f in r["fp_families"]:
            fams[f] = fams.get(f, 0) + 1
    s["families"] = dict(sorted(fams.items(), key=lambda kv: (-kv[1], kv[0])))
    s["crosstab"] = {c: {"footprint": sum(1 for r in fp if r["ai_class"] == c),
                         "none": sum(1 for r in ok if not r["fp"] and r["ai_class"] == c)}
                     for c in CLASSES + ("",)}
    fpc = [r for r in fp if r["ai_class"] in CLASSES]
    s["footprint_not_disclosing"] = share(sum(1 for r in fpc if r["ai_class"] in ("no", "unanswered")), len(fpc))
    s["footprint_says_no_ai"] = share(sum(1 for r in fpc if r["ai_class"] == "no"), len(fpc))
    s["places"] = {}
    for key in ("pct_raw", "pct_rank"):
        p = {"yes_vs_no": study.compare(rows, ("yes",), ("no",), key, iters),
             "no_vs_unanswered": study.compare(rows, ("no",), ("unanswered",), key, iters),
             "yes_vs_rest": study.compare(rows, ("yes",), ("no", "unanswered"), key, iters)}
        marked = [dict(r, ai_class="fp" if r["fp"] else "none") for r in ok]
        p["footprint_vs_none"] = study.compare(marked, ("fp",), ("none",), key, iters)
        s["places"][key] = p
    return s


PRIVATE = ["rank", "rate_id", "game", "repo", "repo_status", "ai_class", "ai_parts", "engines", "pct_raw",
           "pct_rank", "fp", "fp_any", "fp_root", "fp_path", "fp_commit", "fp_head", "fp_families",
           "commits_before_cutoff"]


def write_private(rows, out):
    """Row file for re-checks on the machine only; it names repositories, so it is never published."""
    os.makedirs(os.path.join(out, "private"), exist_ok=True)
    with open(os.path.join(out, "private", "rows.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(PRIVATE)
        for r in rows:
            w.writerow([study.fmt(r.get(k)) for k in PRIVATE])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jam", required=True)
    ap.add_argument("--cutoff", required=True, help="submission deadline, e.g. 2025-12-01T21:37:00Z")
    ap.add_argument("--out", default="out")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between itch.io requests")
    ap.add_argument("--clone-gap", type=float, default=1.0, help="seconds between clones")
    ap.add_argument("--deadline-minutes", type=float, default=170)
    ap.add_argument("--iters", type=int, default=2000)
    a = ap.parse_args(argv)
    start = time.monotonic()
    deadline = start + a.deadline_minutes * 60

    def log(msg):
        print("[%6.0f s] %s" % (time.monotonic() - start, msg), flush=True)

    fetch = study.Fetcher(a.delay, log)
    notes = {}
    samples = os.path.join(a.out, "private", "samples")
    rows = study.collect([{"slug": a.jam, "policy": "not_stated", "group": "ai_not_banned"}], fetch,
                         deadline, log, samples, games_per_jam=0, notes=notes)
    if not rows:
        log("no ranked entries read")
        return 1
    log("submission pages ...")
    for i, r in enumerate(rows):
        r.update({"repo": "", "repo_status": "", "fp": None, "fp_any": None, "fp_root": None, "fp_path": None,
                  "fp_commit": None, "fp_head": None, "fp_families": [], "commits_before_cutoff": ""})
        if not r["rate_id"]:
            r["repo_status"] = "no_rate_id"
            continue
        if time.monotonic() >= deadline:
            r["repo_status"] = "not_fetched"
            continue
        status, page = fetch("https://itch.io/jam/%s/rate/%s" % (a.jam, r["rate_id"]))
        if status != 200:
            r["repo_status"] = "rate_page_%s" % status
            continue
        if i < 2:
            study.save(os.path.join(samples, "rate-%d.html" % i), page)
        r["repo"] = repo_from_rate_page(page)
        if not r["repo"]:
            r["repo_status"] = "no_repo_link"
        if i == 9 and not any(x["repo"] for x in rows[:10]):
            log("WARNING: no repository link found on the first 10 submission pages")
    log("repositories ...")
    workroot = tempfile.mkdtemp(prefix="fp-")
    seen, last = {}, 0.0
    todo = [r for r in rows if r["repo"]]
    for n, r in enumerate(todo):
        key = r["repo"].lower()
        if key not in seen:
            if time.monotonic() >= deadline:
                seen[key] = {"status": "not_fetched"}
            else:
                wait = last + a.clone_gap - time.monotonic()
                if wait > 0:
                    time.sleep(wait)
                seen[key] = read_repo(r["repo"], a.cutoff, workroot)
                last = time.monotonic()
        got = seen[key]
        r["repo_status"] = got["status"]
        cut_fams, cut_any = footprint(got.get("cut"))
        head_fams, _ = footprint(got.get("head"))
        if got["status"] == "ok":
            c = got["cut"]
            r.update({"fp": bool(cut_fams), "fp_any": bool(cut_any), "fp_families": cut_fams,
                      "fp_root": c["root"], "fp_path": bool(c["path_families"]),
                      "fp_commit": bool(c["commit_families"]), "commits_before_cutoff": c["commits"]})
        if got["status"] in ("ok", "late"):
            r["fp_head"] = bool(head_fams)
        if n % 50 == 49:
            log("  repositories: %d of %d entries" % (n + 1, len(todo)))
    shutil.rmtree(workroot, ignore_errors=True)
    summary = analyse(rows, a.jam, a.cutoff, a.iters)
    summary["results_read"] = notes.get(a.jam)
    summary["requests"] = fetch.count
    summary["read_at_utc"] = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1)
    write_private(rows, a.out)
    log("done: %d entries, %d repositories read, %d itch requests" % (len(rows), len(seen), fetch.count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
