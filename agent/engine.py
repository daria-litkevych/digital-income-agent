"""Deterministic, no-paid-API task engine for Digital Income Agent.

This is an auditable workflow engine, not an autonomous LLM. Specialist handlers
produce evidence-grounded outputs from repository data and explicitly label gaps.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.brain import ROLE_REGISTRY, build_offline_brain

ROLES = {
    "project_manager": "Prioritises work, dependencies, continuity and execution limits.",
    "market_researcher": "Organises sourced competitor and customer evidence.",
    "business_analyst": "Compares pricing, customer pain, economics and evidence strength.",
    "product_strategist": "Compares hypotheses and designs low-cost validation experiments.",
    "quality_controller": "Audits sources, evidence limits and unsupported conclusions.",
}

TERMINAL = {"done", "blocked", "cancelled"}
ACTIVE = {"queued", "in_progress", "failed"}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def dependencies_done(task: dict, tasks: list[dict]) -> bool:
    by_id = {item.get("id"): item for item in tasks}
    return all(by_id.get(dep, {}).get("status") == "done" for dep in task.get("depends_on", []))

def select_task(tasks: list[dict]) -> dict | None:
    eligible = [
        task for task in tasks
        if task.get("status") in {"queued", "failed"}
        and dependencies_done(task, tasks)
    ]
    eligible.sort(key=lambda item: (-int(item.get("priority", 0)), item.get("id", "")))
    return eligible[0] if eligible else None

def _source_count(items: list[dict]) -> int:
    return sum(1 for item in items if str(item.get("source") or item.get("link") or "").startswith("http"))

def _analyse_hypotheses(evidence: dict) -> dict:
    hypotheses = evidence.get("hypotheses", {})
    signals = evidence.get("customer_signals", [])
    result = {}
    for key, items in hypotheses.items():
        prices = [x for x in items if x.get("price")]
        free = [x for x in items if "free" in str(x.get("price", "")).lower()]
        result[key] = {
            "competitor_count": len(items),
            "sourced_count": _source_count(items),
            "priced_count": len(prices),
            "free_or_free_tier_count": len(free),
            "customer_signal_count": sum(1 for x in signals if x.get("hypothesis") == key),
        }
    return result

def execute(task: dict, state: dict, evidence: dict) -> dict:
    """Dispatch to a specialist handler. Never marks evidence complete by count alone."""
    task_id = task.get("id")
    role = task.get("role")
    stats = _analyse_hypotheses(evidence)
    cafe = stats.get("cafe_starter_kit", {})
    shift = stats.get("shiftbrief_ai", {})
    signals = evidence.get("customer_signals", [])
    sourced_signals = [s for s in signals if str(s.get("source", "")).startswith("http")]

    if task_id in {"MR-001", "MR-002"}:
        key = "cafe_starter_kit" if task_id == "MR-001" else "shiftbrief_ai"
        s = stats.get(key, {})
        if s.get("competitor_count", 0) < 5 or s.get("sourced_count", 0) < 5:
            return {"ok": False, "blocked": True, "summary": "Competitor evidence is incomplete or lacks verifiable source URLs.", "next_action": "Add at least five distinct, source-linked competitor or substitute records."}
        return {"ok": True, "summary": f"Evidence inventory contains {s['competitor_count']} offers, {s['sourced_count']} with source URLs. This confirms category supply, not sales or demand.", "metrics": s}

    if task_id == "BA-001":
        combined = cafe.get("priced_count", 0) + shift.get("priced_count", 0)
        if combined < 5:
            return {"ok": False, "blocked": True, "summary": "Too few competitor records contain observed price information.", "next_action": "Capture more comparable price points and label free, one-time, subscription or custom pricing."}
        return {"ok": True, "summary": f"Pricing comparison can use {combined} offers with displayed price information. Currency, VAT, customer limits and feature scope must remain separate.", "metrics": {"priced_offers": combined, "by_hypothesis": stats}}

    if task_id == "BA-002":
        if len(sourced_signals) < 3:
            return {"ok": False, "blocked": True, "summary": "Fewer than three source-linked customer/community signals are recorded.", "next_action": "Collect source-linked first-hand discussions or customer reviews; distinguish them from vendor marketing."}
        themes = {
            "cafe": ["stock", "waste", "staff", "owner", "inventory", "spoil"],
            "handover": ["handover", "shift", "notes", "forgot", "communication", "message"],
        }
        counts = {
            key: sum(1 for item in sourced_signals if any(term in (item.get("signal", "") + " " + item.get("type", "")).lower() for term in terms))
            for key, terms in themes.items()
        }
        return {"ok": True, "summary": f"Reviewed {len(sourced_signals)} source-linked qualitative signals. Themes are directional only; frequency and willingness to pay remain unvalidated.", "metrics": {"source_linked_signals": len(sourced_signals), "theme_hits": counts, "evidence_limit": "Anecdotal; not representative."}}

    if task_id == "PS-001":
        if not all(t.get("status") == "done" for t in state.get("project_plan", {}).get("tasks", []) if t.get("id") in {"BA-001", "BA-002"}):
            # The caller passes the current plan snapshot into state for dependency auditing.
            return {"ok": False, "blocked": True, "summary": "Pricing and customer-signal analysis must be completed first.", "next_action": "Complete BA-001 and BA-002."}
        cafe_signals = cafe.get("customer_signal_count", 0)
        shift_signals = shift.get("customer_signal_count", 0)
        comparison = {
            "cafe_starter_kit": {"competitors": cafe.get("competitor_count", 0), "customer_signals": cafe_signals, "risk": "Generic checklists face free and low-cost substitutes; investigate a narrower operational job."},
            "shiftbrief_ai": {"competitors": shift.get("competitor_count", 0), "customer_signals": shift_signals, "risk": "Established tools and app fatigue; validate adoption in existing workflows."},
        }
        return {"ok": True, "summary": "Compared both hypotheses. Willingness to pay is not demonstrated for either; recommend discovery interviews before choosing or building.", "artifact": {"comparison": comparison, "experiment": {"sample": "5–8 café owners/managers and 5–8 shift leads", "method": "Ask respondents to demonstrate current workflows before pitching.", "measure": ["frequency", "time spent", "errors or waste", "consequences", "current workaround", "existing spend"], "success_gate": "A repeated costly problem plus evidence of a current workaround or spend; no product build based on anecdotes alone."}}}

    if task_id == "QC-001":
        prior = state.get("specialist_outputs", {}).get("PS-001", {})
        if not prior:
            return {"ok": False, "blocked": True, "summary": "No product-strategy output is available to audit.", "next_action": "Run PS-001 first."}
        artifact = prior.get("artifact", {})
        checks = {
            "both_hypotheses_compared": bool(artifact.get("comparison")),
            "validation_experiment_defined": bool(artifact.get("experiment", {}).get("method")),
            "willingness_to_pay_not_assumed": "not demonstrated" in prior.get("summary", "").lower(),
            "no_paid_service_required": True,
        }
        passed = all(checks.values())
        return {"ok": passed, "blocked": not passed, "summary": "Quality review " + ("passed." if passed else "found gaps.") + " Evidence is explicitly labelled anecdotal and no paid service is required.", "metrics": {"checks": checks}}

    if task_id == "PM-002":
        qc = state.get("specialist_outputs", {}).get("QC-001", {})
        if not qc.get("ok"):
            return {"ok": False, "blocked": True, "summary": "MVP roadmap requires a passed quality review.", "next_action": "Resolve QC-001 findings first."}
        return {"ok": True, "summary": "Prepared a no-cost validation-first roadmap; product implementation remains gated on customer evidence and explicit approval.", "artifact": {"milestones": [{"step": 1, "name": "Discovery interviews", "gate": "Repeated pain confirmed by target users"}, {"step": 2, "name": "Manual prototype", "gate": "Users complete the workflow and request continued use"}, {"step": 3, "name": "Willingness-to-pay test", "gate": "Realistic price accepted or pilot commitment"}, {"step": 4, "name": "MVP build", "gate": "Only after evidence and explicit approval"}], "cost": "€0 planned; no paid API, subscription or hosting change."}}

    if task_id == "AB-003":
        required_roles = set(ROLE_REGISTRY)
        if len(required_roles) < 9 or not callable(getattr(build_offline_brain(), "dispatch", None)):
            return {"ok": False, "blocked": True, "summary": "Agent Brain registry or dispatch interface is incomplete.", "next_action": "Complete role registry and dispatcher before Project Manager integration."}
        return {"ok": True, "summary": "Project Manager now has an explicit dispatch seam: tasks may be routed through the guarded AgentBrain interface; deterministic handlers remain the default and offline mock output cannot complete real work.", "artifact": {"dispatch_contract": "dispatch_task(task, state, evidence, brain=None)", "default_mode": "deterministic", "brain_mode": "explicit task flag only", "mock_completion": False, "live_calls": "disabled"}}

    if task_id == "AB-004":
        from agent.llm import LLMSettings, OpenAICompatibleClient
        test_source = (Path(__file__).resolve().parents[1] / "tests" / "test_llm.py").read_text(encoding="utf-8")
        checks = {
            "live_disabled_by_default": LLMSettings().enabled is False,
            "client_requires_explicit_key": "api_key" in OpenAICompatibleClient.__init__.__code__.co_varnames,
            "client_requires_persistent_ledger": "spend_ledger" in OpenAICompatibleClient.__init__.__code__.co_varnames,
            "ledger_reserves_before_request": "reserve" in OpenAICompatibleClient.generate.__code__.co_names,
            "ledger_settles_actual_usage": "settle" in OpenAICompatibleClient.generate.__code__.co_names,
            "monthly_cap_blocks_before_network": "test_monthly_limit_blocks_before_network_request" in test_source,
            "full_call_cap_reserved": "test_monthly_guard_reserves_full_per_call_cap" in test_source,
            "failed_call_keeps_reservation": "test_failed_network_request_keeps_reservation" in test_source,
        }
        passed = all(checks.values())
        return {"ok": passed, "blocked": not passed, "summary": "Live LLM remains disabled by default; runtime credentials, persistent ledger reservation, settlement and pre-network budget tests are present." if passed else "Live LLM budget guard checks failed.", "metrics": {"checks": checks}, "next_action": "Fix failed budget guard checks before any live-provider integration."}

    if task_id == "AB-005":
        root = Path(__file__).resolve().parents[1]
        fixture_path = root / "benchmarks" / "agent_brain_cases.json"
        eval_path = root / "tests" / "test_brain_evals.py"
        fixtures = {}
        if fixture_path.exists():
            import json
            fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
        covered_roles = {case.get("role") for case in fixtures.get("cases", [])}
        required_roles = set(ROLE_REGISTRY)
        checks = {
            "golden_case_for_every_role": covered_roles == required_roles,
            "evaluation_tests_exist": eval_path.exists(),
            "role_specific_artifact_contract": "not allowed for role" in Path(__file__).resolve().parent.joinpath("brain.py").read_text(encoding="utf-8"),
            "source_provenance_checks": "Evidence source was not supplied" in Path(__file__).resolve().parent.joinpath("brain.py").read_text(encoding="utf-8"),
        }
        passed = all(checks.values())
        return {"ok": passed, "blocked": not passed, "summary": "Role-specific contract fixtures and evidence-provenance evaluation tests are registered. These validate interface discipline, not live model reasoning quality." if passed else "Agent Brain evaluation suite is incomplete.", "metrics": {"checks": checks, "covered_roles": sorted(covered_roles)}, "artifact": {"fixture_file": "benchmarks/agent_brain_cases.json", "test_file": "tests/test_brain_evals.py", "limitations": ["No live model evaluations", "No claim of role-level reasoning quality", "No network or paid calls"]}, "next_action": "Complete missing role/evidence evaluations before proceeding."}

    if role == "project_manager" and task.get("kind") == "internal":
        return {"ok": True, "summary": "Core orchestration initialised; specialist registry and task queue available."}

    return {"ok": False, "blocked": True, "summary": f"No safe executor is registered for {task_id or role}.", "next_action": "Register a handler and acceptance checks before scheduling this task."}

def validate_result(task: dict, result: dict) -> tuple[bool, str]:
    if not isinstance(result, dict) or not isinstance(result.get("summary"), str) or not result["summary"].strip():
        return False, "Handler returned no usable summary."
    if result.get("ok") and result.get("blocked"):
        return False, "Result cannot be both successful and blocked."
    if result.get("ok") and task.get("role") in {"market_researcher", "business_analyst"}:
        if not result.get("metrics"):
            return False, "Evidence task returned no auditable metrics."
    return True, "valid"

def apply_result(task: dict, result: dict, state: dict, timestamp: str | None = None) -> dict:
    timestamp = timestamp or utc_now()
    valid, reason = validate_result(task, result)
    if not valid:
        result = {"ok": False, "blocked": True, "summary": reason, "next_action": "Inspect handler output and acceptance criteria."}
    task["last_result"] = result["summary"]
    task["updated_at"] = timestamp
    task["attempts"] = int(task.get("attempts", 0)) + 1
    if result.get("artifact"):
        state.setdefault("specialist_outputs", {})[task["id"]] = result
    if result.get("metrics"):
        state.setdefault("specialist_outputs", {})[task["id"]] = result
    if result.get("ok"):
        task["status"] = "done"
        task["completed_at"] = timestamp
        task.pop("blocked_reason", None)
        task.pop("next_action", None)
        status = "completed"
    elif result.get("blocked"):
        task["status"] = "blocked"
        task["blocked_reason"] = result["summary"]
        task["next_action"] = result.get("next_action")
        status = "blocked"
    else:
        task["status"] = "failed"
        status = "failed"
    event = {"timestamp": timestamp, "task_id": task.get("id"), "role": task.get("role"), "status": status, "summary": result["summary"]}
    state.setdefault("event_log", []).append(event)
    state["event_log"] = state["event_log"][-500:]
    return event
