#!/usr/bin/env python3
"""
ATS scanner — Greenhouse, Ashby, Lever
Hits the public JSON APIs, filters for senior product/program roles,
applies comp floor at scan time, auto-sets verified_on (API = live),
and dumps candidates to inbound/YYYY-MM-DD-scan-candidates.md

Usage:  python3 scan.py        (run from your project folder)

Configuration lives in your project folder, never in this script:
  - The screen: a ```scan-screen block in 01-target-roles.md
      comp floor: 160000            (0 turns the floor off)
      level: "director", "head of", "vp "
      include: "product", "platform"
      exclude: "engineer", "sales"
    Terms are double-quoted, so spaces and commas inside a term are kept ("vp ", "head,").
    A key may repeat; its terms add up.
  - The boards: a ```scan-boards block in 04-queries.md, one per line:
      greenhouse | board-slug | Company label
    ats is greenhouse, ashby or lever.
A missing, empty, placeholder or malformed config stops the scan (exit 1) with the file and line.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import date, datetime, timezone

from kit_paths import project_dir, require_project

# ── Config ─────────────────────────────────────────────────────────────────────
TODAY = date.today()

OUTPUT_DIR = os.path.join(project_dir(), "inbound")
SCREEN_FILE = "01-target-roles.md"
BOARDS_FILE = "04-queries.md"
ATS_NAMES = ("greenhouse", "ashby", "lever")

# Filled from your files by load_config() before any board is read. No built-in defaults.
COMP_FLOOR = None
SENIORITY, DOMAIN, EXCLUDE = [], [], []
GREENHOUSE, ASHBY, LEVER = [], [], []


class ConfigError(Exception):
    pass


def read_block(name, tag):
    """Return [(line_number, text)] inside the ```tag fence of a project file, skipping blanks and # comments."""
    path = os.path.join(project_dir(), name)
    if not os.path.exists(path):
        raise ConfigError(f"{name} not found in {project_dir()}: run setup")
    lines = open(path, encoding="utf-8").read().splitlines()
    try:
        first = next(i for i, l in enumerate(lines) if l.strip() == "```" + tag)
    except StopIteration:
        raise ConfigError(f"{name} has no ```{tag} block: run setup, or copy the block from templates/{name}")
    try:
        last = next(i for i in range(first + 1, len(lines)) if lines[i].strip() == "```")
    except StopIteration:
        raise ConfigError(f"{name}:{first + 1}: ```{tag} block is never closed")
    return [(i + 1, lines[i].strip()) for i in range(first + 1, last)
            if lines[i].strip() and not lines[i].strip().startswith("#")]


def placeholder(text):
    return "[" in text or "]" in text


def parse_terms(name, n, line, value):
    """Quoted, comma-separated terms. Anything outside the quotes except commas and spaces is an error."""
    terms = re.findall(r'"([^"]*)"', value)
    if re.sub(r'"[^"]*"', "", value).strip(" ,") or not terms:
        raise ConfigError(f"{name}:{n}: expected quoted terms like \"director\", \"head of\": {line}")
    for t in terms:
        if not t.strip():
            raise ConfigError(f"{name}:{n}: empty term: {line}")
        if placeholder(t):
            raise ConfigError(f"{name}:{n}: placeholder not filled in: {line}")
    return terms


def load_config():
    global COMP_FLOOR, SENIORITY, DOMAIN, EXCLUDE, GREENHOUSE, ASHBY, LEVER
    floor, lists = None, {"level": [], "include": [], "exclude": []}
    for n, line in read_block(SCREEN_FILE, "scan-screen"):
        key, sep, value = line.partition(":")
        key = key.strip().lower()
        if not sep or (key != "comp floor" and key not in lists):
            raise ConfigError(f"{SCREEN_FILE}:{n}: expected 'comp floor:', 'level:', 'include:' or 'exclude:': {line}")
        if key == "comp floor":
            if placeholder(value):
                raise ConfigError(f"{SCREEN_FILE}:{n}: placeholder not filled in: {line}")
            digits = value.strip().replace(",", "").replace("_", "")
            if not digits.isdigit():
                raise ConfigError(f"{SCREEN_FILE}:{n}: comp floor must be a whole number (0 = off): {line}")
            floor = int(digits)
        else:
            lists[key] += parse_terms(SCREEN_FILE, n, line, value)
    if floor is None:
        raise ConfigError(f"{SCREEN_FILE}: the scan-screen block has no 'comp floor:' line")
    for key, terms in lists.items():
        if not terms:
            raise ConfigError(f"{SCREEN_FILE}: the scan-screen block has no terms for '{key}:'")

    boards = {a: [] for a in ATS_NAMES}
    for n, line in read_block(BOARDS_FILE, "scan-boards"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3 or parts[0].lower() not in ATS_NAMES or not parts[1] or not parts[2]:
            raise ConfigError(f"{BOARDS_FILE}:{n}: expected 'greenhouse | slug | Label' (or ashby, lever): {line}")
        if placeholder(line):
            raise ConfigError(f"{BOARDS_FILE}:{n}: placeholder not filled in: {line}")
        boards[parts[0].lower()].append((parts[1], parts[2]))
    if not any(boards.values()):
        raise ConfigError(f"{BOARDS_FILE}: the scan-boards block lists no boards")

    COMP_FLOOR = floor
    SENIORITY, DOMAIN, EXCLUDE = lists["level"], lists["include"], lists["exclude"]
    GREENHOUSE, ASHBY, LEVER = boards["greenhouse"], boards["ashby"], boards["lever"]


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
    require_project()
    try:
        load_config()
    except ConfigError as e:
        print(f"STOP: {e}")
        sys.exit(1)
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
                 "No comp floor set. Set 'comp floor:' in the scan-screen block of 01-target-roles.md to filter by base salary.")

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
        "- Lever: only confirmed-slug companies included. Add slugs to the scan-boards block in 04-queries.md as discovered.",
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
