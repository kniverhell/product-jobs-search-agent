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

### ⚠ Verification rules learned the hard way

Each rule below came from a real miss. Apply them during step 3, before a role reaches the report.

- **"Updated" dates aren't repost dates.** Board metadata like Greenhouse `updated_at` moves on any edit. Only a newer *publish* date on the employer's board resets the staleness clock; otherwise score it as a fork. *Failure: a 116-day-old posting showed "updated today", which would have silently erased a hard staleness blocker.*
- **Dedup on employer req ID and URL, not only on title.** A role you "found" may be one you already passed on under a mistranscribed title. *Failure: a tracker row said "Program Manager" where the employer said "Product Manager"; the same req came back as new three weeks after it was passed on.*
- **Get the employer URL from the job board's "Apply on company website" link.** Unwrap the redirect's `url` parameter and read the host and path. Don't guess ATS tenant or site names. *Failure: guessed Workday tenant names returned nothing, so a live posting looked unverifiable; the Apply link named the exact tenant, site and req ID.*
- **A branded careers site can front a readable ATS.** When a careers domain isn't Greenhouse, Ashby or Lever, look in its page source for the apply URL; it often names a Workday tenant whose JSON endpoint is readable. Record it in `03-portals.md`. *Failure: an employer was logged as unscannable because its careers domain was custom; its apply links pointed at a Workday tenant readable with plain curl.*
- **Scan the employer's board for sibling reqs.** When verifying a role, look for others on the same team at a different level. *Failure: an application went to a senior IC req open ten months while the same board carried a people-leading req on that team, three weeks old and a better level match.*
- **Search the board by function, not title, for "unlisted" or "pulled" roles.** Read every director-level JD; big employers post under generic titles, and one req can carry several openings. *Failure: a referred role looked unlisted but was live under a generic product-manager director title, with the specific opening described only in the JD body.*
- **A referred role can outlive its public posting.** When a referred role's page disappears, record `posting_closed_on`, keep the referral path open, and ask the referrer whether it's still active internally. Keep searching the board under its functional label. *Failure: none yet; recorded so a 404 isn't treated as a dead lead.*
- **Collapse a board to distinct titles before counting new roles.** Group postings by title and count locations per title, and report both numbers ("postings: N · distinct titles: M"). A large gap means cloned evergreen listings: run the legitimacy check on them. *Failure: a board that looked like ten new PM roles held 1,143 product postings but only 65 distinct titles, each cloned across 20–44 countries.*

### Tool behaviour

- **Pace aggregator page loads.** One query every few seconds, reading the rendered results. Never call an aggregator's unauthenticated data endpoint in a loop from the logged-in page. *Failure: ~30 rapid calls to a guest jobs endpoint returned padded results, then triggered a ten-minute rate-limit lockout of the whole site mid-scout.*
- **Test scanner changes against saved output; run the live scan once per cycle.** Repeated live scans trigger rate limits at job-board hosts, and fetching several pages in parallel makes it worse. *Failure: several live reruns in one hour made three large boards return rate-limit errors (reported as unread, as designed).*
- **Browser-tool output filters can block text that looks like `key=value`.** Print extraction results as plain lists, with no `=` and no ids glued to query-like strings. *Failure: an extractor printing "none=false" was blocked twice as cookie/query data, costing two query runs.*

**4. Watchlist pass.** After the queries, check the ~15 employers in `03-portals.md` worth knowing about within days. Depth, not discovery.

**5. Then score.** Drop anything already tracked (fuzzy match). Apply hard blockers, the legitimacy check, staleness, the location modifier from `01-target-roles.md`. Surface nothing below 3.5 post-modifier — **except a forked score whose upper bound clears 3.5, which surfaces as a range with the resolving question.**

**6. Save and record.** Full JD to `inbound/`, with source URL, verification date, and **which query found it**. Tracker row as `New`. If Sheet sync is on, read the Sheet before writing: pick it by title pattern and newest `modifiedTime`, never a stored file ID, and report which Sheet you chose with its title (`SKILL.md` → *Google Sheets sync*).

## Reporting — coverage first, always

Open with the denominator. It counts **every query in `04-queries.md`** and **every source**: LinkedIn, the ATS API script (`python3 "<kit>/scan.py"`, run from the project folder; it reads the `scan-screen` block in `01-target-roles.md` and the `scan-boards` block in `04-queries.md`), Workday `site:` queries, and the watchlist. Name whatever wasn't run.

> `Queries run: 12 of 16 (not run: Q10–Q13, geography). Sources: LinkedIn ✓ · scan.py ✓ · Workday site: ✗ not run · watchlist ✓. Candidates: 31. Verified live: 12. Dead or unverifiable: 19. Above threshold: 4.`

When a board's postings are counted, give distinct titles too (see *Collapse a board to distinct titles*).

Never report an absence without it. "The market is quiet" after running three queries is not a finding, it is an unread report — and the difference between a quiet market and an unread one is the entire value of the scan.

Name any query that could not run and why.

## Then the table

At most ten, best first: Company | Title | Score | Location tier | Posted | Why you'd win it | Link.

**Flag any employer not previously seen.** That is the query-led approach working — a company-led scan structurally cannot surface one, and these are the roles the old approach misses.

## After the run

Update the run and qualifying counts in `04-queries.md`. A query with zero qualifying roles across six runs gets rewritten or retired.

If a qualifying role arrives from outside the query set — a recruiter, a referral, something spotted manually — **work out which query would have caught it and add that query.** That is the mechanism by which this file improves rather than freezing.

## Tuning the title screen

`scan.py`'s title screen (the `scan-screen` block in `01-target-roles.md`) is a pattern plus exclusions plus core-phrase precedence: an include word, an exclusion list, and a short list of core phrases that beat an exclusion. Change one piece at a time, and measure each change on a saved scan output: rows before and after, titles added, titles dropped. List every dropped title before keeping a change. *Failure: an exclusion list removed real leadership titles because a department word appeared in them; it was only noticed by listing every dropped title.*

## When coverage is thin

Widen in this order, and say which lever was pulled:
1. Tier 2 queries
2. Geography tiers not yet run
3. Threshold to 3.2 **for one run only**, labelled

Never quietly relax the standard. Announce it, run it, restore it.
