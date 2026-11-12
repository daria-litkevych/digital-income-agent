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
- A checkpointed multi-specialist coordinator exists with resume support and human-review gates.\n- The Project Manager writes each specialist checkpoint atomically to a workflow-specific file under `data/agent_checkpoints/`, so a process restart can reload completed steps rather than relying on end-of-cycle state persistence.\n- The live composition root injects the persistent evidence store into role-scoped research tools; source retrieval still occurs only when a live specialist explicitly calls a supplied-URL tool.
- A persistent JSON approval-request queue now supports expiry, payload-hash matching, secret-like field rejection and one-time consumption. It records approval state only; it does not authenticate a person or execute an external action.
- The live orchestration path is now connected to Project Manager behind a trusted explicit approval argument, with durable per-step checkpoints and the evidence store available to the read-only research tool registry. The scheduled workflow does not supply that approval and remains deterministic. Live inference remains disabled by default; this is not yet a production autonomous studio.

## Definition of done for Agent Brain

1. Role registry covers the studio lifecycle.
2. A common dispatcher can invoke a supplied LLM client with role-specific system instructions.
3. Structured output is validated and invalid output is rejected.
4. Offline mode is the default and is visibly labelled.
5. Side effects require approval and cannot be executed by model output.
6. Budget enforcement and actual token settlement protect live calls.
7. Each role has task-specific tools, evidence contracts and evaluations.
8. Safe research and workspace tools are integrated with role permissions, provenance and execution limits.
9. The Project Manager coordinates multi-step role handoffs behind a trusted approval gate, persists each checkpoint atomically and resumes safely.
10. End-to-end tests prove a complete task cycle without unapproved network calls or spending.

Items 1–7 have code or test coverage as a guarded foundation. Bounded tool adapters, a checkpointed coordinator and a separately tested approval-request queue have also been added, but the queue is not connected to an authenticated external-action executor and the specialist toolchain is not integrated into scheduled Project Manager execution. The JSON approval queue is not concurrency-hardened and does not authenticate a human. The live execution path is approval-gated but no provider credentials or prices are configured. Live inference is disabled in scheduled runs. The studio must not be described as autonomous until source discovery/evidence storage, authenticated human approval, safe external-action execution, persistence, recovery and end-to-end scheduled handoff are integrated and tested.
