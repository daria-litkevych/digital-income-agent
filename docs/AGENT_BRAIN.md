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
- The dispatcher is still a guarded foundation, not a finished autonomous studio. Specialist work still lacks tool adapters and live tool-use loops for source retrieval, repository changes, execution and verification.

## Definition of done for Agent Brain

1. Role registry covers the studio lifecycle.
2. A common dispatcher can invoke a supplied LLM client with role-specific system instructions.
3. Structured output is validated and invalid output is rejected.
4. Offline mode is the default and is visibly labelled.
5. Side effects require approval and cannot be executed by model output.
6. Budget enforcement and actual token settlement protect live calls.
7. Each role has task-specific tools, evidence contracts and evaluations.
8. The Project Manager can route eligible tasks to the brain, persist outputs and resume safely.
9. End-to-end tests prove a complete task cycle without unapproved network calls or spending.

Items 1–8 now have code or test coverage as a guarded foundation, including budget controls, role-contract fixtures, PM routing, persistence and recovery. Item 9 is being verified by the end-to-end workflow. Actual autonomous specialist work remains incomplete because live inference is disabled and tool adapters/tool-use loops have not yet been implemented. These are distinct from the mock contract tests.
