# Setup Guide

## Prerequisites

- [Claude Code](https://claude.ai/code) installed (free tier works)
- Python 3.7+ if you want to use `scan.py` (optional)
- A Google account if you want the Sheets sync (optional)

---

## Step 1: Clone the repo

```bash
git clone https://github.com/[your-handle]/job-search-agent.git
cd job-search-agent
```

---

## Step 2: Fill out `config.md`

This is the **only file you personalize**. Everything else in the system reads from it.

> **Privacy note:** `config.md` contains your comp floors and salary expectations. If you fork this repo and push, that data goes public. Either keep your fork private, or don't push `config.md` (add it to your `.gitignore`).

Open `config.md` and fill in:

- **Your background** — your domain, seniority level, and what kind of roles you're targeting
- **Comp floors** — your walk-away number by location type (remote / hybrid / on-site)
- **Location** — your home metro and how many days on-site you're willing to do
- **Domain keywords** — the specialties that define your strongest roles (used by `scan.py`)
- **Target titles** — what levels you'll consider (Director, VP, Head of, etc.)
- **Hard blockers** — industries, role types, or specific companies you will not work for
- **Standing constraints** — any claims you must never make in tailored materials (e.g., if you designed something but never shipped it, say so here so the tailoring mode never overclaims)

---

## Step 3: Add your resume and proof points

Copy your resume into `00-master-resume.md`. This is the source of truth. Tailored resumes are always a subset — nothing gets added that isn't here.

Then fill out `05-proof-points.md` with your defensible evidence:
- Every number you can cite, with its source and how you'd defend it in a room
- Claims with status: **Solid** (on resume, fully defensible) / **Derived** (arithmetic from stated figures) / **Soft** (true but approximate) / **Open** (the claim exists, number TBD)
- Hard rules about what you never cite — the `integrity` mode checks these on every tailored file

This takes a few hours the first time. Do it. The payoff is that you never overclaim in a tailored document, and you always know exactly what you can say in an interview.

---

## Step 4: Populate the reference files

Fill out the templates in `templates/`:

- `01-target-roles.md` — role archetypes you're targeting, with scoring notes per archetype
- `03-portals.md` — your ATS registry and employer watchlist
- `04-queries.md` — your query set for web discovery (Tier 1 core, Tier 2 adjacent, Tier 3 geography)
- `06-network.md` — everyone you actually know: former colleagues by employer, vendor contacts, warm ties

`06-network.md` is the most underused asset in most searches. The `contact` mode is only as good as what's in this file.

---

## Step 5: Start Claude Code

```bash
claude
```

Paste a JD or say "run the scout." The system will load `SKILL.md` and run the matching mode.

---

## Optional: Google Sheets sync

If you want to review the pipeline on your phone, the system can mirror `02-tracker.csv` to a Google Sheet.

1. Create a blank Sheet in your Google Drive
2. Open `SKILL.md` and add your Sheet ID where indicated
3. Use the `weekly` review trigger ("where am I at") to sync

**Critical rule:** always read the Sheet *before* writing to the CSV. Any edits you made on your phone live in the Sheet, not the CSV. Writing without reading first destroys them.

---

## Optional: scan.py configuration

Open `scan.py` and adjust:

- `COMP_FLOOR` — your base salary minimum (default: a placeholder — set this)
- `SENIORITY` — title keywords to match (default covers Director/VP/Head of/Principal/Senior Director)
- `DOMAIN` — specialty keywords for your area
- `GREENHOUSE`, `ASHBY`, `LEVER` — company lists (the defaults are an example set; swap in your targets)

Then:

```bash
python scan.py
```

Output writes to `inbound/YYYY-MM-DD-scan-candidates.md`.

---

## The one rule above all others

**The system never submits, sends, or clicks anything.** Every mode stops at a draft. You review it; you decide; you act.

This is not a limitation — it is the point. The cost of a bad application or a tone-deaf outreach note is yours to carry. The system surfaces the draft and tells you what it notices. You own the decision.
