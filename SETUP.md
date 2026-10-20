# Setup Guide

**Most people should install the plugin** with the one command in the README, then say "run setup" in an empty
folder. This guide is the manual route: installing from a clone, and what each file is for.

## Prerequisites

- [Claude Code](https://claude.ai/code) installed (free tier works)
- Python 3.7+ if you want to use `scan.py` (optional)
- A Google account if you want the Sheets sync (optional)

---

## Step 1: Clone and install from the clone

```bash
git clone https://github.com/kniverhell/product-jobs-search-agent.git
claude plugin marketplace add ./product-jobs-search-agent
claude plugin install job-search-agent@product-jobs-search-agent
```

The clone is a local marketplace, so the plugin loads straight from it: edits to modes and scripts apply in your next
session, no reinstall. (Inside a session the same steps are `/plugin marketplace add ./product-jobs-search-agent` and
`/plugin install job-search-agent@product-jobs-search-agent`.)

**The clone holds code only.** Your files go in a separate project folder, never in the clone. If you open Claude
Code in the clone without installing, the root `CLAUDE.md` points it at the skill as a fallback.

## Step 1b: Make your project folder and run setup

```bash
mkdir ~/job-search && cd ~/job-search
claude
```

Say **"run setup"** (or `/job-search-agent:setup`). Setup:

- writes a `.job-search` marker (the scripts stop in any folder without it);
- copies every template that's missing, placeholders only, and never overwrites a file;
- creates `.privacy-patterns` (comments only), a `.gitignore` if there's none, and the output folders;
- checks that the plugin's hooks loaded, and lists what to fill in first.

It refuses to run in your home folder, in `/`, or in the clone.

---

## Step 2: Copy and fill out `config.md`

Setup put `config.md` in your project folder. Edit that copy, never the template. If your project folder is a git
repo, the `.gitignore` setup wrote keeps every personal file out of it.

`config.md` holds **facts about you**, and only facts:

- **Your background:** your domain, seniority level, and what kind of roles you're targeting
- **Comp floors:** your walk-away number by location type (remote / hybrid / on-site)
- **Location:** your home metro, max days on-site, and whether you'd relocate
- **Domain keywords:** the specialties that define your strongest roles (used for queries and `scan.py`)
- **Specialty path:** `SPECIALTY_PATH: protect` (default) lets Trajectory penalize roles that take you out of your specialty; `open-to-drift` means it never does, and reports never call such a role a detour. Your comp floor applies either way

**Rules don't go here.** Title levels, location modifiers, company tiers, hard blockers and the no-go list go in `01-target-roles.md` (Step 4). Claims you must never make go in `06-proof-points.md` (Step 3). One home per rule means no two files can disagree about how a role scores.

---

## Step 3: Add your resume and proof points

Paste your resume into `00-master-resume.md` (setup created it). This is the source of truth. Tailored resumes are always a subset — nothing gets added that isn't here.

Then fill out `06-proof-points.md` with your defensible evidence:
- Every number you can cite, with its source and how you'd defend it in a room
- Claims with status: **Solid** (on resume, fully defensible) / **Derived** (arithmetic from stated figures) / **Soft** (true but approximate) / **Open** (the claim exists, number TBD) / **Confidential** (numbered, but the number isn't yours to disclose) / **Closed as qualitative** (real outcome, number unrecoverable) / **Designed-only** (real work that never reached build)
- Status matters for scoring: only **Solid** entries can carry an Evidence match of 4–5. Confidential and Closed-as-qualitative can support a 3; Open and Designed-only don't count
- **Standing constraints:** claims you must never make, e.g. "shipped" near something you designed but never built, or a figure you've retired. This is the only place claim rules live; the `integrity` mode checks them on every tailored file

This takes a few hours the first time. Do it. The payoff is that you never overclaim in a tailored document, and you always know exactly what you can say in an interview.

---

## Step 4: Populate the reference files

Setup created these too; fill them in:

- `01-target-roles.md`: **all of your scoring rules.** Role archetypes, the problem spaces you've owned (this feeds Domain fit), title levels, location modifiers, company tiers, hard blockers, no-go list, trajectory rule
- `needs-evaluation.md`: starts empty. The system lists unscored roles with an open decision here; a score only ever comes from an evaluation
- `03-portals.md` — your ATS registry and employer watchlist
- `04-queries.md` — your query set for web discovery (Tier 1 core, Tier 2 adjacent, Tier 3 geography)
- `07-network.md` — everyone you actually know: former colleagues by employer, vendor contacts, warm ties
- `application-profile.md` — facts and knockout answers for application forms (see *Filling applications* below)

`07-network.md` is the most underused asset in most searches. The `contact` mode is only as good as what's in this file.

---

## Step 5: Use it

In your project folder, paste a JD or say "run the scout." The plugin's skill loads by itself and runs the matching
mode.

---

## Optional: Google Sheets sync

If you want to review the pipeline on your phone, the system can mirror `02-tracker.csv` to a Google Sheet.

1. Create a blank Sheet in your Google Drive
2. Set `SHEET_TITLE_PATTERN` in your `config.md`. Don't store a file ID: each session picks the newest Sheet matching the title and says which one it used
3. Use the `weekly` review trigger ("where am I at") to sync

**Critical rule:** always read the Sheet *before* writing to the CSV. Any edits you made on your phone live in the Sheet, not the CSV. Writing without reading first destroys them.

---

## Optional: scan.py configuration

`scan.py` keeps no settings of its own. It reads two blocks in your files:

- **The screen:** the `scan-screen` block in `01-target-roles.md`. `comp floor` (0 turns it off), and quoted `level`, `include` and `exclude` terms. A title passes with a level term and an include term and no exclude term.
- **The boards:** the `scan-boards` block in `04-queries.md`, one `greenhouse | slug | Company` line per board (`ashby` and `lever` work too).

Both templates show the format with placeholders. A missing, empty, placeholder or malformed line stops the scan with the file and line number; there are no built-in defaults.

Then say "run the scout", or from your project folder:

```bash
python3 <clone>/scan.py
```

Output writes to `inbound/YYYY-MM-DD-scan-candidates.md`.

---

## Filling applications

`fill` mode fills one page of an application form from your own files and stops. You submit.

1. **Fill in `application-profile.md`** (created by setup; keep it out of git). One `Field: value` per line under `## Factual` (name, contact, links, location) and `## Knockout` (work authorization, sponsorship, relocation, in-office days, travel, clearance, age). Leave a value in `[brackets]` and the field stays blank on every form. **Never store** government ID, SSN, passport, driver's license, date of birth or bank details: `application_profile.py` refuses to print any key that looks like one. 2. **The script guard ships with the plugin** (`hooks/fill_js_guard.py`, wired in `hooks/hooks.json`). It blocks every browser script except the eight read-only pages in `hooks/fill_read/`, matched by sha256, but **only in a project folder that has `application-profile.md`**: other projects, and a fresh install, are never affected. Inside your job-search folder it blocks browser scripts in every session, not only `fill`. Fill mode checks it every time: its first step runs `document.title`, which the guard must block; if it comes back with a title, the mode stops with "fill guard not installed; see SETUP".
3. **Use it.** Sign in and open the application in your own Chrome with Claude in Chrome connected, then say "fill this application for <role>". You get a planned table and a "Fill these?" question first; prefilled fields are replaced only if you name them.

**What it never does:** write free-text answers (employers may have AI-use policies, and the first draft is yours), touch EEO / self-identification, upload files, create accounts, type passwords, solve CAPTCHAs, or click Next, Save or Submit. A form inside an embedded frame from another site can't be read; the mode says so and asks before filling anything.

**Known limit:** "never submit" is an instruction, not an enforced block. A hook can't tell a Submit click from a field click, so the mode uses no clicking tools at all instead. Details in `modes/fill.md`.

---

## Before you push: privacy check

If you push your copy anywhere, check that none of your personal terms (name, employers, phone, local paths) are in it.

1. Add your terms to `.privacy-patterns` in your project folder (setup created it): one term per line, `#` for comments. Matching is case-insensitive and whole-word (a pattern "cat" won't hit "category"; a number won't hit a longer number). The file is gitignored; `privacy_check.py` refuses to run if it's tracked, missing, or empty.
2. Optional: `.privacy-allow` for lines you've decided are fine, one per line: `file | exact line text | YYYY-MM-DD | reason`. Only that exact line passes; a new or edited line with the term still fails. Also gitignored.
3. Run it:
   From your project folder, with `<clone>` the path to the kit:
   - `python3 <clone>/privacy_check.py`: the staged diff (use as a pre-commit check)
   - `python3 <clone>/privacy_check.py --push`: what a push would publish, `HEAD` plus every unpushed commit
   - `python3 <clone>/privacy_check.py --all`: every tracked file in your working tree
   - `python3 <clone>/privacy_check.py --history`: every commit on every local branch, once

**In Claude Code the push check is automatic.** The plugin's hook (`hooks/privacy_before_push.py`) runs `privacy_check.py --push` before any `git push`, `gh pr create` or `gh repo sync` and blocks it on a hit. Until `.privacy-patterns` has a term it allows the push and shows "privacy check not configured", so a fresh install is never blocked. Each check is logged to `.git/privacy-push.log`.

**From your own terminal**, run the `--push` check before pushing, or install a local git `pre-push` hook that runs it.

**The history limit.** `--push` checks `HEAD` and your unpushed commits only. Anything already pushed stays in public history even if you delete it later. `--history` sweeps every commit on your local branches once, but not remote-only branches or other people's forks. The only fix for a hit in pushed history is rewriting history and force-pushing. That's a deliberate decision, never a routine one.

---

## The one rule above all others

**The system never submits, sends, or clicks anything that submits, saves or advances.** `fill` may fill fields on a page you opened; every other mode stops at a draft. You review it; you decide; you submit.

This is not a limitation — it is the point. The cost of a bad application or a tone-deaf outreach note is yours to carry. The system surfaces the draft and tells you what it notices. You own the decision.
