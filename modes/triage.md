# Mode: Outreach triage — who gets a warm connection

Trigger: "triage against <role>" or "who gets outreach". Run only on request.

Applications are cheap; warm connections are scarce. After evaluation, sort every open role into three buckets,
so outreach goes only to roles that beat the role you name as the benchmark.

**Read-only.** This mode never scores, rescores or changes a status, and never writes the tracker or any other
file. It uses the scores the evaluations already recorded.

**You name the benchmark every time** (e.g. your best live process). The system never picks it and never takes it
from memory; its facts come from the tracker, read in code.

## 1. Pull the data

Run `python3 "<kit>/triage.py" "<benchmark>"`. The argument is the role's URL, or words that all appear in its company and
title ("Acme Director Product"). If it exits with `STOP`, show its message and stop: the benchmark is missing, not
found, or matches more than one row (ask which).

The script prints, read-only:
- **DEADLINES:** open roles whose `next_action_due` is within 7 days and whose `next_action` is worded as a
  deadline. Listed first in your report.
- **BENCHMARK:** the named role as the tracker has it.
- **CANDIDATES:** roles at `New`, `Evaluated` or `Tailored` with a score, sorted by score. Ranges sort on their
  upper bound; capped scores sort on the capped value. Each shows `warm_contact`, and "possible warm path (name
  match)" when the company name appears as a whole word in `07-network.md`.
- **UNSCORED:** open roles with no usable score. Name them; they need an evaluation before triage.

Roles you've applied to, and closed or passed roles, are never candidates.

## 2. Sort into buckets (judgment, not arithmetic)

- **Apply and spend outreach:** clearly beats the benchmark on what you'd actually trade it for (level and scope,
  comp against your floor, odds of an offer, trajectory, location), **and** has a confirmed warm path. A filled
  `warm_contact` counts. A "possible warm path (name match)" counts only after you check `07-network.md` and the
  person really connects to this company, or the user confirms it.
- **Apply cold, hold outreach:** worth applying (3.5+, not blocked) but doesn't clearly beat the benchmark. Also
  any role that beats it but has no confirmed warm path; say "beats benchmark, no warm path".
- **Skip:** below 3.5, blocked, on the no-go list in `01-target-roles.md`, or recommended *Pass*.

A 4.2 doesn't automatically beat a 4.0. Name the reason for each call in one line: what makes it better or worse
than the benchmark.

## 3. Report

1. **Deadlines inside 7 days**, first.
2. **Apply and spend outreach.**
3. **Apply cold, hold outreach.**
4. **Skip.**
5. **Unscored**, by name.

Items 2–4 are each a table: Company | Title | Score | Why, in one line | Link.

Then: Blocked on me · Changed (always "Nothing written") · Found. Hand the outreach bucket to `contact`; it goes
first there.
