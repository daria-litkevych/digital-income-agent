"""Manual entrypoint for explicitly approved local-model workflows.

The scheduled GitHub Actions workflow never calls this module. Running it
requires a CLI approval flag and STUDIO_LOCAL_LLM_ENABLED=true.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from agent.autonomous_studio import build_local_studio


FORBIDDEN_CONTEXT_KEYS = ("api_key", "password", "secret", "credential", "access_token", "refresh_token")


def _reject_secret_fields(value: Any, path: str = "context") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if any(marker in key_lower for marker in FORBIDDEN_CONTEXT_KEYS):
                raise ValueError(f"Secret-like field is not allowed in workflow input: {path}.{key}")
            _reject_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secret_fields(child, f"{path}[{index}]")


def _load_workflow(path: str | Path) -> tuple[list[dict], dict]:
    workflow_path = Path(path).expanduser()
    raw = workflow_path.read_bytes()
    if len(raw) > 100_000:
        raise ValueError("Workflow file exceeds the 100 KB limit.")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Workflow file must contain valid UTF-8 JSON.") from error
    if not isinstance(payload, dict):
        raise ValueError("Workflow file must contain a JSON object.")
    tasks = payload.get("tasks")
    context = payload.get("context", {})
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 6:
        raise ValueError("Workflow must contain between 1 and 6 specialist tasks.")
    if not isinstance(context, dict):
        raise ValueError("Workflow context must be a JSON object.")
    _reject_secret_fields(context)
    return tasks, context


def run_local_workflow(
    repository_root: str | Path,
    workflow_file: str | Path,
    workflow_id: str,
    *,
    approval_confirmed: bool = False,
    env: dict[str, str] | None = None,
) -> dict:
    if approval_confirmed is not True:
        raise RuntimeError("Explicit local-run approval is required.")
    if not isinstance(workflow_id, str) or not workflow_id.strip() or len(workflow_id) > 120:
        raise ValueError("Workflow ID must contain 1 to 120 characters.")
    tasks, context = _load_workflow(workflow_file)
    root = Path(repository_root).resolve()
    checkpoint_dir = root / "data" / "agent_checkpoints"
    checkpoint_name = hashlib.sha256(workflow_id.encode("utf-8")).hexdigest() + ".json"
    checkpoint_path = checkpoint_dir / checkpoint_name

    def load_checkpoints():
        if not checkpoint_path.exists():
            return {}
        try:
            return json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Cannot safely load local workflow checkpoint: {error}") from error

    def save_checkpoints(value):
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        temporary = checkpoint_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(checkpoint_path)

    studio = build_local_studio(
        root,
        checkpoint_loader=load_checkpoints,
        checkpoint_saver=save_checkpoints,
        approval_confirmed=True,
        env=env,
    )
    try:
        return studio.orchestrator.run(workflow_id, tasks, context)
    finally:
        studio.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a manually approved local-model specialist workflow.")
    parser.add_argument("--approve-local-run", action="store_true", help="Explicitly approve this local model run.")
    parser.add_argument("--workflow", default="data/local_workflow.example.json", help="Path to a JSON workflow file.")
    parser.add_argument("--workflow-id", required=True, help="Stable ID used for checkpoint recovery.")
    args = parser.parse_args()
    if not args.approve_local_run:
        parser.error("Pass --approve-local-run to confirm this local inference run.")
    result = run_local_workflow(
        Path(__file__).resolve().parents[1],
        args.workflow,
        args.workflow_id,
        approval_confirmed=True,
        env=dict(os.environ),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
