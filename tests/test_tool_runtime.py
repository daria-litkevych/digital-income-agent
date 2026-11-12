import json
import unittest

from agent.brain import BrainError
from agent.llm import LLMResponse, OfflineMockClient
from agent.tool_runtime import AgentTool, AgentToolRuntime, ToolRegistry
from agent.engine import execute


class SequenceClient:
    def __init__(self, messages):
        self.messages = list(messages)
        self.calls = 0
    def generate(self, request):
        self.calls += 1
        text = self.messages.pop(0)
        return LLMResponse(
            text=json.dumps(text), model="fixture-model", provider="fixture",
            input_tokens=10, output_tokens=20, estimated_cost_usd=0.0, is_mock=False,
        )


class ToolRuntimeAcceptanceTests(unittest.TestCase):
    def test_ab007_acceptance_handler_checks_runtime_and_test_artifacts(self):
        result = execute(
            {"id": "AB-007", "role": "developer", "kind": "agent_runtime"},
            {}, {},
        )
        self.assertTrue(result["ok"], result.get("metrics"))
        self.assertTrue(all(result["metrics"]["checks"].values()))


class ToolRegistryTests(unittest.TestCase):
    def test_unknown_tool_is_rejected(self):
        with self.assertRaisesRegex(BrainError, "Unknown tool"):
            ToolRegistry().invoke("not_registered", {})

    def test_arguments_are_schema_checked(self):
        registry = ToolRegistry([AgentTool(
            name="lookup", description="Read one item",
            handler=lambda args: {"value": args["key"]},
            required_arguments=("key",), allowed_arguments=("key",),
            allowed_roles=("market_researcher",),
        )])
        with self.assertRaisesRegex(BrainError, "Unexpected"):
            registry.invoke("lookup", {"key": "x", "extra": True}, role="market_researcher")
        self.assertEqual(registry.invoke("lookup", {"key": "x"}, role="market_researcher"), {"value": "x"})

    def test_side_effect_tool_is_blocked(self):
        registry = ToolRegistry([AgentTool(
            name="publish", description="Publish externally",
            handler=lambda args: {"ok": True},
            allowed_arguments=(), requires_approval=True,
            allowed_roles=("growth_launch",),
        )])
        with self.assertRaisesRegex(BrainError, "human approval"):
            registry.invoke("publish", {}, role="growth_launch")


class AgentToolRuntimeTests(unittest.TestCase):
    def test_offline_mode_never_runs_tools(self):
        called = []
        registry = ToolRegistry([AgentTool(
            name="lookup", description="Lookup",
            handler=lambda args: called.append(args),
            allowed_arguments=(), allowed_roles=("market_researcher",),
        )])
        result = AgentToolRuntime(OfflineMockClient(), registry).run(
            "market_researcher", "Summarise sources", {}
        )
        self.assertEqual(result["execution_mode"], "offline_mock")
        self.assertEqual(called, [])

    def test_live_client_requires_explicit_approval(self):
        client = SequenceClient([{"type": "final", "result": {}}])
        runtime = AgentToolRuntime(client, ToolRegistry(), live_approved=False)
        with self.assertRaisesRegex(BrainError, "not approved"):
            runtime.run("market_researcher", "Summarise sources", {})
        self.assertEqual(client.calls, 0)

    def test_tool_loop_executes_allowlisted_tool_then_validates_final_result(self):
        source = "https://example.test/source"
        client = SequenceClient([
            {"type": "tool_call", "tool": "read_source", "arguments": {"url": source}},
            {"type": "final", "result": {
                "status": "draft",
                "summary": "A summary based on the supplied source.",
                "artifact": {"research_summary": {"finding": "fixture"}},
                "evidence": [{"source": source}],
                "assumptions": [], "risks": [],
                "confidence": "low", "requires_human_approval": True,
            }},
        ])
        registry = ToolRegistry([AgentTool(
            name="read_source", description="Read supplied public source",
            handler=lambda args: {"url": args["url"], "content": "fixture text"},
            required_arguments=("url",), allowed_arguments=("url",),
            allowed_roles=("market_researcher",),
        )])
        result = AgentToolRuntime(client, registry, live_approved=True).run(
            "market_researcher", "Summarise supplied sources", {"url": source}
        )
        self.assertEqual(client.calls, 2)
        self.assertEqual(result["tool_steps"], 2)
        self.assertEqual(result["tool_trace"][0]["tool"], "read_source")
        self.assertEqual(result["execution_mode"], "live")

    def test_unknown_tool_request_fails_closed(self):
        client = SequenceClient([{"type": "tool_call", "tool": "shell", "arguments": {}}])
        with self.assertRaisesRegex(BrainError, "Unknown tool"):
            AgentToolRuntime(client, ToolRegistry(), live_approved=True).run(
                "developer", "Prepare an implementation plan", {}
            )

    def test_tool_loop_has_a_hard_step_limit(self):
        client = SequenceClient([
            {"type": "tool_call", "tool": "lookup", "arguments": {}},
            {"type": "tool_call", "tool": "lookup", "arguments": {}},
        ])
        registry = ToolRegistry([AgentTool(
            name="lookup", description="Fixture lookup",
            handler=lambda args: {"ok": True}, allowed_arguments=(),
        )])
        result = AgentToolRuntime(
            client, registry, live_approved=True, max_steps=2
        ).run("market_researcher", "Check source", {})
        self.assertEqual(result["status"], "needs_evidence")
        self.assertEqual(len(result["tool_trace"]), 2)


if __name__ == "__main__":
    unittest.main()
