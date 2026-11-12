# Project Manager — Online Passive Income

Last cycle: 2026-11-12T14:23:11.062374+00:00

**Goal:** Build a low-cost, mostly automated digital product business targeting €1,000/month within five years.

## Current status

- Completed: 2 | Queued: 6 | In progress: 0 | Blocked: 0
- Total cycles: 1
- Last selected task: MR-001
- Cycle result: completed

## Specialist roles

- **Project Manager** — Plans work, manages dependencies, preserves progress and creates next tasks.
- **Market Researcher** — Finds competitors, products, market opportunities and customer pain points.
- **Business Analyst** — Evaluates pricing, demand signals, reviews, economics and profitability.
- **Product Strategist** — Compares product ideas, tests assumptions and recommends next experiments.
- **Quality Controller** — Checks evidence quality, output completeness and unsupported claims.

## Five-stage implementation plan

1. **Cloud infrastructure** — completed. Private repository, persistent data, cloud execution and cost guardrails
2. **Agent brain** — in_progress. Orchestrator, specialist roles, memory, task queue and resume logic
3. **Automated research** — planned. Search, browser research, evidence capture and source checks
4. **Scheduling and reports** — planned. Five bounded daily cycles, saved results and notifications
5. **Management dashboard** — planned. Connect the MVP to persistent project data and show actual agent progress

## Task queue

- **PM-001 · Build persistent Project Manager and specialist role registry** — done · Project Manager
  - Acceptance: Orchestrator loads state, selects work, validates, saves progress and creates follow-up tasks.
- **MR-001 · Map direct competitors and substitutes for café starter kit** — done · Market Researcher
  - Acceptance: At least five relevant products or substitutes with source, price, audience and core promise.
  - Latest: Initial sourced competitor scan saved: 6 café template products/substitutes. See data/market_research.json; this is discovery evidence, not proof of sales.
- **MR-002 · Map direct competitors and substitutes for ShiftBrief AI** — queued · Market Researcher
  - Acceptance: At least five relevant products or substitutes with source, price, audience and core promise.
- **BA-001 · Compare competitor pricing and business models** — queued · Business Analyst
  - Acceptance: Pricing table distinguishes one-time, subscription, free and custom pricing.
- **BA-002 · Identify recurring customer complaints and unmet needs** — queued · Business Analyst
  - Acceptance: Pain-point list backed by reviews or first-hand community discussions.
- **PS-001 · Compare the two hypotheses and choose the cheapest demand test** — queued · Product Strategist
  - Acceptance: Evidence-based comparison, risks and a low-cost validation experiment.
- **QC-001 · Quality review of market evidence and recommendation** — queued · Quality Controller
  - Acceptance: Sources checked, weak evidence labelled, unsupported claims removed.
- **PM-002 · Prepare first product MVP scope and launch roadmap** — queued · Project Manager
  - Acceptance: Smallest testable MVP, milestones, costs and approval gates.

## Guardrails

- No paid APIs, subscriptions, servers or domains are enabled.
- No product is published and no commercial messages are sent without explicit approval.
- Research tasks that need live web evidence remain blocked rather than inventing facts.
- Each invocation handles at most one task to keep runs bounded and resumable.
