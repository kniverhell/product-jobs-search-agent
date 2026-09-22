#!/usr/bin/env python3
"""
ATS scanner — Greenhouse, Ashby, Lever
Hits the public JSON APIs, filters for senior product/program roles,
applies comp floor at scan time, auto-sets verified_on (API = live),
and dumps candidates to inbound/YYYY-MM-DD-scan-candidates.md

Usage:  python3 scan.py

Configuration:
  - Set COMP_FLOOR to your base salary minimum
  - Customize GREENHOUSE, ASHBY, LEVER company lists to match your targets
  - Adjust SENIORITY and DOMAIN keyword lists to fit your specialty
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date, datetime, timezone

# ── Config ─────────────────────────────────────────────────────────────────────
COMP_FLOOR = 0   # ← Set your base salary floor. Roles where disclosed max is below this are dropped.
                 #   Example: COMP_FLOOR = 160_000
                 #   Set to 0 to disable comp floor filtering.
TODAY = date.today()

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "inbound")

# ── Company registry ──────────────────────────────────────────────────────────
# These are example lists for an identity/fintech PM search.
# Replace or extend with the companies relevant to your search.
# Format: (ats_slug, display_label)
# To find a slug: look for the company's Greenhouse/Ashby/Lever board and copy the
# identifier from the URL (e.g., greenhouse.io/v1/boards/{slug}/jobs).

GREENHOUSE = [
    # Identity / fraud / trust vendors
    ("prove",           "Prove"),
    ("forter",          "Forter"),
    ("huntress",        "Huntress"),
    ("workatbackbase",  "Backbase"),
    ("alloy",           "Alloy"),
    ("twilio",          "Twilio"),
    # Fintech / payments
    ("affirm",          "Affirm"),
    # Consumer platforms with identity/trust/account surfaces
    ("airbnb",          "Airbnb"),
    ("reddit",          "Reddit"),
    ("discord",         "Discord"),
    ("fanduel",         "FanDuel"),
    ("roblox",          "Roblox"),
    # News / media (for reference, adjust to your search)
    ("thenewyorktimes", "NYT"),
    ("lyft",            "Lyft"),
]

ASHBY = [
    # Identity / KYC / fraud vendors
    ("socure",    "Socure"),
    ("persona",   "Persona"),
    ("stytch",    "Stytch"),
    ("middesk",   "Middesk"),
    ("sift",      "Sift"),
    ("sentilink", "SentiLink"),
    ("trulioo",   "Trulioo"),
    ("sardine",   "Sardine"),
    # Auth / access
    ("workos",    "WorkOS"),
    # Fintech
    ("airwallex", "Airwallex"),
    ("ramp",      "Ramp"),
    ("unit",      "Unit"),
]

LEVER = [
    ("narmi",  "Narmi"),
    # Add Lever-based companies here. Format: (slug, label)
    # Find the slug from job URLs like jobs.lever.co/{slug}/...
]

# ── Filters ───────────────────────────────────────────────────────────────────
# Customize these to match your target seniority and domain.

SENIORITY = [
    "director", "head of", "head,", "vp ", "vp,", "vice president",
    "senior director", "sr director", "sr. director", "principal",
    "staff product", "staff technical program", "staff program",
]

DOMAIN = [
    "product", "program", "platform", "identity", "ciam", "authentication",
    "auth", "trust", "fraud", "kyc", "onboarding", "iam", "verification",
    "security", "access management",
]

EXCLUDE = [
    "engineer", "engineering", "sales", "marketing", "recruiter", "recruiting",
    "financial analyst", "legal", "data scientist", "data science", "developer",
    "architect", "design", "designer", "security researcher", "research scientist",
    "business development", "account manager", "account executive",
    "customer success",
]


def passes_title(title: str) -> bool:
    t = title.lower()
    if not any(s in t for s in SENIORITY):
        return False
    if not any(d in t for d in DOMAIN):
        return False
    if any(e in t for e in EXCLUDE):
        return False
    return True


def staleness_flag(posted_date: str) -> str:
    """Return staleness band string given a YYYY-MM-DD posted date."""
    if not posted_date or posted_date == "unknown":
        return "⚠ date unknown"
    try:
        posted = date.fromisoformat(posted_date[:10])
        days = (TODAY - posted).days
        if days <= 30:
            return f"{days}d ✓"
        elif days <= 60:
            return f"{days}d −0.2"
        elif days <= 90:
            return f"{days}d −0.4 ⚠"
        else:
            return f"{days}d 🚫 BLOCKER"
    except Exception:
        return "⚠ parse error"


# ── Date/comp helpers ─────────────────────────────────────────────────────────

def epoch_ms_to_date(ts) -> str:
    if not ts:
        return "unknown"
    try:
        return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return "unknown"


def iso_to_date(s) -> str:
    if not s:
        return "unknown"
    return str(s)[:10]


def parse_comp_range(raw):
    """
    Try to extract (min_base, max_base, display_string) from various comp shapes.
    Returns (None, None, "") when comp is absent or unparseable.
    """
    if not raw:
        return None, None, ""
    if isinstance(raw, dict):
        # Ashby shape: {"summaryComponents": [{"label": "...", "value": "..."}], ...}
        components = raw.get("summaryComponents") or []
        if components:
            parts = [c.get("label", "") or c.get("value", "") for c in components if isinstance(c, dict)]
            display = " / ".join(p for p in parts if p)
            if display:
                import re
                nums = [int(n.replace(",", "")) for n in re.findall(r"[\d,]{4,}", display)]
                if len(nums) >= 2:
                    return nums[0], nums[-1], display
                return None, None, display
        # Lever shape: {"min": 150000, "max": 200000, "currency": "USD"}
        lo  = raw.get("min") or raw.get("minValue")
        hi  = raw.get("max") or raw.get("maxValue")
        curr = raw.get("currency", "USD")
        if lo or hi:
            display = f"${lo:,}–${hi:,} {curr}" if lo and hi else f"${lo or hi:,} {curr}"
            return (lo or 0), (hi or lo or 0), display
    return None, None, ""


def above_floor(comp_min, comp_max) -> bool:
    """
    Returns True (keep the role) unless BOTH bounds are disclosed and max < floor.
    If comp is absent, keep — we can't rule it out.
    """
    if COMP_FLOOR == 0:
        return True
    if comp_max is None:
        return True
    return comp_max >= COMP_FLOOR


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch(url: str, timeout: int = 12):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)[:120]}


# ── Per-ATS scrapers ──────────────────────────────────────────────────────────

def scan_greenhouse(slug, label):
    """Returns (candidates, error_str|None). API hit = verified_on today."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    data = fetch(url)
    if "_error" in data:
        return [], data["_error"]

    jobs = data.get("jobs", [])
    out = []
    for j in jobs:
        title = j.get("title", "")
        if not passes_title(title):
            continue

        posted = iso_to_date(j.get("first_published") or j.get("updated_at"))
        updated = iso_to_date(j.get("updated_at"))

        loc = j.get("location", {})
        loc_str = loc.get("name", "") if isinstance(loc, dict) else str(loc)

        # Greenhouse basic endpoint doesn't return comp; fetch per-job with ?content=true for comp data
        comp_min, comp_max, comp_str = None, None, ""

        out.append({
            "company":      label,
            "ats":          "Greenhouse",
            "title":        title,
            "location":     loc_str,
            "url":          j.get("absolute_url", ""),
            "posted":       posted,
            "updated":      updated,
            "verified_on":  TODAY.isoformat(),
            "staleness":    staleness_flag(posted),
            "comp":         comp_str,
            "comp_min":     comp_min,
            "comp_max":     comp_max,
            "below_floor":  not above_floor(comp_min, comp_max),
        })
    return out, None


def scan_ashby(slug, label):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    data = fetch(url)
    if "_error" in data:
        return [], data["_error"]

    jobs = data.get("jobPostings") or data.get("jobs", [])
    out = []
    for j in jobs:
        title = j.get("title", "")
        if not passes_title(title):
            continue

        posted = iso_to_date(j.get("publishedAt"))
        comp_min, comp_max, comp_str = parse_comp_range(j.get("compensation"))

        if not above_floor(comp_min, comp_max):
            continue

        loc = j.get("location", "") or j.get("workplaceType", "")

        out.append({
            "company":      label,
            "ats":          "Ashby",
            "title":        title,
            "location":     loc,
            "url":          j.get("jobUrl", "") or j.get("applyUrl", ""),
            "posted":       posted,
            "updated":      posted,
            "verified_on":  TODAY.isoformat(),
            "staleness":    staleness_flag(posted),
            "comp":         comp_str,
            "comp_min":     comp_min,
            "comp_max":     comp_max,
            "below_floor":  False,
        })
    return out, None


def scan_lever(slug, label):
    url = f"https://api.lever.co/v0/postings/{slug}"
    data = fetch(url)
    if isinstance(data, dict):
        if "_error" in data:
            return [], data["_error"]
        if not data.get("ok", True):
            return [], data.get("error", "unknown lever error")
        return [], f"unexpected shape: {str(data)[:60]}"
    if not isinstance(data, list):
        return [], f"unexpected type {type(data)}"

    out = []
    for j in data:
        title = j.get("text", "")
        if not passes_title(title):
            continue

        posted = epoch_ms_to_date(j.get("createdAt"))
        cats   = j.get("categories", {})
        comp_min, comp_max, comp_str = parse_comp_range(j.get("salaryRange"))

        if not above_floor(comp_min, comp_max):
            continue

        out.append({
            "company":      label,
            "ats":          "Lever",
            "title":        title,
            "location":     cats.get("location", ""),
            "url":          j.get("hostedUrl", ""),
            "posted":       posted,
            "updated":      posted,
            "verified_on":  TODAY.isoformat(),
            "staleness":    staleness_flag(posted),
            "comp":         comp_str,
            "comp_min":     comp_min,
            "comp_max":     comp_max,
            "below_floor":  False,
        })
    return out, None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outpath = os.path.join(OUTPUT_DIR, f"{TODAY.isoformat()}-scan-candidates.md")

    total = len(GREENHOUSE) + len(ASHBY) + len(LEVER)
    print(f"Scanning {total} companies ({len(GREENHOUSE)} Greenhouse · "
          f"{len(ASHBY)} Ashby · {len(LEVER)} Lever)…\n")

    candidates = []
    failed     = []
    ok_count   = 0

    for slug, label in GREENHOUSE:
        print(f"  GH  {label:<22}", end=" ", flush=True)
        hits, err = scan_greenhouse(slug, label)
        if err:
            failed.append((label, "Greenhouse", err))
            print(f"ERROR: {err}")
        else:
            ok_count += 1
            candidates.extend(hits)
            print(f"{len(hits)} hits")

    for slug, label in ASHBY:
        print(f"  ASH {label:<22}", end=" ", flush=True)
        hits, err = scan_ashby(slug, label)
        if err:
            failed.append((label, "Ashby", err))
            print(f"ERROR: {err}")
        else:
            ok_count += 1
            candidates.extend(hits)
            print(f"{len(hits)} hits")

    for slug, label in LEVER:
        print(f"  LEV {label:<22}", end=" ", flush=True)
        hits, err = scan_lever(slug, label)
        if err:
            failed.append((label, "Lever", err))
            print(f"ERROR: {err}")
        else:
            ok_count += 1
            candidates.extend(hits)
            print(f"{len(hits)} hits")

    # ── Build output ──────────────────────────────────────────────────────────
    comp_note = (f"Comp floor ${COMP_FLOOR:,} applied at scan time where compensation is disclosed."
                 if COMP_FLOOR > 0 else
                 "No comp floor set. Set COMP_FLOOR in scan.py to filter by base salary.")

    lines = [
        f"# ATS scan — {TODAY.isoformat()}",
        f"",
        f"**Boards read: {ok_count} of {total}. "
        f"Failed: {len(failed)} ({', '.join(f[0] for f in failed) or 'none'}). "
        f"Candidates above filter: {len(candidates)}.**",
        f"",
        f"Verified_on: {TODAY.isoformat()} — API responses are live by definition. "
        f"Roles here satisfy the verification gate; no manual ATS check required.",
        f"",
        comp_note,
        f"",
    ]

    if candidates:
        lines += [
            "## Candidates\n",
            "| Company | ATS | Title | Location | Posted | Age | Comp | URL |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for c in sorted(candidates, key=lambda x: x["company"]):
            lines.append(
                f"| {c['company']} | {c['ats']} | {c['title']} "
                f"| {c['location']} | {c['posted']} | {c['staleness']} "
                f"| {c['comp'] or '—'} | {c['url']} |"
            )
        lines.append("")
    else:
        lines += ["## Candidates\n", "None above filter threshold this run.\n"]

    if failed:
        lines += [
            "## Errors — slugs to investigate\n",
            "| Company | ATS | Error |",
            "|---|---|---|",
        ]
        for label, ats, err in failed:
            lines.append(f"| {label} | {ats} | {err} |")
        lines.append("")

    lines += [
        "## Notes",
        "",
        "- Greenhouse comp not in list endpoint — fetch per-job with `?content=true` for comp data.",
        "- Workday, Avature, custom career sites: not covered here.",
        "- Lever: only confirmed-slug companies included. Add slugs to LEVER list as discovered.",
        "- `site:` dork results still need manual ATS verification before tracker entry.",
        "",
    ]

    with open(outpath, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n{'─'*60}")
    print(f"Boards read: {ok_count}/{total}. Candidates: {len(candidates)}.")
    print(f"Output → {outpath}")
    if failed:
        print(f"Failed: {', '.join(f'{f[0]} ({f[2]})' for f in failed)}")


if __name__ == "__main__":
    main()
