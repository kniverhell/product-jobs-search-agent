# Changelog

Every release bumps `version` in `.claude-plugin/plugin.json` and adds an entry here, in the same commit. Installed
copies update only when the version changes.

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
