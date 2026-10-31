#!/usr/bin/env python3
# Gate: read no data until the pre-registration is public. By MV2 of Munim, Inc., made with AI agents. Apache-2.0.
"""Waits until PREREGISTRATION-game-off-2026.md is on the main branch of munimtechnologies/jam-ai-ranks
and contains --must, then writes when it was seen and the file's SHA-256 to --out. Exit 1 if it never
appears, so the footprint run that follows it (with &&) never starts."""

import argparse
import hashlib
import json
import sys
import time
import urllib.request

URL = "https://raw.githubusercontent.com/munimtechnologies/jam-ai-ranks/main/PREREGISTRATION-game-off-2026.md"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--must", default="Pre-registration: AI-agent footprints")
    ap.add_argument("--wait-minutes", type=float, default=60)
    a = ap.parse_args(argv)
    end = time.time() + a.wait_minutes * 60
    while True:
        try:
            req = urllib.request.Request(URL + "?t=%d" % time.time(), headers={"User-Agent": "MV2-jam-study"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
            if a.must.encode() in body:
                seen = {"url": URL, "seen_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
                with open(a.out, "w", encoding="utf-8") as f:
                    json.dump(seen, f, indent=1)
                print("pre-registration is public:", json.dumps(seen))
                return 0
            print("pre-registration found but without the expected heading; waiting")
        except Exception as e:  # 404 until it is committed
            print("not public yet (%s); waiting" % type(e).__name__)
        if time.time() > end:
            print("pre-registration never appeared; reading no data")
            return 1
        time.sleep(120)


if __name__ == "__main__":
    sys.exit(main())
