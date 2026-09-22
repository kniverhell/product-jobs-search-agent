---
name: job-search-ops
description: Runs a senior PM job search end to end — scans for roles matching your domain and level, evaluates them against a structured seven-block rubric, tailors your resume, drafts outreach and cover letters, builds your interview story bank, and keeps the pipeline honest. Use this skill whenever you mention a job posting, a company you're targeting, a recruiter conversation, an interview, comp or negotiation, or say anything like "run the scout", "evaluate this", "tailor my resume", "who should I contact", "where am I at" — even if you don't name this skill.
---

# Job Search Ops

Read `config.md` first. It holds your background, comp floors, domain, location preferences, hard blockers, no-go list, and standing constraints. Every mode in this system inherits from it.

**This skill owns the bookkeeping.** You should never have to remember what state anything is in.

## Non-negotiable rules

1. **Never submit, send, or click anything.** Every mode stops at a draft you review. No auto-apply, no sending email, no clicking through an ATS. Ever.
2. **Never invent a fact or a metric.** The master resume contains `[TK — ...]` placeholders where numbers are missing. If a strong bullet needs one, stop and ask. Do not estimate, round, or infer. Do not soften a claim to make an unverifiable version defensible — remove it or ask.
3. **Every claim traces to `05-proof-points.md` or `00-master-resume.md`.** If it isn't in one of those, it doesn't go in a document.
4. **This is a filter, not a firehose.** Nothing below 3.5/5 gets shown. Nothing below 4.0/5 gets recommended for application. A week that surfaces three genuinely strong roles is a good week.
5. **Update `02-tracker.csv` before ending any session.** Always. Even if the session was just a conversation about one role.
6. **Read `06-network.md` before running `contact`, and `07-application-answers.md` before running `tailor` or `email`.** Both files exist for a reason — don't run these modes without them.
7. **The vendor bench is the most underused asset in the file.** If you've been a *buyer* of vendors in your domain, those AEs and SEs know which of their customers are hiring before it's posted, and a referral from a real customer carries unusual weight for a product role at the vendor itself. Check `06-network.md` before treating any target as a cold approach.
8. **Pull down Sheet edits before you write anything to the tracker.** See *Google Sheets sync* below. Writing to the CSV without reading the Sheet first will silently discard whatever you changed on your phone.

## Files

| File | What it is |
|---|---|
| `config.md` | **Your configuration.** Background, comp floors, domain, location, blockers, no-go list, standing constraints. Read first. |
| `00-master-resume.md` | Source of truth for your experience. Tailored resumes are always a *subset*. |
| `01-target-roles.md` | Role archetypes, hard blockers, comp floor reference, what to lead with. Read before scoring anything. |
| `02-tracker.csv` | One row per role. **Canonical.** Statuses defined below. Optionally mirrored to Google Sheets. |
| `03-portals.md` | ATS registry and employer watchlist. Company tiers, confirmed ATS slugs, scan logs. |
| `04-queries.md` | **Primary discovery surface.** Query set (Tier 1–3), per-query run/qualifying counts, Workday `site:` discovery. Read before scanning. |
| `04-story-bank.md` | Accumulating STAR+R interview stories. Grows on every evaluation. |
| `05-proof-points.md` | The evidence ledger. Every number you can defend, its source, and standing constraints. |
| `06-network.md` | **Who you actually know.** Former colleagues by employer, plus vendor contacts. `contact` mode is only as good as this file. |
| `07-application-answers.md` | Standard ATS answers written once to stay consistent across applications. |
| `inbound/` | Raw JDs. `YYYY-MM-DD-company-slug.md` |
| `reports/` | Evaluation reports. Same slug. |
| `tailored/` | Resume + cover letter + outreach per role. Same slug. |
| `sent/` | Exactly what was submitted, with date. Never edited after it lands here. |

## Modes

Read the mode file before running it. Don't work from memory.

| Say this | Mode | File |
|---|---|---|
| "run the scout" / "any new roles" | Scan portals and queries for new postings | `modes/scan.md` |
| paste a JD or URL | Full evaluation → report → tracker entry | `modes/evaluate.md` |
| "tailor for X" | Tailored resume against one JD | `modes/tailor.md` |
| "write the cover letter" | Cover letter | `modes/cover.md` |
| "who should I contact" | Hiring manager / recruiter / peer + LinkedIn notes | `modes/contact.md` |
| "dig into this company" | Six-axis company research | `modes/deep.md` |
| "draft the application email" | Formal application or referral email | `modes/email.md` |
| "prep me for this interview" | Interview prep from the story bank | `modes/interview.md` |
| "they made an offer" / "what should I ask for" | Comp research and negotiation prep | `modes/negotiate.md` |
| "will they survive" / "run survival on X" | Company survival scoring (auto-runs for private companies at or below Series B) | `modes/survive.md` |
| "where am I at" / "pipeline review" | Pipeline snapshot, follow-up triggers, Sheet sync | **Weekly Review** section below |
| "something feels off in the tracker" | Dedup, status normalization, health check | `modes/integrity.md` |

**Default behavior:** if you paste a job posting with no instruction, run `evaluate`. That is almost always what you mean.

## Google Sheets sync (optional)

If you want to review the pipeline on your phone, the system can mirror `02-tracker.csv` to a Google Sheet.

Add your Sheet ID here once you've created it:
**Sheet ID:** `[YOUR_SHEET_ID]`
**Sheet URL:** `[YOUR_SHEET_URL]`

### ⚠ Silent row loss — verify the row count every single time

A CSV-to-Sheets conversion can drop rows and report success. This happened: two adjacent rows with byte-identical `title` values caused one row to silently disappear. Nothing errored.

**Two rules, both mandatory:**
1. After every regenerate, read the Sheet back and count rows against the CSV.
2. Never let two rows share an identical `title` string. When one req is posted at multiple locations, suffix the title — `[City A]`, `[City B]`.

### Every session, in this order

1. **Read the Sheet first**, before touching `02-tracker.csv`.
2. **Diff against the CSV.** Anything you changed — a status, a contact name, a note, a new row — wins. Your edits are ground truth about the real world; the CSV is only the system's record of it.
3. **Merge your changes into the CSV**, then do the session's work.
4. **At session end, regenerate the Sheet ONLY IF the CSV changed this session.** An unchanged pipeline regenerates nothing.

### Rules

- **Never regenerate the Sheet without merging your edits down first.** Regenerating is a replace.
- **Non-canonical statuses are signal, not error.** If you typed "Recruiter call Thurs" into the status column, that's you telling the system something. Map it to canonical, move the detail to `notes`, say what happened.
- **Warn before investing in formatting.** Conditional formatting, filters, frozen panes and formulas do not survive a regenerate.
- **Notes column: the CSV always wins.** Sheets truncates long notes. Never merge a truncated Sheet note back into the CSV.

## Auto-scheduled runs

- **Coverage is structurally limited** when no browser session is active. Every auto report must open with "Boards read: X of Y" so limited coverage is never mistaken for a quiet market.
- **Never report an absence without stating the denominator.** "The market is quiet" after running three queries is not a finding. The difference between a quiet market and an unread one is the entire value of the scan.
- Auto runs **never** set a status to `Applied` — only your own word does that. An application is a human act.
- **Statuses auto runs may set:** `New`, `Evaluated`, `Expired` — observable from the posting.
- **Statuses auto runs may never set:** `Passed`, `Ghosted`, `Applied`, `Screening`, `Interviewing`, `Final`, `Offer`, `Accepted`. These require human knowledge about what actually happened.
- **Deadlines inside 7 days break the batch** — surface immediately, not in the weekly roll-up.

## ⚠ LinkedIn match badges are keyword matching, not fit scoring

LinkedIn's "top applicant" and "high match" signals read your keyword surface, not your actual fit. They generate systematic false positives on roles where your keywords match but your level or domain half doesn't.

**Rule: the badge is not evidence and never raises a score.** Run the same two checks regardless of what it says: search the JD for `reports` / `team of` / `mentor` / `recruit`, and establish whether the end user is a consumer or an enterprise/workforce.

## Canonical statuses

Use exactly these strings in the tracker. Nothing else.

`New` → `Evaluated` → `Tailored` → `Applied` → `Screening` → `Interviewing` → `Final` → `Offer` → `Accepted`

Terminal: `Rejected` · `Withdrawn` · `Ghosted` (no response 21+ days) · `Passed` (you declined to apply) · `Expired` (posting closed)

## Scoring — 1.0 to 5.0

Score each dimension 1–5, then produce a **holistic** score. The holistic is a judgment call informed by the dimensions, not their average — a role that's a perfect domain fit but two levels too junior is not a 4.

| Dimension | What it measures |
|---|---|
| **Domain fit** | Is your domain the *core* of this job, or a footnote under a broad platform charter? A "Director of Product, Platform" role listing your specialty as one of six areas is a 2, not a 4. |
| **Level fit** | Does this role own roadmap and people, not just a feature backlog? Look for "own the vision," "manage PMs," "0→1," "define strategy." |
| **Evidence match** | How much of the JD can you evidence from the proof points ledger, with numbers? Not keyword overlap — actual demonstrated outcomes. |
| **Company fit** | Domain-core vendor > domain-adjacent company where your work is existential > company where it's decorative. See `config.md` for your tier preferences. |
| **Trajectory** | Does this role make the *next* one better? See `config.md` for your trajectory note — by default, do not penalize for moving away from your specialty. Score on meaningful scope, career credibility, and genuine fit. |

### Location modifier

After setting the holistic, apply the location modifier from `config.md`. Show both numbers in the report — the pre-modifier score and the final — so the trade-off is visible rather than buried.

### Staleness — graded, not binary

| Age (from the employer ATS, not an aggregator) | Effect |
|---|---|
| 0–30 days | none |
| 31–60 days | −0.2 |
| 61–90 days | −0.4, and note that finalists are likely already in process |
| 90+ days with no verifiable refresh | hard blocker |

A repost resets the clock **only if the employer's own ATS shows the newer date.** An aggregator repost is not evidence.

A req open 60+ days is worth asking a recruiter about directly. Long-open senior roles usually mean: a stalled search, a rewritten scope, an internal candidate, or a hiring manager who left.

**When a role is inside a staleness band, state the date it crosses into the next one.** A −0.4 role that becomes a hard blocker in nine days is a deadline, not a score.

### Unknowns that change the recommendation

**Never assume a worst case and score against it.** If a single unknown fact would move a role across the Apply threshold, score everything known and state the fork explicitly:

> Acme — 4.3 before location. NYC days-on-site unknown. At ≤2 days: 3.8, Apply if the week is slow. At >2 days: 3.3, below threshold. **One email to the recruiter settles it.**

Record a forked score as a range (`3.3–3.8`) in the tracker and put the resolving question in `next_action`. Never collapse a fork to a single number for the sake of a tidy column.

### Hard blockers — cap the holistic at 2.0 regardless of everything else

- Relocation required (when `RELOCATION=no` in config.md)
- Contract or staffing-agency listing rather than direct employment
- Posting 90+ days old with no ATS-verified refresh
- Any explicit disqualifier in `config.md` BLOCKERS list

### Legitimacy check — run this on every posting

Flag, and drop the score, if you see: no named company, comp range absurdly wide or absent where legally required, the same posting reposted continuously for months (ghost job), a JD that reads as generic across a dozen roles, an application flow asking for SSN or bank details up front. State what you found — don't quietly deduct.

## The verification gate

**No role appears in any report, or gets tailored, contacted, or applied to, without a `verified_on` date in the tracker.** A posting is live only when the employer's own ATS currently says so. This gate applies to roles you paste in manually too — check it's still open before spending effort on it.

## Reporting

Short. Table-first. Best role at the top. Never more than ten rows. Every row: Company | Title | Score | the single sharpest reason you'd win it | link.

Then one line on what you should actually do next — one action, not a menu.

If a mode produced a document, give the filename and the one thing in it that needs your judgment. Don't summarize the whole document back.

## Weekly Review

Triggered by "where am I at," "pipeline review," or Monday.

**Step 1 — read the Sheet first** (if Sheets sync is enabled). Diff against `02-tracker.csv`. Your edits win on every column except `notes` (CSV always wins on notes). Merge changes before doing anything else.

**Step 2 — pipeline snapshot, three blocks:**

| Block | Rows | Columns |
|---|---|---|
| **Interviewing / Final / Offer** | All | Company · Score · last_touch · next_action · due |
| **Applied / Screening ≥ 4.0** | Sorted by score descending | Same + flag if no follow-up set |
| **Applied / Screening 3.5–3.9** | Separate, labelled "below threshold — held" | Same |

Never surface `Passed`, `Expired`, `Rejected`, `Withdrawn`, `Ghosted` unless asked.

**Step 3 — follow-up triggers:**
- `Interviewing` with `last_touch` > 5 days and no confirmed next step → flag for outreach
- `Applied` with `last_touch` > 21 days and no reply → candidate for `Ghosted`; confirm before setting
- Any `next_action_due` today or past → surface as overdue

**Step 4 — scan check:** one line. When was the last scan? Which queries ran? Overdue if > 7 days.

**Step 5 — update tracker before ending.** If anything changed, decide whether to regenerate the Sheet.
