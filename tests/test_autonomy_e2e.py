import json
import unittest

from agent.brain import BrainError
from agent.llm import LLMResponse
from agent.orchestrator import MultiAgentOrchestrator
from agent.tool_runtime import AgentTool, AgentToolRuntime, ToolRegistry


class ScriptedClient:
    def __init__(self, messages):
        self.messages = list(messages)
        self.calls = 0
    def generate(self, request):
        self.calls += 1
        message = self.messages.pop(0)
        return LLMResponse(
            text=json.dumps(message), model="fake-model", provider="fake-provider",
            input_tokens=20, output_tokens=30, estimated_cost_usd=0.0, is_mock=False,
        )


def final_payload(role, artifact, evidence=None, status="draft"):
    return {
        "status": status,
        "summary": "Fixture output for " + role,
        "artifact": artifact,
        "evidence": evidence or [],
        "assumptions": [],
        "risks": [],
        "confidence": "low",
        "requires_human_approval": True,
    }


class AutonomyE2EAcceptanceTests(unittest.TestCase):
    def test_ab014_acceptance_handler_checks_offline_e2e_suite(self):
        from agent.engine import execute
        result = execute({"id": "AB-014", "role": "quality_controller", "kind": "autonomy_e2e"}, {}, {})
        self.assertTrue(result["ok"], result.get("metrics"))
        self.assertTrue(all(result["metrics"]["checks"].values()))


class AutonomyE2ETests(unittest.TestCase):
    def test_two_roles_use_only_their_tools_and_checkpoint_outputs(self):
        source = "https://example.test/market-evidence"
        client = ScriptedClient([
            {"type": "tool_call", "tool": "fetch_public_url", "arguments": {"url": source}},
            {"type": "final", "result": final_payload("market_researcher", {"research_summary": {"finding": "Fixture evidence"}}, [{"source": source}])},
            {"type": "tool_call", "tool": "propose_patch", "arguments": {"path": "agent/demo.py", "content": "print(1)"}},
            {"type": "final", "result": final_payload("developer", {"implementation_plan": {"files": ["agent/demo.py"]}})},
        ])
        seen = []
        registry = ToolRegistry([
            AgentTool(
                name="fetch_public_url", description="Fetch a supplied URL",
                handler=lambda args: {"url": args["url"], "text": "Fixture page"},
                required_arguments=("url",), allowed_arguments=("url",),
                allowed_roles=("market_researcher",),
            ),
            AgentTool(
                name="propose_patch", description="Propose a temporary code edit",
                handler=lambda args: seen.append(args) or {"path": args["path"], "proposal_only": True},
                required_arguments=("path", "content"), allowed_arguments=("path", "content"),
                allowed_roles=("developer",),
            ),
        ])
        runtime = AgentToolRuntime(client, registry, live_approved=True)
        store = {}
        orchestrator = MultiAgentOrchestrator(
            runtime, checkpoint_loader=lambda: store,
            checkpoint_saver=lambda updated: store.update(updated),
        )
        result = orchestrator.run(
            "offline-e2e-fixture",
            [
                {"role": "market_researcher", "task": "Collect and summarise the supplied public source"},
                {"role": "developer", "task": "Prepare an implementation plan and proposed patch"},
            ],
            {"source_url": source},
        )
        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["completed_steps"], 2)
        self.assertEqual(client.calls, 4)
        self.assertEqual(len(seen), 1)
        self.assertEqual(store["workflows"]["offline-e2e-fixture"]["status"], "review_required")
        self.assertTrue(result["requires_human_approval"])

    def test_wrong_role_cannot_call_another_specialists_tool(self):
        client = ScriptedClient([{"type": "tool_call", "tool": "propose_patch", "arguments": {"path": "x", "content": "y"}}])
        registry = ToolRegistry([AgentTool(
            name="propose_patch", description="Developer-only edit",
            handler=lambda args: {"ok": True}, allowed_arguments=("path", "content"),
            allowed_roles=("developer",),
        )])
        runtime = AgentToolRuntime(client, registry, live_approved=True)
        with self.assertRaisesRegex(BrainError, "not allowed"):
            runtime.run("market_researcher", "Research only", {})

    def test_interrupted_workflow_resumes_from_saved_checkpoint(self):
        store = {}
        first_client = ScriptedClient([
            {"type": "final", "result": final_payload("market_researcher", {"research_summary": {"finding": "done"}})},
            {"type": "final", "result": final_payload("developer", {}, status="blocked")},
        ])
        registry = ToolRegistry([])
        first_runtime = AgentToolRuntime(first_client, registry, live_approved=True)
        workflow = [
            {"role": "market_researcher", "task": "Summarise evidence"},
            {"role": "developer", "task": "Prepare implementation"},
        ]
        first = MultiAgentOrchestrator(
            first_runtime, checkpoint_loader=lambda: store,
            checkpoint_saver=lambda updated: store.update(updated),
        ).run("recover-e2e", workflow, {})
        self.assertEqual(first["status"], "blocked")
        self.assertEqual(first["completed_steps"], 1)
        second_client = ScriptedClient([
            {"type": "final", "result": final_payload("developer", {"implementation_plan": {"ready": True}})},
        ])
        second_runtime = AgentToolRuntime(second_client, registry, live_approved=True)
        resumed = MultiAgentOrchestrator(
            second_runtime, checkpoint_loader=lambda: store,
            checkpoint_saver=lambda updated: store.update(updated),
        ).run("recover-e2e", workflow, {})
        self.assertEqual(resumed["status"], "review_required")
        self.assertEqual(resumed["completed_steps"], 2)
        self.assertEqual(second_client.calls, 1)


if __name__ == "__main__":
    unittest.main()