# Target Roles

Defines the role archetypes you're targeting, scoring guidance per archetype, hard disqualifiers,
and what to lead with in tailored materials.

Read this file before scoring any role.

**This is the only place your scoring rules live.** Title levels, location modifiers, company tiers,
blockers, the no-go list, survival verdict effects and the trajectory rule are all here. `SKILL.md` holds the framework (dimensions,
staleness, forks, the verification gate). `config.md` holds facts about you (floors, home metro,
relocation). No other file (memory, notes, reports) may score, cap or block a role (`SKILL.md` rule 9).

---

## Your target archetypes

Define 2–4 archetypes that describe the roles you want most. For each:
- What the role is
- What the JD should contain to qualify
- What you'd lead with in tailored materials

### Archetype 1: [Name, e.g. "Director/Head, core domain"]

**What it is:** [e.g. "Director or Head of Product in [your domain], owning the roadmap and managing PMs.
Typically at a company where your domain is a core product — a vendor in the space, or a regulated
company where it's existential."]

**JD signals:** [e.g. "own the vision", "manage PMs", "0→1", "enterprise customers", "roadmap authority"]

**What to lead with in tailored materials:**
- [Proof point #1 — your strongest outcome in this archetype]
- [Proof point #2]
- [Proof point #3]

**Score guidance:**
- Domain: use the problem-ownership scale in `SKILL.md`. Name the problem this archetype exists to solve; see *Problem spaces you've owned* below
- Level: 4–5 if it owns roadmap + people; 2–3 if it's IC wearing a Director title
- Evidence: [the ledger entries that usually carry this archetype's core requirements]

---

### Archetype 2: [Name, e.g. "Senior/Principal IC PM, remote, core domain"]

**What it is:** [e.g. "Senior or Principal PM in [your domain], individual contributor, remote-first.
Typically at a company where you'd have significant scope but report into a Director or VP."]

**JD signals:** [e.g. "own the product area", "technical PM", "work closely with engineering", "no direct reports"]

**What to lead with in tailored materials:**
- [Proof point #1 — your strongest IC/technical execution evidence]
- [Proof point #2]

---

### Archetype 3: [Optional — e.g. "Director, adjacent platform (non-core domain)"]

[Add if you're open to roles outside your core domain. Define what "adjacent" means for you,
and what makes a non-core role worth considering. See *Trajectory rule* below.]

---

## Hard disqualifiers

Any role with these characteristics is capped at 2.0 regardless of everything else.
This is the complete list; there is no second one anywhere else.

- Staffing agency or contract listing rather than direct employment
- 90+ days posted with no ATS-verified refresh
- IC role wearing a Director title (no direct reports, no roadmap ownership)
- Relocation required, **only if** `RELOCATION: no` in `config.md` (see *Location modifiers*)
- [Add your own, e.g. "Crypto/Web3 mechanics as a core requirement", "Company stage pre-Series B if base < comp floor"]

**Prefer a modifier to a blocker.** A blocker hides a role you might have wanted; a penalty shows it with
the cost stated. Only add a blocker for things that are a hard no every single time.

---

## Survival verdicts

What a `survive` verdict does to the role's holistic score. `modes/survive.md` produces the verdict; this table
is the only place its effect is defined. Survival never raises a score.

| Verdict | Effect on the role's holistic |
|---|---|
| Durable | none |
| Conditional | note the risk in the report; no cap |
| Fragile | cap at 3.0, and say the cap is what put it there |
| Too early to judge | no cap, but state that the survival question is unanswered and must be asked in the process |

A capped score is not a rejection. It means the offer has to be better to be worth the same risk, and cash has to
carry more of the package. Change the cap to suit you.

---

## No-go list

Specific employers you will not work for. Never surface, evaluate, or recommend.

| Employer | Reason (optional) |
|---|---|
| [Employer name] | |

---

## Title levels

Titles outside these levels are flagged, not automatically blocked. And never score level from a title:
search the JD for "reports", "team of", "mentor", "recruit".

```
TITLE_ACCEPT:   [e.g. "VP of Product", "Head of Product", "Director of Product",
                 "Senior Director of Product", "Principal PM"]
TITLE_STRETCH:  [e.g. "Group Product Manager", "Staff PM"]
TITLE_PASS:     [e.g. "Senior PM" (IC only, no team), "Associate PM"]
```

---

## Location modifiers

Applied after the holistic score. Show both numbers in every report (pre-modifier and final). Uses the facts in `config.md`.
These values are defaults. Change any of them to suit you, including the −0.5 for relocation when
`RELOCATION: yes`. `RELOCATION: no` is the one case that isn't a modifier: it's a hard blocker.

```
Remote (home metro or East Coast-friendly timezone):  0
Hybrid 2 days/week or fewer:                         -0.2
Hybrid 3 days/week:                                  -0.5
On-site 4-5 days/week (home metro):                  -0.7
Relocation required, RELOCATION: yes:                -0.5
Relocation required, RELOCATION: open:               -0.5, and flag it prominently
Relocation required, RELOCATION: no:                 hard blocker (see Hard disqualifiers)
```

---

## Company tiers

Scoring guidance for the Company dimension (1–5).

```
COMPANY_TIER1:  [Your highest-preference company types. e.g. "Identity vendors, fraud
                 vendors, fintech infrastructure companies where your domain is existential"]
COMPANY_TIER2:  [Good companies. e.g. "Fintech, digital banking, large FIs
                 where identity/payments is a real platform"]
COMPANY_TIER3:  [Acceptable. e.g. "Any well-run company with a genuine Director-level
                 platform PM role in your domain"]
COMPANY_AVOID:  [Company types that score low regardless of role. e.g. "Companies
                 where identity is a utility function, not a product"]
```

---

## Problem spaces you've owned

Feeds the Domain fit scale in `SKILL.md` (problem ownership, 5 to 1). List problem spaces, not job titles or
industries. Domain is judged on the problem the job exists to solve, never on the company's industry.

```
OWNED (5):        [Problem spaces you owned end to end. e.g. "customer onboarding and activation funnels"]
ADJACENT (4):     [The same problems you owned in another form. e.g. "consolidating business lines onto a shared service"]
PARTIAL (3):      [Spaces you owned part of, or worked alongside. e.g. "partnered with fraud ops on step-up rules"]
NEVER OWNED (2):  [Named technical domains you haven't worked in. e.g. "building ML models", "ad auctions"]
```

Building models caps Domain at 2 unless you have built models; owning the decisions the models feed does not.
See *Building models vs owning decisions* in `SKILL.md`.

---

## Trajectory rule

Set `SPECIALTY_PATH` in `config.md` (`protect` or `open-to-drift`); `SKILL.md` → *Trajectory and specialty path*
defines what each does. Add anything else that should shape Trajectory here.

```
TRAJECTORY_NOTE: [e.g. "Score on meaningful scope, career credibility of the company,
                  and whether I can be strong in the role given my full background."]
```

---

## Score guidance by company type

Company type sets the **Company** score only. It never sets Domain: Domain is judged on the problem, not
the industry.

| Company type | Company score | Notes |
|---|---|---|
| Vendor in your exact domain | 5 | Core product, your background is the hire |
| Regulated company where your domain is existential | 4 | It's their product, not a utility |
| Large enterprise where your domain is a platform function | 3–4 | Scope may be large but the work is internal |
| Company where your domain is infrastructure, not product | 2–3 | You'll be maintaining, not building |

---

## Query tiers (for `04-queries.md`)

**Tier 1 — Core domain:**
[List 5–8 search queries for your exact domain. These run every scan.
Example: `"director of product" "identity" "CIAM" site:linkedin.com`]

**Tier 2 — Adjacent framings:**
[List 3–5 queries for roles that are one step away from your core but worth seeing.
Run these when Tier 1 is thin.]

**Tier 3 — Geography:**
[List 2–3 location-specific queries for your home metro.
Run these every scan to catch postings that use location instead of domain keywords.]

---

## Notes on the market in your domain

[Add observations as you scan — patterns you notice, companies that post a lot but never close,
title inflation in specific sectors, anything that changes how you interpret what you see.]
