# Job Search Agent — for Product Managers

A file-based agentic system that runs a senior PM job search end to end. Built with [Claude Code](https://claude.ai/code). No external services, no subscriptions, no database.

Based on career-ops ([career-ops-hq/career-ops](https://github.com/career-ops-hq/career-ops)) by Santiago Fernández de Valderrama ([@santifer](https://github.com/santifer)), MIT-licensed. Portions of this project are derived from it; see [NOTICE](NOTICE). Not affiliated with or endorsed by the career-ops project.

What's derived from career-ops: the mode structure, the role archetypes, and the interview story bank.

**Designed for:** Senior / Director / VP product managers in a specialized domain (identity, fintech, SaaS, data platforms, etc.) who want a structured system rather than ad-hoc AI prompting.

## Install

```bash
claude plugin install job-search-agent --marketplace kniverhell/product-jobs-search-agent
```

Then make an empty folder for your job search, open Claude Code in it, and say **"run setup"** (or `/job-search-agent:setup`). Every mode also has its own command, such as `/job-search-agent:triage` or `/job-search-agent:fill`. Setup creates your files from templates (placeholders only, never overwriting) and tells you what to fill in first.

Inside a Claude Code session the same install works as `/plugin install job-search-agent --marketplace kniverhell/product-jobs-search-agent`. On older Claude Code versions use two steps: `claude plugin marketplace add kniverhell/product-jobs-search-agent`, then `claude plugin install job-search-agent@product-jobs-search-agent`. To install from a clone instead, see [SETUP.md](SETUP.md).

---

## The problem this solves

Most AI job search tools stop at resume rewriting. This one runs the whole operation:

- **Finds roles** — query-led web discovery, watchlist passes, and a Python ATS scanner across 27 boards
- **Verifies them** — every role confirmed on the employer's own ATS before any effort goes into it
- **Scores them** — 5-dimension rubric: domain fit (have you *owned* this problem?), evidence match (can you *prove* this JD's asks with numbers from your ledger, requirement by requirement?), level fit, company fit, trajectory. Then location and staleness modifiers, shown as separate numbers. Not keyword matching, and never a hand-typed score
- **Evaluates each role** — 7-block structured report covering fit, comp, personalization angle, interview stories, and blockers
- **Tailors your materials** — resume and cover letter calibrated to one specific JD
- **Prepares you** — company research, interview story mapping, negotiation prep
- **Scores company survival** — 9 dimensions, stated confidence, and what it means for your equity and your next two years
- **Keeps the pipeline honest** — dedup, staleness enforcement, proof-point integrity, and a validating tracker writer (`tracker_io.py`) so a stray comma can't shift a row

**Key finding:** ~32% of apparently live listings were already closed *(8 of ~25, first week, checked against the employer's own ATS)*. Dead reqs stay indexed on aggregators for months. The verification gate catches them before you invest any time. A "quiet market" that hasn't been verified is not a finding — it's an unread report.

---

## The 15 modes

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
| "will they survive" | **Survive** | 9-dimension company survival score; auto-runs for private companies at or below Series B |
| "triage against <role>" | **Triage** | Open roles sorted into apply + outreach / apply cold / skip against a role you name; read-only |
| "friction <company>" | **Friction** | Low-star user complaints mined for failure modes, a 90-day thesis and a proof-point map. On request only |
| "fill this application for <role>" | **Fill** | Fills one page of an application you opened in Chrome from your own files; lists every field; never submits |
| "where am I at" / "pipeline review" | **Weekly Review** | New roles first, pipeline in one line, tracker sync (no follow-up nagging) |

---

## What it won't do

The system **never submits, sends, or clicks anything that submits, saves or advances.** `fill` may fill fields on a page you opened; submitting is always yours. Every other mode stops at a draft you review. No auto-apply, no sending email, no clicking through an ATS. Ever.

This is not an oversight — it is a design decision. An application is a human act. The tracker records it after the fact, when you say so.

---

## 8 weeks of learnings encoded as rules

These findings are now permanent rules in the system:

**Titles lie; the comp band is the tell.** Never score level from a title. Search the JD for "reports," "team of," "mentor," "recruit."

**Aggregator metadata is wrong in every field.** Title, location, arrangement, and date must come from the employer's ATS or be recorded UNKNOWN.

**Filters can reject the market rather than the roles.** A comp floor tiered too finely, or a location rule that's a hard blocker when it should be a modifier, produces false negatives. The system uses modifiers, not binary blockers, for location and adjacent domains.

**Blockers hide; modifiers reveal.** Recalibrate periodically. The right question is: "Is this a hard no or a penalty I can weigh?"

**LinkedIn Boolean out-performs board sweeps.** One targeted query exposes role + connection degree in one pass, merging discovery and warm-path mapping.

**Proof-point integrity is its own system.** Every external claim should have a status (Solid / Derived / Soft / Open / Confidential / Closed as qualitative / Designed-only), and only Solid entries can carry a top Evidence score. The system checks tailored resumes for numbers that aren't in the proof-points ledger. A claim that crept in without provenance is the one that blows up in an interview.

**Every mode but one verifies; `survive` estimates.** Survival scoring works from incomplete public data, so it states confidence per dimension and treats missing data as unknown rather than as a middling score. It can cap a role score, never raise one.

**Access, not discovery, is the constraint at Director level.** The warm path (referral, vendor contact, former colleague) consistently outperforms the cold application. Build and work `07-network.md` before treating any target as a cold approach.

---

## Setup

1. Install (one command, above).
2. In an empty folder for your job search, say "run setup".
3. Fill in `config.md` (facts about you) and `01-target-roles.md` (your scoring rules), then `00-master-resume.md` and `06-proof-points.md`.
4. Paste a JD or say "run the scout".

Your files stay in that project folder; the plugin's folder holds only code. Manual install from a clone: [SETUP.md](SETUP.md).

---

## The optional Python scanner (`scan.py`)

A standalone Python 3 script (no dependencies outside stdlib) that queries the public JSON APIs of Greenhouse, Ashby, and Lever boards directly — faster and more reliable than scraping rendered pages.

```bash
python3 scan.py
```

Screens titles with your level, include and exclude terms, enforces your comp floor, applies staleness bands, and writes a Markdown candidate table to `inbound/`. The screen comes from the `scan-screen` block in your `01-target-roles.md` and the boards from the `scan-boards` block in your `04-queries.md`; the script itself holds no settings, and stops with the file and line if either block is missing or unfilled.

---

## Fill mode: filling an application form

Sign in and open the application in your own Chrome (Claude in Chrome), then say "fill this application for <role>". The agent fills one page from your own files, lists every field, and stops. **You review and click Submit.**

- **Sources:** your resume (the role's tailored version if there is one) and `application-profile.md`, the one home for facts and knockout answers (name, contact, work authorization, sponsorship, relocation, in-office days). It's gitignored; a template is in `templates/`.
- **Fills:** factual fields, and knockout questions only when your profile answers them explicitly. A missing answer stays blank and is listed.
- **Never fills:** free-text answers (employers may have AI-use policies, and the first draft is yours), EEO / self-identification, file uploads, passwords, account creation, CAPTCHAs, government ID, date of birth or bank details. It never clicks Next, Save or Submit.
- **Asks first:** before filling anything ("Fill these?"), before replacing a value the site already filled in, and before touching a form inside an embedded frame it can't read.
- **Enforced:** browser scripts are limited to eight pinned read-only scripts by a hook that ships with the plugin (`hooks/fill_js_guard.py`). It's active only in a job-search folder that has `application-profile.md`, so it never touches other projects; the mode checks it's live before every run and stops if it isn't.
- **Not enforced:** "never submit" is an instruction. A hook can't tell a Submit click from a field click, so the mode uses no clicking tools at all. Pages over about 50 fields stop; you fill those yourself.

Tested on a local fixture with fictional data: Haiku (the default) and Sonnet both passed with every knockout right, zero clicks and zero submissions. Setup: [SETUP.md](SETUP.md#filling-applications). Rules: [`modes/fill.md`](modes/fill.md).

---

## What this won't tell you

- Whether to take a specific job — that's yours
- What your resume should say — that's yours (configure `00-master-resume.md` with your actual history)
- Whether a company is a good place to work — research that yourself with `deep` mode
- Whether your comp floor is the right number — see `config.md` and your own market research

---

## License

MIT (see [LICENSE](LICENSE)). Take it, adapt it, share it. Portions are derived from career-ops (MIT); its copyright and license notice are kept in [NOTICE](NOTICE).
