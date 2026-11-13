"""Provider-free Product Designer specialist.

Turns a supplied, structured brief into a reviewable design artifact. It does
not invent customer evidence, choose a market, edit product files or publish.
"""
from typing import Any


class DesignBriefError(ValueError):
    pass


def build_design_artifact(brief: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(brief, dict):
        raise DesignBriefError("Design brief must be an object.")
    required = ("target_user", "user_problem", "desired_outcome", "constraints")
    missing = [key for key in required if not brief.get(key)]
    if missing:
        raise DesignBriefError("Design brief is missing: " + ", ".join(missing))

    target = str(brief["target_user"]).strip()
    problem = str(brief["user_problem"]).strip()
    outcome = str(brief["desired_outcome"]).strip()
    constraints = brief["constraints"]
    if not target or not problem or not outcome or not isinstance(constraints, list):
        raise DesignBriefError("Brief fields must contain usable text and a constraints array.")
    if not all(isinstance(item, str) and item.strip() for item in constraints):
        raise DesignBriefError("Every design constraint must be a non-empty string.")

    primary_action = str(brief.get("primary_action") or outcome).strip()
    journey = [
        {"step": 1, "name": "Orient", "user_goal": "Understand what the tool does and what information is needed."},
        {"step": 2, "name": "Provide input", "user_goal": problem},
        {"step": 3, "name": "Review result", "user_goal": "Check the proposed result and correct any input."},
        {"step": 4, "name": "Complete task", "user_goal": primary_action},
    ]
    wireframe = {
        "screen": "Single-purpose workspace",
        "regions": [
            {"name": "Context", "purpose": "State the target outcome and required inputs."},
            {"name": "Input", "purpose": "Collect only the minimum information required."},
            {"name": "Result", "purpose": "Show a preview before any irreversible action."},
            {"name": "Controls", "purpose": "Edit, reset and export only where explicitly supported."},
        ],
        "interaction_principles": [
            "One primary action per screen.",
            "Show validation beside the relevant field.",
            "Preserve user input after validation errors.",
            "Make the result reviewable before completion.",
        ],
    }
    criteria = [
        {"id": "AC-01", "given": "The user opens the tool", "when": "The initial screen loads", "then": "The purpose and required inputs are clear."},
        {"id": "AC-02", "given": "A required input is missing", "when": "The user attempts the primary action", "then": "The tool explains the missing field without losing entered data."},
        {"id": "AC-03", "given": "Valid inputs are supplied", "when": "The user requests the outcome", "then": "A result is generated for review before completion."},
        {"id": "AC-04", "given": "The result is displayed", "when": "The user reviews it", "then": "The user can identify assumptions, limitations and next action."},
    ]
    return {
        "user_journey": {"target_user": target, "problem": problem, "desired_outcome": outcome, "steps": journey},
        "wireframe_spec": wireframe,
        "acceptance_criteria": criteria,
        "assumptions": ["The supplied brief is accurate; no independent customer research was performed."],
        "constraints": constraints,
        "requires_human_review": True,
    }


def execute_design_task(task: dict[str, Any]) -> dict[str, Any]:
    try:
        artifact = build_design_artifact(task.get("design_brief"))
    except DesignBriefError as error:
        return {
            "ok": False, "blocked": True,
            "summary": str(error),
            "next_action": "Supply target_user, user_problem, desired_outcome and explicit constraints.",
        }
    return {
        "ok": True,
        "summary": "Created a reviewable Product Designer artifact from the supplied brief. No customer evidence or product requirements were invented.",
        "artifact": artifact,
        "metrics": {"acceptance_criteria": len(artifact["acceptance_criteria"]), "journey_steps": len(artifact["user_journey"]["steps"])},
    }


def evaluate(repository_root) -> dict[str, Any]:
    from pathlib import Path
    root = Path(repository_root)
    test_path = root / "tests" / "test_product_designer.py"
    source_path = root / "agent" / "product_designer.py"
    if not source_path.is_file() or not test_path.is_file():
        return {"ok": False, "blocked": True, "summary": "Product Designer implementation or tests are missing.", "next_action": "Restore the specialist module and its tests."}
    fixture = {
        "target_user": "A generic independent professional",
        "user_problem": "They need to turn a vague request into a clear next action.",
        "desired_outcome": "A concise, reviewable action summary",
        "constraints": ["No external integrations", "No paid services", "Human review before sending"],
    }
    result = execute_design_task({"design_brief": fixture})
    passed = (
        result.get("ok") is True
        and set(result["artifact"]) >= {"user_journey", "wireframe_spec", "acceptance_criteria"}
        and result["artifact"]["requires_human_review"] is True
        and result["metrics"]["acceptance_criteria"] >= 4
    )
    return {
        "ok": passed, "blocked": not passed,
        "summary": "Product Designer now produces structured user journeys, wireframe specifications and acceptance criteria from a complete supplied brief." if passed else "Product Designer capability evaluation failed.",
        "metrics": {"fixture_passed": passed, **result.get("metrics", {})},
        "artifact": {"module": "agent/product_designer.py", "tests": "tests/test_product_designer.py", "mode": "deterministic provider-free specialist"},
        "next_action": "Connect the role to the bounded orchestration runtime and keep all generated requirements subject to review.",
    }
