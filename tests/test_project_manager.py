import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent import project_manager


class ProjectManagerIntegrationTests(unittest.TestCase):
    def test_cycle_executes_and_persists_one_eligible_task(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_file = root / "data" / "state.json"
            plan_file = root / "data" / "project_plan.json"
            evidence_file = root / "data" / "market_research.json"
            report_file = root / "reports" / "project-manager.md"

            plan = {
                "name": "Test project",
                "goal": "Verify orchestration",
                "phases": [{"id": 1, "name": "Core", "goal": "Run one task", "status": "planned"}],
                "tasks": [{
                    "id": "PM-TEST",
                    "title": "Initialise test workflow",
                    "phase": 1,
                    "role": "project_manager",
                    "kind": "internal",
                    "status": "queued",
                    "priority": 100,
                    "depends_on": [],
                }],
            }
            state = {"agent_name": "Test Agent", "pm_run_count": 0}
            plan_file.parent.mkdir(parents=True)
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            state_file.write_text(json.dumps(state), encoding="utf-8")
            evidence_file.write_text("{}", encoding="utf-8")

            with (
                patch.object(project_manager, "PLAN_FILE", plan_file),
                patch.object(project_manager, "STATE_FILE", state_file),
                patch.object(project_manager, "EVIDENCE_FILE", evidence_file),
                patch.object(project_manager, "REPORT_FILE", report_file),
            ):
                project_manager.main()

            saved_plan = json.loads(plan_file.read_text(encoding="utf-8"))
            saved_state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(saved_plan["tasks"][0]["status"], "done")
            self.assertEqual(saved_plan["phases"][0]["status"], "completed")
            self.assertEqual(saved_state["pm_run_count"], 1)
            self.assertEqual(saved_state["pm_last_cycle"]["task_id"], "PM-TEST")
            self.assertEqual(saved_state["pm_last_cycle"]["status"], "completed")
            self.assertTrue(report_file.exists())
            self.assertIn("Project Manager cycles: 1", report_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
