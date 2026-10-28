# Roadmap

Improvements queued from continued live use of the system. Each item names the failure that prompted it, because the failure is the spec.

Status key: **Next** = ready to build · **Later** = worth doing, not urgent

**Separate kits:** Claim Check is planned.

---

## Next

### 2. `scan.py` dedups against the tracker
**Problem:** Dedup of scan output against the tracker is done by the agent by hand (rule 18). (The other half of this item, reading the screen and boards from your files, is done; see *Done*.)

**Build:** A dedup step that matches scan output against `02-tracker.csv` on req ID and URL (via `tracker_io.read_tracker`) and prints only new rows.

**Done when:** a re-run against a saved output reports zero new rows for roles already tracked.

### 3. Move "Titles lie" into `SKILL.md`
**Problem:** The rule "never score level from a title; search the JD for 'reports'" is in the README but not in `SKILL.md`, so the agent never reads it at scoring time. A "Director" title on an explicit IC role, and a "Principal" role with no reports, both score as leadership roles.

**Build:** Add the section under Scoring, with the observed title-vs-actual-level table, and reference it from the Level fit dimension.

---

## Later

### 4. Resume variants as a first-class concept
**Problem:** The system assumes one master resume plus per-JD tailoring. Real searches settle into a few standing variants: people-leader, senior IC, and a domain-specific one such as AI or decisioning. That produces stray copies and confusion about which file was submitted.

**Build:** A `variants` table in `config.md` (file, archetype, when to use), a rule that every variant is a subset of the master, and the `integrity` mode covering all of them. `tailor` picks the variant before tailoring.

### 5. `sent/` capture includes free-text answers
**Problem:** ATS forms ask "why this company," "what qualifies you," and "salary expectation." Those answers are drafted in chat and then lost. The next application at the same company risks contradicting them, and nobody can later confirm which resume file was uploaded.

**Build:** On "I applied," `sent/{slug}/` records the exact resume file, the cover letter, every free-text answer, and the comp answer given. Reusable answers get promoted to `08-application-answers.md`.

### 6. Block clicks during a fill session
**Problem:** `fill` mode's "never submit" is an instruction, not an enforced block. A PreToolUse hook sees a tool's name and an element ref or coordinates, not what the element is, so it can't tell a Submit click from a field click.

**Build:** A hook that blocks `computer` clicks, key presses and typing, and `navigate`, while a fill session is active, keyed to a session marker the mode sets and clears. Test it against the fixture with a planted Submit click.

**Also scope the script guard to fill sessions.** `hooks/fill_js_guard.py` today blocks every browser script in the folder, in every session, so other work (debugging a page, checking a scan) can't run one. Key it to the same session marker: inside a fill session only the pinned read pages run; outside one, scripts are allowed. The preflight (`document.title` must come back blocked) then checks that the marker is set, not only that the hook is installed.

### 7. Retired
Shipped as the scope guard in v1.1.0; see *Done*. The number stays so the others keep theirs.

### 8. A dedicated, signed-in test config for install tests
**Problem:** The fresh-install tests run `claude -p` sessions against a test marketplace. A fully separate config (`CLAUDE_CONFIG_DIR` pointing at a temp folder) isn't signed in, so the tests used the maintainer's real config with a temp plugin folder. Adding a marketplace still wrote to the real `~/.claude/settings.json` and `known_marketplaces.json`; the tests removed those entries and checked the files against a baseline, but a test should never touch the real config at all.

**Build:** A persistent test config folder outside the repo, signed in once by the maintainer (`CLAUDE_CONFIG_DIR=<test config> claude auth login`), used for every install test with its own plugin folder. The install tests refuse to run without it, and never fall back to the real config.

**Evidence rule:** test runs keep commands-only evidence: the commands run, whether each was blocked or allowed, and the hash comparison. Never store prompts, model replies or transcript text, and delete the raw session logs when the run ends.

**Done when:** a full install-test run (setup plus every script-calling mode, uninstall, reinstall, update) leaves `~/.claude/settings.json`, `known_marketplaces.json` and `installed_plugins.json` byte-identical, with no cleanup step needed.

### 9. One master, one path
**Problem:** When the real master resume lived outside the project folder, `tailor` quietly read an older in-folder copy that was missing recent bullets.

**Build:** `config.md` names the master's path explicitly. `SETUP.md` says to keep exactly one master, and `integrity` warns if more than one file matches `*master*resume*`.

### 10. Ship the LinkedIn ban as a hook
**Problem:** "The agent never opens, searches or reads LinkedIn" (`modes/contact.md`, `modes/interview.md`) is an instruction. A lock on one door is not a lock.

**Build:** A PreToolUse hook that blocks browser navigation, search and fetch calls to linkedin.com in a marked project, with a test against the fixture. Instructions stay; the hook is the enforcement.

### 11. Graded mock interviews (parked)
Practice rounds where the agent asks questions and grades the answers. Parked: the current practice loop only cuts and tightens what the user says. Not planned.

---

## Done

- **Scope guard hook** *(2026-10-20, v1.1.0)*. `hooks/scope_guard.py`, active only in a folder with the `.job-search` marker: Read, Glob, Grep, Write, Edit and NotebookEdit on paths outside the project and the kit root are blocked, and so is any Bash argument or redirect target that resolves outside them (`locate` and `mdfind` always). Allowed besides: this project's own scratch folder `/private/tmp/claude-<uid>/<slug>/` and its own `~/.claude/projects/` folder. It fails closed with a message if it cannot check a call. Known gap: paths built inside `python3 -c`, scripts or variables are not seen. Live-tested from a local export (pre-release `1.1.0-dev.1`) in sandboxed sessions.
- **One-command install as a Claude Code plugin** *(2026-10-20, v1.0.0)*. `claude plugin install job-search-agent --marketplace kniverhell/product-jobs-search-agent`, then "run setup" in an empty folder. The repo is both the marketplace and the plugin; the one `SKILL.md` lives at `skills/job-search-ops/`, and clone installs use the clone as a local marketplace (this closes *Install as a thin skill*). Your data lives in your project folder, marked by `.job-search`; data scripts stop anywhere else, and setup refuses your home folder, `/` and the kit's own folder. Setup never overwrites. Both hooks ship with the plugin and check themselves (the push check needs terms in `.privacy-patterns`; the fill guard needs `application-profile.md`), so a fresh install is never blocked. Semantic versions with a CHANGELOG; nothing updates without a version bump.
- **`scan.py` reads its rules** *(2026-10-20)*. The comp floor and the level, include and exclude terms come from a `scan-screen` block in `01-target-roles.md`; the boards come from a `scan-boards` block in `04-queries.md`. The script holds no settings and no default company list. A missing, empty, placeholder or malformed line exits 1 with the file and line. Output is unchanged for the same config, except two hints that used to say "edit scan.py". All scripts now find your data in the project folder (the working directory, or `$JOB_SEARCH_DIR`), not next to themselves.
- **Fill mode** *(2026-10-16)*. `modes/fill.md` fills one page of an application you opened, from the resume and a new gitignored `application-profile.md` (the one home for facts and knockout answers; `08-application-answers.md` points to it). `application_profile.py` parses it in code and never prints denylisted keys (government ID, date of birth, bank details). Knockouts fill only from explicit answers; free text, EEO, uploads, passwords and submit are always yours; prefilled fields are replaced only with a yes. Field values are read by eight pinned read-only scripts (`hooks/fill_read/`), and `hooks/fill_js_guard.py` blocks every other browser script by sha256. A form in an unreadable frame stops the fill. Haiku and Sonnet both passed a fixture with stale prefills and a framed form; Haiku is the default.
- **Privacy check in code** *(2026-10-15)*. `privacy_check.py` reads literal patterns from a gitignored `.privacy-patterns` and exact-line exceptions from `.privacy-allow`. It checks the staged diff, `--all`, `--push` (`HEAD` plus unpushed commits) or `--history`; it fails when it has nothing to check or a pattern file is tracked; it reports locations and pattern line numbers, never the terms. Enforced before push by a local Claude Code hook, and before commit by a local git hook; `SETUP.md` documents both and the history limit.
- **Outreach triage mode** *(2026-10-15)*. `modes/triage.md` plus the read-only `triage.py`: the user names the benchmark role; deadlines inside 7 days come first; open roles go into apply + outreach / apply cold / skip by judgment. Scores are parsed in code (ranges on their upper bound, capped scores on the capped value), and network matches are whole-word hints, not confirmed paths.
- **Merge-blocker fixes** *(2026-09-24)*. The survival cap table moved to `01-target-roles.md` (`survive` produces a verdict only; rule 9 unchanged). `tracker_io.py` counts raw records for the shrink guard and has a `repair` command that realigns only rows whose extra cells are empty. Sheet status overwrites only when non-empty. A new `posting_closed_on` column: `Expired` is only for roles never applied to.
- **Domain fit and Evidence match split** *(2026-09-24)*. Domain is problem ownership (have you *owned* this problem?); Evidence is provable with numbers (this JD, requirement by requirement, against the ledger). The two scales sit side by side in `SKILL.md`, 5 to 1, with half points, a partial-evidence cap at 3, and two worked examples. The "generalist platform role = Domain 2" rule is retired, and company type no longer sets Domain.
- **Building models vs owning decisions** *(2026-09-24)*. In ML-heavy domains, model-building roles cap Domain at 2 unless you've built models; roles that own the decisions the models feed score normally.
- **`SPECIALTY_PATH` setting** *(2026-09-24)*. `protect` (default) or `open-to-drift`, set in `config.md`; `open-to-drift` bans "re-label"/"detour" language in reports. The comp floor applies either way.
- **No human scores** *(2026-09-24)*. The Sheet's score columns are ignored in every merge; scores come only from evaluations; Sheet-created rows start blank. New `templates/needs-evaluation.md` lists unscored rows with an open decision.
- **"Designed-only" claim status** *(2026-09-24)*. It's in the ledger template alongside Confidential and Closed as qualitative, each with how it counts for Evidence.
- **Session rules** *(2026-09-24)*. Long tasks run off `TASKS.md`; keep going on bookkeeping and stop for the user's decisions (named list); long runs end with Blocked on me · Changed · Found.
- **Scan learnings** *(2026-09-24)*. LinkedIn's "No matching jobs found" padding counts as zero; background tabs render ~7 cards, so titles come from `/jobs/view/{id}`; LinkedIn reading stays user-initiated and low volume. The coverage line counts every query and every source. The Sheet is chosen by title pattern and newest `modifiedTime`, never a stored ID. Superseded: the agent no longer reads LinkedIn (see item 10).
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
- **Every release bumps the version.** `version` in `.claude-plugin/plugin.json` and a `CHANGELOG.md` entry change in the same commit; installed copies don't update otherwise.
