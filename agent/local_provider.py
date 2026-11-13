"""Acceptance evaluator for the optional local inference path."""
from pathlib import Path


def evaluate(repository_root) -> dict:
    root = Path(repository_root)
    llm_path = root / "agent" / "llm.py"
    studio_path = root / "agent" / "autonomous_studio.py"
    pm_path = root / "agent" / "project_manager.py"
    llm_tests = root / "tests" / "test_local_llm.py"
    studio_tests = root / "tests" / "test_local_studio.py"
    sources = (llm_path, studio_path, pm_path, llm_tests, studio_tests)
    if not all(path.is_file() for path in sources):
        return {"ok": False, "blocked": True, "summary": "Local inference implementation or its tests are missing.", "next_action": "Restore the local client, composition root and no-network tests."}
    llm = llm_path.read_text(encoding="utf-8")
    studio = studio_path.read_text(encoding="utf-8")
    pm = pm_path.read_text(encoding="utf-8")
    runner_path = root / "agent" / "local_runner.py"
    runner_tests = root / "tests" / "test_local_runner.py"
    docs_path = root / "docs" / "local-model-setup.md"
    checks = {
        "local_client_is_explicitly_disabled_by_default": "enabled: bool = False" in llm and "Local LLM is disabled" in llm,
        "endpoint_is_loopback_only": "address.is_loopback" in llm and "ipaddress.ip_address" in llm,
        "no_model_downloads": "models are never downloaded automatically" in llm,
        "zero_cost_response": 'provider="ollama-local"' in llm and "estimated_cost_usd=0.0" in llm,
        "bounded_request_and_response": "max_input_characters" in llm and "max_response_bytes + 1" in llm,
        "local_factory_requires_approval_and_opt_in": "approval_confirmed is not True" in studio and "STUDIO_LOCAL_LLM_ENABLED" in studio,
        "project_manager_routes_local_provider_explicitly": "build_local_studio if runtime_env.get(\"STUDIO_LOCAL_LLM_ENABLED\", \"\").lower() == \"true\" else build_live_studio" in pm,
        "client_and_factory_tests_exist": llm_tests.is_file() and studio_tests.is_file(),
        "manual_runner_requires_explicit_approval": runner_path.is_file() and "approval_confirmed is not True" in runner_path.read_text(encoding="utf-8"),
        "runner_rejects_secret_fields_and_is_documented": runner_tests.is_file() and docs_path.is_file() and "Secret-like field" in runner_path.read_text(encoding="utf-8"),
    }
    passed = all(checks.values())
    return {
        "ok": passed, "blocked": not passed,
        "summary": "Optional local Ollama inference is wired behind explicit approval, restricted to loopback, free of API billing and model downloads, and covered by no-network construction tests." if passed else "Local inference acceptance checks are incomplete.",
        "metrics": {"checks": checks, "passed": sum(checks.values()), "total": len(checks)},
        "artifact": {"client": "agent/llm.py", "composition_root": "agent/autonomous_studio.py", "tests": ["tests/test_local_llm.py", "tests/test_local_studio.py"]},
        "next_action": "Keep the local model path off until a user explicitly enables it and installs a model locally.",
    }
