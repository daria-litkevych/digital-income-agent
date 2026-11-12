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


    def test_quality_gate_and_roadmap_run_in_separate_cycles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_file = root / "data" / "state.json"
            plan_file = root / "data" / "project_plan.json"
            evidence_file = root / "data" / "market_research.json"
            report_file = root / "reports" / "project-manager.md"
            plan = {
                "name": "Test project",
                "goal": "Verify quality gate",
                "phases": [{"id": 1, "name": "Core", "goal": "Run chain", "status": "planned"}],
                "tasks": [
                    {"id": "PS-001", "title": "Strategy", "phase": 1, "role": "product_strategist", "status": "done", "priority": 70, "depends_on": []},
                    {"id": "QC-001", "title": "Quality", "phase": 1, "role": "quality_controller", "status": "queued", "priority": 60, "depends_on": ["PS-001"]},
                    {"id": "PM-002", "title": "Roadmap", "phase": 1, "role": "project_manager", "status": "queued", "priority": 50, "depends_on": ["QC-001"]},
                ],
            }
            state = {
                "agent_name": "Test Agent",
                "pm_run_count": 0,
                "specialist_outputs": {
                    "PS-001": {
                        "ok": True,
                        "summary": "Willingness to pay is not demonstrated for either hypothesis.",
                        "artifact": {"comparison": {"cafe": {}, "shift": {}}, "experiment": {"method": "interviews"}},
                    }
                },
            }
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
                after_qc = json.loads(plan_file.read_text(encoding="utf-8"))
                after_qc_state = json.loads(state_file.read_text(encoding="utf-8"))
                self.assertEqual(after_qc["tasks"][1]["status"], "done")
                self.assertEqual(after_qc["tasks"][2]["status"], "queued")
                self.assertTrue(after_qc_state["specialist_outputs"]["QC-001"]["ok"])

                project_manager.main()

            final_plan = json.loads(plan_file.read_text(encoding="utf-8"))
            final_state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(final_plan["tasks"][2]["status"], "done")
            self.assertEqual(final_state["pm_run_count"], 2)
            self.assertIn("PM-002", final_state["specialist_outputs"])
            self.assertEqual(final_state["specialist_outputs"]["PM-002"]["artifact"]["cost"], "€0 planned; no paid API, subscription or hosting change.")

    def test_interrupted_task_is_requeued_and_recovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_file = root / "data" / "state.json"
            plan_file = root / "data" / "project_plan.json"
            evidence_file = root / "data" / "market_research.json"
            report_file = root / "reports" / "project-manager.md"
            plan = {
                "name": "Recovery test",
                "goal": "Recover interrupted work",
                "phases": [{"id": 1, "name": "Core", "goal": "Recover", "status": "in_progress"}],
                "tasks": [{
                    "id": "PM-RECOVER",
                    "title": "Recover task",
                    "phase": 1,
                    "role": "project_manager",
                    "kind": "internal",
                    "status": "in_progress",
                    "priority": 10,
                    "depends_on": [],
                }],
            }
            plan_file.parent.mkdir(parents=True)
            plan_file.write_text(json.dumps(plan), encoding="utf-8")
            state_file.write_text(json.dumps({"agent_name": "Test Agent", "pm_run_count": 0}), encoding="utf-8")
            evidence_file.write_text("{}", encoding="utf-8")

            with (
                patch.object(project_manager, "PLAN_FILE", plan_file),
                patch.object(project_manager, "STATE_FILE", state_file),
                patch.object(project_manager, "EVIDENCE_FILE", evidence_file),
                patch.object(project_manager, "REPORT_FILE", report_file),
            ):
                project_manager.main()

            saved_plan = json.loads(plan_file.read_text(encoding="utf-8"))
            self.assertEqual(saved_plan["tasks"][0]["status"], "done")
            self.assertIn("recovered_at", saved_plan["tasks"][0])


if __name__ == "__main__":
    unittest.main()
