# Digital Product Studio — Operating Blueprint

## 1. Mission

Build a portfolio of small, useful digital products. The studio discovers opportunities across B2C, B2B and prosumer segments, validates a narrow problem, builds a usable MVP, prepares a commercial listing, and learns from real customer behaviour.

**North-star business target:** €1,000/month within five years.  
**First revenue milestone:** €100–300.  
**Cost envelope:** €0–50 initial budget; preferred recurring cost ≤€10/month.

## 2. Studio vs. product teams

The **studio** manages the portfolio, standards, budget, research process, prioritisation and approval gates.

Each **product workspace** owns its own customer, problem, PRD, design, code, tests, listing assets, release checklist and metrics. A product must not become entangled with unrelated product hypotheses.

Suggested workspace:

```text
products/<product-slug>/
  README.md
  research/
    customer-problem.md
    competitors.md
    evidence-log.json
  product/
    PRD.md
    user-journey.md
    acceptance-criteria.md
  design/
    wireframes.md
    assets/
  app/                 # working product source
  tests/
  launch/
    positioning.md
    listing-copy.md
    pricing-hypothesis.md
    screenshots/
    release-checklist.md
  analytics/
    metrics-plan.md
```

## 3. Specialist roles and maturity

| Role | Responsibility | Current maturity |
|---|---|---|
| Project Manager | Task dependencies, priorities, continuity, approval gates | Deterministic handler exists |
| Market Researcher | Find customer problems, competitors, substitutes and price evidence | Limited RSS/evidence handling exists; broad research agent planned |
| Business Analyst | Compare economics, evidence strength, demand signals and build effort | Deterministic analysis exists; portfolio scorecard planned |
| Product Strategist | Select a narrow problem and design validation | Basic deterministic handler exists |
| Product Designer | PRD, user journey, prototype and acceptance criteria | Planned |
| Developer | Build and document working MVP | Planned |
| QA Tester | Functional, edge-case, mobile, accessibility and privacy checks | Existing evidence QC only; product QA planned |
| Growth & Launch | Positioning, listing assets, pricing tests and distribution | Planned |

A guarded Agent Brain foundation now exists in `agent/brain.py`: central role registry, injected provider interface, structured JSON contract, offline mock default and fail-closed output validation. It is not yet fully integrated into Project Manager. The scheduled system is still deterministic, not an autonomous LLM team. Live model use remains disabled and requires explicit provider, pricing, spend caps and credential approval.

## 4. Opportunity discovery framework

Search broadly, then narrow. Do not preselect a vertical.

- **B2C:** consumer tools for concrete recurring jobs (finance decisions, life admin, events, household organisation).
- **B2B:** small-business operations and administration (quoting, invoicing reminders, records, staff workflows, niche operations).
- **Prosumer:** freelancers, creators and independent professionals (scope control, pricing, client handover, content and deliverable workflows).

Every candidate must be described as:
1. Specific user and situation.
2. Job they are trying to complete.
3. Current workaround and its cost.
4. Frequency and consequence of the problem.
5. Existing alternatives and why they fall short.
6. Evidence source and confidence.
7. Smallest product that could improve the job.
8. Likely distribution channel and support burden.

## 5. Evidence and scoring rules

Score candidates separately on:
- pain intensity and recurrence;
- clarity and reachability of the buyer;
- evidence of current workaround or spending;
- competitor/substitute density and differentiation;
- MVP effort and ongoing maintenance;
- distribution access and willingness-to-pay evidence.

Keep **opportunity attractiveness** separate from **evidence confidence**. Search volume is interest, not purchase intent. Competitor listings show supply, not sales. Community posts are qualitative clues, not representative samples. AI-generated scores are prioritisation aids, not facts.

A candidate cannot pass validation on desk research alone. Seek direct user feedback, observed workflow demonstrations, prototype completion, pre-orders/pilot commitments or other concrete behaviour. Do not claim validation without evidence.

## 6. Product lifecycle gates

| Gate | Deliverable | Pass condition |
|---|---|---|
| Discovery | Opportunity brief | Specific problem and initial source trail |
| Validation | Evidence log and test result | Repeated pain plus credible workaround/spend or prototype commitment |
| Selection | Decision memo | Best candidate, alternatives, confidence and assumptions |
| Design | PRD and prototype | User can understand and complete the core job |
| Build | Working MVP | Core workflow works without paid dependencies unless approved |
| QA | Test report | No release-blocking defects; limitations documented |
| Launch prep | Listing package | Clear promise, screenshots, instructions, price hypothesis and support plan |
| Publication | Approved listing | User approves exact platform, content, price and any fees |
| Iteration | Metrics review | Decisions based on actual traffic, conversion, sales, refunds and support |

## 7. Autonomy and safety boundaries

The studio may autonomously research public information, draft artifacts, write code in the private repository, run tests and recommend decisions once those capabilities are implemented and verified.

It must **not** autonomously:
- spend money, start subscriptions, top up credits or use paid APIs;
- contact prospects or customers;
- publish public listings or deploy private project data;
- change account settings, billing or access permissions;
- make legal, tax, financial or compliance claims without appropriate verification.

Each external side effect requires explicit user approval. The user should be interrupted only for material business choices, access requirements, or approval gates—not minor implementation details.

## 8. Immediate roadmap

1. Complete the first broad opportunity scan (initial scan is recorded in `reports/opportunity-scan.md`).
2. Build a comparable scorecard and deep-dive the strongest three.
3. Recommend one first MVP, including why it beats alternatives.
4. Create a product workspace and a concrete PRD.
5. Build and test a small working product while improving studio automation in parallel.
6. Prepare the actual marketplace listing; request approval only at the public launch/payment gate.
