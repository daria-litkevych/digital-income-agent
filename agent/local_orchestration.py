"""Acceptance evaluator for local multi-specialist orchestration."""
from pathlib import Path


def evaluate(repository_root) -> dict:
    root = Path(repository_root)
    test_path = root / "tests" / "test_local_orchestration.py"
    if not test_path.is_file():
        return {"ok": False, "blocked": True, "summary": "Local orchestration integration tests are missing.", "next_action": "Restore the fake-local-provider multi-specialist tests."}
    tests = test_path.read_text(encoding="utf-8")
    checks = {
        "uses_local_model_client": "LocalOllamaClient" in tests,
        "uses_bounded_tool_runtime": "AgentToolRuntime" in tests and "read_fixture_record" in tests,
        "runs_multiple_specialists": "market_researcher" in tests and "business_analyst" in tests,
        "checkpoints_are_persisted": "checkpoint_saver" in tests and "review_required" in tests,
        "invalid_role_output_fails_closed": "test_invalid_role_output_fails_closed" in tests,
        "provider_calls_are_mocked_to_loopback": '@patch("agent.llm.urlopen")' in tests and "127.0.0.1:11434" in tests,
    }
    passed = all(checks.values())
    return {
        "ok": passed, "blocked": not passed,
        "summary": "Local inference is covered through a mocked loopback provider, bounded tool use, two-specialist handoff, durable checkpoints and mandatory human review." if passed else "Local multi-specialist orchestration checks are incomplete.",
        "metrics": {"checks": checks, "passed": sum(checks.values()), "total": len(checks)},
        "artifact": {"tests": "tests/test_local_orchestration.py", "network": "mocked loopback only", "billing": "zero"},
        "next_action": "Run the full suite and keep real local inference opt-in until a local model is installed and approved.",
    }
