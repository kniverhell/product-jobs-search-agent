# Query Set — Scan Discovery

The primary discovery surface for `scan` mode. The company is the output; the query is the input.

---

## Problem-space layer — build queries from the problem, not the title

The differentiator in this system is that discovery starts from *what you know how to solve*, not from a job title. A title-first query finds every listing that uses your title. A problem-first query finds listings where the problem you solve is urgent — even if they use a different title, a different level, or a term you haven't heard before.

**The pattern:** Name the user problem or failure mode. Turn it into search terms that describe the symptom, not the solution. The employer is the output, not the input.

### How to build a problem-space query

1. List 3–5 problems your domain solves. Be specific about the failure mode — not "identity" but "account takeover after password reset."
2. Write the query as the victim or the business would describe the problem: words like "risk," "friction," "fraud," "drop-off," "recovery," "trust," "step-up," "attrition."
3. No title keywords. No company names. If the query works only when you already know the employer, it's a watchlist pass, not a problem-space query.

### Worked example — identity/CIAM domain

These queries contain no job titles and no company names. They find the problem, and the employer is what comes back.

| Problem cluster | Query | What comes back |
|---|---|---|
| Account takeover / contact-change fraud | `"contact change" "fraud" "product" site:linkedin.com` | PM roles at companies where ATO via phone/email update is a live threat |
| Account takeover / contact-change fraud | `"account recovery" "risk" "drop-off" product` | Roles where recovery friction is the design tension |
| Step-up authentication friction | `"step-up" "authentication" "product" "friction"` | Roles defining step-up policy; often buried in platform or trust orgs |
| Step-up authentication friction | `"MFA" "abandonment" "product manager"` | Companies where MFA friction is causing measurable drop-off |
| Onboarding/KYC conversion | `"KYC" "onboarding" "conversion" "product"` | Regulated fintechs where identity verification is a conversion bottleneck |
| Onboarding/KYC conversion | `"identity verification" "funnel" "product" site:linkedin.com` | Roles where the business problem is verification-rate vs. fraud-rate tradeoff |

### Adapt this to your domain

Replace the problem clusters above with the 3–5 failure modes in your domain. For each:
- What does the failure look like to the user?
- What does the failure look like to the business (fraud, churn, cost, compliance)?
- What words would a non-PM stakeholder (risk, ops, engineering, legal) use to describe it?

Those words are your query terms.

---

## How this file works

- **Tier 1 queries** run every scan (your core domain)
- **Tier 2 queries** run when Tier 1 is thin (adjacent framings)
- **Tier 3 queries** run every scan (geography — catches postings that use location, not domain)
- After each run, update the `run_count` and `qualifying_count` columns
- A query with zero qualifying roles across 6 runs gets rewritten or retired

---

## Tier 1 — Core domain (run every scan)

| Query | Run count | Qualifying count | Notes |
|---|---|---|---|
| `"director of product" "[your domain keyword]" -engineer` | 0 | 0 | |
| `"head of product" "[your domain keyword]"` | 0 | 0 | |
| `"VP product" "[your domain keyword]"` | 0 | 0 | |
| `site:linkedin.com "head of product" "[your domain]"` | 0 | 0 | LinkedIn Boolean — also shows connection degree |
| [Add your Tier 1 queries here] | | | |

**Query writing tips:**
- Quote multi-word phrases: `"head of product"` not `head of product`
- Use `-engineer` to exclude engineering roles where the domain keyword appears
- Boolean on LinkedIn: `"director OR VP" "[domain]" -staffing -contract`
- Workday site search: `site:[company].wd1.myworkdayjobs.com "director" "[domain]"`

---

## Tier 2 — Adjacent framings (run when Tier 1 is thin)

| Query | Run count | Qualifying count | Notes |
|---|---|---|---|
| [e.g. `"director of product" "platform" "authentication"`] | 0 | 0 | |
| [e.g. `"head of product" "trust and safety"`] | 0 | 0 | |
| [Add your Tier 2 queries here] | | | |

---

## Tier 3 — Geography (run every scan)

| Query | Run count | Qualifying count | Notes |
|---|---|---|---|
| `"director of product" "[your metro]" "[domain keyword]"` | 0 | 0 | |
| `"head of product" "[your metro]"` | 0 | 0 | |
| [Add your geography queries here] | | | |

---

## Query graveyard — retired queries

Queries that produced zero qualifying roles after 6+ runs.

| Query | Retired | Reason |
|---|---|---|
| [query] | [date] | [e.g. "Returns engineering roles, domain keyword not specific enough"] |

---

## Inbound roles (not from queries)

When a qualifying role arrives from outside the query set (recruiter, referral, manual), record
which query would have caught it. That's how the query set improves.

| Role | Source | Query that would have caught it | Added query? |
|---|---|---|---|
| [Company / Title] | [Recruiter / Referral / Manual] | [Query text] | [Yes / No / Already exists] |
