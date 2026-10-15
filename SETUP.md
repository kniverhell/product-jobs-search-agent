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

## Step 2: Copy and fill out `config.md`

Before your first run, copy the template to the repo root:

```bash
cp templates/config.md config.md
```

Edit the root `config.md`, not the template. It's gitignored, so your comp floors never get pushed, even if you forget. The same goes for every personal file you create in the root (see `.gitignore`).

`config.md` holds **facts about you**, and only facts:

- **Your background:** your domain, seniority level, and what kind of roles you're targeting
- **Comp floors:** your walk-away number by location type (remote / hybrid / on-site)
- **Location:** your home metro, max days on-site, and whether you'd relocate
- **Domain keywords:** the specialties that define your strongest roles (used for queries and `scan.py`)
- **Specialty path:** `SPECIALTY_PATH: protect` (default) lets Trajectory penalize roles that take you out of your specialty; `open-to-drift` means it never does, and reports never call such a role a detour. Your comp floor applies either way

**Rules don't go here.** Title levels, location modifiers, company tiers, hard blockers and the no-go list go in `01-target-roles.md` (Step 4). Claims you must never make go in `06-proof-points.md` (Step 3). One home per rule means no two files can disagree about how a role scores.

---

## Step 3: Add your resume and proof points

Copy the two templates to the root (`cp -n templates/00-master-resume.md templates/06-proof-points.md .`), then paste your resume into `00-master-resume.md`. This is the source of truth. Tailored resumes are always a subset — nothing gets added that isn't here.

Then fill out `06-proof-points.md` with your defensible evidence:
- Every number you can cite, with its source and how you'd defend it in a room
- Claims with status: **Solid** (on resume, fully defensible) / **Derived** (arithmetic from stated figures) / **Soft** (true but approximate) / **Open** (the claim exists, number TBD) / **Confidential** (numbered, but the number isn't yours to disclose) / **Closed as qualitative** (real outcome, number unrecoverable) / **Designed-only** (real work that never reached build)
- Status matters for scoring: only **Solid** entries can carry an Evidence match of 4–5. Confidential and Closed-as-qualitative can support a 3; Open and Designed-only don't count
- **Standing constraints:** claims you must never make, e.g. "shipped" near something you designed but never built, or a figure you've retired. This is the only place claim rules live; the `integrity` mode checks them on every tailored file

This takes a few hours the first time. Do it. The payoff is that you never overclaim in a tailored document, and you always know exactly what you can say in an interview.

---

## Step 4: Populate the reference files

Copy the remaining templates to the repo root and fill them in:

```bash
cp -n templates/*.md templates/02-tracker.csv .
```

- `01-target-roles.md`: **all of your scoring rules.** Role archetypes, the problem spaces you've owned (this feeds Domain fit), title levels, location modifiers, company tiers, hard blockers, no-go list, trajectory rule
- `needs-evaluation.md`: starts empty. The system lists unscored roles with an open decision here; a score only ever comes from an evaluation
- `03-portals.md` — your ATS registry and employer watchlist
- `04-queries.md` — your query set for web discovery (Tier 1 core, Tier 2 adjacent, Tier 3 geography)
- `07-network.md` — everyone you actually know: former colleagues by employer, vendor contacts, warm ties

`07-network.md` is the most underused asset in most searches. The `contact` mode is only as good as what's in this file.

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
2. Open `SKILL.md` and set your Sheet **title pattern** where indicated. Don't store a file ID: each session picks the newest Sheet matching the title and says which one it used
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

## Before you push: privacy check

If you push your copy anywhere, check that none of your personal terms (name, employers, phone, local paths) are in it.

1. Create `.privacy-patterns` in the repo root: one term per line, `#` for comments. Matching is case-insensitive and whole-word (a pattern "cat" won't hit "category"; a number won't hit a longer number). The file is gitignored; `privacy_check.py` refuses to run if it's tracked, missing, or empty.
2. Optional: `.privacy-allow` for lines you've decided are fine, one per line: `file | exact line text | YYYY-MM-DD | reason`. Only that exact line passes; a new or edited line with the term still fails. Also gitignored.
3. Run it:
   - `python3 privacy_check.py`: the staged diff (use as a pre-commit check)
   - `python3 privacy_check.py --push`: what a push would publish, `HEAD` plus every unpushed commit
   - `python3 privacy_check.py --all`: every tracked file in your working tree
   - `python3 privacy_check.py --history`: every commit on every local branch, once

**From Claude Code**, you can make the push check automatic with a PreToolUse hook in `.claude/settings.local.json` that blocks `git push`, `gh pr create` and `gh repo sync` when `privacy_check.py --push` fails:

```json
{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
  "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/privacy_before_push.py\""}]}]}}
```

The hook script reads the tool input from stdin, runs the check only for those three commands, and exits 2 with the checker's output to block. Keep it in `.claude/hooks/` (gitignored).

**From your own terminal**, run `python3 privacy_check.py --push` before pushing, or install a local git `pre-push` hook that runs it.

**The history limit.** `--push` checks `HEAD` and your unpushed commits only. Anything already pushed stays in public history even if you delete it later. `--history` sweeps every commit on your local branches once, but not remote-only branches or other people's forks. The only fix for a hit in pushed history is rewriting history and force-pushing. That's a deliberate decision, never a routine one.

---

## The one rule above all others

**The system never submits, sends, or clicks anything.** Every mode stops at a draft. You review it; you decide; you act.

This is not a limitation — it is the point. The cost of a bad application or a tone-deaf outreach note is yours to carry. The system surfaces the draft and tells you what it notices. You own the decision.
