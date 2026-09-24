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

Matching works per sentence and per bullet clause, not per line, so an unrelated "built" three items away doesn't trigger a false positive. Reviewer checklist lines that quote the rules back are skipped. The script exits 1 on any FAIL, so it can gate a pre-send step.

**Done when:** a planted test file with one violation per rule type fails on every line, and the shipped templates pass clean.

### 2. Move "Titles lie" into `SKILL.md`
**Problem:** The rule "never score level from a title; search the JD for 'reports'" is in the README but not in `SKILL.md`, so the agent never reads it at scoring time. A "Director" title on an explicit IC role, and a "Principal" role with no reports, both score as leadership roles.

**Build:** Add the section under Scoring, with the observed title-vs-actual-level table, and reference it from the Level fit dimension.

---

## Later

### 3. Resume variants as a first-class concept
**Problem:** The system assumes one master resume plus per-JD tailoring. Real searches settle into a few standing variants: people-leader, senior IC, and a domain-specific one such as AI or decisioning. That produces stray copies and confusion about which file was submitted.

**Build:** A `variants` table in `config.md` (file, archetype, when to use), a rule that every variant is a subset of the master, and linter coverage for all of them. `tailor` picks the variant before tailoring.

### 4. `sent/` capture includes free-text answers
**Problem:** ATS forms ask "why this company," "what qualifies you," and "salary expectation." Those answers are drafted in chat and then lost. The next application at the same company risks contradicting them, and nobody can later confirm which resume file was uploaded.

**Build:** On "I applied," `sent/{slug}/` records the exact resume file, the cover letter, every free-text answer, and the comp answer given. Reusable answers get promoted to `08-application-answers.md`.

### 5. Install as a thin skill
**Problem:** Installing the system as a packaged Claude skill copies the mode files into the skill. The repo keeps evolving, the installed copy doesn't, and the agent silently runs stale modes with outdated filenames.

**Build:** Document an install path where the packaged skill contains `SKILL.md` only, with the repo path stated at the top ("all relative paths resolve to `<your clone>`"). Mode edits in the repo then take effect immediately, with no re-packaging. Add a one-line `make-skill` script to build the package.

### 6. One master, one path
**Problem:** When the real master resume lived outside the project folder, `tailor` quietly read an older in-folder copy that was missing recent bullets.

**Build:** `config.md` names the master's path explicitly. `SETUP.md` says to keep exactly one master, and `integrity` warns if more than one file matches `*master*resume*`.

---

## Done

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
