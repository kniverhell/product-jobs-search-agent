# Job Search Configuration: personal facts

Copy this file to `config.md` in the repo root before your first session (`cp templates/config.md config.md`).
The root copy is gitignored because it holds your comp floors.

**This file holds facts about you, not rules.** Scoring, blockers, location modifiers, company tiers and
the no-go list all live in `01-target-roles.md`, and nowhere else. Claims you must never make live in
`06-proof-points.md`. If you find yourself writing "cap at", "penalize" or "never surface" here, it
belongs in one of those two files instead.

---

## Your background

Describe your domain, seniority, and the kind of PM roles you're targeting.
Be specific. This shapes how the system reads every JD.

```
[FILL IN: 2–3 sentences. Example: "Senior product leader with 10+ years in fintech,
specializing in payments infrastructure and risk. Most recently a Director at [Company],
owning the fraud platform product. Targeting Director and VP roles at banks, fintechs,
and fraud/risk vendors."]
```

---

## Comp floors

Your walk-away numbers (base salary), not your ask. `negotiate` reads these; `evaluate` compares posted ranges against them.

```
COMP_FLOOR_REMOTE:    $[YOUR NUMBER]     # Fully remote
COMP_FLOOR_HYBRID:    $[YOUR NUMBER]     # Up to 2 days/week on-site
COMP_FLOOR_ONSITE:    $[YOUR NUMBER]     # More than 2 days/week
```

---

## Location

```
HOME_METRO:           [City, State]       # e.g. "Greater New York / NJ"
MAX_COMMUTE_DAYS:     [0-5]               # Days/week on-site you'll accept
RELOCATION:           [yes / no / open]   # Will you relocate for the right role?
```

How each of these changes a score is defined in `01-target-roles.md` → *Location modifiers*.

---

## Specialty path

Your stance on moving out of your specialty. This is a setting, not a scoring rule: what each value does is
defined in `SKILL.md` → *Trajectory and specialty path*.

```
SPECIALTY_PATH:       protect             # protect | open-to-drift (default: protect)
```

- `protect`: Trajectory may penalize a role that takes you out of your specialty.
- `open-to-drift`: Trajectory never penalizes it, and reports never call an off-specialty role a re-label or a detour.

Your comp floor applies either way.

---

## Domain keywords

Your specialty, in the words JDs use. Used to write `04-queries.md` and to set `DOMAIN` in `scan.py`.

```
DOMAIN_TIER1:  [Your core specialty. e.g. "identity, CIAM, authentication, IAM, login,
                MFA, passkeys, passwordless, device trust, account takeover"]

DOMAIN_TIER2:  [Adjacent areas you'd consider. e.g. "fraud, risk, onboarding, KYC,
                eIDV, access management, zero trust"]

DOMAIN_TIER3:  [Broader platform/product areas that sometimes overlap with your work.
                e.g. "platform, infrastructure, security, compliance"]
```

---

## Notes for the system

Anything else the system should know about your situation. Facts, not scoring rules.

```
[FILL IN or delete this section]
```
