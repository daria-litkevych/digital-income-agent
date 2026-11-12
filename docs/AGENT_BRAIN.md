# Agent Brain — implementation contract

## Purpose

Agent Brain is the guarded intelligence layer between the Project Manager and specialist roles. It does not replace deterministic workflow controls. It provides role-specific instructions, structured outputs, evidence discipline and a permission boundary.

## Implemented in this milestone

- A central role registry for Project Manager, Market Researcher, Business Analyst, Product Strategist, Product Designer, Developer, Quality Controller, Growth & Launch and Analytics.
- A common dispatch contract and JSON output validation.
- An injected provider interface using the existing `LLMClient` protocol.
- An offline mock default that is explicitly labelled as mock and cannot be mistaken for research or work completion.
- Rejection of tasks requesting publishing, outreach, purchases, billing changes or other external side effects.
- Fail-closed handling for malformed or incomplete model responses.
- Tests using fake clients; tests do not send network requests.
- Explicit live-client approval gate: a live-capable client is refused unless the dispatcher is constructed with approval.
- Monthly spend reservations use the full configured per-call ceiling before network use, then settle provider-reported usage.
- Per-role artifact sections are restricted by role; evidence URLs must match URLs present in supplied context.
- Nine role-specific evaluation fixtures and end-to-end tests cover persistence, recovery and the rule that offline mock output cannot complete work.

## Not enabled

- The scheduled workflow does not call a live LLM.
- No API key, provider, endpoint, paid call or automatic top-up is configured.
- The live client remains disabled unless the user explicitly approves a provider, price, hard cap and credential setup.
- Bounded tool-call runtime exists, with explicit registry, argument validation, approval checks and step/output limits.
- Read-only public-source retrieval exists for supplied HTTPS URLs, with public-IP checks, redirect refusal and response bounds. It does not discover URLs itself and fetched content remains ungraded.
- Temporary workspace tools exist for allowlisted file proposals and named test modules. They do not modify the checked-out repository and are not an OS security sandbox.
- A checkpointed multi-specialist coordinator exists with resume support and human-review gates.
- These adapters are not yet connected as production tools in the scheduled Project Manager cycle. Live inference remains disabled; therefore this is not yet an autonomous studio.

## Definition of done for Agent Brain

1. Role registry covers the studio lifecycle.
2. A common dispatcher can invoke a supplied LLM client with role-specific system instructions.
3. Structured output is validated and invalid output is rejected.
4. Offline mode is the default and is visibly labelled.
5. Side effects require approval and cannot be executed by model output.
6. Budget enforcement and actual token settlement protect live calls.
7. Each role has task-specific tools, evidence contracts and evaluations.
8. Safe research and workspace tools are integrated with role permissions, provenance and execution limits.
9. The Project Manager coordinates multi-step role handoffs, persists checkpoints and resumes safely.
10. End-to-end tests prove a complete task cycle without unapproved network calls or spending.

Items 1–7 have code or test coverage as a guarded foundation. Bounded tool adapters and a checkpointed coordinator have also been added, but they are not yet integrated into scheduled Project Manager execution. Live inference is disabled. The studio must not be described as autonomous until the full tool permissions, source provenance, persistence, recovery and end-to-end handoff are integrated and tested.
