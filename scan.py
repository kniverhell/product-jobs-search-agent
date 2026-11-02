#!/usr/bin/env python3
"""
ATS scanner — Greenhouse, Ashby, Lever
Hits the public JSON APIs, filters for senior product/program roles,
applies comp floor at scan time, auto-sets verified_on (API = live),
and dumps candidates to inbound/YYYY-MM-DD-scan-candidates.md

Usage:  python3 scan.py        (run from your project folder)
        python3 scan.py alerts [alerts-YYYY-MM-DD.csv]   discover boards from alert fields (see modes/discover.md)
        python3 scan.py parse-alerts                      inbound/alerts/*.eml -> inbound/alerts-<today>.csv
        python3 scan.py decide "Company" keep|pause|remove   the answer to the rejection question

Configuration lives in your project folder, never in this script:
  - The screen: a ```scan-screen block in 01-target-roles.md
      comp floor: 160000            (0 turns the floor off)
      level: "director", "head of", "vp "
      include: "product", "platform"
      exclude: "engineer", "sales"
    Terms are double-quoted, so spaces and commas inside a term are kept ("vp ", "head,").
    A key may repeat; its terms add up.
  - The boards: a ```scan-boards block in 04-queries.md, one per line:
      greenhouse | board-slug | Company label | status | source
    ats is greenhouse, ashby or lever. status is active (the default when missing), probation or paused; source is
    free text (e.g. "alert 2026-11-03", "paused 2026-10-20 rejected"). Paused boards are still scanned; their roles are
    labeled "paused: rejected <date>". Probation boards become active after a scan reads real listings.
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
STATUSES = ("active", "probation", "paused")
BOARD_META = {}   # (ats, slug) -> (status, source); filled by load_config()
LAST_RAW = 0      # postings the last board returned before the title filter


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
        if not 3 <= len(parts) <= 5 or parts[0].lower() not in ATS_NAMES or not parts[1] or not parts[2]:
            raise ConfigError(f"{BOARDS_FILE}:{n}: expected 'greenhouse | slug | Label' (or ashby, lever), "
                              f"optionally '| status | source': {line}")
        if placeholder(line):
            raise ConfigError(f"{BOARDS_FILE}:{n}: placeholder not filled in: {line}")
        status = (parts[3].lower() if len(parts) > 3 else "") or "active"
        if status not in STATUSES:
            raise ConfigError(f"{BOARDS_FILE}:{n}: status must be active, probation or paused: {line}")
        boards[parts[0].lower()].append((parts[1], parts[2]))
        BOARD_META[(parts[0].lower(), parts[1])] = (status, parts[4] if len(parts) > 4 else "")
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


def set_raw(n):
    global LAST_RAW
    LAST_RAW = n


def paused_label(source):
    """'paused 2026-10-20 rejected' -> 'paused: rejected 2026-10-20'."""
    m = re.match(r"paused\s+(\d{4}-\d{2}-\d{2})\s+rejected", source or "")
    return f"paused: rejected {m.group(1)}" if m else "paused"


def board_note(ats, slug):
    status, source = BOARD_META.get((ats, slug), ("active", ""))
    return paused_label(source) if status == "paused" else ""


# ── Per-ATS scrapers ──────────────────────────────────────────────────────────

def scan_greenhouse(slug, label):
    """Returns (candidates, error_str|None). API hit = verified_on today."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    data = fetch(url)
    if "_error" in data:
        return [], data["_error"]

    jobs = data.get("jobs", [])
    set_raw(len(jobs))
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
    set_raw(len(jobs))
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

    set_raw(len(data))
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

def norm(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def days_since(source):
    """Days since the first YYYY-MM-DD in a board's source text; 0 when there is none."""
    m = re.search(r"\d{4}-\d{2}-\d{2}", source or "")
    try:
        return (TODAY - date.fromisoformat(m.group(0))).days if m else 0
    except ValueError:
        return 0


def read_table_rows(name, heading):
    """First-column cells of the markdown table under '## heading' in a project file; placeholders skipped."""
    path = os.path.join(project_dir(), name)
    if not os.path.exists(path):
        return []
    rows, on = [], False
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            on = line[3:].strip().lower().startswith(heading.lower())
            continue
        if on and line.startswith("|"):
            cell = line.strip("|").split("|")[0].strip()
            if cell and not set(cell) <= set("-: ") and cell.lower() != "employer" and not placeholder(cell):
                rows.append(cell)
    return rows


def load_nogo():
    return {norm(c) for c in read_table_rows(SCREEN_FILE, "No-go list")}


def rewrite_board(ats, slug, status, source):
    """Change one line of the scan-boards block in place: same ats, slug and label, new status and source."""
    path = os.path.join(project_dir(), BOARDS_FILE)
    lines = open(path, encoding="utf-8").read().splitlines()
    for n, line in read_block(BOARDS_FILE, "scan-boards"):
        parts = [p.strip() for p in line.split("|")]
        if parts[0].lower() == ats and parts[1] == slug:
            lines[n - 1] = " | ".join([parts[0], parts[1], parts[2], status, source]).rstrip(" |")
            open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
            return True
    return False


def append_board(ats, slug, label, source):
    path = os.path.join(project_dir(), BOARDS_FILE)
    lines = open(path, encoding="utf-8").read().splitlines()
    first = next(i for i, l in enumerate(lines) if l.strip() == "```scan-boards")
    last = next(i for i in range(first + 1, len(lines)) if lines[i].strip() == "```")
    lines.insert(last, f"{ats} | {slug} | {label} | probation | {source}")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")


# ── Discover: boards from alerts, and the rejection answer ───────────────────

DETECT_SLUGS_MAX = 3
COMPANY_SUFFIXES = {"inc", "llc", "ltd", "corp", "co", "the", "company"}


def slug_candidates(company):
    words = [w for w in re.findall(r"[a-z0-9]+", company.lower()) if w not in COMPANY_SUFFIXES]
    out = []
    for c in ("".join(words), "-".join(words), words[0] if words else ""):
        if c and c not in out:
            out.append(c)
    return out[:DETECT_SLUGS_MAX]


def board_snapshot(ats, slug):
    """(board's own company name or '', [posting titles]) or None when the board can't be read. No retries."""
    if ats == "greenhouse":
        data = fetch(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        if not isinstance(data, dict) or "_error" in data:
            return None
        name = fetch(f"https://boards-api.greenhouse.io/v1/boards/{slug}")
        name = name.get("name", "") if isinstance(name, dict) else ""
        return name, [j.get("title", "") for j in data.get("jobs", [])]
    if ats == "ashby":
        data = fetch(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        if not isinstance(data, dict) or "_error" in data:
            return None
        return "", [j.get("title", "") for j in (data.get("jobPostings") or data.get("jobs", []))]
    data = fetch(f"https://api.lever.co/v0/postings/{slug}")
    if not isinstance(data, list):
        return None
    return "", [j.get("text", "") for j in data]


def same_title(a, b):
    a, b = norm(a), norm(b)
    return bool(a) and bool(b) and (a == b or a in b or b in a)


def same_company(a, b):
    a, b = norm(a), norm(b)
    return bool(a) and bool(b) and (a == b or a.startswith(b) or b.startswith(a))


def detect_board(company, title):
    """Try up to 3 slug candidates against the three fetchers. The board must confirm the company: its own name matches
    the alert's company, or (where the board states no name) one of its postings matches the alert's title. A board
    that states a different company name is a miss, whatever its titles. Returns (ats, slug, how, tries, title_found);
    ats is None on a miss. No retries."""
    tries = 0
    for slug in slug_candidates(company):
        tries += 1
        for ats in ATS_NAMES:
            snap = board_snapshot(ats, slug)
            if snap is None:
                continue
            name, titles = snap
            title_found = any(same_title(t, title) for t in titles)
            if name:
                if same_company(name, company):
                    return ats, slug, "board name matches", tries, title_found
                continue
            if title_found:
                return ats, slug, "posting matches the alert title", tries, True
    return None, None, "no board confirmed the company", tries, False


def add_alerts_only(company, title, source):
    path = os.path.join(project_dir(), "03-portals.md")
    lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
    if any(norm(company) == norm(l.strip("|").split("|")[0]) for l in lines if l.startswith("|")):
        return False
    start = next((i for i, l in enumerate(lines) if l.startswith("## Watchlist")), None)
    if start is None:
        return False
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == "---"), len(lines))
    at = max([i for i in range(start, end) if lines[i].startswith("|")] or [end - 1]) + 1
    lines.insert(at, f"| {company} | alerts-only | — | {title} | {source} |")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return True


def alerts_csv(arg):
    import csv, glob
    path = arg or max(glob.glob(os.path.join(OUTPUT_DIR, "alerts-*.csv")), default=None)
    if not path or not os.path.exists(path):
        print("STOP: no alerts CSV. Run `parse-alerts`, or save the fields the mode extracted to inbound/alerts-YYYY-MM-DD.csv.")
        raise SystemExit(1)
    return path, list(csv.DictReader(open(path, encoding="utf-8")))


def cmd_alerts(arg=None):
    require_project()
    try:
        load_config()
    except ConfigError as e:
        print(f"STOP: {e}")
        raise SystemExit(1)
    path, rows = alerts_csv(arg)
    have = {norm(l) for bl in (GREENHOUSE, ASHBY, LEVER) for _, l in bl}
    nogo = load_nogo()
    read = verified = unreadable = 0
    added, watch, notes = [], [], []
    seen = set()
    for r in rows:
        read += 1
        company, title = (r.get("company") or "").strip(), (r.get("title") or "").strip()
        if not company or not title or (r.get("parsed_by") or "").strip() == "unreadable":
            unreadable += 1
            continue
        key = norm(company)
        if key in seen:
            continue
        seen.add(key)
        if not passes_title(title):
            notes.append(f"{company}: title filtered out ({title})")
        elif key in nogo:
            notes.append(f"{company}: on the no-go list, ignored")
        elif key in have:
            notes.append(f"{company}: already on the board list, covered by the scan")
        else:
            ats, slug, how, tries, title_found = detect_board(company, title)
            if ats:
                verified += bool(title_found)
                append_board(ats, slug, company, f"alert {TODAY.isoformat()}")
                added.append(f"{company} -> {ats}/{slug} ({how})")
            else:
                if add_alerts_only(company, title, f"alert {TODAY.isoformat()}"):
                    watch.append(company)
                notes.append(f"{company}: {how} after {tries} slug tries -> alerts-only watchlist")
    print(f"Alerts: {read} read, {verified} verified on employer sites, {unreadable} unreadable · "
          f"Boards added: {len(added)} (probation) · Alerts-only: {len(watch)}")
    for line in added + notes:
        print("  " + line)
    print("Alert roles are leads, not evidence: only the employer's own posting counts (verification gate).")


def parse_alert_text(text):
    """Roles in an alert's plain-text body: [(title, company, location)], and the job count the digest header states.
    Each role ends at a "View job:" line and is the unbroken run of lines above it: title, company, location, then any
    badge lines ("Top applicant", "2 connections"). Also reads the older "title / Company · Location" form. URLs are
    removed before anything else, so none can reach the output."""
    text = re.sub(r"https?://\S+|www\.\S+|\S*(?:linkedin\.com|lnkd\.in)\S*", "", text)
    lines = [l.strip() for l in text.splitlines()]
    roles = []
    for k, line in enumerate(lines):
        if not line.lower().startswith("view job"):
            continue
        j = k
        while j > 0 and lines[j - 1] and not re.match(r"^-{3,}$", lines[j - 1]):
            j -= 1
        group = lines[j:k]
        if len(group) == 2 and " · " in group[1] and " · " not in group[0]:
            company, _, loc = group[1].partition(" · ")
            title = group[0]
        elif len(group) >= 3 and not any(" · " in g for g in group[:3]):
            title, company, loc = group[:3]
        else:
            continue
        if len(title) < 140 and title and company.strip():
            roles.append((title, company.strip(), loc.strip()))
    if not roles:  # no "View job" markers: the plain "title, then Company · Location" pair
        for i in range(len(lines) - 1):
            if lines[i] and " · " in lines[i + 1] and " · " not in lines[i] and len(lines[i]) < 120:
                company, _, loc = lines[i + 1].partition(" · ")
                roles.append((lines[i], company.strip(), loc.strip()))
    m = re.search(r"\b(\d+)\s+new\s+jobs?\b", text, re.I)
    return roles, int(m.group(1)) if m else 0


def cmd_parse_alerts():
    import csv, glob
    from email import policy
    from email.parser import BytesParser
    from email.utils import parsedate_to_datetime
    require_project()
    folder = os.path.join(project_dir(), "inbound", "alerts")
    rows, unreadable, notes = [], [], []
    for f in sorted(glob.glob(os.path.join(folder, "*.eml"))):
        msg = BytesParser(policy=policy.default).parse(open(f, "rb"))
        body = msg.get_body(preferencelist=("plain",))
        text = body.get_content() if body else ""
        try:
            adate = parsedate_to_datetime(msg["Date"]).date().isoformat()
        except Exception:
            adate = TODAY.isoformat()
        roles, listed = parse_alert_text(text)
        for title, company, loc in roles:
            rows.append({"company": company, "title": title, "location": loc, "alert_date": adate, "parsed_by": "code"})
        if not roles:
            unreadable.append(os.path.basename(f))
        elif listed and listed != len(roles):
            notes.append(f"{os.path.basename(f)}: the digest says {listed} jobs, the email lists {len(roles)}")
    out = os.path.join(OUTPUT_DIR, f"alerts-{TODAY.isoformat()}.csv")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, ["company", "title", "location", "alert_date", "parsed_by"])
        w.writeheader()
        w.writerows(rows)
    print(f"Parsed {len(rows)} roles from {len(glob.glob(os.path.join(folder, '*.eml')))} files -> {out} "
          f"(fields only; no bodies, no URLs). Unreadable by code: {', '.join(unreadable) or 'none'}.")
    for n in notes:
        print("  " + n)
    print(f"Fields read by code: {len(rows) * 3} of {len(rows) * 3} (company, title, location per role) plus the date from "
          "the Date header. The format is matched by pattern (see parse_alert_text); unreadable files go to the model, "
          "recorded as 'parsed by model'.")


def cmd_decide(company, choice):
    """The answer to 'Rejected at [Company]': keep (nothing changes), pause (label, still scanned), remove (no-go + stop)."""
    require_project()
    choice = choice.lower()
    if choice not in ("keep", "pause", "remove"):
        print("STOP: choose keep, pause or remove.")
        raise SystemExit(1)
    if choice == "keep":
        print(f"{company}: kept. Nothing changed.")
        return
    load_config()
    src = f"paused {TODAY.isoformat()} rejected"
    hit = False
    for ats, boards in (("greenhouse", GREENHOUSE), ("ashby", ASHBY), ("lever", LEVER)):
        for slug, label in boards:
            if norm(label) == norm(company):
                hit = rewrite_board(ats, slug, "paused", src) or hit
    if choice == "remove":
        path = os.path.join(project_dir(), SCREEN_FILE)
        lines = open(path, encoding="utf-8").read().splitlines()
        start = next((i for i, l in enumerate(lines) if l.startswith("## No-go list")), None)
        if start is None:
            print(f"STOP: {SCREEN_FILE} has no '## No-go list' section.")
            raise SystemExit(1)
        end = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == "---"), len(lines))
        if norm(company) not in {norm(c) for c in read_table_rows(SCREEN_FILE, "No-go list")}:
            at = max([i for i in range(start, end) if lines[i].startswith("|")]) + 1
            lines.insert(at, f"| {company} | rejected {TODAY.isoformat()} |")
            open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"{company}: {choice}. Board line {'updated' if hit else 'not found (no change to 04-queries.md)'}"
          f"{'; added to the no-go list (scanning stops)' if choice == 'remove' else '; still scanned, roles labeled'}.")



def main():
    require_project()
    try:
        load_config()
    except ConfigError as e:
        print(f"STOP: {e}")
        sys.exit(1)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outpath = os.path.join(OUTPUT_DIR, f"{TODAY.isoformat()}-scan-candidates.md")

    nogo = load_nogo()
    skipped_nogo = [l for bl in (GREENHOUSE, ASHBY, LEVER) for _, l in bl if norm(l) in nogo]
    total = len(GREENHOUSE) + len(ASHBY) + len(LEVER) - len(skipped_nogo)
    print(f"Scanning {total} companies ({len(GREENHOUSE)} Greenhouse · "
          f"{len(ASHBY)} Ashby · {len(LEVER)} Lever)…\n" if not skipped_nogo else
          f"Scanning {total} companies (no-go list skipped: {len(skipped_nogo)})…\n")

    candidates = []
    failed     = []
    ok_count   = 0
    tally      = {s_: 0 for s_ in STATUSES}
    promote    = []     # probation boards that returned real listings
    retire     = []     # probation boards 30+ days old with no role passing the filter
    to_review  = []     # paused boards 90+ days old

    for key, tag, boards, fn, name in (("greenhouse", "GH", GREENHOUSE, scan_greenhouse, "Greenhouse"),
                                       ("ashby", "ASH", ASHBY, scan_ashby, "Ashby"),
                                       ("lever", "LEV", LEVER, scan_lever, "Lever")):
        for slug, label in boards:
            if norm(label) in nogo:
                continue
            print(f"  {tag:<3} {label:<22}", end=" ", flush=True)
            set_raw(0)
            hits, err = fn(slug, label)
            status, source = BOARD_META.get((key, slug), ("active", ""))
            tally[status] += 1
            if err:
                failed.append((label, name, err))
                print(f"ERROR: {err}")
                continue
            ok_count += 1
            note = board_note(key, slug)
            for h in hits:
                if note:
                    h["company"] = f"{h['company']} ({note})"
            candidates.extend(hits)
            print(f"{len(hits)} hits")
            if status == "probation" and LAST_RAW > 0:
                promote.append((key, slug, label))
            if source.startswith("alert") and not hits and days_since(source) >= 30:
                retire.append(label)
            if status == "paused" and days_since(source) >= 90:
                to_review.append(f"{label} ({paused_label(source)})")
    for key, slug, label in promote:
        rewrite_board(key, slug, "active", BOARD_META[(key, slug)][1])
    retire = sorted(set(retire))

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
        *([f"Boards by status: {tally['active']} active · {tally['probation']} probation · {tally['paused']} paused "
           f"(scanned, labeled)" + (f" · {len(skipped_nogo)} skipped (no-go list)" if skipped_nogo else "") + ".", ""]
          if tally["probation"] or tally["paused"] or skipped_nogo else []),
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

    if promote or retire or to_review:
        lines += ["## Board status changes and proposals\n"]
        lines += [f"- Probation to active (real listings read): {l}" for _, _, l in promote]
        lines += [f"- Proposed for retirement (30+ days on probation, no role passing the filter; your call): {l}" for l in retire]
        lines += [f"- Paused 90+ days: keep the label or clear it? {l}" for l in to_review]
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
    args = sys.argv[1:]
    if not args:
        main()
    elif args[0] == "alerts" and len(args) <= 2:
        cmd_alerts(args[1] if len(args) > 1 else None)
    elif args[0] == "parse-alerts" and len(args) == 1:
        cmd_parse_alerts()
    elif args[0] == "decide" and len(args) == 3:
        cmd_decide(args[1], args[2])
    else:
        print("Usage: scan.py | scan.py alerts [csv] | scan.py parse-alerts | scan.py decide \"Company\" keep|pause|remove")
        sys.exit(2)
