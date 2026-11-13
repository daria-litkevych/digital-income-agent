"""Provider-free Developer proposal validator.

Validates a supplied code proposal in a temporary allowlisted workspace,
produces a unified diff and runs one allowlisted test module. It never writes
to the checked-out repository and is not an autonomous code generator.
"""
from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from agent.workspace_tools import DEFAULT_ALLOWED_FILES, DEFAULT_ALLOWED_TESTS, ProposalWorkspace, WorkspaceError


def execute_developer_task(task: dict[str, Any], repository_root: str | Path) -> dict[str, Any]:
    target = task.get("target_path")
    proposed = task.get("proposed_content")
    test_module = task.get("test_module")
    if not isinstance(target, str) or target not in DEFAULT_ALLOWED_FILES:
        return {"ok": False, "blocked": True, "summary": "Target path is not in the developer workspace allowlist.", "next_action": "Choose an existing allowlisted project file."}
    if not isinstance(test_module, str) or test_module not in DEFAULT_ALLOWED_TESTS:
        return {"ok": False, "blocked": True, "summary": "Test module is not in the developer workspace allowlist.", "next_action": "Choose one existing allowlisted unittest module."}
    if not isinstance(proposed, str) or not proposed.strip() or len(proposed) > 30000:
        return {"ok": False, "blocked": True, "summary": "Proposed content must be non-empty text of at most 30,000 characters.", "next_action": "Supply a bounded text proposal."}

    workspace = None
    try:
        workspace = ProposalWorkspace(repository_root)
        original = workspace.read_file(target)
        write_result = workspace.propose_write(target, proposed)
        test_result = workspace.run_tests(test_module)
        diff = "".join(difflib.unified_diff(
            original.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile=f"a/{target}",
            tofile=f"b/{target}",
        ))
        if not test_result["passed"]:
            return {
                "ok": False, "blocked": True,
                "summary": "Developer proposal was isolated successfully, but its allowlisted tests failed.",
                "artifact": {"code_patch": diff, "test_plan": {"module": test_module, "result": test_result}, "repository_modified": False},
                "next_action": "Review the test failure and revise the proposal; do not apply it to the repository.",
            }
        return {
            "ok": True,
            "summary": "Developer proposal passed its allowlisted tests in a temporary workspace; the repository was not modified.",
            "artifact": {
                "code_patch": diff,
                "test_plan": {"module": test_module, "result": test_result},
                "implementation_plan": {"target_path": target, "status": write_result["status"]},
                "repository_modified": False,
                "requires_human_review": True,
            },
            "metrics": {"test_module": test_module, "tests_passed": True, "patch_characters": len(diff)},
        }
    except (WorkspaceError, OSError, UnicodeError) as error:
        return {"ok": False, "blocked": True, "summary": f"Developer proposal blocked safely: {error}", "next_action": "Use an allowlisted file and test module with a bounded text proposal."}
    finally:
        if workspace is not None:
            workspace.close()


def evaluate(repository_root: str | Path) -> dict[str, Any]:
    root = Path(repository_root)
    source_path = root / "agent" / "developer.py"
    test_path = root / "tests" / "test_developer.py"
    workspace_source = root / "agent" / "workspace_tools.py"
    if not all(path.is_file() for path in (source_path, test_path, workspace_source)):
        return {"ok": False, "blocked": True, "summary": "Developer proposal validator, tests or workspace tools are missing.", "next_action": "Restore the isolated developer proposal path and tests."}
    original = (root / "agent" / "product_designer.py").read_text(encoding="utf-8")
    proposal = original + "\n# Offline developer proposal fixture; never applied to the repository.\n"
    result = execute_developer_task({
        "target_path": "agent/product_designer.py",
        "proposed_content": proposal,
        "test_module": "tests.test_product_designer",
    }, root)
    passed = (
        result.get("ok") is True
        and result.get("artifact", {}).get("repository_modified") is False
        and result.get("artifact", {}).get("test_plan", {}).get("result", {}).get("passed") is True
        and "Offline developer proposal fixture" in result.get("artifact", {}).get("code_patch", "")
    )
    return {
        "ok": passed, "blocked": not passed,
        "summary": "Developer can stage a bounded code proposal, produce a diff and run allowlisted tests in an isolated temporary workspace without modifying the repository." if passed else "Developer proposal validation did not pass its isolated-workspace acceptance check.",
        "metrics": {"fixture_passed": passed, **result.get("metrics", {})},
        "artifact": {"module": "agent/developer.py", "workspace": "agent/workspace_tools.py", "tests": "tests/test_developer.py", "mode": "proposal validation only; not autonomous code generation"},
        "next_action": "Connect a reviewed code-generation client only after explicit approval; preserve proposal-only writes and test gates.",
    }
