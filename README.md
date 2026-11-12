# Digital Income Agent

Cloud-based autonomous project-management and research system for the **Online Passive Income** project.

## Main Project Manager

On each scheduled or manual GitHub Actions run, the Project Manager:
1. Loads the saved project plan and previous state.
2. Checks unfinished tasks and dependencies.
3. Selects the highest-priority eligible task.
4. Invokes the relevant specialist role.
5. validates the result or marks the task as blocked when required evidence/tools are unavailable.
6. Saves state and progress.
7. Keeps the next tasks in the persistent queue.

## Specialist roles

- **Market Researcher** — competitors, products and market opportunities.
- **Business Analyst** — pricing, demand signals, reviews and unit economics.
- **Product Strategist** — product hypotheses and low-cost validation experiments.
- **Quality Controller** — evidence quality, source checks and unsupported claims.
- **Project Manager** — priorities, dependencies, task queue and continuity.

## Five implementation stages

1. Cloud infrastructure — private GitHub repository, persistent files and cloud execution.
2. Agent brain — orchestration, specialist roles, memory, task queue and resume logic.
3. Automated research — search/browser automation, evidence capture and source verification.
4. Scheduling and reports — bounded daily cycles, saved results and notifications.
5. Management dashboard — display actual agent progress and project data.

## Current limitations and safety

The GitHub runner currently collects Google News RSS signals and runs the task orchestrator. It does **not** yet have an approved live browser/search integration, so tasks requiring competitor pages, current prices, customer reviews or source verification are explicitly blocked instead of being fabricated. Those findings can be added after evidence-backed research in the assistant session.

No paid API, subscription, server or domain is enabled. No product publication, customer outreach or paid action occurs without explicit approval.

## Main files

- `agent/main.py` — RSS signal collection.
- `agent/project_manager.py` — persistent task orchestration and specialist role registry.
- `data/state.json` — saved execution and research state.
- `data/project_plan.json` — persistent project phases and task queue.
- `reports/latest.md` — research signals report.
- `reports/project-manager.md` — current project dashboard and task status.
- `.github/workflows/daily-agent.yml` — cloud schedule and execution.
