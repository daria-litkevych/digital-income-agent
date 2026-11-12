# LLM integration plan

## Current implementation

- `agent/llm.py` defines the provider-neutral request/response contract,
  deterministic offline mock, explicit live settings, request-size checks,
  cost preflight and an OpenAI-compatible HTTPS client.
- The live client is **not connected** to Project Manager, specialist roles or
  the scheduled workflow. Default execution remains offline.
- `agent/spend_ledger.py` provides a transactional SQLite monthly spend
  ledger. It reserves estimated cost before a call and replaces the
  reservation with actual reported cost after settlement. Unsettled
  reservations continue to consume budget, which is intentionally fail-safe.
- The ledger is not yet wired into `OpenAICompatibleClient`; no live use is
  authorized until this integration is completed and tested.
- `benchmarks/cases.json` contains four synthetic specialty-café tasks.
  `python -m agent.benchmark` runs them with the offline mock by default.
  The report labels mock output and leaves human scoring blank.

## Safety defaults

- Live use is disabled by default and no API key is read from environment or
  repository files.
- The scheduled workflow does not call an LLM provider.
- A future live caller must explicitly supply enabled settings and a runtime
  API key, use HTTPS, set verified input/output prices and obey per-call
  request limits.
- The cost preflight is an estimate, not a guaranteed invoice ceiling.
  Provider tokenization, retries, taxes and billing rules may differ.
- Monthly reservations are a second guard, not a substitute for provider-side
  spending limits. A crash leaves a reservation committed until reconciled.
- Never send private personal, shelter, health, account or customer-identifying
  data to a benchmark provider.

## Benchmark protocol

Use the same synthetic task set and identical prompt snapshots for each model.
Review each response manually against the expected behaviours in the dataset.
Score each dimension from 0 to 2:

| Dimension | 0 | 1 | 2 |
|---|---|---|---|
| Factual discipline | Invents or contradicts facts | Minor unsupported detail | Uses only supplied facts |
| Completeness | Misses critical items | Partial coverage | Covers all expected behaviours |
| Uncertainty | Hides unknowns | Some uncertainty retained | Clearly preserves unknowns |
| Actionability | Unusable | Needs editing | Clear and ready to use |
| Format | Does not follow task | Minor formatting issues | Follows requested structure |

Also record actual provider/model ID, input/output tokens, reported cost,
latency, errors and any safety failures. Do not treat synthetic benchmark
scores as customer demand or product-market fit. A model response is never
market evidence and must not be written into `data/market_research.json`.

## Remaining gates before live use

1. Verify one provider's official current model ID, prices, rate limits,
   API compatibility, privacy terms and EU data-processing terms.
2. Wire the monthly ledger into the request lifecycle: reserve before network
   I/O, settle from provider usage, retain failed/unsettled reservations, and
   ensure duplicate request IDs cannot be charged twice.
3. Add tests for timeout, HTTP errors, malformed responses, settlement,
   concurrent reservations and monthly rollover.
4. Run offline tests and inspect benchmark reports.
5. Obtain explicit approval for the provider, model and maximum monthly
   spend before configuring any runtime key or making a live request.

No signup, key creation, payment, provider call, customer outreach or public
publishing is part of this implementation.
