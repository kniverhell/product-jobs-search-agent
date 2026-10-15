#!/usr/bin/env python3
"""Read-only data pull for outreach triage (modes/triage.md). Never writes anything.

Usage:
    python3 triage.py "<benchmark>"            # the role to measure against: a URL, or words from company + title
    python3 triage.py "<benchmark>" --today 2026-10-15   # fix "today" (for testing)

Prints four plain lists: DEADLINES (first), BENCHMARK, CANDIDATES, UNSCORED. The model does the sorting into
buckets; this script only reads the tracker and the network file so that matching is exact (SKILL.md rule 18).

Exit codes: 0 ok · 1 tracker missing or unreadable · 2 benchmark missing, not found, or ambiguous.
"""
import datetime
import os
import re
import sys

from tracker_io import TRACKER, TrackerError, read_tracker

HERE = os.path.dirname(os.path.abspath(__file__))
NETWORK = os.path.join(HERE, "07-network.md")

OPEN = {"New", "Evaluated", "Tailored"}
LIVE = {"Interviewing", "Final", "Offer"}
DEADLINE_WORDS = re.compile(r"deadline|\bcloses?\b|close date|apply by|applications? due|last day", re.I)

NUM = r"(\d+(?:\.\d+)?)"
SCORE_NUMBER = re.compile(rf"^\s*{NUM}\s*$")
SCORE_RANGE = re.compile(rf"^\s*{NUM}\s*[–-]\s*{NUM}\s*$")
SCORE_CAPPED = re.compile(rf"^\s*{NUM}\s*/\s*{NUM}\s*$")


def parse_score(raw):
    """Return (sort_value, shown) or None if blank or unparseable.
    A range sorts on its upper bound; a capped form "capped / pre-cap" sorts on the capped value."""
    raw = (raw or "").strip()
    if m := SCORE_NUMBER.match(raw):
        return float(m.group(1)), raw
    if m := SCORE_RANGE.match(raw):
        hi = max(float(m.group(1)), float(m.group(2)))
        return hi, f"{raw} (sorts on {hi:g}, the upper bound)"
    if m := SCORE_CAPPED.match(raw):
        capped = float(m.group(1))
        return capped, f"{m.group(1)} capped, {m.group(2)} before the cap"
    return None


def find_benchmark(rows, arg):
    if arg.lower().startswith(("http://", "https://")):
        want = arg.rstrip("/")
        return [r for r in rows if (r.get("url") or "").rstrip("/") == want]
    words = [w for w in re.split(r"\s+", arg.lower()) if w]
    return [r for r in rows if all(w in f"{r.get('company', '')} {r.get('title', '')}".lower() for w in words)]


def due_within(raw, today, days=7):
    try:
        due = datetime.date.fromisoformat((raw or "").strip()[:10])
    except ValueError:
        return False
    return today <= due <= today + datetime.timedelta(days=days)


def line(r, *extra):
    parts = [r.get("company", ""), r.get("title", "")] + [x for x in extra if x] + [r.get("url", "")]
    return "  - " + " | ".join(p for p in parts if p)


def main(argv):
    today = datetime.date.today()
    if "--today" in argv:
        i = argv.index("--today")
        today = datetime.date.fromisoformat(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]

    if not os.path.exists(TRACKER):
        print(f"STOP  tracker not found: {os.path.relpath(TRACKER, HERE)}")
        return 1
    try:
        rows, _ = read_tracker()
    except TrackerError as e:
        print(f"STOP  tracker unreadable: {e}")
        return 1

    if not argv:
        print("STOP  name the role to triage against: python3 triage.py \"<company and title words, or URL>\"")
        live = [r for r in rows if r.get("status") in LIVE]
        if live:
            print("Rows currently at Interviewing / Final / Offer, for reference (not chosen for you):")
            for r in live:
                print(line(r, r.get("status")))
        return 2

    matches = find_benchmark(rows, " ".join(argv))
    if not matches:
        print(f"STOP  benchmark not found in 02-tracker.csv: {' '.join(argv)!r}")
        return 2
    if len(matches) > 1:
        print(f"STOP  {len(matches)} rows match {' '.join(argv)!r}. Which one?")
        for r in matches:
            print(line(r, r.get("status")))
        return 2
    bench = matches[0]

    network = None
    if os.path.exists(NETWORK):
        network = open(NETWORK, encoding="utf-8").read()
    else:
        print("WARN  network file not found (07-network.md); warm path from warm_contact only")

    def name_match(company):
        company = (company or "").strip()
        return bool(network and company and re.search(rf"\b{re.escape(company)}\b", network, re.I))

    open_rows = [r for r in rows if r.get("status") in OPEN and r is not bench]
    scored, unscored = [], []
    for r in open_rows:
        p = parse_score(r.get("score"))
        (scored if p else unscored).append((p, r))
    scored.sort(key=lambda pr: pr[0][0], reverse=True)

    print("DEADLINES (inside 7 days)")
    dl = [r for r in open_rows if due_within(r.get("next_action_due"), today) and DEADLINE_WORDS.search(r.get("next_action") or "")]
    for r in sorted(dl, key=lambda r: r.get("next_action_due", "")):
        print(line(r, f"due {r.get('next_action_due')}", r.get("next_action")))
    if not dl:
        print("  none")

    print("\nBENCHMARK")
    print(line(bench, bench.get("status"), f"score {bench.get('score') or 'blank'}",
               f"tier {bench.get('location_tier')}" if bench.get("location_tier") else "", bench.get("archetype")))
    if bench.get("notes"):
        print("    notes: " + bench["notes"][:300] + ("…" if len(bench["notes"]) > 300 else ""))

    print("\nCANDIDATES (New / Evaluated / Tailored, by score)")
    for (_, shown), r in scored:
        warm = []
        if (r.get("warm_contact") or "").strip():
            warm.append(f"warm_contact {r['warm_contact'].strip()}")
        if name_match(r.get("company")):
            warm.append("possible warm path (name match)")
        print(line(r, f"score {shown}", f"tier {r.get('location_tier')}" if r.get("location_tier") else "",
                   r.get("archetype"), " · ".join(warm)))
    if not scored:
        print("  none")

    print("\nUNSCORED (open, but no parseable score; evaluate first)")
    for _, r in unscored:
        print(line(r, f"score {r.get('score') or 'blank'!r}", r.get("status")))
    if not unscored:
        print("  none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
