"""Persistent Project Manager for the Digital Income Agent."""
from __future__ import annotations

from pathlib import Path
import json
import hashlib

from agent.engine import ROLES, apply_result, execute, select_task, utc_now
from agent.brain import build_offline_brain

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "data" / "state.json"
PLAN_FILE = ROOT / "data" / "project_plan.json"
EVIDENCE_FILE = ROOT / "data" / "market_research.json"
REPORT_FILE = ROOT / "reports" / "project-manager.md"
CHECKPOINT_DIR = ROOT / "data" / "agent_checkpoints"
MAX_ATTEMPTS = 3
DEFAULT_BRAIN = build_offline_brain()

def dispatch_task(task, state, evidence, brain=None, *, autonomous_approval=False, env=None):
    """Route tasks to deterministic handlers, guarded Brain drafts or approved autonomy."""
    if task.get("kind") == "agent_evaluation":
        from agent.quality_gates import evaluate
        return evaluate(ROOT)

    if task.get("dispatch_to_autonomous_studio"):
        if autonomous_approval is not True:
            return {
                "ok": False, "blocked": True,
                "summary": "Autonomous studio execution is disabled in the Project Manager; explicit human approval was not supplied.",
                "next_action": "Obtain explicit approval for provider, verified token prices, per-call cap, monthly cap and credentials before a live run.",
            }
        from agent.autonomous_studio import build_live_studio
        workflow_steps = task.get("workflow_steps", [])
        workflow_id = str(task.get("id", "autonomous-task"))
        if not workflow_id.strip() or len(workflow_id) > 120:
            return {
                "ok": False, "blocked": True,
                "summary": "Autonomous workflow ID is missing or exceeds the allowed length.",
                "next_action": "Use a stable workflow task ID of at most 120 characters.",
            }
        checkpoint_name = hashlib.sha256(workflow_id.encode("utf-8")).hexdigest() + ".json"
        checkpoint_dir = ROOT / "data" / "agent_checkpoints"
        checkpoint_path = checkpoint_dir / checkpoint_name
        def load_checkpoints():
            return load_json(checkpoint_path, {})
        def save_checkpoints(updated):
            # Persist after every specialist handoff, not only at PM cycle end.
            save_json(checkpoint_path, updated)
        studio = build_live_studio(
            ROOT,
            checkpoint_loader=load_checkpoints,
            checkpoint_saver=save_checkpoints,
            approval_confirmed=True,
            env=env,
        )
        try:
            result = studio.orchestrator.run(
                str(task.get("id", "autonomous-task")),
                workflow_steps,
                {"project_state": state, "evidence": evidence},
            )
        finally:
            studio.close()
        if result.get("status") == "review_required":
            return {"ok": False, "blocked": True, "summary": "Autonomous specialist drafts are ready for human review; the Project Manager will not mark this task complete.", "artifact": result, "next_action": "Review all specialist drafts and evidence before accepting any result."}
        return {"ok": False, "blocked": True, "summary": result.get("reason", "Autonomous studio did not complete the workflow."), "artifact": result, "next_action": "Resolve the blocked step and explicitly approve a later run."}

    if not task.get("dispatch_to_brain"):
        return execute(task, state, evidence)
    selected_brain = brain or DEFAULT_BRAIN
    output = selected_brain.dispatch(
        task.get("role", ""),
        task.get("title", "Execute specialist task"),
        {"task": task, "project_state": state, "evidence": evidence},
    )
    # Drafts from a model are never auto-marked as completed work.
    return {
        "ok": False,
        "blocked": True,
        "summary": "Agent Brain returned a draft requiring review; no task was auto-completed.",
        "artifact": {"agent_brain_output": output},
        "next_action": "Review the structured draft, evidence and risks before accepting it as task output.",
    }
def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise RuntimeError(f"Cannot safely load {path}: {error}") from error

def atomic_write_text(path, content):
    """Atomically replace a text file after the complete new content is written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(path)

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)

def refresh_phases(plan):
    for phase in plan.get("phases", []):
        phase_tasks = [t for t in plan.get("tasks", []) if t.get("phase") == phase.get("id")]
        if not phase_tasks:
            continue
        if any(t.get("status") == "blocked" for t in phase_tasks):
            phase["status"] = "blocked"
        elif any(t.get("status") == "failed" for t in phase_tasks):
            phase["status"] = "in_progress"
        elif all(t.get("status") == "done" for t in phase_tasks):
            phase["status"] = "completed"
        elif any(t.get("status") in {"in_progress", "done"} for t in phase_tasks):
            phase["status"] = "in_progress"
        else:
            phase["status"] = "planned"

def render_report(plan, state, record):
    tasks = plan.get("tasks", [])
    counts = {status: sum(1 for t in tasks if t.get("status") == status) for status in ["done", "queued", "in_progress", "blocked", "failed"]}
    lines = [
        "# Project Manager — Online Passive Income", "",
        f"**Last cycle:** {record['timestamp']}", "",
        f"**Goal:** {plan.get('goal', '')}", "",
        "## Execution status", "",
        f"- Completed: {counts['done']} | Queued: {counts['queued']} | Running: {counts['in_progress']} | Blocked: {counts['blocked']} | Failed: {counts['failed']}",
        f"- Project Manager cycles: {state.get('pm_run_count', 0)}",
        f"- Last task: {record.get('task_id') or 'None'} ({record.get('status')})", "",
        "## Specialist registry", ""
    ]
    for role, description in ROLES.items():
        lines.append(f"- **{role.replace('_', ' ').title()}** — {description}")
    lines += ["", "## Phases", ""]
    for phase in plan.get("phases", []):
        lines.append(f"- **{phase['id']}. {phase['name']}** — {phase['status']}: {phase['goal']}")
    lines += ["", "## Task queue", ""]
    for task in sorted(tasks, key=lambda x: (-int(x.get("priority", 0)), x.get("id", ""))):
        lines.append(f"- **{task.get('id')} · {task.get('title')}** — {task.get('status')} · {task.get('role')}")
        if task.get("last_result"):
            lines.append(f"  - Latest: {task['last_result']}")
        if task.get("next_action"):
            lines.append(f"  - Next action: {task['next_action']}")
    lines += [
        "", "## Agent architecture and limits", "",
        "- Deterministic specialist handlers run without paid LLM/API services.",
        "- One task is executed per invocation; task results and a bounded event log are persisted.",
        "- Failed tasks may retry up to three times; blocked tasks require new evidence or a deliberate plan change.",
        "- No paid services, publishing, customer outreach or external commitments are permitted automatically.",
        "- Research findings are evidence signals, not proof of demand or revenue.", ""
    ]
    return "\n".join(lines)

def main():
    plan = load_json(PLAN_FILE, {"name": "Online Passive Income", "tasks": [], "phases": []})
    state = load_json(STATE_FILE, {"agent_name": "Digital Income Agent", "run_count": 0})
    evidence = load_json(EVIDENCE_FILE, {})
    if not isinstance(plan.get("tasks"), list):
        raise RuntimeError("project_plan.json must contain a tasks array")

    # Recover interrupted work safely. It returns to the queue, not to done.
    # AB-020 was blocked only because its deterministic evaluator was not registered.
    # Re-queue that one known task now that the safe handler is available.
    for task in plan["tasks"]:
        if task.get("id") == "AB-020" and task.get("status") == "blocked" and "No safe executor is registered" in str(task.get("blocked_reason", "")):
            task["status"] = "queued"
            task.pop("blocked_reason", None)
            task.pop("next_action", None)
            task["last_result"] = "Re-queued after registering the offline cross-role quality gate evaluator."
    for task in plan["tasks"]:
        if task.get("status") == "in_progress":
            task["status"] = "queued"
            task["recovered_at"] = utc_now()

    state["project_plan"] = plan
    selected = select_task(plan["tasks"])
    timestamp = utc_now()
    if selected:
        selected["status"] = "in_progress"
        selected["started_at"] = timestamp
        state["project_plan"] = plan
        result = dispatch_task(selected, state, evidence)
        event = apply_result(selected, result, state)
        if selected.get("status") == "failed" and selected.get("attempts", 0) >= MAX_ATTEMPTS:
            selected["status"] = "blocked"
            selected["blocked_reason"] = f"Retry limit reached after {MAX_ATTEMPTS} attempts."
            selected["next_action"] = "Review the error and explicitly re-queue after fixing the cause."
            event["status"] = "blocked"
        record = dict(event)
    else:
        record = {"timestamp": timestamp, "task_id": None, "status": "no_eligible_tasks", "summary": "No queued or retryable task has all dependencies completed."}
        state.setdefault("event_log", []).append(record)
        state["event_log"] = state["event_log"][-500:]

    refresh_phases(plan)
    state["pm_run_count"] = int(state.get("pm_run_count", 0)) + 1
    state["pm_last_cycle"] = record
    state["project_manager_status"] = "operational"
    state["specialist_roles"] = ROLES
    state["project_plan"] = plan
    state["last_run_utc"] = utc_now()
    save_json(PLAN_FILE, plan)
    save_json(STATE_FILE, state)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(REPORT_FILE, render_report(plan, state, record))
    print(json.dumps(record, ensure_ascii=False))
    print(f"Saved plan, state and report. Selected task: {record.get('task_id')}")

if __name__ == "__main__":
    main()
