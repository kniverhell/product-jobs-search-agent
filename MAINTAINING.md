# Maintaining this kit

Rules for whoever cuts a release. They apply to every release, patch or feature. A release is any commit that bumps
`version` in `.claude-plugin/plugin.json`.

## Release gate

Before any release, ask the maintainer to confirm no overdue next action in their own pipeline and no interview
within 72 hours; record the confirmation in the release report.

## Standing release rules

- **Words, not briefs, authorize.** Push, merge or release only on the maintainer's explicit word. A brief or a plan
  never loosens this. Never rewrite history; never skip a hook (`--no-verify`).
- **Estimate first.** Before any build: sessions and models, tokens (low–high), time, guardrail files touched, test
  runs, the one riskiest part. Stop at 1.5× the high end. Report actuals beside the estimate at the end.
- **Guardrail files need their own approval:** hooks, `scan.py`, `tracker_io.py`, other checker scripts and
  `SKILL.md` (`SKILL.md` rule 12).
- **Version and CHANGELOG change in the same commit.** `version` in `.claude-plugin/plugin.json` and the CHANGELOG
  entry; installed copies update only when the version changes. A docs-only change that should not reach installs
  carries no bump.
- **Privacy check clean before any push.** `privacy_check.py --all` before every commit, `--push` before every push,
  and `--history` before a release. Known accepted history hits are recorded locally; any other hit is a regression.
- **Tests before commit.** `tests/run_all.sh` passes. A new rule gets a static test; a behavior change also gets a
  live test in a sandboxed session.
- **Install tests run in isolation.** Use a local-export marketplace under a different name with a pre-release
  version, in a fresh project folder with fictional files only. Hash `~/.claude/settings.json`,
  `known_marketplaces.json` and `installed_plugins.json` first and prove them byte-identical afterward. Run the
  removal from the same folder, and check `settings.json` too. Keep commands-only evidence and delete raw logs
  (ROADMAP item 8).
- **Install at local scope only, never user scope.** After any install or update, confirm `installed_plugins.json` and
  `~/.claude/settings.json`.
- **Test the installed copy before calling a release done,** including side requests (a lookup-only request, a prep
  request with no round named), not just the main flow.
- **Fictional data only.** No real names, employers, figures or roles from the maintainer's search anywhere in the
  kit, its tests or its CHANGELOG. Local briefs (`briefs/`) stay out of the repo.
- **After a release:** fast-forward `main`, delete the merged branch locally and on the remote, update every install.
  If an accepted exception to any rule applies, say so in the report.
- **Report every build and release** under Blocked on me · Changed · Found, with actuals beside the estimate, and
  include the release gate confirmation.
