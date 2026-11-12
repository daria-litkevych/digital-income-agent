import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import agent.project_manager as project_manager

from agent.project_manager import dispatch_task


class ProjectManagerAutonomyGateTests(unittest.TestCase):
    def test_autonomous_workflow_is_blocked_without_explicit_approval(self):
        task = {
            "id": "TEST-AUTO",
            "dispatch_to_autonomous_studio": True,
            "workflow_steps": [{"role": "market_researcher", "task": "Collect evidence"}],
        }
        state = {}
        result = dispatch_task(task, state, {})
        self.assertTrue(result["blocked"])
        self.assertIn("explicit human approval was not supplied", result["summary"])
        self.assertNotIn("autonomous_workflow_checkpoints", state)

    def test_normal_tasks_still_use_deterministic_execution(self):
        result = dispatch_task({"id": "PM-001", "role": "project_manager", "kind": "internal"}, {}, {})
        self.assertTrue(result["ok"])


    def test_approved_dispatch_persists_each_checkpoint_to_disk_and_keeps_review_gate(self):
        import hashlib
        import json
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checkpoint_dir = root / "data" / "agent_checkpoints"
            class FakeOrchestrator:
                def __init__(self, saver):
                    self.saver = saver
                def run(self, workflow_id, steps, context):
                    self.saver({"workflows": {workflow_id: {
                        "status": "in_progress",
                        "completed": {"1": {"status": "draft"}},
                    }}})
                    path = checkpoint_dir / (hashlib.sha256(workflow_id.encode("utf-8")).hexdigest() + ".json")
                    self.persisted_during_handoff = json.loads(path.read_text(encoding="utf-8"))
                    return {
                        "status": "review_required", "completed_steps": 1,
                        "outputs": {"1": {"status": "draft"}},
                        "requires_human_approval": True,
                    }
            class FakeStudio:
                def __init__(self, saver):
                    self.orchestrator = FakeOrchestrator(saver)
                def close(self):
                    pass
            holder = {}
            def factory(repository_root, *, checkpoint_loader, checkpoint_saver, approval_confirmed, env):
                self.assertEqual(repository_root, root)
                self.assertTrue(approval_confirmed)
                holder["loader"] = checkpoint_loader
                studio = FakeStudio(checkpoint_saver)
                holder["studio"] = studio
                return studio
            task = {
                "id": "AB-TEST-DURABLE",
                "dispatch_to_autonomous_studio": True,
                "workflow_steps": [{"role": "market_researcher", "task": "Inspect supplied evidence"}],
            }
            with patch.object(project_manager, "ROOT", root), patch(
                "agent.autonomous_studio.build_live_studio", side_effect=factory
            ):
                result = dispatch_task(task, {}, {}, autonomous_approval=True, env={})
            self.assertTrue(result["blocked"])
            self.assertIn("human review", result["summary"].lower())
            self.assertEqual(holder["studio"].orchestrator.persisted_during_handoff["workflows"]["AB-TEST-DURABLE"]["completed"]["1"]["status"], "draft")
            self.assertEqual(holder["loader"](), holder["studio"].orchestrator.persisted_during_handoff)
            self.assertEqual(len(list(checkpoint_dir.glob("*.json"))), 1)

if __name__ == "__main__":
    unittest.main()