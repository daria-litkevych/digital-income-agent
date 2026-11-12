# Evidence grading rules

Use this rubric for all opportunity research. Keep **evidence strength** separate from **opportunity attractiveness**.

## Source classes

| Class | Source type | Typical examples | What it can support |
|---|---|---|---|
| A | Primary operational evidence | Official pricing/feature pages, help docs, terms, changelogs | What a product offers, displayed price, limits and mechanics |
| B | Independent behavioural evidence | Verified customer reviews, detailed first-person use reports, app-store reviews with usage context | Specific experience, recurring friction, adoption or churn reasons |
| C | First-person problem evidence | Community posts describing a concrete incident, workaround, frequency or cost | Existence of a pain/workaround in that case; qualitative themes |
| D | Independent market research | Transparent surveys, industry reports, datasets with method and sample | Directional trends within stated sample/method limits |
| E | Discovery/marketing evidence | News RSS, trend articles, SEO roundups, vendor blogs, founder launch posts | Discovery of candidates and competitors only |
| F | Weak or unverifiable evidence | Scraped snippets, unattributed claims, generic AI summaries | Search leads only; not decision evidence |

## Confidence

- **High:** Multiple independent A/B sources, or robust D research with a clear method, support the same narrow claim.
- **Medium:** One credible A/B source or several independent C sources support a bounded qualitative claim.
- **Low:** One anecdote, founder marketing, low-engagement thread, vendor claim without independent corroboration, or incomplete source inspection.
- **Unverified:** Snippet-only, broken link, no accessible source page, or claim cannot be traced.

Confidence applies to an individual claim, not an entire market.

## Keep four questions separate

1. **Pain:** Does a specific user experience a problem? Record context, consequence and frequency only when stated.
2. **Workaround:** What do they do now? Record time, money and manual steps only when stated.
3. **Demand / willingness to pay:** Did they pay, switch, commit, request access, pre-order or state a credible price? A complaint or "I'd use this" is not purchase evidence.
4. **Competition:** What alternative exists, what does it cost and what job does it perform? Listings and feature pages show supply, not sales.

## Anti-bias and deduplication

- Mark founder posts, affiliate roundups and vendor-owned comparisons as interested sources.
- Do not count the same story reposted across sites as independent evidence.
- Low-engagement threads are clues, not market trends.
- Do not infer frequency from search-result counts.
- Record publication date and date checked for volatile prices.
- Preserve contradictory evidence and objections.
- Repetition in internal reports does not upgrade an unverified claim.

## Minimum evidence-log fields

Each record should contain: `claim`, `source_url`, `source_type`, `publisher_interest`, `published_at`, `checked_at`, `segment`, `hypothesis`, `first_hand`, `pain_signal`, `workaround`, `payment_signal`, `confidence`, `limitations`.

## Decision discipline

A candidate cannot be marked validated on RSS, search snippets, competitor count or community complaints alone. Desk research can rank what to test. Validation requires observed behaviour, prototype task completion, current spend/workaround evidence, credible pilot commitment or an actual transaction. Keep assumptions visible and state when a test has not happened.
