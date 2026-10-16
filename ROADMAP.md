# Roadmap

Improvements queued from continued live use of the system. Each item names the failure that prompted it, because the failure is the spec.

Status key: **Next** = ready to build · **Later** = worth doing, not urgent

---

## Next

### 1. Claims linter: `check_claims.py`
**Problem:** Proof-point integrity is enforced today by the `integrity` mode, which is a manual read. In live use, a stray duplicate resume file (`resume (1).md`) carried a claim marked "designed, never built" into the profile section, and nothing would have caught it before submission. Rules that live only in a ledger depend on someone remembering to check.

**Build:** A stdlib-only Python script that scans the master resume, every variant, and `tailored/` and `sent/`. Rules are read from the *Standing constraints* table in `06-proof-points.md` (the one home for claim rules), and nothing is hardcoded:
- **Retired figures:** numbers that must never appear (e.g. a headline figure you've decided not to defend)
- **Restricted verbs:** topics that must never sit near "shipped / launched / deployed / delivered" (e.g. something you designed but never built)
- **Required qualifiers:** a figure that must always travel with a word (e.g. a savings number that must always say "projected")
- **Required clauses:** an outcome that must always carry its context (e.g. a conversion lift that must always mention the fraud trade-off)
- **Profile-only bans:** claims allowed in experience bullets but never in the headline or summary

**Waivers need an end condition.** If the linter supports waivers, each one records when it ends (the fix lands, a stage exits), lives in the task list, and needs the user's quote to remove. A blanket waiver hides every later failure on that path.

**Role-framing check (candidate).** Product verbs, not engineering verbs, for the person's own work. Write it from a real failing example, not before; until then the rule lives in `modes/tailor.md`.

**Zero inputs is a FAIL.** If the globs match no files, the script prints a FAIL with its own message ("no files found at …, nothing checked"), never "0 FAIL". A missing source of truth must not look like a clean bill of health.

**Test each rule against the violation alone.** A rule like "use the percentage, never a dollar figure" fires on any dollar figure in that context, not only when the permitted form is on the same line.

Matching works per sentence and per bullet clause, not per line, so an unrelated "built" three items away doesn't trigger a false positive. Reviewer checklist lines that quote the rules back are skipped. The script exits 1 on any FAIL, so it can gate a pre-send step.

**Done when:** a planted test file with one violation per rule type fails on every line; each rule also fails on a line containing only its violation (no permitted form alongside); a run whose globs match nothing exits 1 with a "no files" FAIL; and the shipped templates pass clean.

### 2. `scan.py` reads its rules instead of keeping copies
**Problem:** `scan.py` keeps its own `COMP_FLOOR`, `SENIORITY` and `DOMAIN` lists, set by hand per `SETUP.md`. They drift from `config.md` and `01-target-roles.md` without any error (`SKILL.md` rule 17). Dedup against the tracker is also done by the agent by hand (rule 18).

**Build:** `scan.py` reads the floor and keywords from a small machine-readable block in `config.md` and stops with a clear message when it can't. Add a dedup step that matches scan output against `02-tracker.csv` on req ID and URL (via `tracker_io.read_tracker`) and prints only new rows.

**Done when:** changing the floor in `config.md` changes what `scan.py` drops, with no edit to `scan.py`; a missing or malformed block stops the scan with a message; a re-run against a saved output reports zero new rows for roles already tracked.

### 3. Move "Titles lie" into `SKILL.md`
**Problem:** The rule "never score level from a title; search the JD for 'reports'" is in the README but not in `SKILL.md`, so the agent never reads it at scoring time. A "Director" title on an explicit IC role, and a "Principal" role with no reports, both score as leadership roles.

**Build:** Add the section under Scoring, with the observed title-vs-actual-level table, and reference it from the Level fit dimension.

---

## Later

### 4. Resume variants as a first-class concept
**Problem:** The system assumes one master resume plus per-JD tailoring. Real searches settle into a few standing variants: people-leader, senior IC, and a domain-specific one such as AI or decisioning. That produces stray copies and confusion about which file was submitted.

**Build:** A `variants` table in `config.md` (file, archetype, when to use), a rule that every variant is a subset of the master, and linter coverage for all of them. `tailor` picks the variant before tailoring.

### 5. `sent/` capture includes free-text answers
**Problem:** ATS forms ask "why this company," "what qualifies you," and "salary expectation." Those answers are drafted in chat and then lost. The next application at the same company risks contradicting them, and nobody can later confirm which resume file was uploaded.

**Build:** On "I applied," `sent/{slug}/` records the exact resume file, the cover letter, every free-text answer, and the comp answer given. Reusable answers get promoted to `08-application-answers.md`.

### 6. Install as a thin skill
**Problem:** Installing the system as a packaged Claude skill copies the mode files into the skill. The repo keeps evolving, the installed copy doesn't, and the agent silently runs stale modes with outdated filenames.

**Build:** Document an install path where the packaged skill contains `SKILL.md` only, with the repo path stated at the top ("all relative paths resolve to `<your clone>`"). Mode edits in the repo then take effect immediately, with no re-packaging. Add a one-line `make-skill` script to build the package.

### 7. Block clicks during a fill session
**Problem:** `fill` mode's "never submit" is an instruction, not an enforced block. A PreToolUse hook sees a tool's name and an element ref or coordinates, not what the element is, so it can't tell a Submit click from a field click.

**Build:** A hook that blocks `computer` clicks, key presses and typing, and `navigate`, while a fill session is active, keyed to a session marker the mode sets and clears. Test it against the fixture with a planted Submit click.

**Also scope the script guard to fill sessions.** `hooks/fill_js_guard.py` today blocks every browser script in the folder, in every session, so other work (debugging a page, checking a scan) can't run one. Key it to the same session marker: inside a fill session only the pinned read pages run; outside one, scripts are allowed. The preflight (`document.title` must come back blocked) then checks that the marker is set, not only that the hook is installed.

### 8. One master, one path
**Problem:** When the real master resume lived outside the project folder, `tailor` quietly read an older in-folder copy that was missing recent bullets.

**Build:** `config.md` names the master's path explicitly. `SETUP.md` says to keep exactly one master, and `integrity` warns if more than one file matches `*master*resume*`.

---

## Done

- **Fill mode** *(2026-10-16)*. `modes/fill.md` fills one page of an application you opened, from the resume and a new gitignored `application-profile.md` (the one home for facts and knockout answers; `08-application-answers.md` points to it). `application_profile.py` parses it in code and never prints denylisted keys (government ID, date of birth, bank details). Knockouts fill only from explicit answers; free text, EEO, uploads, passwords and submit are always yours; prefilled fields are replaced only with a yes. Field values are read by eight pinned read-only scripts (`hooks/fill_read/`), and `hooks/fill_js_guard.py` blocks every other browser script by sha256. A form in an unreadable frame stops the fill. Haiku and Sonnet both passed a fixture with stale prefills and a framed form; Haiku is the default.
- **Privacy check in code** *(2026-10-15)*. `privacy_check.py` reads literal patterns from a gitignored `.privacy-patterns` and exact-line exceptions from `.privacy-allow`. It checks the staged diff, `--all`, `--push` (`HEAD` plus unpushed commits) or `--history`; it fails when it has nothing to check or a pattern file is tracked; it reports locations and pattern line numbers, never the terms. Enforced before push by a local Claude Code hook, and before commit by a local git hook; `SETUP.md` documents both and the history limit.
- **Outreach triage mode** *(2026-10-15)*. `modes/triage.md` plus the read-only `triage.py`: the user names the benchmark role; deadlines inside 7 days come first; open roles go into apply + outreach / apply cold / skip by judgment. Scores are parsed in code (ranges on their upper bound, capped scores on the capped value), and network matches are whole-word hints, not confirmed paths.
- **Merge-blocker fixes** *(2026-09-24)*. The survival cap table moved to `01-target-roles.md` (`survive` produces a verdict only; rule 9 unchanged). `tracker_io.py` counts raw records for the shrink guard and has a `repair` command that realigns only rows whose extra cells are empty. Sheet status overwrites only when non-empty. A new `posting_closed_on` column: `Expired` is only for roles never applied to.
- **Domain fit and Evidence match split** *(2026-09-24)*. Domain is problem ownership (have you *owned* this problem?); Evidence is provable with numbers (this JD, requirement by requirement, against the ledger). The two scales sit side by side in `SKILL.md`, 5 to 1, with half points, a partial-evidence cap at 3, and two worked examples. The "generalist platform role = Domain 2" rule is retired, and company type no longer sets Domain.
- **Building models vs owning decisions** *(2026-09-24)*. In ML-heavy domains, model-building roles cap Domain at 2 unless you've built models; roles that own the decisions the models feed score normally.
- **`SPECIALTY_PATH` setting** *(2026-09-24)*. `protect` (default) or `open-to-drift`, set in `config.md`; `open-to-drift` bans "re-label"/"detour" language in reports. The comp floor applies either way.
- **No human scores** *(2026-09-24)*. The Sheet's score columns are ignored in every merge; scores come only from evaluations; Sheet-created rows start blank. New `templates/needs-evaluation.md` lists unscored rows with an open decision.
- **"Designed-only" claim status** *(2026-09-24)*. It's in the ledger template alongside Confidential and Closed as qualitative, each with how it counts for Evidence. Wiring it into the claims linter stays in *Claims linter* above.
- **Session rules** *(2026-09-24)*. Long tasks run off `TASKS.md`; keep going on bookkeeping and stop for the user's decisions (named list); long runs end with Blocked on me · Changed · Found.
- **Scan learnings** *(2026-09-24)*. LinkedIn's "No matching jobs found" padding counts as zero; background tabs render ~7 cards, so titles come from `/jobs/view/{id}`; LinkedIn reading stays user-initiated and low volume. The coverage line counts every query and every source. The Sheet is chosen by title pattern and newest `modifiedTime`, never a stored ID.
- **Weekly Review: lead with roles, drop follow-up auditing** *(2026-09-24)*. It now runs new roles first, then the pipeline in one line, one deadlined item and one action. Past-due dates stay in the tracker and aren't surfaced.
- **Tracker column-width validation** *(2026-09-24)*. `tracker_io.py` is now the only writer (SKILL.md rule 10). It quotes every field, validates width and row count on a temp file, refuses silent shrinkage, backs up to `archive/`, and swaps atomically. `python3 tracker_io.py` validates without writing.
- **One rule source** *(2026-09-24)*. `config.md` holds facts only; scoring and blockers live in `01-target-roles.md` (SKILL.md rule 9); claim rules live in `06-proof-points.md`.

---

## Principles for anything added here

- **Generic by construction.** Facts come from the user's `config.md`, scoring rules from `01-target-roles.md`, claim rules from the ledger. Never from the repo.
- **One home per rule.** If two files could disagree about how a role scores, one of them is wrong.
- **Blockers hide; modifiers reveal.** Prefer a penalty with the cost stated over a filter that hides the role.
- **Never report an absence without the denominator.**
- **The system drafts; the human sends.**
