# Mode: Evaluate

The core mode. Triggered by any pasted JD or URL, with or without instruction.

Write the report to `reports/YYYY-MM-DD-company-slug.md` with these seven blocks. Then update the tracker to `Evaluated` with the score and archetype, and remove the row from `needs-evaluation.md` if it was there. This is the only way a role gets a score.

## A. Role summary
What the job actually is, in three sentences, stripped of the recruiting language. What problem are they hiring this person to solve? Who does it report to and what does that reveal? If the JD is vague about scope, say so — vagueness at Director level is usually a signal about the org, not the writer.

## B. Fit assessment
Score all five dimensions with a sentence each, then the holistic 1.0–5.0. Use the scales in `SKILL.md`: **Domain is problem ownership** (have you owned the problem this job exists to solve?) and **Evidence is provable with numbers** (score it requirement by requirement, naming the ledger entry and its status for each: Solid, partial, or none). Keep a gap in one dimension, not both. When you give a half point, state the split: what pushed it up and what held it back. If `SPECIALTY_PATH` is `open-to-drift`, never describe an off-specialty role as a re-label or a detour. Name the archetype. Then state the **location tier and modifier** from `01-target-roles.md`, and the final score — showing both numbers. If the modifier is what pushes it below the Apply threshold, say that explicitly; it's a different decision from a role that's simply weak.

Then two lists:
- **Where you're strong** — JD requirement → the specific proof point that answers it, with the number
- **Where you're exposed** — JD requirement → nothing in the ledger answers this. Be blunt. This list is more useful than the first one.

## C. Level & scope strategy
Is this the right level, one below, or a stretch? If the title is Director but the scope reads VP, say so — that's a negotiation lever later. If it's the reverse, that's a flag. Note whether it has direct reports; a "Director" with no team is a senior IC with a nice title.

## D. Comp read
What this role likely pays, based on company stage, location, and any posted range. Identify the days-on-site expectation, pick the matching floor from `config.md`, and compare.

State one of: **clears the floor**, **below the floor** (hard blocker — say so plainly), or **can't tell** (no posted range; note what the floor would be and move on without guessing). If posted comp clears the floor by 15%+, apply the halved location penalty and show the adjustment.

## E. Personalization angle
The one thing you'd say that no other candidate would. Usually one of: the specific problem this company visibly has and you've solved before, a reference implementation of yours that's directly relevant, or an asymmetry in your background that matches their exact situation. **This is the block that gets interviews.** Spend real effort here. Research the company's actual product surface — sign-up flow, login page, onboarding, whichever applies — and reference what you find specifically.

## F. Interview stories
Which three stories from `05-story-bank.md` this role would draw on. If the role needs a story that doesn't exist yet, **draft the skeleton and append it to the story bank.** The bank grows on every evaluation — that's the compounding part.

## G. Legitimacy & blockers
Ghost-job signals, scam signals, staleness, work authorization, relocation, anything that caps the score. State findings plainly.

**Run `survive` before recommending Apply** when the employer is a private company at or below Series B, or when stage is unknown and the company is clearly venture-backed. Apply the verdict's effect from `01-target-roles.md` → *Survival verdicts* (by default, Fragile caps the holistic). Cite the survival verdict and confidence in this block; do not repeat the whole report.

---

## Recommendation

End with one of exactly these, and one sentence of why:

- **Apply** (4.0+) — worth the tailoring effort
- **Apply if the week is slow** (3.5–3.9) — real but not exciting
- **Pass** (below 3.5) — and say what would have to be different

If the recommendation is Apply, offer to run `tailor` next. Don't run it automatically — tailoring is expensive and you may want to batch.
