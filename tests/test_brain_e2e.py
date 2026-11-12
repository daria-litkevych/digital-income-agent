import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent import project_manager
from agent.engine import execute


class AgentBrainEndToEndTests(unittest.TestCase):
    def test_ab006_acceptance_handler_checks_real_e2e_artifacts(self):
        result = execute(
            {"id": "AB-006", "role": "project_manager", "kind": "end_to_end"},
            {}, {},
        )
        self.assertTrue(result["ok"], result.get("metrics"))
        self.assertTrue(all(result["metrics"]["checks"].values()))

    def test_offline_brain_draft_is_dispatched_persisted_and_not_marked_done(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan_path = root / "project_plan.json"
            state_path = root / "state.json"
            evidence_path = root / "evidence.json"
            report_path = root / "project-manager.md"
            plan = {
                "name": "Test studio",
                "goal": "Verify safe task lifecycle",
                "phases": [{"id": 9, "name": "Agent Brain", "status": "in_progress", "goal": "test"}],
                "tasks": [{
                    "id": "E2E-BRAIN", "title": "Summarise supplied sources",
                    "phase": 9, "role": "market_researcher", "kind": "research",
                    "status": "in_progress", "priority": 10, "depends_on": [],
                    "dispatch_to_brain": True,
                }],
            }
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            state_path.write_text(json.dumps({"pm_run_count": 0}), encoding="utf-8")
            evidence_path.write_text(json.dumps({"sources": []}), encoding="utf-8")

            with patch.object(project_manager, "PLAN_FILE", plan_path), \
                 patch.object(project_manager, "STATE_FILE", state_path), \
                 patch.object(project_manager, "EVIDENCE_FILE", evidence_path), \
                 patch.object(project_manager, "REPORT_FILE", report_path):
                project_manager.main()

            saved_plan = json.loads(plan_path.read_text(encoding="utf-8"))
            saved_state = json.loads(state_path.read_text(encoding="utf-8"))
            task = saved_plan["tasks"][0]
            self.assertEqual(task["status"], "blocked")
            self.assertEqual(saved_state["specialist_outputs"]["E2E-BRAIN"]["artifact"]["agent_brain_output"]["execution_mode"], "offline_mock")
            self.assertEqual(saved_state["pm_last_cycle"]["task_id"], "E2E-BRAIN")
            self.assertTrue(report_path.exists())

    def test_interrupted_brain_task_is_requeued_then_safely_blocked_for_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            plan_path = root / "project_plan.json"
            state_path = root / "state.json"
            evidence_path = root / "evidence.json"
            report_path = root / "project-manager.md"
            plan = {
                "name": "Recovery test",
                "goal": "Recover interrupted brain work",
                "phases": [{"id": 9, "name": "Agent Brain", "status": "in_progress", "goal": "test"}],
                "tasks": [{
                    "id": "E2E-RECOVER", "title": "Summarise supplied sources",
                    "phase": 9, "role": "market_researcher", "kind": "research",
                    "status": "in_progress", "priority": 10, "depends_on": [],
                    "dispatch_to_brain": True,
                }],
            }
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            state_path.write_text(json.dumps({"pm_run_count": 0}), encoding="utf-8")
            evidence_path.write_text(json.dumps({"sources": []}), encoding="utf-8")
            with patch.object(project_manager, "PLAN_FILE", plan_path), \
                 patch.object(project_manager, "STATE_FILE", state_path), \
                 patch.object(project_manager, "EVIDENCE_FILE", evidence_path), \
                 patch.object(project_manager, "REPORT_FILE", report_path):
                project_manager.main()
            saved_plan = json.loads(plan_path.read_text(encoding="utf-8"))
            self.assertEqual(saved_plan["tasks"][0]["status"], "blocked")
            self.assertIn("recovered_at", saved_plan["tasks"][0])


if __name__ == "__main__":
    unittest.main()
