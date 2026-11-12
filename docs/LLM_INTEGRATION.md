# LLM integration plan

## Current implementation

`agent/llm.py` adds a provider-neutral request/response contract, an offline
mock client, explicit live-configuration validation, token-price estimation
and fail-closed per-request limits.

`OpenAICompatibleClient` is now implemented for future explicit use, with HTTPS-only endpoints, an explicitly supplied runtime API key, bounded timeouts, response validation and usage-based cost reporting. **It is not called by the Project Manager or scheduled workflow.** Tests mock the HTTP response; no real provider is contacted.

## Safety defaults

- Live use is disabled by default.
- No API key is read, requested, stored or transmitted.
- This module makes no network requests.
- Live configuration requires provider, endpoint, model, verified input/output
  token prices and a positive per-call USD cap.
- Prompt character and maximum output-token limits are checked before a
  future provider request.
- The cost estimate is a planning guard, not a guaranteed invoice ceiling:
  provider tokenization and billing can differ.

## Next engineering steps

1. Select a provider only after checking official current prices, model ID,
   structured-output support, rate limits, privacy terms and EU data handling.
2. Before any live call, choose one provider and model and verify its official current price and API compatibility. Supply its key only at runtime through a secret store; never commit it to the repository.
3. Add mocked HTTP tests for success, timeout, malformed JSON, provider errors
   and missing credentials.
4. Add a persistent monthly spend ledger and hard monthly ceiling before
   enabling any live call.
5. Benchmark identical tasks and evidence snapshots for correctness, source
   discipline, JSON validity, latency and actual billed cost.
6. Enable live mode only after explicit user approval.

## Benchmark protocol

Use synthetic or public business examples only. Do not send private personal,
shelter, health or account information. Compare factual accuracy, source
traceability, distinction between evidence and assumptions, usefulness,
structured-output validity, latency and actual cost.

A mock response is never market evidence and must never be written into
`data/market_research.json` as a real finding.
