import unittest

from agent.engine import apply_result, dependencies_done, execute, select_task, validate_result

class EngineTests(unittest.TestCase):
    def test_dependencies_must_be_done(self):
        tasks = [{"id":"A","status":"blocked"}]
        self.assertFalse(dependencies_done({"depends_on":["A"]}, tasks))
        tasks[0]["status"] = "done"
        self.assertTrue(dependencies_done({"depends_on":["A"]}, tasks))

    def test_selects_highest_priority_eligible(self):
        tasks = [
            {"id":"A","status":"queued","priority":99,"depends_on":["MISSING"]},
            {"id":"B","status":"queued","priority":10,"depends_on":[]},
            {"id":"C","status":"queued","priority":20,"depends_on":[]},
        ]
        self.assertEqual(select_task(tasks)["id"], "C")

    def test_blocked_task_is_not_retried_automatically(self):
        self.assertIsNone(select_task([{"id":"A","status":"blocked","priority":10,"depends_on":[]}]))
    
    def test_retries_failed_task(self):
        self.assertEqual(select_task([{"id":"A","status":"failed","priority":10,"depends_on":[]}])["id"], "A")

    def test_rejects_success_without_metrics_for_research(self):
        ok, _ = validate_result({"role":"market_researcher"},{"ok":True,"summary":"Done"})
        self.assertFalse(ok)

    def test_apply_result_persists_artifact_and_event(self):
        task={"id":"PS-001","role":"product_strategist"}
        state={}
        event=apply_result(task,{"ok":True,"summary":"Done","artifact":{"x":1}},state,"2026-01-01T00:00:00+00:00")
        self.assertEqual(task["status"],"done")
        self.assertEqual(state["specialist_outputs"]["PS-001"]["artifact"]["x"],1)
        self.assertEqual(len(state["event_log"]),1)
        self.assertEqual(event["status"],"completed")

    def test_product_strategist_creates_validation_plan_without_claiming_demand(self):
        plan_tasks=[{"id":"BA-001","status":"done"},{"id":"BA-002","status":"done"}]
        state={"project_plan":{"tasks":plan_tasks}}
        result=execute({"id":"PS-001","role":"product_strategist"},state,{"hypotheses":{},"customer_signals":[]})
        self.assertTrue(result["ok"])
        self.assertIn("not demonstrated",result["summary"])
        self.assertIn("experiment",result["artifact"])

    def test_quality_controller_blocks_missing_strategy_output(self):
        result=execute({"id":"QC-001","role":"quality_controller"},{"specialist_outputs":{}},{})
        self.assertTrue(result["blocked"])

    def test_quality_controller_accepts_auditable_strategy_output(self):
        prior={"ok":True,"summary":"Willingness to pay is not demonstrated for either hypothesis.","artifact":{"comparison":{"a":1},"experiment":{"method":"interviews"}}}
        result=execute({"id":"QC-001","role":"quality_controller"},{"specialist_outputs":{"PS-001":prior}},{})
        self.assertTrue(result["ok"])
        self.assertTrue(all(result["metrics"]["checks"].values()))

if __name__ == "__main__":
    unittest.main()
