# Mode: Friction — what users are failing at

Trigger: you say "friction <company>" (or the phrase set as `FRICTION_TRIGGER` in `config.md`).
Run only on request. Never run it automatically, from a scan, or inside a pipeline.

Purpose: mine low-star customer complaints about the employer's product for friction in the area you'd own,
and turn them into interview prep tied to your own proof points. The defaults below are written for
identity, authentication, onboarding and fraud. Keep them, and add failure modes for your own specialty
(`DOMAIN_TIER1` in `config.md`).

It never scores, caps or blocks a role (scoring rules live only in `SKILL.md` and `01-target-roles.md`), and it
never changes a tracker row. If the employer is on the no-go list in `01-target-roles.md`, stop without writing a
report and without naming the employer or the list.

Scope: the employer's product plus 2–3 competitors named in its own report or the posting. Don't widen it.

## Failure modes

The five below are defaults for identity, authentication, onboarding and fraud. **Add your own specialty's
failure modes to this list** before the first run (e.g. for payments: "Payout Delay", "Chargeback Loss"). Tag
every complaint with one. During a run, add another only if the complaints show it, and say which complaints.

- **Lock-Out:** freezes, holds, bans, suspended access
- **Verification Loop:** ID, MFA or passkey retries, repeated document requests, codes that don't arrive
- **Black Box:** declines or closures with no stated reason and no appeal
- **Support Wall:** no path to a human
- **Takeover:** account-takeover and fraud-loss complaints

## Sources

Defaults: app-store reviews rated 1–3 stars from the last 12 months; community forums; consumer review sites;
the regulator's public consumer-complaint database, where one exists; and the company's replies to bad reviews
(the same boilerplate reply to a repeated complaint suggests the cause is structural).

Access limits: web search and fetch tools only, at human pace, no scripted loops, any curl with a
`FRICTION_CURL_TIMEOUT`-second timeout (`config.md`; default 20), and nothing from `FRICTION_SOURCES_BARRED`
(`config.md`). A source that can't be read is unread, not empty: name it.

## Output

`reports/<company>-friction-<date>.md`

a. **Coverage line:** every source, run or not run, with its access method, and how many reviews or complaints
   were read from what window.

b. **Matrix:** product | promise (their own marketing quote) | failure mode | top complaint | frequency | where
   users say they switched.

c. **Taxonomy:** root causes ranked by frequency, each marked fixable-by-product or structural (business model,
   regulation, compliance stack), with the reason.

d. **Verbatim bank:** 10–15 quotes in the users' own words, each with source URL and date. A theme with fewer
   than 3 independent instances (different users, not one person across sites) is marked anecdotal.

e. **90-day thesis,** one sentence: "Users of <company> fail at <job> because <cause>; I'd fix it by <approach>,
   as I did at <proof point>."

f. **Proof-point map:** each top theme → an entry in `06-proof-points.md` you're allowed to cite, under its
   status and the standing constraints there. Work that was only designed (`Designed-only`) is labeled
   designed, never shipped. A theme with no match says "no proof point"; don't stretch an entry to cover it.
