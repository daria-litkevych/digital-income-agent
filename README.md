# Digital Product Studio

A private, low-cost project for discovering, validating, building and selling useful digital products across **B2C, B2B and prosumer** markets.

## Business goal

Build a mostly automated digital-product portfolio targeting **€1,000/month within five years**, with an initial revenue milestone of €100–300. The operating principle is to ship simple products that solve a concrete job and are immediately usable—not generic templates or generic AI wrappers.

## Studio operating model

The studio follows one product lifecycle:

1. Opportunity discovery across consumer, small-business and independent-professional markets.
2. Evidence collection: customer pain, workarounds, competitors, substitutes, pricing and distribution.
3. Opportunity scoring and validation experiments.
4. Product requirements, user journey and prototype.
5. MVP development in an isolated product workspace.
6. Quality assurance, privacy and usability checks.
7. Sales assets and marketplace listing preparation.
8. Explicit user approval before any public listing, payment, outreach or account change.
9. Analytics, iteration or product retirement based on actual behaviour.

The current candidates are hypotheses, not validated business opportunities. See [the opportunity scan](reports/opportunity-scan.md) and [the project plan](data/project_plan.json).

## Current technical state — important distinction

The repository currently contains a **deterministic Python workflow**, not a fully autonomous AI studio.

- `agent/main.py` collects Google News RSS discovery signals. Its current query configuration is still focused on cafés and hospitality.
- `agent/engine.py` contains five deterministic specialist handlers.
- `agent/project_manager.py` executes one eligible task per run, checks dependencies, persists state and produces reports.
- `agent/llm.py` provides a provider-neutral client and offline mock. The live client is **not connected** to specialist roles or scheduled runs.
- `agent/spend_ledger.py` protects future live calls with reservations and settlement. No live provider request or charge is enabled.
- `dashboard/` displays project plan, task, research and finance snapshots.
- `tests/` and GitHub Actions provide automated checks.

The next technical work is to implement cross-market research, evidence grading, opportunity scoring, product-specific workspaces, and eventually guarded AI role dispatch. Until those are implemented and tested, the planned roles must not be described as active autonomous agents.

## Specialist roster

| Role | Current status |
|---|---|
| Project Manager | Deterministic workflow handler |
| Market Researcher | Limited deterministic collection/organization; broad research pipeline planned |
| Business Analyst | Deterministic analysis; richer evidence scoring planned |
| Product Strategist | Deterministic candidate comparison; validation workflow planned |
| Product Designer | Planned |
| Developer | Planned |
| Quality Controller | Deterministic evidence checks; product QA pipeline planned |
| Growth & Launch | Planned |

## Product portfolio

Discovery is deliberately open across three segments:

- **B2C:** personal-finance decision tools, low-friction life-admin tools, modular wedding planning.
- **B2B:** micro-business admin workflows, focused operations tools, café/hospitality tools.
- **Prosumer:** freelancer scope/pricing tools and creator workflow utilities.

These examples are research candidates only. The studio must compare them using evidence and buildability rather than choosing based on personal preference or trend articles.

## Budget, privacy and approval gates

- Initial project budget: €0–50; preferred recurring cost: ≤€10/month.
- No paid API, subscription, domain, hosting change, credit purchase or other spending without explicit approval.
- No customer outreach or public publishing without explicit approval.
- Keep source, research and product work private until a specific launch is approved.
- Do not treat marketplace search volume, competitor existence or anecdotal posts as proof of sales or willingness to pay.
- GitHub Actions usage remains subject to the GitHub account plan and limits.
- Netlify auto-publishing remains locked. The €9 plan upgrade is a recorded expense; verify renewal terms before recommending further use.

## Local test

```bash
python -m unittest discover -s tests -v
```

## Scheduled workflow

GitHub Actions runs the bounded workflow on its configured schedule or by manual dispatch. It runs tests, collects RSS signals, executes one Project Manager task, syncs snapshots and commits changed state. The workflow does not make paid LLM calls, contact customers or publish products.

See [docs/DIGITAL_PRODUCT_STUDIO.md](docs/DIGITAL_PRODUCT_STUDIO.md) for the architecture and implementation roadmap.
