"""Provider-free Growth & Launch specialist for private launch preparation.

Produces positioning and listing drafts from a supplied product brief. It
never publishes, contacts users or invents evidence-backed claims.
"""
from pathlib import Path
from typing import Any


class LaunchBriefError(ValueError):
    pass


def build_launch_assets(brief: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(brief, dict):
        raise LaunchBriefError("Launch brief must be an object.")
    required = ("product_name", "target_user", "user_problem", "desired_outcome", "features", "limitations")
    missing = [key for key in required if not brief.get(key)]
    if missing:
        raise LaunchBriefError("Launch brief is missing: " + ", ".join(missing))
    for key in ("product_name", "target_user", "user_problem", "desired_outcome"):
        if not isinstance(brief[key], str) or not brief[key].strip():
            raise LaunchBriefError(f"{key} must be non-empty text.")
    if not isinstance(brief["features"], list) or not all(isinstance(x, str) and x.strip() for x in brief["features"]):
        raise LaunchBriefError("features must be an array of non-empty strings.")
    if not isinstance(brief["limitations"], list) or not all(isinstance(x, str) and x.strip() for x in brief["limitations"]):
        raise LaunchBriefError("limitations must be an array of non-empty strings.")

    verified_facts = brief.get("verified_facts", [])
    if not isinstance(verified_facts, list):
        raise LaunchBriefError("verified_facts must be an array.")
    backed = []
    for item in verified_facts:
        if not isinstance(item, dict) or not isinstance(item.get("claim"), str) or not item["claim"].strip():
            raise LaunchBriefError("Every verified fact needs a non-empty claim.")
        source = item.get("source_url", "")
        if not isinstance(source, str) or not source.startswith("https://"):
            raise LaunchBriefError("Every evidence-backed claim must have a supplied HTTPS source URL.")
        backed.append({"claim": item["claim"].strip(), "source_url": source})

    name = brief["product_name"].strip()
    user = brief["target_user"].strip()
    problem = brief["user_problem"].strip()
    outcome = brief["desired_outcome"].strip()
    return {
        "positioning": {
            "product": name,
            "audience": user,
            "problem": problem,
            "outcome": outcome,
            "positioning_statement": f"{name} helps {user} address {problem.lower()} and work toward {outcome.lower()}.",
            "evidence_status": "Draft positioning based only on the supplied brief; not independently validated.",
        },
        "listing_draft": {
            "headline": f"{name}: {outcome}",
            "for_whom": user,
            "problem": problem,
            "included_features": list(brief["features"]),
            "limitations": list(brief["limitations"]),
            "evidence_backed_claims": backed,
            "unverified_claims": [],
            "publication_status": "private_draft_only",
        },
        "launch_checklist": [
            {"item": "Verify every factual product claim against its source", "status": "pending"},
            {"item": "Confirm price, fees, VAT and refund terms", "status": "pending"},
            {"item": "Review privacy, support and accessibility information", "status": "pending"},
            {"item": "Check platform rules and final listing presentation", "status": "pending"},
            {"item": "Obtain explicit human approval before any publication", "status": "mandatory_gate"},
        ],
        "requires_human_review": True,
        "external_actions_performed": False,
    }


def execute_growth_task(task: dict[str, Any]) -> dict[str, Any]:
    try:
        artifact = build_launch_assets(task.get("launch_brief"))
    except LaunchBriefError as error:
        return {"ok": False, "blocked": True, "summary": str(error), "next_action": "Supply a complete product brief and source URLs for any evidence-backed claims."}
    return {
        "ok": True,
        "summary": "Prepared private positioning and listing drafts using only supplied facts; publication and outreach remain disabled.",
        "artifact": artifact,
        "metrics": {"features_listed": len(artifact["listing_draft"]["included_features"]), "verified_claims": len(artifact["listing_draft"]["evidence_backed_claims"])},
    }


def evaluate(repository_root) -> dict[str, Any]:
    root = Path(repository_root)
    if not (root / "tests" / "test_growth_launch.py").is_file():
        return {"ok": False, "blocked": True, "summary": "Growth & Launch tests are missing.", "next_action": "Restore the private launch preparation tests."}
    fixture = {
        "product_name": "Example Utility",
        "target_user": "independent professionals",
        "user_problem": "they need to clarify small changes to client work",
        "desired_outcome": "a reviewable change summary",
        "features": ["structured inputs", "editable summary"],
        "limitations": ["No client messaging", "No account integrations"],
    }
    result = execute_growth_task({"launch_brief": fixture})
    passed = (
        result.get("ok") is True
        and result["artifact"]["listing_draft"]["publication_status"] == "private_draft_only"
        and result["artifact"]["external_actions_performed"] is False
        and not result["artifact"]["listing_draft"]["unverified_claims"]
    )
    return {
        "ok": passed, "blocked": not passed,
        "summary": "Growth & Launch now prepares private positioning, listing drafts and a human-approval checklist without publishing or inventing evidence." if passed else "Growth & Launch capability evaluation failed.",
        "metrics": {"fixture_passed": passed, **result.get("metrics", {})},
        "artifact": {"module": "agent/growth_launch.py", "tests": "tests/test_growth_launch.py", "mode": "private draft preparation only"},
        "next_action": "Keep publication and customer outreach behind a separately approved action flow.",
    }
