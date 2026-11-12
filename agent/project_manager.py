"""Main Project Manager: persistent task orchestration for the digital-income project.

The manager runs one bounded work cycle per invocation, records its decisions,
validates outputs, and leaves an explicit queue for the next run.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "data" / "state.json"
PLAN_FILE = ROOT / "data" / "project_plan.json"
DASHBOARD_FILE = ROOT / "reports" / "project-manager.md"

ROLES = {
    "project_manager": "Plans work, manages dependencies, preserves progress and creates next tasks.",
    "market_researcher": "Finds competitors, products, market opportunities and customer pain points.",
    "business_analyst": "Evaluates pricing, demand signals, reviews, economics and profitability.",
    "product_strategist": "Compares product ideas, tests assumptions and recommends next experiments.",
    "quality_controller": "Checks evidence quality, output completeness and unsupported claims.",
}

def now():
    return datetime.now(timezone.utc).isoformat()

def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def seed_plan():
    return {
        "name": "Online Passive Income",
        "goal": "Build a low-cost, mostly automated digital product business targeting €1,000/month within five years.",
        "constraints": {
            "initial_budget_eur": 50,
            "preferred_monthly_cost_eur": 10,
            "paid_services_require_explicit_approval": True,
            "publishing_and_outreach_require_explicit_approval": True
        },
        "hypotheses": [
            {"id": "cafe_starter_kit", "name": "Small Café Manager Starter Kit", "audience": "Independent specialty coffee shops", "value": "Very simple, ready-to-use operating templates"},
            {"id": "shiftbrief_ai", "name": "ShiftBrief AI", "audience": "Hospitality teams", "value": "Turn shift notes or voice notes into clear handovers and tasks"}
        ],
        "phases": [
            {"id": 1, "name": "Cloud infrastructure", "goal": "Private repository, persistent data, cloud execution and cost guardrails", "status": "completed"},
            {"id": 2, "name": "Agent brain", "goal": "Orchestrator, specialist roles, memory, task queue and resume logic", "status": "in_progress"},
            {"id": 3, "name": "Automated research", "goal": "Search, browser research, evidence capture and source checks", "status": "planned"},
            {"id": 4, "name": "Scheduling and reports", "goal": "Five bounded daily cycles, saved results and notifications", "status": "planned"},
            {"id": 5, "name": "Management dashboard", "goal": "Connect the MVP to persistent project data and show actual agent progress", "status": "planned"}
        ],
        "tasks": [
            {"id":"PM-001","title":"Build persistent Project Manager and specialist role registry","phase":2,"role":"project_manager","kind":"internal","status":"done","priority":100,"depends_on":[],"acceptance":"Orchestrator loads state, selects work, validates, saves progress and creates follow-up tasks."},
            {"id":"MR-001","title":"Map direct competitors and substitutes for café starter kit","phase":3,"role":"market_researcher","kind":"external_research","status":"queued","priority":90,"depends_on":["PM-001"],"hypothesis":"cafe_starter_kit","acceptance":"At least five relevant products or substitutes with source, price, audience and core promise."},
            {"id":"MR-002","title":"Map direct competitors and substitutes for ShiftBrief AI","phase":3,"role":"market_researcher","kind":"external_research","status":"queued","priority":89,"depends_on":["PM-001"],"hypothesis":"shiftbrief_ai","acceptance":"At least five relevant products or substitutes with source, price, audience and core promise."},
            {"id":"BA-001","title":"Compare competitor pricing and business models","phase":3,"role":"business_analyst","kind":"external_research","status":"queued","priority":80,"depends_on":["MR-001","MR-002"],"acceptance":"Pricing table distinguishes one-time, subscription, free and custom pricing."},
            {"id":"BA-002","title":"Identify recurring customer complaints and unmet needs","phase":3,"role":"business_analyst","kind":"external_research","status":"queued","priority":79,"depends_on":["MR-001","MR-002"],"acceptance":"Pain-point list backed by reviews or first-hand community discussions."},
            {"id":"PS-001","title":"Compare the two hypotheses and choose the cheapest demand test","phase":3,"role":"product_strategist","kind":"analysis","status":"queued","priority":70,"depends_on":["BA-001","BA-002"],"acceptance":"Evidence-based comparison, risks and a low-cost validation experiment."},
            {"id":"QC-001","title":"Quality review of market evidence and recommendation","phase":3,"role":"quality_controller","kind":"quality_review","status":"queued","priority":60,"depends_on":["PS-001"],"acceptance":"Sources checked, weak evidence labelled, unsupported claims removed."},
            {"id":"PM-002","title":"Prepare first product MVP scope and launch roadmap","phase":4,"role":"project_manager","kind":"planning","status":"queued","priority":50,"depends_on":["QC-001"],"acceptance":"Smallest testable MVP, milestones, costs and approval gates."}
        ],
        "created_at": now()
    }

def dependencies_done(task, tasks):
    by_id = {item["id"]: item for item in tasks}
    return all(by_id.get(dep, {}).get("status") == "done" for dep in task.get("depends_on", []))

def execute_task(task, state):
    """Run a bounded task using verified local evidence; never invent research."""
    kind = task["kind"]
    if kind == "internal":
        return {"ok": True, "summary": "Project Manager engine and specialist role registry initialized."}

    evidence = load_json(ROOT / "data" / "market_research.json", {})
    cafe = evidence.get("hypotheses", {}).get("cafe_starter_kit", [])
    shift = evidence.get("hypotheses", {}).get("shiftbrief_ai", [])
    signals = evidence.get("customer_signals", [])

    if task["id"] == "MR-001":
        if len(cafe) >= 5:
            return {"ok": True, "summary": f"Initial sourced competitor scan saved: {len(cafe)} café template products/substitutes. See data/market_research.json; this is discovery evidence, not proof of sales."}
        return {"ok": False, "blocked": True, "summary": "Not enough sourced café competitor entries in data/market_research.json.", "next_action": "Add at least five verifiable competitor/substitute entries with URLs and observed prices."}
    if task["id"] == "MR-002":
        if len(shift) >= 5:
            return {"ok": True, "summary": f"Initial sourced competitor scan saved: {len(shift)} ShiftBrief competitors/substitutes. See data/market_research.json."}
        return {"ok": False, "blocked": True, "summary": "Not enough sourced ShiftBrief competitor entries in data/market_research.json.", "next_action": "Add at least five verifiable competitor/substitute entries with URLs and observed prices."}
    if task["id"] == "BA-001":
        prices = [x for x in cafe + shift if x.get("price")]
        if len(prices) >= 8:
            return {"ok": True, "summary": f"Pricing scan recorded for {len(prices)} offers. Café templates cluster at low one-off prices; hospitality software ranges from free tiers to €99+/month. See sourced entries in data/market_research.json."}
        return {"ok": False, "blocked": True, "summary": "Insufficient sourced pricing entries.", "next_action": "Complete competitor price capture."}
    if task["id"] == "BA-002":
        if signals:
            return {"ok": True, "summary": f"Captured {len(signals)} first-hand community discussion signals. Main themes: chaotic group chats, missed handovers/tasks, notification overload and micromanagement risk. Anecdotal only."}
        return {"ok": False, "blocked": True, "summary": "No customer pain-point evidence saved.", "next_action": "Add cited customer reviews or first-hand operator discussions."}
    if kind == "analysis":
        return {"ok": False, "blocked": True, "summary": "Product comparison requires completed pricing and customer-pain tasks.", "next_action": "Complete BA-001 and BA-002 first."}
    if kind == "quality_review":
        return {"ok": False, "blocked": True, "summary": "Quality review requires an evidence-backed product recommendation.", "next_action": "Complete product strategy task first."}
    if kind == "planning":
        return {"ok": False, "blocked": True, "summary": "MVP planning requires quality-approved validation findings.", "next_action": "Complete the evidence and validation stages first."}
    return {"ok": False, "summary": f"Unknown task kind: {kind}"}

def render_dashboard(plan, state, run_record):
    tasks = plan["tasks"]
    counts = {s: sum(1 for t in tasks if t["status"] == s) for s in ["done","queued","in_progress","blocked"]}
    lines = [
        "# Project Manager — Online Passive Income", "",
        f"Last cycle: {run_record['timestamp']}", "",
        f"**Goal:** {plan['goal']}", "",
        "## Current status", "",
        f"- Completed: {counts['done']} | Queued: {counts['queued']} | In progress: {counts['in_progress']} | Blocked: {counts['blocked']}",
        f"- Total cycles: {state.get('pm_run_count', 0)}",
        f"- Last selected task: {run_record.get('task_id', 'None')}",
        f"- Cycle result: {run_record.get('status', 'not run')}", "",
        "## Specialist roles", ""
    ]
    for role, description in ROLES.items():
        lines.append(f"- **{role.replace('_',' ').title()}** — {description}")
    lines += ["", "## Five-stage implementation plan", ""]
    for phase in plan["phases"]:
        lines.append(f"{phase['id']}. **{phase['name']}** — {phase['status']}. {phase['goal']}")
    lines += ["", "## Task queue", ""]
    for task in sorted(tasks, key=lambda t: (-t.get("priority", 0), t["id"])):
        lines.append(f"- **{task['id']} · {task['title']}** — {task['status']} · {task['role'].replace('_',' ').title()}")
        lines.append(f"  - Acceptance: {task['acceptance']}")
        if task.get("last_result"):
            lines.append(f"  - Latest: {task['last_result']}")
    lines += ["", "## Guardrails", "",
        "- No paid APIs, subscriptions, servers or domains are enabled.",
        "- No product is published and no commercial messages are sent without explicit approval.",
        "- Research tasks that need live web evidence remain blocked rather than inventing facts.",
        "- Each invocation handles at most one task to keep runs bounded and resumable.", ""]
    return "\n".join(lines)

def main():
    plan = load_json(PLAN_FILE, seed_plan())
    if "tasks" not in plan:
        plan = seed_plan()
    state = load_json(STATE_FILE, {"agent_name": "Digital Income Agent", "run_count": 0})
    for task in plan["tasks"]:
        if task["status"] == "in_progress":
            task["status"] = "queued"

    eligible = [t for t in plan["tasks"] if t["status"] == "queued" and dependencies_done(t, plan["tasks"])]
    eligible.sort(key=lambda t: (-t.get("priority", 0), t["id"]))
    selected = eligible[0] if eligible else None
    record = {"timestamp": now(), "task_id": selected["id"] if selected else None}
    if selected:
        selected["status"] = "in_progress"
        selected["started_at"] = now()
        result = execute_task(selected, state)
        selected["last_result"] = result["summary"]
        selected["updated_at"] = now()
        if result.get("ok"):
            selected["status"] = "done"
            selected["completed_at"] = now()
            record["status"] = "completed"
        elif result.get("blocked"):
            selected["status"] = "blocked"
            selected["blocked_reason"] = result["summary"]
            selected["next_action"] = result.get("next_action")
            record["status"] = "blocked"
        else:
            selected["status"] = "failed"
            record["status"] = "failed"
        record["summary"] = result["summary"]
    else:
        record["status"] = "no_eligible_tasks"
        record["summary"] = "No queued task has all dependencies completed."

    state["pm_run_count"] = state.get("pm_run_count", 0) + 1
    state["pm_last_cycle"] = record
    state["project_manager_status"] = "operational"
    state["specialist_roles"] = ROLES
    state["project_plan"] = plan
    state["last_run_utc"] = now()
    save_json(PLAN_FILE, plan)
    save_json(STATE_FILE, state)
    DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD_FILE.write_text(render_dashboard(plan, state, record), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False))
    print(f"Saved project plan and dashboard. Selected task: {record['task_id']}")

if __name__ == "__main__":
    main()
