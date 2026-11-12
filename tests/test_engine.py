import unittest

from agent.engine import apply_result, dependencies_done, select_task, validate_result

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
        tasks = [{"id":"A","status":"blocked","priority":10,"depends_on":[]}]
        self.assertIsNone(select_task(tasks))

    def test_retries_failed_task(self):
        tasks = [{"id":"A","status":"failed","priority":10,"depends_on":[]}]
        self.assertEqual(select_task(tasks)["id"], "A")

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

if __name__ == "__main__":
    unittest.main()
