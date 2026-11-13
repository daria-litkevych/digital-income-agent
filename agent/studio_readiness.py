"""Final readiness audit for the private autonomous agent studio."""
import json
from pathlib import Path

from agent.brain import ROLE_REGISTRY
from agent.llm import LLMSettings, LocalLLMSettings


def evaluate(repository_root) -> dict:
    root = Path(repository_root)
    plan_path = root / "data" / "project_plan.json"
    if not plan_path.is_file():
        return {"ok": False, "blocked": True, "summary": "Project plan is missing; readiness cannot be established.", "next_action": "Restore the project plan and rerun the audit."}
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    tasks = plan.get("tasks", [])
    by_id = {task.get("id"): task for task in tasks}
    ab_tasks = [task for task in tasks if str(task.get("id", "")).startswith("AB-") and task.get("id") != "AB-028"]
    required_modules = [
        "agent/product_designer.py", "agent/developer.py", "agent/growth_launch.py",
        "agent/analytics.py", "agent/local_provider.py", "agent/local_runner.py",
        "agent/local_orchestration.py", "agent/quality_gates.py",
    ]
    required_tests = [
        "tests/test_role_quality_gates.py", "tests/test_product_designer.py",
        "tests/test_developer.py", "tests/test_growth_launch.py", "tests/test_analytics.py",
        "tests/test_local_llm.py", "tests/test_local_studio.py",
        "tests/test_local_orchestration.py", "tests/test_local_runner.py",
    ]
    workflow_path = root / ".github" / "workflows" / "daily-agent.yml"
    workflow = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
    checks = {
        "nine_roles_registered": len(ROLE_REGISTRY) == 9,
        "all_prior_agent_build_tasks_done": bool(ab_tasks) and all(task.get("status") == "done" for task in ab_tasks),
        "specialist_modules_present": all((root / path).is_file() for path in required_modules),
        "specialist_and_safety_tests_present": all((root / path).is_file() for path in required_tests),
        "full_unittest_suite_in_ci": "python -m unittest discover -s tests -v" in workflow,
        "paid_llm_disabled_by_default": LLMSettings().enabled is False,
        "local_llm_disabled_by_default": LocalLLMSettings().enabled is False,
        "local_cli_requires_explicit_approval": (root / "agent" / "local_runner.py").is_file() and "--approve-local-run" in (root / "agent" / "local_runner.py").read_text(encoding="utf-8"),
        "scheduled_workflow_does_not_run_local_cli": "agent.local_runner" not in workflow,
        "cafe_product_tasks_remain_paused": by_id.get("DS-007", {}).get("status") == "blocked" and by_id.get("DS-008", {}).get("status") == "queued",
    }
    passed = all(checks.values())
    return {
        "ok": passed, "blocked": not passed,
        "summary": (
            "Studio readiness audit passed: all nine roles are registered, provider-free specialist capabilities and safeguards are tested, paid and local inference remain off by default, and product work remains paused."
            if passed else "Studio readiness audit found incomplete capabilities or guardrails."
        ),
        "metrics": {"checks": checks, "passed": sum(checks.values()), "total": len(checks)},
        "artifact": {
            "role_count": len(ROLE_REGISTRY),
            "prior_agent_tasks_done": len(ab_tasks),
            "execution_mode": "scheduled deterministic; optional local inference available only through manual approval",
            "remaining_user_action": "Install and start a local Ollama service, install a compatible model, then explicitly approve a manual local run.",
            "limitations": ["No model is installed or run by this audit", "No semantic quality of a particular model is claimed", "No paid API, publication, outreach or spending is enabled"],
        },
        "next_action": "Install and start a local model service, then explicitly approve the first real inference run.",
    }
