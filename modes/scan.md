# Mode: Scan  (query-led)

Find roles by **position, not by company**. The query is the input; the employer is the output.

## Order of operations

**1. Run the queries.** Work `04-queries.md` — Tier 1 always, Tier 2 when Tier 1 is thin, Tier 3 geography every run. Record which queries ran; they get performance-tracked.

**2. Discovery produces candidates, never results.** Every hit is an unverified claim. Google's cache and every aggregator go stale in both directions — dead reqs stay indexed for months, live ones get marked closed on old scrapes.

**3. Verify every candidate on the employer's own ATS.** Confirm: the page loads as a specific req, not an index or redirect · title and location match · a live application mechanism exists · no closure language · capture the posted date.

Reject if it 404s, redirects to a careers homepage, is absent from the employer's board, or exists only on an aggregator. **No `verified_on`, no report.**

### ⚠ Aggregator metadata is wrong in every field

LinkedIn, Indeed, Glassdoor, Built In and the rest are discovery tools only. In live use, every field has been observed wrong:

| Field | Observed |
|---|---|
| **Posted date** | "Reposted 3 days ago" on the aggregator; the employer ATS showed the req first posted 80 days earlier. It closed four days later. |
| **Location** | Aggregator listed one city; the employer posting listed three, including one within commuting range. |
| **Work arrangement** | Aggregator listed a city; the role was fully remote, a 0.8-point swing on the top-scored role. |

**Rule: title, location, work arrangement and posted date come from the employer's own posting**, never from an aggregator, a search snippet, or a LinkedIn card. If the employer's posting can't be reached, record the field as `UNKNOWN` and mark the score provisional. An `UNKNOWN` that resolves later is cheap; a wrong value that looks certain costs roles.

### LinkedIn: read it the way it actually renders

- **Zero is zero.** When a search has no results, LinkedIn shows "No matching jobs found" and fills the page with "jobs you may be interested in". Count that query as **0**. Never count the padding as hits.
- **Background tabs render ~7 cards.** A LinkedIn results list opened in a background tab renders only about seven result cards, however many results it says it has. Read titles from each job's own page (`/jobs/view/{id}`), not from the list.
- **Terms of use.** LinkedIn's terms restrict automated access. Keep LinkedIn reading user-initiated, low volume, and in your own logged-in browser. No scripted crawling, no scheduled runs against it.

**4. Watchlist pass.** After the queries, check the ~15 employers in `03-portals.md` worth knowing about within days. Depth, not discovery.

**5. Then score.** Drop anything already tracked (fuzzy match). Apply hard blockers, the legitimacy check, staleness, the location modifier from `01-target-roles.md`. Surface nothing below 3.5 post-modifier — **except a forked score whose upper bound clears 3.5, which surfaces as a range with the resolving question.**

**6. Save and record.** Full JD to `inbound/`, with source URL, verification date, and **which query found it**. Tracker row as `New`. If Sheet sync is on, read the Sheet before writing: pick it by title pattern and newest `modifiedTime`, never a stored file ID, and report which Sheet you chose with its title (`SKILL.md` → *Google Sheets sync*).

## Reporting — coverage first, always

Open with the denominator. It counts **every query in `04-queries.md`** and **every source**: LinkedIn, the ATS API script (`scan.py`), Workday `site:` queries, and the watchlist. Name whatever wasn't run.

> `Queries run: 12 of 16 (not run: Q10–Q13, geography). Sources: LinkedIn ✓ · scan.py ✓ · Workday site: ✗ not run · watchlist ✓. Candidates: 31. Verified live: 12. Dead or unverifiable: 19. Above threshold: 4.`

Never report an absence without it. "The market is quiet" after running three queries is not a finding, it is an unread report — and the difference between a quiet market and an unread one is the entire value of the scan.

Name any query that could not run and why.

## Then the table

At most ten, best first: Company | Title | Score | Location tier | Posted | Why you'd win it | Link.

**Flag any employer not previously seen.** That is the query-led approach working — a company-led scan structurally cannot surface one, and these are the roles the old approach misses.

## After the run

Update the run and qualifying counts in `04-queries.md`. A query with zero qualifying roles across six runs gets rewritten or retired.

If a qualifying role arrives from outside the query set — a recruiter, a referral, something spotted manually — **work out which query would have caught it and add that query.** That is the mechanism by which this file improves rather than freezing.

## When coverage is thin

Widen in this order, and say which lever was pulled:
1. Tier 2 queries
2. Geography tiers not yet run
3. Threshold to 3.2 **for one run only**, labelled

Never quietly relax the standard. Announce it, run it, restore it.
