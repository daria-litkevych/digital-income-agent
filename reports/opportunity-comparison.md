# Opportunity Comparison — First MVP Decision

**Date:** 2026-11-12  
**Method:** Public desk research, competitor/substitute inspection and qualitative community signals.  
**Important:** This is not customer validation. No interviews, pre-orders, verified sales or conversion data have been collected.

## Shortlist

| Candidate | Problem signal | Competition / substitutes | Build and support burden | First-MVP view |
|---|---|---|---|---|
| Freelancer scope-change utility | Multiple first-hand posts describe unpaid extra work, unclear revisions and awkward approval; one post quantified $2,300 in unpaid work. [Example](https://www.reddit.com/r/freelance/comments/1ozc3zq/lost_2300_to_scope_creep_on_one_project_how_do/) | Templates and broad client-management suites exist, including [Dubsado](https://www.dubsado.com/pricing/) and [ScopeDue](https://scopedue.com/templates/change-request/freelance-change-request-template/). | Low for a standalone calculator/document generator; high if adding contract analysis, email or client accounts. | **Best prototype candidate** if kept narrow: no-login change estimator + client-ready brief. |
| Micro-business invoice follow-up | European SME research points to recurring admin burden; billing and reminders are common desired functions. [Visma](https://www.visma.com/insights/content/insights-from-european-entrepreneurs-on-running-a-business) · [inTandem](https://intandem.vcita.com/content-hub/the-2026-small-business-digital-adoption-report) | Dense field: [Vordero](https://vordero.eu/en/prijzen), [Dunlio](https://dunlio.com/), [Babara](https://babara.app/pricing), [Dunningly](https://www.dunningly.app/), [Quotup](https://quotup.com/). Free plans are common; paid tiers range from €9/month and upward in examples. | High: email sending, invoice imports, privacy, reminders, integrations, customer support. | Real recurring need, but too integration-heavy and competitive for first low-budget MVP. |
| Wedding planning module | First-hand users describe spreadsheet friction, guest/household tracking and scattered information. [Guest list](https://www.reddit.com/r/wedding/comments/1r3ocq4/finally-got-our-guest-list-under-control-after/) · [Planning chaos](https://www.reddit.com/r/weddingplanning/comments/1sitnn9/how_are-you-all_actually-organizing-everything_bc/) | Several free suites already include guests, RSVPs, seating and budgets: [WedMap](https://wedmap.wedding/), [Stellanza](https://www.stellanza.com/en), [Shaadi DIY](https://www.shaadi.diy/), [Ever After List](https://everafterlist.com/features/guest-list/). | Medium: collaborative state, invitations, personal data and event-specific support. | Need exists, but strong free substitutes and one-time usage weaken the first-product case. |
| Personal-finance utility | Market coverage shows interest in budget spreadsheets and planners, but broad category is saturated. [Keeper](https://www.keepertax.com/posts/digital-products-to-sell) | Mature alternatives with free tiers include [Actual Budget](https://actualbudget.org/), [Spendee](https://www.spendee.com/pricing/) and [Empower](https://www.empower.com/). | Medium/high if bank data or financial recommendations are involved; low only for a narrow calculator. | Do not build a generic budget app. Revisit only with a specific underserved calculation/job. |

## Decision: ScopeSnap

**ScopeSnap** is the selected first MVP hypothesis: a lightweight browser utility for freelancers and independent service providers.

Core job: when a client asks for work outside the agreed scope, calculate the additional fee/time and prepare a clear change summary for client approval *before* the extra work begins.

### Why this one first

- The pain is concrete and can have a direct financial consequence.
- The first version can work entirely in the browser without accounts, data storage, email sending, integrations or paid APIs.
- A useful result can be produced immediately: a priced change summary that the freelancer can copy, print or save as PDF.
- It is possible to test usability before investing in backend infrastructure.

### MVP boundary

Included:
- Original scope / project reference.
- New request description.
- Additional hours, hourly rate and extra costs.
- Calculated additional price and revised time estimate.
- Client-ready summary with clear approval wording.
- Copy and print/save-as-PDF actions.

Excluded:
- Contract upload or AI legal interpretation.
- E-signatures or claims of legal enforceability.
- Client accounts, CRM, payments, invoicing or email sending.
- Cloud storage or collection of client information.

### Confidence and validation gate

Confidence is **low-to-moderate**. Community evidence is qualitative and self-selected. Competitors and templates exist. We do not know whether freelancers will choose a standalone tool or pay for it.

Before public launch, test the prototype with 5–8 freelancers:
1. Can they create a usable change summary without help?
2. Does it feel easier than their current process?
3. Would they actually send the output to a client?
4. What do they currently use (contract clause, email, template, CRM)?
5. Would they pay for a useful export/template bundle or is free enough?

No public listing or paid validation campaign is authorised at this stage.
