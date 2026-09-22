# ATS Registry & Employer Watchlist

## How to use this file

`03-portals.md` has two jobs:
1. **ATS registry** — confirmed slugs and API endpoints for each employer you're tracking
2. **Watchlist** — the ~15 employers worth checking within days of a new posting, not just during weekly scans

The `scan` mode checks this file for the watchlist pass (step 4 in the scan protocol).

---

## ATS endpoint patterns

Use these to verify a posting is live on the employer's own board.

### Greenhouse
```
Board index:    https://boards.greenhouse.io/{slug}
API (JSON):     https://boards-api.greenhouse.io/v1/boards/{slug}/jobs
```
Verification: the role must appear in the board index, not just have a working req URL.
An Apply button on a req page proves a form exists, not that the job does.

### Ashby
```
Board index:    https://jobs.ashbyhq.com/{slug}
API (JSON):     https://api.ashbyhq.com/posting-api/job-board/{slug}
```

### Lever
```
Board index:    https://jobs.lever.co/{slug}
API (JSON):     https://api.lever.co/v0/postings/{slug}
```

### Workday
```
Board index:    https://{company}.wd{N}.myworkdayjobs.com/{company}/jobs
Search (JSON):  POST to /wday/cxs/{company}/{company}/jobs  (requires browser session)
```
Workday renders dynamically — use browser search, not API. The `site:` dork is the fastest
discovery path: `site:{company}.wd1.myworkdayjobs.com "product manager" "director"`

### iCIMS / SmartRecruiters / Taleo / custom ATS
Verify manually. Pattern: search the careers page for the req title and confirm it appears
on the employer's own domain.

---

## Watchlist — priority employers

These employers post roles you care about frequently. Check them on every scan, not just
when the query-led search surfaces them.

Add employers here as you discover them. For each, note the ATS type, the slug, and
what specifically you're watching for.

| Employer | ATS | Slug / URL | What you're watching for | Last checked |
|---|---|---|---|---|
| [Company] | [Greenhouse / Ashby / Lever / Workday] | [slug or URL] | [e.g. "Director of Product, Identity"] | [date] |

---

## Company registry

Employers scanned by `scan.py` are defined in the `GREENHOUSE`, `ASHBY`, and `LEVER` lists
in `scan.py` itself. This file holds extended notes that don't belong in code.

For each employer you add to `scan.py`, add a row here with:
- Confirmed slug and date confirmed
- What they're building that's relevant to your search
- Any notes about the company (hiring pattern, team size, known contacts)

| Employer | ATS | Slug | Confirmed | Notes |
|---|---|---|---|---|
| [Company] | Greenhouse | [slug] | [date] | [e.g. "Identity platform; 3 reqs in last 6 months, all IC"] |

---

## Ghost job registry

A posting seen 3+ times across scans over months without resolution is a ghost job.
Log it here and stop surfacing it.

| Employer | Title | First seen | Times seen | Notes |
|---|---|---|---|---|
| [Company] | [Title] | [date] | [count] | [e.g. "Same req, reposted every 60 days — likely evergreen or frozen"] |

---

## Scan log

Record each scan run here with coverage and results.

| Date | Queries run | Boards checked | Verified live | Above threshold | Notes |
|---|---|---|---|---|---|
| [YYYY-MM-DD] | [X of Y] | [X of Y] | [N] | [N] | [e.g. "Workday down — 5 boards unreadable"] |
