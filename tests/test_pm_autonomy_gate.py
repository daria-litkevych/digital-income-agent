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


if __name__ == "__main__":
    unittest.main()