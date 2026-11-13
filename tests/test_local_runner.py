import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.local_runner import _load_workflow, run_local_workflow


class FakeOrchestrator:
    def __init__(self):
        self.args = None
    def run(self, workflow_id, tasks, context):
        self.args = (workflow_id, tasks, context)
        return {"status": "review_required", "requires_human_approval": True}


class FakeStudio:
    def __init__(self):
        self.orchestrator = FakeOrchestrator()
        self.closed = False
    def close(self):
        self.closed = True


class LocalRunnerTests(unittest.TestCase):
    def test_explicit_approval_is_required_before_workflow_read(self):
        with self.assertRaisesRegex(RuntimeError, "approval"):
            run_local_workflow("/tmp", "/missing.json", "workflow-1", approval_confirmed=False)

    def test_workflow_rejects_secret_like_context_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "workflow.json"
            path.write_text(json.dumps({
                "tasks": [{"role": "quality_controller", "task": "Review"}],
                "context": {"nested": {"api_key": "do-not-send"}},
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Secret-like"):
                _load_workflow(path)

    def test_workflow_size_and_task_count_are_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "workflow.json"
            path.write_text(json.dumps({"tasks": [], "context": {}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "between 1 and 6"):
                _load_workflow(path)

    def test_example_workflow_has_valid_non_sensitive_structure(self):
        root = Path(__file__).resolve().parents[1]
        tasks, context = _load_workflow(root / "data" / "local_workflow.example.json")
        self.assertEqual(len(tasks), 2)
        self.assertEqual(tasks[0]["role"], "market_researcher")
        self.assertIsInstance(context, dict)

    def test_runner_passes_tasks_and_persists_checkpoints_then_closes_studio(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            workflow = root / "workflow.json"
            workflow.write_text(json.dumps({
                "tasks": [{"role": "quality_controller", "task": "Review supplied fixture data."}],
                "context": {"notes": "Synthetic only."},
            }), encoding="utf-8")
            studio = FakeStudio()
            with patch("agent.local_runner.build_local_studio", return_value=studio) as factory:
                result = run_local_workflow(
                    root, workflow, "workflow-42",
                    approval_confirmed=True,
                    env={"STUDIO_LOCAL_LLM_ENABLED": "true", "STUDIO_LOCAL_LLM_MODEL": "fixture"},
                )
                self.assertEqual(result["status"], "review_required")
                self.assertTrue(studio.closed)
                self.assertEqual(studio.orchestrator.args[0], "workflow-42")
                saver = factory.call_args.kwargs["checkpoint_saver"]
                saver({"workflows": {"workflow-42": {"status": "review_required"}}})
                checkpoint_dir = root / "data" / "agent_checkpoints"
                self.assertEqual(len(list(checkpoint_dir.glob("*.json"))), 1)
                self.assertIn("workflow-42", next(checkpoint_dir.glob("*.json")).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
