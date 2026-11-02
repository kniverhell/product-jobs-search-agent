# Changelog

Every release bumps `version` in `.claude-plugin/plugin.json` and adds an entry here, in the same commit. Installed
copies update only when the version changes.

## 1.4.0 (2026-10-27)

- New `discover` mode: reads your labeled job-alert emails (Gmail connector, read-only, one label; or `.eml` files),
  finds the employers' public boards, and adds them to `04-queries.md` on probation. A company whose board can't be
  confirmed goes to the watchlist as `alerts-only`. Detection is code: at most 3 slug candidates, and the board must
  confirm the company.
- `scan-boards` lines take two optional fields, `status` (`active`, `probation`, `paused`) and `source`. Three-field
  lines still work. Probation boards become active after a scan reads real listings. Boards added from alerts that show
  no role passing the screen after 30 days are proposed for retirement; nothing retires on its own.
- After a rejection the mode asks: keep scanning, pause 90 days, or remove. No answer changes nothing. Pause is a label:
  the board is still scanned and its roles show `paused: rejected <date>`. Remove adds the company to the no-go list and
  stops scanning it. `scan.py decide` applies the answer.
- New hook `label_guard.py`: mail searches must AND `label:<alerts_label>` with the rest (no `OR`, groups, other labels);
  reads by ID are allowed only for IDs a label-scoped search returned in the session. New `config.md` field
  `mail_connector` names the mail server; the hook guards every tool on it and allows only `search_threads`,
  `get_thread` and `get_message`. A mail search or read tool on any other server is blocked, and with the field blank
  the Gmail route is off (`.eml` only). `mail_connector` takes a comma-separated list, because one connector can have
  a different server name in the desktop app and the command line. Tested against the real Gmail connector in the
  command line: an unlabeled search and a read of an unreturned ID are blocked, and a labeled search and a read of its
  result go through. Not tested in the desktop app (see README).
- The alert parser reads the plain-text digest layout (title, company, location, badge lines, "View job"), decodes
  quoted-printable, takes the date from the `Date` header, and notes when a digest's job count differs from the roles
  it lists.
- `scan.py` gains `alerts`, `parse-alerts` and `decide`. `config.md` gains `alerts_label`.

## 1.3.2 (2026-10-29)

- fill: never on linkedin.com, including Easy Apply. LinkedIn's terms prohibit automated actions on its site, so the
  agent stops before running anything there and you fill those forms yourself. This is an instruction, not an enforced
  block.

## 1.3.1 (2026-10-27)

- interview: the request is sorted before any prep. A lookup-only or side request is refused (ask for a paste, no prep
  sections); a prep request with no round named gets one question; a prep request with a round gets that round's
  sections only. Before, a lookup-only request could produce a blended prep with sections the round doesn't get.
- interview: prep goes to chat. A file is written only when you ask, to a path you name.

## 1.3.0 (2026-10-26)

- interview: each round now lists the sections it gets, and only those are produced (a recruiter screen no longer gets
  hiring-manager material).
- interview: new content by round. Screen: screening answers anchored to your own comp floor, unstated items left
  `[UNKNOWN]`. Hiring manager: a pain-to-asset map (a partial match is never upgraded to strong) and up to three delivery
  scenarios from your own ledger and story bank, a missing metric marked and never invented. Panel: persona strategy per
  interviewer or role type, built only from what you paste. Executive or final: a 60–90 second positioning narrative and
  up to five labeled domain notes. Every round: a checklist (numbers to memorize with status, claims that break under
  follow-up, trap answers, next 48 hours) and a practice loop that cuts your pitch without adding claims.
- interview fix: a resume figure that conflicts with a Derived ledger figure is flagged and the Derived figure is
  offered with its arithmetic, instead of dropping both.

## 1.2.0 (2026-10-26)

- interview: prep is now by round (recruiter or coordinator screen, hiring manager, peer or panel, executive or final),
  so depth matches what that person decides.
- interview: sources are ranked JD, then your proof-point ledger, then your resume (checked against the ledger);
  anything else is a claim. Unverified facts, yours or theirs, are labeled and turned into a question to ask.
- interview: anchors for the call come from the ledger with their status; interviewer research is pasted in by you,
  never looked up by the agent.

## 1.1.2 (2026-10-22)

- contact: LinkedIn searches are always done by the user by hand; the agent never opens or reads LinkedIn.
- scan: neutral wording for a rate-limit failure note.

## 1.1.1 (2026-10-20)

- The scope guard no longer splits a command at parentheses, semicolons or pipes inside quotes, so a block names the
  right command (before, `python3 -c 'print(1)' > /x` named a stray quote). Command substitution inside double quotes
  is still checked.
- README: start every session in your project folder.

## 1.1.0 (2026-10-20)

- New scope guard hook: in a job-search project (a folder with `.job-search`), Read, Glob, Grep, Write, Edit and
  NotebookEdit are limited to the project folder and the kit, and so is every path in a Bash command, including
  redirect targets. `locate` and `mdfind` are blocked. Scratch files are allowed only in this project's own
  `/private/tmp/claude-<uid>/<slug>/` folder.
- Fails closed with a message if it cannot check a call. Other folders are untouched.
- Known gap: paths built inside `python3 -c`, scripts or shell variables are not seen.
- Run `claude plugin update` to get it.

## 1.0.0 (2026-10-20)

First plugin release.

- Install with one command; say "run setup" in an empty project folder to create your files from templates.
- Your data lives in your project folder (marked by `.job-search`), never in the plugin's folder. Scripts stop with
  "run setup" anywhere else.
- Hooks ship with the plugin and check themselves: the push privacy check runs only once `.privacy-patterns` has
  terms, and the fill-mode script guard only in a folder with `application-profile.md`.
- `scan.py` reads its screen and boards from your `01-target-roles.md` and `04-queries.md`; it holds no settings.
- One command per mode (`/job-search-agent:setup`, `:scan`, `:evaluate`, `:triage`, `:fill`, `:track`, `:review`, …). In a job-search folder, a SessionStart hook tells each session where the kit is and to never search outside the project and the kit.
- Tests in `tests/` (fictional data only): `bash tests/run_all.sh`.
- Modes: scan, evaluate, tailor, cover, contact, deep, email, interview, negotiate, survive, integrity, triage,
  friction, fill, setup, and the weekly review.
