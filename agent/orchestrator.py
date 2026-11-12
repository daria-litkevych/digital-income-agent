"""Checkpointed multi-specialist orchestration with explicit live approval."""
from __future__ import annotations

from typing import Any, Callable

from agent.brain import BrainError, ROLE_REGISTRY
from agent.tool_runtime import AgentToolRuntime


class MultiAgentOrchestrator:
    """Run a declared sequence of specialist tasks and persist each checkpoint.

    This coordinator does not enable live inference by itself. The injected
    runtime must already have been created with an approved live client and
    explicit tool registry. Results remain drafts for human review.
    """

    def __init__(
        self,
        runtime: AgentToolRuntime,
        *,
        checkpoint_loader: Callable[[], dict[str, Any]],
        checkpoint_saver: Callable[[dict[str, Any]], None],
        max_tasks: int = 6,
    ):
        if max_tasks < 1 or max_tasks > 9:
            raise ValueError("max_tasks must be between 1 and 9")
        self.runtime = runtime
        self.checkpoint_loader = checkpoint_loader
        self.checkpoint_saver = checkpoint_saver
        self.max_tasks = max_tasks

    def run(self, workflow_id: str, tasks: list[dict[str, str]], context: dict[str, Any]) -> dict[str, Any]:
        if not workflow_id or len(workflow_id) > 120:
            raise BrainError("A bounded workflow identifier is required.")
        if not isinstance(tasks, list) or not tasks or len(tasks) > self.max_tasks:
            raise BrainError("Workflow must contain between 1 and the configured maximum number of tasks.")
        for item in tasks:
            if not isinstance(item, dict) or item.get("role") not in ROLE_REGISTRY:
                raise BrainError("Every workflow step must declare a registered specialist role.")
            if not isinstance(item.get("task"), str) or not item["task"].strip() or len(item["task"]) > 4000:
                raise BrainError("Every workflow step must contain a bounded task description.")

        store = self.checkpoint_loader() or {}
        workflows = store.setdefault("workflows", {})
        record = workflows.setdefault(workflow_id, {"completed": {}, "status": "in_progress"})
        completed = record.setdefault("completed", {})
        outputs = dict(completed)

        for index, item in enumerate(tasks):
            step_id = str(index + 1)
            if step_id in completed:
                continue
            result = self.runtime.run(item["role"], item["task"], {
                **context,
                "workflow_id": workflow_id,
                "workflow_step": index + 1,
                "prior_specialist_outputs": outputs,
            })
            if result.get("status") == "blocked":
                record["status"] = "blocked"
                record["blocked_at_step"] = index + 1
                self.checkpoint_saver(store)
                return {
                    "status": "blocked",
                    "workflow_id": workflow_id,
                    "completed_steps": len(completed),
                    "outputs": outputs,
                    "reason": result.get("summary", "Specialist runtime blocked."),
                    "requires_human_approval": True,
                }
            outputs[step_id] = result
            completed[step_id] = result
            record["last_completed_step"] = index + 1
            record["status"] = "in_progress"
            self.checkpoint_saver(store)

        record["status"] = "review_required"
        record["requires_human_approval"] = True
        self.checkpoint_saver(store)
        return {
            "status": "review_required",
            "workflow_id": workflow_id,
            "completed_steps": len(completed),
            "outputs": outputs,
            "requires_human_approval": True,
            "note": "Specialist outputs are drafts. This coordinator never publishes, contacts customers, spends money or marks a business task complete.",
        }