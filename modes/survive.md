# Mode: Survive — Will This Company Still Exist?

Run before accepting an offer, and before investing real effort in a private company at or below Series B. `evaluate` calls this automatically for those; you can also trigger it by name ("will they survive", "run survival on X").

This mode answers one question: **is this company likely to be solvent and independent in 3–5 years?** It is not a judgment of whether the product is good or the people are smart. Interesting and durable are different things.

Write to `reports/YYYY-MM-DD-company-slug-survive.md`.

## What this mode can and cannot do

Every other mode in this system verifies. This one estimates. There is no ATS to check a runway against, and private companies do not publish the numbers that would settle the question.

Rules that follow from that:

- **State confidence on every dimension**, not just the verdict. High confidence needs a primary source: a filing, a published financial statement, a funding announcement from the company, a regulator's action.
- **Missing data lowers confidence — it never becomes a mid score.** "No disclosed revenue" is not a 5/10 on unit economics. It is an unknown, and the score says so.
- **Never invent a runway.** If burn isn't knowable, say the estimate depends on burn and name what would reveal it.
- **Too early to judge is a valid finding.** A seed-stage company with no shipped product cannot be scored for five-year survival. Say that instead of producing a number.

## Baseline rates to score against

Use these as the base rate, not as the answer.

- About 20% of US businesses fail in year one, and about half by year five (BLS). The "90% of startups fail" figure is overstated for businesses generally and closer to accurate for venture-backed, high-growth companies specifically.
- Running out of cash is the last event, not the cause. The recurring root causes are no market need or weak product-market fit, bad timing, unsustainable unit economics, the wrong team, and being outcompeted.
- **Funded is not safe.** Capital delays death; it does not create demand. A large recent raise moves the date, not the outcome.

## The eight dimensions

Score each 1–10 with the evidence behind it, the confidence (high / medium / low), and what would change the score. This is a 1–10 scale on purpose — it is deliberately not the 1–5 role rubric, because survival is a separate question from fit and the two should never be averaged together.

| # | Dimension | The question |
|---|---|---|
| 1 | **Market need / PMF** | Do customers pay, come back, and expand? Or is this a solution hunting a problem? |
| 2 | **Unit economics** | Is there a path to positive contribution margin and sane payback without heroic assumptions? |
| 3 | **Cash & runway** | Months of life at current burn. How dependent is this on the next raise? |
| 4 | **Competition & moat** | Who wins if a well-funded rival copies this in 18 months? |
| 5 | **Team** | Can this team execute the next stage, not just the pitch? Look at tenure and at who has left. |
| 6 | **Timing & macro** | Is the window still open, or did the hype already peak? |
| 7 | **Concentration risk** | One customer, one platform, one channel, one regulation? |
| 8 | **Model quality** | Recurring or one-shot? Pricing power? Switching costs? |

Flag these explicitly wherever they appear, because each one has killed companies faster than the base rate suggests: **thin AI wrappers** over someone else's model, **marketplace chicken-and-egg** where neither side shows up first, and **regulatory exposure** where one rule change removes the product.

## Research to run

Search for, and cite: the last funding round with its date and size, headcount trend, any layoffs, customer names and whether any one of them is load-bearing, the competitive set including incumbents, pricing, any enforcement action or consent order, and executive departures in the last 12 months. For a public parent or acquirer, use the filings.

Note what you could not find. A company with no discoverable customers after a real search is itself a finding.

## Output

```
**Company:**
**Stage / model (inferred):**
**Verdict:** Durable / Conditional / Fragile / Too early to judge
**3–5 year survival:** X% (low / medium / high confidence)
**One-sentence thesis:**
```

Then:

**Scorecard** — table: Dimension | Score /10 | Evidence | Confidence | What would change it

**Competitive map** — direct competitors · substitutes · incumbents who could crush this · unowned ground, if any

**Kill scenarios, ranked** — what most likely ends this company by year 3, and by year 5

**What would make this durable** — three concrete conditions that would have to become true

**What this means for you as a candidate**

This is the part that separates the mode from an investor memo. You are not allocating capital; you are deciding whether to spend two years of your career here.

- **Take / take with conditions / pass**, and the conditions in plain terms
- **What the equity is worth assuming.** For a fragile company, assume zero and judge the offer on cash alone. Say so plainly.
- **What the downside actually looks like** — a company that shuts down is different from one that gets acquired and reorganizes, and both are different from a slow decline with layoffs. Say which is most likely.
- **Questions to ask the hiring manager**, worded so they are askable. "How long is the current runway" is fair in a final round. Some are better aimed at a recruiter, and some are only answerable by someone who works there.
- **The one unknown to resolve before deciding**, and who can answer it.

## How this interacts with the role score

Survival never raises a role score. It caps it.

| Verdict | Effect on the role's holistic |
|---|---|
| Durable | none |
| Conditional | note the risk in the report; no cap |
| Fragile | cap at 3.0, and say the cap is what put it there |
| Too early to judge | no cap, but state that the survival question is unanswered and must be asked in the process |

A capped score is not a rejection. It means the offer has to be better to be worth the same risk, and cash has to carry more of the package.
