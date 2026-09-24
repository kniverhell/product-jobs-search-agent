---
name: job-search-ops
description: Runs a senior PM job search end to end — scans for roles matching your domain and level, evaluates them against a structured seven-block rubric, tailors your resume, drafts outreach and cover letters, builds your interview story bank, and keeps the pipeline honest. Use this skill whenever you mention a job posting, a company you're targeting, a recruiter conversation, an interview, comp or negotiation, or say anything like "run the scout", "evaluate this", "tailor my resume", "who should I contact", "where am I at" — even if you don't name this skill.
---

# Job Search Ops

Read `config.md` and `01-target-roles.md` first. `config.md` holds **facts about you**: background, comp floors, home metro, relocation, domain keywords. `01-target-roles.md` holds **your scoring rules**: archetypes, title levels, location modifiers, company tiers, blockers, no-go list. Claim rules live in `06-proof-points.md`. Every mode inherits from these three.

**This skill owns the bookkeeping.** You should never have to remember what state anything is in.

## Non-negotiable rules

1. **Never submit, send, or click anything.** Every mode stops at a draft you review. No auto-apply, no sending email, no clicking through an ATS. Ever.
2. **Never invent a fact or a metric.** The master resume contains `[TK — ...]` placeholders where numbers are missing. If a strong bullet needs one, stop and ask. Do not estimate, round, or infer. Do not soften a claim to make an unverifiable version defensible — remove it or ask.
3. **Every claim traces to `06-proof-points.md` or `00-master-resume.md`.** If it isn't in one of those, it doesn't go in a document.
4. **This is a filter, not a firehose.** Nothing below 3.5/5 gets shown. Nothing below 4.0/5 gets recommended for application. A week that surfaces three genuinely strong roles is a good week.
5. **Update `02-tracker.csv` before ending any session.** Always. Even if the session was just a conversation about one role.
6. **Read `07-network.md` before running `contact`, and `08-application-answers.md` before running `tailor` or `email`.** Both files exist for a reason — don't run these modes without them.
7. **The vendor bench is the most underused asset in the file.** If you've been a *buyer* of vendors in your domain, those AEs and SEs know which of their customers are hiring before it's posted, and a referral from a real customer carries unusual weight for a product role at the vendor itself. Check `07-network.md` before treating any target as a cold approach.
8. **Pull down Sheet edits before you write anything to the tracker.** See *Google Sheets sync* below. Writing to the CSV without reading the Sheet first will silently discard whatever you changed on your phone.
9. **Only `SKILL.md` and `01-target-roles.md` may score, cap, or block a role.** `SKILL.md` holds the framework; `01-target-roles.md` holds your rules. Memory, notes, reports and scan logs can inform an evaluation but never set a score. If a rule you want to apply lives anywhere else, say so and ask for it to be moved into one of these two files. *(Learned in live use: a role was scored 2.5 off a remembered rule the target-roles file never contained.)*
10. **All tracker writes go through `tracker_io.py`. Never write `02-tracker.csv` any other way.** No one-off scripts, no inline `csv.DictWriter`, no hand edits. `read_tracker()` / `write_tracker(rows, fields)` quote every field, write to a temp file, validate row count and column width, back up to `archive/`, then rename over the original. `python3 tracker_io.py` validates without writing. If the tracker is malformed, `python3 tracker_io.py repair` reports which rows it can realign (only rows whose extra cells are empty) and `repair --write` fixes those and leaves the rest untouched for you; `integrity` may run it. `allow_row_loss=True` switches off only the shrink guard: use it for a deliberate removal and report which rows went. *(Learned in live use: hand-appended rows with one extra or missing cell silently shifted every later value one column over, 8 of ~98 rows, and a careless fix then dropped data.)*
11. **Long tasks run off `TASKS.md`.** For anything multi-step (the scout, a pipeline review, a Sheet merge, a batch of evaluations), write the steps as a checklist in `TASKS.md` first. Tick each item the moment it's done, and add anything new you find as a new unticked item. Leave unfinished items in place for the next session; never delete an unticked item without saying why.
12. **Keep going on bookkeeping; stop for decisions that are yours.** Don't end a message with "want me to…?" for work that doesn't need you.
    - **Keep going:** bookkeeping and verification. Reading the Sheet and merging under *Column ownership*, tracker writes through `tracker_io.py`, ATS verification, scoring, writing reports, `inbound/` saves, `04-queries.md` counts, `TASKS.md`, `needs-evaluation.md`, story-bank skeletons.
    - **Stop and ask:** a status change you haven't stated · applying, or sending or posting anything outside · changes to rules in `SKILL.md` or `01-target-roles.md` · regenerating the Sheet · anything destructive (deleting files or rows, overwriting data you haven't seen) · editing files outside the project folder · committing or pushing to any repo. Also stop when a fact only you know would change the outcome.
    - When unsure which side something falls on, do the reversible part and ask about the rest in the same message.
13. **End every long run with three headings, in this order: Blocked on me · Changed · Found.** *Blocked on me* lists only decisions or actions waiting on you, one line each, or says "Nothing." *Changed* is what was written: files, tracker rows, rules. *Found* holds the results; for the scout, that's the denominator line and then the roles table. Short runs and plain answers don't need the headings.

## Files

| File | What it is |
|---|---|
| `config.md` | **Facts about you:** background, comp floors, home metro, relocation, domain keywords. Copied from `templates/config.md`. **No rules.** |
| `00-master-resume.md` | Source of truth for your experience. Tailored resumes are always a *subset*. |
| `01-target-roles.md` | **Your scoring rules, all of them:** archetypes, title levels, location modifiers, company tiers, blockers, no-go list, survival verdict effects, trajectory rule. Read before scoring anything. |
| `02-tracker.csv` | One row per role. Statuses defined below. Optionally mirrored to Google Sheets. With sync on, ownership is split by column (see *Column ownership*). |
| `tracker_io.py` | **The only tracker writer.** See rule 10. |
| `needs-evaluation.md` | Unscored rows (blank or `TBD`) **with a decision still open**: `New`, `Evaluated`, or a live process (`Screening`, `Interviewing`, `Final`, `Offer`). Applied, closed and passed rows stay off; an applied role comes back if it moves to `Screening`. Remove a row when its score is written. Copied from `templates/needs-evaluation.md`. |
| `TASKS.md` | The checklist for the current long task (rule 11). Unticked items carry over to the next session. |
| `03-portals.md` | ATS registry and employer watchlist. Company tiers, confirmed ATS slugs, scan logs. |
| `04-queries.md` | **Primary discovery surface.** Query set (Tier 1–3), per-query run/qualifying counts, Workday `site:` discovery. Read before scanning. |
| `05-story-bank.md` | Accumulating STAR+R interview stories. Grows on every evaluation. |
| `06-proof-points.md` | The evidence ledger. Every number you can defend, its source, and standing constraints. |
| `07-network.md` | **Who you actually know.** Former colleagues by employer, plus vendor contacts. `contact` mode is only as good as this file. |
| `08-application-answers.md` | Standard ATS answers written once to stay consistent across applications. |
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
| "where am I at" / "pipeline review" | New roles first, pipeline in one line, Sheet sync | **Weekly Review** section below |
| "something feels off in the tracker" | Dedup, status normalization, health check | `modes/integrity.md` |

**Default behavior:** if you paste a job posting with no instruction, run `evaluate`. That is almost always what you mean.

## Google Sheets sync (optional)

If you want to review the pipeline on your phone, the system can mirror `02-tracker.csv` to a Google Sheet.

**Find the Sheet by title, never by a stored file ID.** Regenerating creates a new file, and a phone edit can land in any copy, so an ID saved here goes stale. Every session: search Drive for Sheets matching your title pattern, take the one with the most recent `modifiedTime`, and **report which Sheet was chosen, with its title and modified time.**

**Sheet title pattern:** `[YOUR_SHEET_TITLE_PATTERN]` *(e.g. "Job Search Tracker")*

### Column ownership

Sheet and CSV each own different columns. Neither file wins everything.

| Owner | Columns | Rule |
|---|---|---|
| **Sheet wins** | `status`, `last_touch`, `hiring_manager`, `recruiter`, `warm_contact`, and **any custom columns you add** | **A non-empty** Sheet value overwrites the CSV on every sync. An empty Sheet cell never overwrites; the CSV keeps its value. **Exception for `Expired`:** the Sheet may overwrite a CSV `Expired` only with a human-event status (`Applied`, `Screening`, `Interviewing`, `Final`, `Offer`, `Accepted`, `Rejected`, `Withdrawn`, `Ghosted`, `Passed`), never with `New` or `Evaluated`. These describe what happened between you and a human; only you know. |
| **CSV wins** | `archetype`, `location_tier`, `verified_on`, `verified_url`, `posting_closed_on`, `url`, `next_action`, `next_action_due` | The system's evaluation and verification record. A differing Sheet value is ignored on merge; report it if it looks deliberate (e.g. a hand-typed score). **`next_action` and `next_action_due` are set by the agent**: a forked score's resolving question, a stale req's recruiter question, a stated application deadline. A differing non-empty Sheet value in either is **reported to you**, never applied and never discarded silently. For a row that exists **only** in the Sheet, its values seed the new CSV row. |
| **Merge** | `notes` | **Never overwrite, either direction.** Sheet → CSV: append any Sheet text not already in the CSV note, tagged `[SHEET <date>: …]`. Ignore truncated text ending `[FULL NOTE IN 02-tracker.csv]`; that's an artifact, not an edit. CSV → Sheet: keep your existing cell text verbatim. |
| *Unlisted* (`company`, `title`, `date_found`) | — | CSV wins; a Sheet value fills a **blank** CSV cell; a conflicting non-blank Sheet value is **reported, not applied**. |

**No human scores.** The Sheet's `score` and `score_pre_modifier` columns are **ignored in every merge**. A score comes only from an evaluation (`modes/evaluate.md`). A row created from the Sheet starts with a **blank** score and goes on `needs-evaluation.md` if its decision is still open.

**Code never writes `status` back to the Sheet.** Status flows Sheet → CSV only. If the Sheet is regenerated, status cells and your custom columns are copied verbatim from the Sheet as last read; a row the Sheet has never seen goes in with an **empty** status for you to set.

### ⚠ Silent row loss — verify the row count every single time

A CSV-to-Sheets conversion can drop rows and report success. This happened: two adjacent rows with byte-identical `title` values caused one row to silently disappear. Nothing errored.

**Two rules, both mandatory:**
1. After every regenerate, read the Sheet back and count rows against the CSV.
2. Never let two rows share an identical `title` string. When one req is posted at multiple locations, suffix the title — `[City A]`, `[City B]`.

### Every session, in this order

1. **Read the Sheet first**, before touching `02-tracker.csv`. Pick it by title pattern and newest `modifiedTime` (above), and say which one you picked.
2. **Diff against the CSV, column by column, under *Column ownership* above.** Sheet-owned columns win, CSV-owned columns stay, notes merge, and conflicts on unlisted columns get reported.
3. **Merge your changes into the CSV**, then do the session's work.
4. **At session end, regenerate the Sheet ONLY IF the CSV changed this session.** An unchanged pipeline regenerates nothing.

### Rules

- **Never regenerate the Sheet without merging your edits down first.** Regenerating is a replace.
- **Non-canonical statuses are signal, not error.** If you typed "Recruiter call Thurs" into the status column, that's you telling the system something. Map it to canonical, move the detail to `notes`, say what happened.
- **Warn before investing in formatting.** Conditional formatting, filters, frozen panes and formulas do not survive a regenerate.
- **Notes merge, never overwrite.** See *Column ownership*. Sheets truncates long notes, so never treat a truncated Sheet note as an edit.

## Auto-scheduled runs

- **Coverage is structurally limited** when no browser session is active. Every auto report must open with the coverage line from `modes/scan.md`: all queries in `04-queries.md` and all sources, naming what wasn't run, so limited coverage is never mistaken for a quiet market. Auto runs never read LinkedIn (see `modes/scan.md` → *Terms of use*).
- **Never report an absence without stating the denominator.** "The market is quiet" after running three queries is not a finding. The difference between a quiet market and an unread one is the entire value of the scan.
- Auto runs **never** set a status to `Applied` — only your own word does that. An application is a human act.
- **Statuses auto runs may set:** `New`, `Evaluated`, `Expired` — observable from the posting. `Expired` only for a role never applied to; when an applied role's posting closes, set `posting_closed_on` and leave the status alone.
- **Statuses auto runs may never set:** `Passed`, `Ghosted`, `Applied`, `Screening`, `Interviewing`, `Final`, `Offer`, `Accepted`. These require human knowledge about what actually happened.
- **Deadlines inside 7 days break the batch** — surface immediately, not in the weekly roll-up.

## ⚠ LinkedIn match badges are keyword matching, not fit scoring

LinkedIn's "top applicant" and "high match" signals read your keyword surface, not your actual fit. They generate systematic false positives on roles where your keywords match but your level or domain half doesn't.

**Rule: the badge is not evidence and never raises a score.** Run the same two checks regardless of what it says: search the JD for `reports` / `team of` / `mentor` / `recruit`, and establish whether the end user is a consumer or an enterprise/workforce.

## Canonical statuses

Use exactly these strings in the tracker. Nothing else.

`New` → `Evaluated` → `Tailored` → `Applied` → `Screening` → `Interviewing` → `Final` → `Offer` → `Accepted`

Terminal: `Rejected` · `Withdrawn` · `Ghosted` (no response 21+ days) · `Passed` (you declined to apply) · `Expired` (posting closed **before you applied**)

**A posting that closes after you applied is not `Expired`.** Your application is still live on their side. Record the date in `posting_closed_on` and leave the status as it is (`Applied`, `Screening`…). `Expired` is only for roles at `New`, `Evaluated` or `Tailored`.

## Scoring — 1.0 to 5.0

Score each dimension 1–5, then produce a **holistic** score. The holistic is a judgment call informed by the dimensions, not their average — a role that's a perfect domain fit but two levels too junior is not a 4.

| Dimension | What it measures |
|---|---|
| **Domain fit** | **Problem ownership.** Is the core problem space one you have **owned**? Judged on the problem the job exists to solve, not on whether the ledger has a number for it. Scale below. |
| **Level fit** | Does this role own roadmap and people, not just a feature backlog? Look for "own the vision," "manage PMs," "0→1," "define strategy." |
| **Evidence match** | **Provable with numbers.** How much of **this JD** can you prove with numbers from `06-proof-points.md`, requirement by requirement? Not keyword overlap. Scale below. |
| **Company fit** | Domain-core vendor > domain-adjacent company where your work is existential > company where it's decorative. See *Company tiers* in `01-target-roles.md`. |
| **Trajectory** | Does this role make the *next* one better? Growing scope, better story, stronger network. How it treats a move out of your specialty depends on `SPECIALTY_PATH` in `config.md`; see *Trajectory and specialty path* below. |

### Domain fit and Evidence match: two different questions

Domain asks whether you have **owned** this kind of problem. Evidence asks whether you can **prove** this JD's asks with numbers. A gap belongs to one of them, never both.

| Score | **Domain fit: problem ownership** | **Evidence match: provable with numbers** |
|---|---|---|
| *Judged on* | The problem the job exists to solve. Ignore whether the ledger has a metric for it. | The JD's specific requirements, one by one, against ledger entries. |
| *Doesn't count* | Keyword overlap; the company's industry | Anything not in the ledger; designed-not-built work; ledger items marked Open |
| **5** | Owned this exact problem space | Nearly every core requirement has a **Solid** ledger entry with a number |
| **4** | Owned an adjacent space in another form (same problem, different product, rail, customer or scale) | Most core requirements have a **Solid** numbered entry; the gaps are secondary or preferred qualifications |
| **3** | Owned part of it, or worked alongside it without owning the whole | About half the core requirements are provable, **or** the core rests on partial evidence (below) |
| **2** | Never owned it: a named technical domain you haven't worked in | Only the edges of the JD are provable; core requirements have no entry |
| **1** | Unrelated problem space | Nothing in the ledger applies |

**Half points** are allowed on both when a role sits between two descriptions (3.5, 4.5). State the split in the report: what pushed it up, what held it back.

**Partial evidence.** Ledger items marked **Confidential** or **Closed as qualitative** can support an Evidence 3, never a 4 or 5; only **Solid** entries carry 4–5, and partial evidence can't lift a score to 3.5. **Open** items and **Designed-only** work don't count at all.

**Score the charter, not the label.** A broad "platform" title is not an automatic Domain 2. Score whether you have owned the problem that platform's charter exists to solve.

**Building models vs owning decisions.** In ML-heavy domains (fraud, risk, recommendations, ranking, pricing), a role whose core is **building models** (data science, model ops, ML platform) caps Domain at 2 unless you have built models yourself. A role that **owns the product decisions the models feed** (what to approve, block, step up, rank or show) scores normally.

**Worked examples** (fictional roles):
- *High Domain, low Evidence.* Director of Product, Payments Risk. You owned risk decisioning for a card platform; this role owns it for bank transfers. **Domain 4.5**: same problem on a different rail, and the rail is the half point held back. The JD's core asks are dispute-automation outcomes and network-rule compliance, and your ledger has nothing on either; only the roadmap and stakeholder asks at the edges are provable. **Evidence 2.**
- *Low Domain, high Evidence.* Senior Director, Enterprise Data Platform at a regulated insurer. You've never owned a data platform: **Domain 2**. But the JD's core asks are delivery against a regulatory deadline, consolidating business lines onto a shared service, and managing managers, and each has a Solid numbered ledger entry. **Evidence 4.**

### Trajectory and specialty path

Set once in `config.md` as `SPECIALTY_PATH`. Default: `protect`.

- **`protect`**: Trajectory may penalize a role that moves you out of your specialty.
- **`open-to-drift`**: Trajectory must not penalize it, and reports never call an off-specialty role a "re-label" or a "detour". Score scope, credibility and fit instead.

The comp floor applies either way.

### Location modifier

After setting the holistic, apply the location modifier from `01-target-roles.md`. Show both numbers in the report — the pre-modifier score and the final — so the trade-off is visible rather than buried.

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

> Acme — 4.6 before location. Days on-site unknown. At ≤2 days: 4.1, Apply. At >2 days: 3.7, below threshold. **One email to the recruiter settles it.**

A score built on a guess about a fact looks like an answer and is actually a deferral. Say what's unknown, say what it's worth, and name the cheapest way to resolve it.

Record a forked score as a range (`3.7-4.1`) in the tracker and put the resolving question in `next_action`. Never collapse a fork to a single number for the sake of a tidy column.

### Hard blockers — cap the holistic at 2.0 regardless of everything else

The list lives in `01-target-roles.md` → *Hard disqualifiers*, and only there (rule 9). Don't restate it here and don't add a second one anywhere else. The no-go list is in the same file.

### Legitimacy check — run this on every posting

Flag, and drop the score, if you see: no named company, comp range absurdly wide or absent where legally required, the same posting reposted continuously for months (ghost job), a JD that reads as generic across a dozen roles, an application flow asking for SSN or bank details up front. State what you found — don't quietly deduct.

## The verification gate

**No role appears in any report, or gets tailored, contacted, or applied to, without a `verified_on` date in the tracker.** A posting is live only when the employer's own ATS currently says so. This gate applies to roles you paste in manually too — check it's still open before spending effort on it.

## Reporting

Short. Table-first. Best role at the top. Never more than ten rows. Every row: Company | Title | Score | the single sharpest reason you'd win it | link.

Then one line on what you should actually do next — one action, not a menu.

For long runs, this table sits under **Found**, after **Blocked on me** and **Changed** (rule 13). Decisions first, results second.

If a mode produced a document, give the filename and the one thing in it that needs your judgment. Don't summarize the whole document back.

## Weekly Review

Triggered by "where am I at," "pipeline review," or Monday.

The weekly review is about finding and moving on new roles, not auditing follow-ups. A list of unanswered applications is demoralizing noise, not action. Lead with opportunity; keep the pipeline summary brief.

**Step 1 — read the Sheet first** (if Sheets sync is enabled). Diff against `02-tracker.csv` under *Column ownership*. Merge before doing anything else.

**Step 2 — new roles this week.** Run the scout against `04-queries.md`. Surface everything 4.0+. Table-first: Company | Title | Score | Why you'd win it | Link. Best role first. State the denominator.

**Step 3 — pipeline in one line.** Counts only: X applied, Y in screening/interviewing, Z stalled. **No overdue follow-ups, no past-due `next_action_due` dates, no nagging about individual replies.** Those dates stay in the tracker as a record; they are not surfaced.

Never surface `Passed`, `Expired`, `Rejected`, `Withdrawn` or `Ghosted` unless asked.

**Step 4 — one deadlined item.** Only a hard external deadline inside 7 days (application close, scheduled interview) or a role crossing the 90-day staleness cliff this week. State it once. If nothing qualifies, skip this step.

**Step 5 — one action.** The single thing that most moves the search forward this week: finding or advancing a role, not chasing a reply.

**Step 6 — update the tracker before ending** (via `tracker_io.py`). Regenerate the Sheet only if a row actually changed.

**Tone:** job searching is grinding. Lead with what's good. Don't manufacture enthusiasm about a thin week; say it's thin and say why.
