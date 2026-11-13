"""Offline acceptance checks for cross-role Agent Brain quality gates.

These checks validate role contracts and fail-closed behaviour only. They do
not claim to measure semantic reasoning quality of a live language model.
"""
from pathlib import Path


def evaluate(repository_root: Path) -> dict:
    root = Path(repository_root)
    brain_path = root / "agent" / "brain.py"
    test_path = root / "tests" / "test_role_quality_gates.py"
    workflow_path = root / ".github" / "workflows" / "daily-agent.yml"

    if not all(path.is_file() for path in (brain_path, test_path, workflow_path)):
        missing = [str(path.relative_to(root)) for path in (brain_path, test_path, workflow_path) if not path.is_file()]
        return {
            "ok": False, "blocked": True,
            "summary": "Cross-role quality gate prerequisites are missing.",
            "metrics": {"missing_files": missing},
            "next_action": "Restore the Agent Brain, cross-role tests and CI workflow before evaluating.",
        }

    brain = brain_path.read_text(encoding="utf-8")
    tests = test_path.read_text(encoding="utf-8")
    workflow = workflow_path.read_text(encoding="utf-8")

    from agent.brain import ROLE_REGISTRY

    required_test_contracts = {
        "allowed_outputs_tested": "test_every_allowed_artifact_section_is_accepted_only_by_its_role",
        "foreign_role_rejected": "test_every_role_rejects_an_artifact_owned_by_another_role",
        "evidence_provenance_enforced": "test_evidence_must_reference_a_url_present_in_supplied_context",
        "unapproved_provider_blocked": "test_live_capable_client_is_not_called_without_approval",
        "external_side_effect_blocked": "test_external_side_effect_requests_are_rejected_before_provider_call",
        "empty_draft_rejected": "test_draft_without_artifact_is_rejected",
    }
    checks = {
        "nine_specialist_roles_registered": len(ROLE_REGISTRY) == 9,
        "role_output_allowlist_enforced": "unexpected_sections = set(payload[\"artifact\"]) - set(spec.allowed_outputs)" in brain,
        "evidence_url_provenance_enforced": "Evidence source was not supplied in task context" in brain,
        "unapproved_live_client_blocked_before_call": "if not self.live_approved and not isinstance(self.client, OfflineMockClient)" in brain,
        "external_side_effect_blocked_before_call": "FORBIDDEN_REQUESTS" in brain and "external side effect" in brain,
        "ci_runs_complete_unittest_suite": "python -m unittest discover -s tests -v" in workflow,
        "fixture_provider_has_zero_cost": "estimated_cost_usd=0.0" in tests and "fixture-model" in tests,
        **{key: marker in tests for key, marker in required_test_contracts.items()},
    }
    passed = all(checks.values())
    return {
        "ok": passed,
        "blocked": not passed,
        "summary": (
            "Cross-role structural quality and safety gates passed for all nine registered roles. "
            "These are offline contract tests, not semantic model-quality benchmarks."
            if passed else "Cross-role quality gate checks found missing or weakened safeguards."
        ),
        "metrics": {"checks": checks, "registered_roles": len(ROLE_REGISTRY), "passed": sum(checks.values()), "total": len(checks)},
        "artifact": {
            "evaluator": "agent/quality_gates.py",
            "tests": "tests/test_role_quality_gates.py",
            "scope": "Role contracts, evidence provenance, approval gating and external-side-effect rejection.",
            "limitations": ["No live model calls", "No paid API calls", "No claim of semantic reasoning quality"],
        },
        "next_action": "Keep these checks in CI and add separately reviewed semantic evaluations only when a safe, approved evaluation method exists.",
    }
