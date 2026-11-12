import unittest

from agent.project_manager import dispatch_task


class ProjectManagerBrainRoutingTests(unittest.TestCase):
    def test_deterministic_execution_remains_default(self):
        task = {"id": "PM-001", "role": "project_manager", "kind": "internal", "title": "Initialise"}
        result = dispatch_task(task, {}, {})
        self.assertTrue(result["ok"])

    def test_brain_dispatch_is_explicit_and_mock_draft_cannot_complete_task(self):
        task = {
            "id": "BRAIN-TEST", "role": "market_researcher",
            "title": "Summarise supplied sources", "dispatch_to_brain": True,
        }
        result = dispatch_task(task, {}, {"sources": []})
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])
        self.assertIn("draft requiring review", result["summary"])
        self.assertEqual(result["artifact"]["agent_brain_output"]["execution_mode"], "offline_mock")


if __name__ == "__main__":
    unittest.main()
