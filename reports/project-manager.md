# Project Manager — Online Passive Income

**Last cycle:** 2026-11-13T13:21:18.464346+00:00

**Goal:** Build an AI-assisted Digital Product Studio that discovers, validates, designs, builds, tests, prepares and (with explicit approval) publishes digital products across B2C, B2B and prosumer markets, targeting €1,000/month within five years.

## Execution status

- Completed: 34 | Queued: 1 | Running: 0 | Blocked: 1 | Failed: 0
- Project Manager cycles: 65
- Last task: None (no_eligible_tasks)

## Specialist registry

- **Project Manager** — Prioritises work, dependencies, continuity and execution limits.
- **Market Researcher** — Organises sourced competitor and customer evidence.
- **Business Analyst** — Compares pricing, customer pain, economics and evidence strength.
- **Product Strategist** — Compares hypotheses and designs low-cost validation experiments.
- **Quality Controller** — Audits sources, evidence limits and unsupported conclusions.

## Phases

- **0. Existing workflow foundation** — completed: Private repository, deterministic orchestration, scheduled RSS discovery, reports, dashboard and spend guardrails; this is not yet an autonomous LLM studio.
- **1. Cross-market opportunity discovery** — completed: Scan B2C, B2B and prosumer markets; collect competitor, pricing, pain-point and substitute evidence; score evidence quality.
- **2. Demand validation and opportunity selection** — completed: Narrow the best candidates, identify target users, test current workarounds and willingness to pay before committing to a build.
- **3. Product requirements and design** — completed: Create a concise PRD, user journey, prototype, acceptance criteria and smallest useful MVP.
- **4. Product development** — completed: Build a working product in its own product folder with reproducible setup and documentation.
- **5. Quality assurance** — blocked: Test core flows, edge cases, accessibility, mobile usability, privacy and reliability.
- **6. Sales and launch assets** — planned: Prepare product name, positioning, screenshots, instructions, pricing hypothesis, support and listing copy.
- **7. Approval and publication** — planned: Review platform fees, tax/VAT, privacy and listing details; publish only after explicit user approval.
- **8. Analytics and iteration** — planned: Measure visits, conversion, refunds, support and revenue; improve, reposition or stop products based on evidence.
- **9. Autonomous studio capability** — completed: Implement and integrate guarded role-based AI dispatch with offline default, structured outputs, human approval gates, spend enforcement, persistence and evaluations. Live paid inference remains disabled until explicit approval.

## Task queue

- **AB-001 · Create central specialist registry and guarded Agent Brain dispatcher** — done · project_manager
  - Latest: Implemented agent/brain.py with nine specialist roles, common dispatch contract, fail-closed JSON validation and offline mock default. Live calls are not enabled.
- **AB-002 · Add Agent Brain safety, role coverage and contract tests** — done · quality_controller
  - Latest: Added tests/test_brain.py with fake-client tests; no network calls or paid services.
- **AB-003 · Integrate guarded Agent Brain dispatch into Project Manager** — done · developer
  - Latest: Project Manager now has an explicit dispatch seam: tasks may be routed through the guarded AgentBrain interface; deterministic handlers remain the default and offline mock output cannot complete real work.
- **AB-004 · Connect live LLM dispatch to spend ledger and approval configuration** — done · developer
  - Latest: Live LLM remains disabled by default; runtime credentials, persistent ledger reservation, settlement and pre-network budget tests are present.
- **AB-005 · Build specialist evaluation suite and evidence-quality tests** — done · quality_controller
  - Latest: Role-specific contract fixtures and evidence-provenance evaluation tests are registered. These validate interface discipline, not live model reasoning quality.
- **AB-006 · Run end-to-end Agent Brain workflow and document autonomy limits** — done · project_manager
  - Latest: End-to-end tests cover queued/in-progress task recovery, guarded specialist dispatch, persisted mock draft and human-review blocking.
- **AB-007 · Build bounded specialist tool-call runtime** — done · developer
  - Latest: Bounded JSON tool-call runtime is implemented with an allowlisted registry, argument validation, approval gates, hard step/output limits and AgentBrain final-output validation.
- **AB-008 · Add safe source-retrieval tools and evidence provenance** — done · market_researcher
  - Latest: Read-only public-source retrieval is implemented with HTTPS and public-IP checks, redirect refusal, response bounds and explicit ungraded evidence metadata.
- **AB-009 · Add sandboxed workspace editing and test execution tools** — done · developer
  - Latest: Temporary proposal workspace tools are implemented with path allowlists, repository-isolated edits, allowlisted test modules and execution timeouts.
- **AB-010 · Integrate autonomous multi-step specialist orchestration** — done · project_manager
  - Latest: Checkpointed multi-specialist orchestration is implemented with bounded workflows, role validation, recovery and human-review gates.
- **AB-011 · Build explicitly approved live studio composition root** — done · developer
  - Latest: A live studio composition root now requires explicit host approval, an explicit live flag, runtime credentials, verified token pricing and a monthly spend ledger; construction itself makes no provider call.
- **AB-012 · Integrate default-off autonomous dispatch into Project Manager** — done · project_manager
  - Latest: Project Manager now has a default-off autonomous dispatch path with explicit approval, persisted checkpoints and mandatory human review of specialist drafts.
- **AB-013 · Enforce role-specific tool permissions and audit boundaries** — done · quality_controller
  - Latest: Specialist tool permissions are now enforced by role at both discovery and invocation; cross-role access fails closed.
- **AB-014 · Run full offline autonomy integration and recovery suite** — done · quality_controller
  - Latest: Offline end-to-end fixtures cover multi-role tool execution, role permission boundaries, checkpoint persistence, interruption and resume without paid provider calls.
- **AB-015 · Audit public source retrieval against DNS rebinding and transport risks** — done · quality_controller
  - Latest: Public-source retrieval now pins the HTTPS socket to a validated public IP while preserving hostname TLS verification, preventing DNS rebinding between validation and connection.
- **DS-001 · Run initial cross-market opportunity scan across B2C, B2B and prosumer** — done · market_researcher
  - Latest: Completed a first desk-research scan. Identified eight candidates across B2C, B2B and prosumer; this is directional evidence only, not validation or proof of sales.
- **PM-001 · Build persistent Project Manager and specialist role registry** — done · project_manager
- **AB-016 · Implement and verify one-time human approval queue for external actions** — done · quality_controller
  - Latest: A persistent, expiring, payload-hash-bound, one-time human approval queue is covered by offline security and lifecycle tests; it records approvals but does not execute external actions.
- **AB-017 · Connect cross-market RSS discovery to a provenance-aware evidence store** — done · market_researcher
  - Latest: RSS discovery now feeds a persistent provenance-aware evidence store; leads remain explicitly unverified until inspected and graded.
- **DS-002 · Build comparable opportunity scorecard and rank candidates** — done · business_analyst
  - Latest: Created a qualitative, evidence-confidence-aware comparison. No numerical market-size or sales claims were inferred from search results.
- **AB-018 · Join safe source retrieval to the evidence ledger with reviewable provenance** — done · market_researcher
  - Latest: A role-scoped research tool now fetches the exact public HTTPS URL for a known discovery record and stores a bounded, hash-addressed excerpt while preserving Unverified status.
- **AB-019 · Integrate durable specialist orchestration and evidence tools into Project Manager** — done · project_manager
  - Latest: Project Manager now persists specialist checkpoints after every handoff, reloads them on resume, and injects the provenance-aware evidence store into the approved research tool registry. Scheduled execution still supplies no live approval and all outputs remain subject to human review.
- **AB-020 · Build cross-role specialist evaluation and adversarial quality gates** — done · quality_controller
  - Latest: Cross-role structural quality and safety gates passed for all nine registered roles. These are offline contract tests, not semantic model-quality benchmarks.
- **DS-003 · Deep-dive top three opportunities and identify validation experiments** — done · market_researcher
  - Latest: Deep-dived freelancer scope changes, micro-business invoice follow-up and wedding workflows. Competitors/free alternatives are material in all three.
- **MR-001 · Map direct competitors and substitutes for café starter kit** — done · market_researcher
  - Latest: Initial sourced competitor scan saved: 6 café template products/substitutes. See data/market_research.json; this is discovery evidence, not proof of sales.
- **MR-002 · Map direct competitors and substitutes for ShiftBrief AI** — done · market_researcher
  - Latest: Mapped six handover/logbook competitors and substitutes; official pricing pages checked for ShiftForce, Shifo, Venheim and Rotahr. See data/market_research.json and reports/market-research.md.
- **DS-004 · Recommend one first MVP based on evidence and buildability** — done · product_strategist
  - Latest: Selected ScopeSnap as the first low-cost MVP hypothesis: a no-login scope-change estimator and client-ready approval brief. Rationale: repeated first-hand pain signals, narrow build, immediate utility, no integrations or sensitive data required. Confidence remains low-to-moderate until user testing.
- **BA-001 · Compare competitor pricing and business models** — done · business_analyst
  - Latest: Compared visible one-time/free/subscription price anchors. Prices differ by currency, tax, venue/team size and scope; some older observations remain flagged for recheck.
- **DS-005 · Create product-specific workspace and product requirements** — done · product_designer
  - Latest: Created product workspace, PRD and an initial working browser prototype. Product is a testable hypothesis, not a validated or published product.
- **BA-002 · Identify recurring customer complaints and unmet needs** — done · business_analyst
  - Latest: Added first-hand/community discussion evidence for café stock consistency, staffing/owner overload and food waste, plus a hotel shift-handover example where buried notes led to forgotten guest requests. Evidence remains anecdotal and does not establish willingness to pay.
- **DS-006 · Build the first usable MVP** — done · developer
  - Latest: Created a self-contained browser MVP at products/scopesnap/app/index.html. No backend, external library, paid API, account or persistent data storage. Local test instructions included.
  - Next action: Register a handler and acceptance checks before scheduling this task.
- **DS-007 · Test MVP and fix release-blocking issues** — blocked · quality_controller
  - Latest: No safe executor is registered for DS-007.
  - Next action: Register a handler and acceptance checks before scheduling this task.
- **PS-001 · Compare the two hypotheses and choose the cheapest demand test** — done · product_strategist
  - Latest: Compared both hypotheses. Willingness to pay is not demonstrated for either; recommend discovery interviews before choosing or building.
- **DS-008 · Prepare sales page and marketplace listing package** — queued · growth_launch
  - Latest: Drafted listing copy, untested pricing hypothesis and participant usability-test script. No platform selected and nothing published.
- **DS-009 · Obtain explicit approval and publish first product** — planned · project_manager
- **QC-001 · Quality review of market evidence and recommendation** — done · quality_controller
  - Latest: Quality review passed. Evidence is explicitly labelled anecdotal and no paid service is required.
- **DS-010 · Review launch metrics and decide iteration** — planned · business_analyst
- **PM-002 · Prepare first product MVP scope and launch roadmap** — done · project_manager
  - Latest: Prepared a no-cost validation-first roadmap; product implementation remains gated on customer evidence and explicit approval.

## Agent architecture and limits

- Deterministic specialist handlers run without paid LLM/API services.
- One task is executed per invocation; task results and a bounded event log are persisted.
- Failed tasks may retry up to three times; blocked tasks require new evidence or a deliberate plan change.
- No paid services, publishing, customer outreach or external commitments are permitted automatically.
- Research findings are evidence signals, not proof of demand or revenue.
