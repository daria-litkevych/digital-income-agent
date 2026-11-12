import unittest

from agent.brain import BrainError
from agent.engine import execute
from agent.orchestrator import MultiAgentOrchestrator


class FakeRuntime:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []
    def run(self, role, task, context):
        self.calls.append((role, task, context))
        if self.results:
            return self.results.pop(0)
        return {"status": "draft", "summary": "Draft output", "requires_human_approval": True}


class OrchestratorAcceptanceTests(unittest.TestCase):
    def test_ab010_acceptance_handler_checks_orchestrator_and_tests(self):
        result = execute({"id": "AB-010", "role": "project_manager", "kind": "autonomy_loop"}, {}, {})
        self.assertTrue(result["ok"], result.get("metrics"))
        self.assertTrue(all(result["metrics"]["checks"].values()))


class MultiAgentOrchestratorTests(unittest.TestCase):
    def make_orchestrator(self, runtime, store):
        return MultiAgentOrchestrator(
            runtime,
            checkpoint_loader=lambda: store,
            checkpoint_saver=lambda updated: store.update(updated),
        )

    def test_specialists_run_in_order_and_checkpoint_each_step(self):
        runtime = FakeRuntime()
        store = {}
        result = self.make_orchestrator(runtime, store).run(
            "wf-1",
            [{"role": "market_researcher", "task": "Gather evidence"}, {"role": "business_analyst", "task": "Compare evidence"}],
            {"source_urls": []},
        )
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["completed_steps"], 2)
        self.assertEqual(len(runtime.calls), 2)
        self.assertEqual(runtime.calls[1][2]["prior_specialist_outputs"]["1"]["summary"], "Draft output")
        self.assertEqual(store["workflows"]["wf-1"]["status"], "review_required")
        self.assertTrue(result["requires_human_approval"])

    def test_resume_skips_already_checkpointed_steps(self):
        runtime = FakeRuntime()
        store = {"workflows": {"wf-2": {"status": "in_progress", "completed": {
            "1": {"status": "draft", "summary": "Previously completed draft"}
        }}}}
        result = self.make_orchestrator(runtime, store).run(
            "wf-2",
            [{"role": "market_researcher", "task": "Gather evidence"}, {"role": "quality_controller", "task": "Audit"}],
            {},
        )
        self.assertEqual(len(runtime.calls), 1)
        self.assertEqual(runtime.calls[0][0], "quality_controller")
        self.assertEqual(result["completed_steps"], 2)

    def test_blocked_step_persists_checkpoint_and_stops(self):
        runtime = FakeRuntime([{"status": "blocked", "summary": "Live model not approved"}])
        store = {}
        result = self.make_orchestrator(runtime, store).run(
            "wf-3", [{"role": "developer", "task": "Implement"}], {},
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(store["workflows"]["wf-3"]["status"], "blocked")
        self.assertEqual(len(runtime.calls), 1)

    def test_unknown_roles_and_oversized_workflows_are_rejected(self):
        orchestrator = self.make_orchestrator(FakeRuntime(), {})
        with self.assertRaises(BrainError):
            orchestrator.run("wf-4", [{"role": "unknown", "task": "Do work"}], {})
        with self.assertRaises(BrainError):
            orchestrator.run("wf-5", [{"role": "developer", "task": "x"}] * 7, {})

    def test_outputs_never_claim_external_publication(self):
        result = self.make_orchestrator(FakeRuntime(), {}).run(
            "wf-6", [{"role": "growth_launch", "task": "Draft launch plan"}], {},
        )
        self.assertEqual(result["status"], "review_required")
        self.assertIn("never publishes", result["note"])


if __name__ == "__main__":
    unittest.main()