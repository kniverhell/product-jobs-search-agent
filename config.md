# Job Search Configuration

This is the only file you personalize. The skill and all modes read from it.
Fill in every section before your first session.

---

## Your background

Describe your domain, seniority, and the kind of PM roles you're targeting.
Be specific — this shapes how the system interprets every JD and scores every role.

```
[FILL IN: 2–3 sentences. Example: "Senior product leader with 10+ years in fintech,
specializing in payments infrastructure and risk. Most recently a Director at [Company],
owning the fraud platform product. Targeting Director and VP roles at banks, fintechs,
and fraud/risk vendors."]
```

---

## Comp floors

These are your walk-away numbers, not your ask. The system shows both the pre-modifier
score and the post-modifier score so the location trade-off stays visible.

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

If `RELOCATION` is `no`, relocation requirements are a hard blocker.
If `open`, apply a -0.5 score modifier and flag it — it's a trade-off, not a disqualifier.

---

## Location score modifiers

Customize these to your situation. Shown in every evaluation report.

```
Remote (home metro or East Coast-friendly timezone):  0
Hybrid 2 days/week or fewer:                         -0.2
Hybrid 3 days/week:                                  -0.5
On-site 4-5 days/week (home metro):                  -0.7
On-site 4-5 days/week (requires relocation):          BLOCKER unless RELOCATION=open
```

---

## Target titles

List the title levels you want the system to surface. Anything outside these levels
is flagged, not automatically blocked — it might still be worth a look.

```
TITLE_ACCEPT:   [e.g. "VP of Product", "Head of Product", "Director of Product",
                 "Senior Director of Product", "Principal PM"]
TITLE_STRETCH:  [e.g. "Group Product Manager", "Staff PM"]
TITLE_PASS:     [e.g. "Senior PM" (IC only, no team), "Associate PM"]
```

---

## Domain keywords

Your specialty area — used by `scan.py` to filter roles and by the scan mode
to prioritize queries.

```
DOMAIN_TIER1:  [Your core specialty. e.g. "identity, CIAM, authentication, IAM, login,
                MFA, passkeys, passwordless, device trust, account takeover"]

DOMAIN_TIER2:  [Adjacent areas you'd consider. e.g. "fraud, risk, onboarding, KYC,
                eIDV, access management, zero trust"]

DOMAIN_TIER3:  [Broader platform/product areas that sometimes overlap with your work.
                e.g. "platform, infrastructure, security, compliance"]
```

---

## Company tier preferences

Scoring guidance for the Company dimension (1–5).

```
COMPANY_TIER1:  [Your highest-preference company types. e.g. "Identity vendors, fraud
                 vendors, fintech infrastructure companies where your domain is existential"]

COMPANY_TIER2:  [Good companies. e.g. "Fintech, digital banking, crypto, large FIs
                 where identity/payments is a real platform"]

COMPANY_TIER3:  [Acceptable. e.g. "Any well-run company with a genuine Director-level
                 platform PM role in your domain"]

COMPANY_AVOID:  [Company types that score low regardless of role. e.g. "Companies
                 where identity is a utility function, not a product"]
```

---

## Hard blockers

Roles with any of these characteristics get capped at 2.0 regardless of everything else.

```
BLOCKERS:
  - Staffing agency or contract listing rather than direct employment
  - Posting 90+ days old with no ATS-verified refresh
  - Relocation required (when RELOCATION=no)
  - [Add your own — e.g. "Crypto/Web3 (mechanics as core requirement)", "Healthcare only"]
```

---

## No-go list

Specific employers you will not work for. Never surface, evaluate, or recommend.

```
NO_GO:
  - [Employer name]    # Reason (optional)
  - [Employer name]
```

---

## Standing proof-point constraints

Claims you must never make in tailored materials, ever.
Add one line per constraint. These are checked by the `integrity` mode.

Format: `NEVER [verb] "[claim context]"` + reason

```
CONSTRAINTS:
  - NEVER use "shipped/launched/deployed/delivered" near [topic you designed but didn't ship]
    Reason: [e.g. "Designed the architecture but left before implementation"]

  - NEVER cite [specific dollar figure or metric]
    Reason: [e.g. "Retired — too ambiguous to defend in a room"]

  - [Add your own]
```

---

## Trajectory scoring rule

How to score the Trajectory dimension for roles outside your core domain.

```
TRAJECTORY_NOTE: [e.g. "Do not penalize for moving away from [your domain].
                  Score on meaningful scope, career credibility of the company,
                  and whether I can be strong in the role given my full background.
                  I am not protecting a specialty path — I am looking for my next role."]
```

---

## Notes for the system

Anything else the system should know about your situation, constraints, or preferences.

```
[FILL IN or delete this section]
```
