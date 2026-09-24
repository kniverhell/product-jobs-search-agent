# Mode: Integrity Check

Run monthly, or whenever the tracker feels off.

0. **Tracker shape** — run `python3 tracker_io.py`. If it fails, run `python3 tracker_io.py repair` to see which rows can be realigned, then `repair --write`. Report every row it leaves as-is; those need a person.
1. **Dedup** — same company + similar title within 30 days is one role. Merge, keep the earliest `date_found` and the richest notes.
2. **Status normalization** — every row uses exactly the canonical statuses in `SKILL.md`. Fix anything else.
3. **Orphans** — a `reports/` file with no tracker row, a tracker row at `Tailored` with no file in `tailored/`, a slug that doesn't match across folders. Fix or flag.
4. **Staleness** — anything at `New` for over 14 days is either evaluated now or moved to `Passed`. A backlog of unevaluated roles is the thing that quietly kills a search.
5. **Liveness** — check whether each open role's posting is still up. If it's gone: a role never applied to (`New`, `Evaluated`, `Tailored`) becomes `Expired`; a role you applied to keeps its status and gets today's date in `posting_closed_on`.
6. **Ghost jobs** — a posting seen three or more times across scans over months is a ghost. Note it in `03-portals.md` and stop surfacing it.
7. **Proof-point drift** — any number appearing in a `tailored/` file that isn't in `06-proof-points.md`, or that violates a standing constraint in `06-proof-points.md`. **Report this loudly.** A number that crept in without provenance is the one that blows up in an interview.

Report only what changed and what needs a decision. If everything's clean, one line saying so is the whole report.
