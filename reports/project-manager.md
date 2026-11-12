# Project Manager — Online Passive Income

**Research update:** 2026-11-12

**Goal:** Build a low-cost, mostly automated digital product business targeting €1,000/month within five years.

## Current status

- Completed: 4 tasks | In progress: 1 | Queued: 3 | Blocked: 0
- Research tasks completed: competitor mapping for both hypotheses and first pricing comparison.
- Next active work: strengthen customer pain evidence before choosing a product.
- Dashboard: local-first interface in `dashboard/index.html`; no public hosting.

## Specialist roles

- **Project Manager** — Plans work, manages dependencies, preserves progress and creates next tasks.
- **Market Researcher** — Finds competitors, products, market opportunities and customer pain points.
- **Business Analyst** — Evaluates pricing, demand signals, reviews, economics and profitability.
- **Product Strategist** — Compares product ideas, tests assumptions and recommends next experiments.
- **Quality Controller** — Checks evidence quality, output completeness and unsupported claims.

## Five-stage implementation plan

1. **Cloud infrastructure** — completed. Private repository, persistent data, cloud execution and cost guardrails
2. **Agent brain** — in_progress. Orchestrator, specialist roles, memory, task queue and resume logic
3. **Automated research** — in_progress. Search, browser research, evidence capture and source checks
4. **Scheduling and reports** — planned. Five bounded daily cycles, saved results and notifications
5. **Management dashboard** — implementation started. Local-first HTML dashboard created; data import and browser use are manual, not automatic sync.

## Task queue

- **PM-001 · Build persistent Project Manager and specialist role registry** — done
- **MR-001 · Map café starter-kit competitors and substitutes** — done. Six paid Etsy marketplace results/substitutes recorded.
- **MR-002 · Map ShiftBrief AI competitors and substitutes** — done. Six competitors/substitutes mapped; official prices checked for ShiftForce, Shifo, Venheim and Rotahr.
- **BA-001 · Compare competitor pricing and business models** — done. Price anchors recorded with tax, currency and scope caveats.
- **BA-002 · Identify recurring customer complaints and unmet needs** — in progress. Current evidence includes anecdotal worker discussions and free café checklist substitutes; stronger first-hand review/interview evidence is still needed.
- **PS-001 · Compare the two hypotheses and choose the cheapest demand test** — queued; depends on BA-002.
- **QC-001 · Quality review of market evidence and recommendation** — queued; depends on PS-001.
- **PM-002 · Prepare first product MVP scope and launch roadmap** — queued; depends on QC-001.

## Current evidence-based observations

1. Generic café checklists are difficult to sell as a standalone paid product: cheap paid templates and free specialty-coffee checklist resources already exist.
2. A café product would need to solve a more specific recurring and costly job, such as waste reduction, quality consistency or barista onboarding.
3. Shift handover is an established software category with existing competitors and bundled operations suites.
4. Worker discussions indicate both handover friction and app fatigue; a new app must prove that it reduces friction rather than adding another communication channel.
5. Neither hypothesis has demonstrated willingness to pay. Do not select a winner or build a full product yet.

## Next validation

- Observe/interview 5–8 independent specialty coffee shop owners/managers about their current routines and costly operational problems.
- Interview 5–8 shift leads about handover failures, consequences, current tools and app fatigue.
- Record actual workflow, frequency, consequences, workaround and existing spend. Avoid pitching before understanding the process.

## Guardrails

- No paid APIs, subscriptions, servers or domains are enabled.
- No product is published and no commercial messages are sent without explicit approval.
- Research claims without live evidence remain labelled as incomplete.
- Each automated invocation handles at most one task to keep runs bounded and resumable.
- Dashboard data is loaded locally by the user; no private data is published through GitHub Pages.
