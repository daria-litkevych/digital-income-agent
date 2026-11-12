# Digital Income Agent

A private, low-cost project agent for the **Online Passive Income** project.

## What it currently is

The repository contains a deterministic Python workflow agent. It does **not** call a paid LLM API and should not be described as a fully autonomous reasoning model. Specialist roles are implemented as auditable task handlers that read stored evidence, produce structured outputs, enforce evidence limits and persist their work.

## Architecture

- `agent/main.py` — collects Google News RSS discovery signals, deduplicates and stores them.
- `agent/engine.py` — role registry, task selection, specialist handlers, result validation, retry-safe state transitions and event logging.
- `agent/project_manager.py` — bounded orchestration: one task per run, dependency checks, interrupted-run recovery, phase progress and reports.
- `data/project_plan.json` — persistent task queue, dependencies, priorities and acceptance criteria.
- `data/state.json` — run history, specialist outputs and bounded event log.
- `data/market_research.json` — sourced competitor and qualitative customer evidence.
- `reports/` — human-readable agent and research reports.
- `dashboard/` — private project dashboard and synchronized data snapshots.
- `tests/` — standard-library unit and Project Manager integration tests.

## Execution flow

1. Run the unit test suite.
2. Collect RSS discovery signals; individual query failures are recorded without discarding successful results.
3. Load plan, state and evidence.
4. Recover interrupted tasks to the queue.
5. Select the highest-priority eligible queued/failed task whose dependencies are complete.
6. Execute its registered specialist handler and validate the output.
7. Persist result, specialist artifact, event log, task status and phase progress.
8. Sync dashboard snapshots and commit changed data.

Only one task is executed per invocation. Failed tasks can be retried up to three times; blocked tasks require a deliberate correction or new evidence before re-queuing.

## Specialist roles

- **Project Manager** — priorities, dependencies, execution limits and continuity.
- **Market Researcher** — source-linked competitor and substitute evidence.
- **Business Analyst** — pricing, customer signals, economics and evidence strength.
- **Product Strategist** — hypothesis comparison and low-cost validation design.
- **Quality Controller** — evidence limits, traceability and unsupported-claim checks.

## Important limitations

- This is a deterministic rules-based agent, not an LLM-powered agent. It cannot independently reason over arbitrary websites or browse the web beyond the RSS collector.
- RSS results are discovery signals, not validated customer demand.
- Community posts are anecdotal; they do not prove market size, willingness to pay or sales.
- The agent does not contact customers, publish products, spend money, provision paid services or change account settings.
- No paid API, subscription, server or domain is required by the current workflow.
- GitHub Actions runs on GitHub-hosted infrastructure; its usage is subject to the account's GitHub plan and limits.
- The dashboard deploy must remain private. Netlify auto-publishing is intentionally locked to prevent routine agent commits from triggering production deploys. Dashboard snapshots continue syncing in GitHub; publish manually only after an approved dashboard change. Do not move private project data to a public static host.

## Project spending and tool watchlist

- **Netlify:** The user has spent **€9** on a Netlify plan upgrade (recorded 2026-11-12). Treat this as an actual project expense, not a recurring-cost assumption; verify the current billing cycle and renewal terms before recommending further Netlify use. Auto-publishing remains locked, and no deploy/unlock or plan change is authorized without explicit approval.
- **Haimaker AI:** The user found https://haimaker.ai/ and asked whether it may be useful later. Status: **unassessed / watchlist only**. Do not integrate, subscribe, connect accounts, upload private project data, or incur costs until its current capabilities, pricing, privacy/data handling, export options and fit with the project's needs have been independently checked and the user approves.

## Local test

```bash
python -m unittest discover -s tests -v
```

## Scheduled workflow

GitHub Actions runs the bounded workflow on the configured schedule or by manual dispatch. The workflow commits updated state and dashboard snapshots when files change.
