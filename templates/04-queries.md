# Query Set — Scan Discovery

The primary discovery surface for `scan` mode. The company is the output; the query is the input.

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
