# Job Search Agent — for Product Managers

A file-based agentic system that runs a senior PM job search end to end. Built with [Claude Code](https://claude.ai/code). No external services, no subscriptions, no database.

**Designed for:** Senior / Director / VP product managers in a specialized domain (identity, fintech, SaaS, data platforms, etc.) who want a structured system rather than ad-hoc AI prompting.

---

## The problem this solves

Most AI job search tools stop at resume rewriting. This one runs the whole operation:

- **Finds roles** — query-led web discovery, watchlist passes, and a Python ATS scanner across 29+ boards
- **Verifies them** — every role confirmed on the employer's own ATS before any effort goes into it
- **Scores them** — 5-dimension rubric with transparent modifiers, not keyword matching
- **Tailors your materials** — resume and cover letter calibrated to one specific JD
- **Prepares you** — company research, interview story mapping, negotiation prep
- **Keeps the pipeline honest** — dedup, staleness enforcement, proof-point integrity

**Key finding from 7 weeks of operation:** ~32% of apparently live job board listings are already closed. The verification gate catches them before you invest any time. A "quiet market" that hasn't been verified is not a finding — it's an unread report.

---

## The 10 modes

| Trigger | Mode | What it does |
|---|---|---|
| "run the scout" / "any new roles" | **Scan** | Query-led discovery + ATS verification |
| Paste a JD or URL | **Evaluate** | 7-block report + score + tracker entry |
| "tailor for [company]" | **Tailor** | Resume calibrated to one JD |
| "write the cover letter" | **Cover** | Under 250 words, company-specific |
| "who should I contact" | **Contact** | Hiring manager + peer + warm-path notes |
| "dig into this company" | **Deep** | 6-axis pre-interview research |
| "draft the application email" | **Email** | Recruiter / referral / cold variants |
| "prep me for this interview" | **Interview** | Story mapping + gap bridges + 5 questions |
| "they made an offer" | **Negotiate** | Comp research + anchoring prep |
| "something feels off in the tracker" | **Integrity** | Dedup, staleness, proof-point drift check |

---

## What it won't do

The system **never submits, sends, or clicks anything.** Every mode stops at a draft you review. No auto-apply, no sending email, no clicking through an ATS. Ever.

This is not an oversight — it is a design decision. An application is a human act. The tracker records it after the fact, when you say so.

---

## 7 weeks of learnings encoded as rules

These findings are now permanent rules in the system:

**Titles lie; the comp band is the tell.** Never score level from a title. Search the JD for "reports," "team of," "mentor," "recruit."

**Aggregator metadata is wrong in every field.** Title, location, arrangement, and date must come from the employer's ATS or be recorded UNKNOWN.

**Filters can reject the market rather than the roles.** A comp floor tiered too finely, or a location rule that's a hard blocker when it should be a modifier, produces false negatives. The system uses modifiers, not binary blockers, for location and adjacent domains.

**Blockers hide; modifiers reveal.** Recalibrate periodically. The right question is: "Is this a hard no or a penalty I can weigh?"

**LinkedIn Boolean out-performs board sweeps.** One targeted query exposes role + connection degree in one pass, merging discovery and warm-path mapping.

**Proof-point integrity is its own system.** Every external claim should have a status (Solid / Derived / Soft / Open). The system checks tailored resumes for numbers that aren't in the proof-points ledger. A claim that crept in without provenance is the one that blows up in an interview.

**Access, not discovery, is the constraint at Director level.** The warm path (referral, vendor contact, former colleague) consistently outperforms the cold application. Build and work `06-network.md` before treating any target as a cold approach.

---

## Setup

See [SETUP.md](SETUP.md).

Short version:
1. Clone this repo
2. Open `config.md` and fill in your background, comp floors, location, domain, and blockers — this is the only file you personalize
3. Open Claude Code in this directory
4. Paste a JD or say "run the scout"

---

## The optional Python scanner (`scan.py`)

A standalone Python 3 script (no dependencies outside stdlib) that queries the public JSON APIs of Greenhouse, Ashby, and Lever boards directly — faster and more reliable than scraping rendered pages.

```bash
python scan.py
```

Filters by your `SENIORITY` and `DOMAIN` keywords, enforces your comp floor, applies staleness bands, writes a Markdown candidate table to `inbound/`.

Customize the company lists in `scan.py` to match your target employers. The default list is a starting point, not a recommendation.

---

## What this won't tell you

- Whether to take a specific job — that's yours
- What your resume should say — that's yours (configure `00-master-resume.md` with your actual history)
- Whether a company is a good place to work — research that yourself with `deep` mode
- Whether your comp floor is the right number — see `config.md` and your own market research

---

## License

MIT. Take it, adapt it, share it.
