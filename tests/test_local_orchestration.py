import json
import unittest
from unittest.mock import patch

from agent.brain import BrainError
from agent.llm import LocalLLMSettings, LocalOllamaClient
from agent.orchestrator import MultiAgentOrchestrator
from agent.tool_runtime import AgentTool, AgentToolRuntime, ToolRegistry


class FakeLocalHTTPResponse:
    def __init__(self, message):
        self.body = json.dumps({
            "message": {"content": json.dumps(message)},
            "prompt_eval_count": 20,
            "eval_count": 30,
        }).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size=-1):
        return self.body if size < 0 else self.body[:size]


def final_payload(section, value):
    return {
        "status": "draft",
        "summary": "A fixture-only local specialist draft.",
        "artifact": {section: value},
        "evidence": [],
        "assumptions": ["Synthetic fixture only."],
        "risks": ["No live customer or market evidence was collected."],
        "confidence": "low",
        "requires_human_approval": True,
    }


class LocalOrchestrationTests(unittest.TestCase):
    def setUp(self):
        settings = LocalLLMSettings(enabled=True, base_url="http://127.0.0.1:11434", model="fixture-model")
        self.client = LocalOllamaClient(settings)

    @patch("agent.llm.urlopen")
    def test_local_provider_runs_tool_call_and_two_specialists_to_review_gate(self, mocked_urlopen):
        mocked_urlopen.side_effect = [
            FakeLocalHTTPResponse({"type": "tool_call", "tool": "read_fixture_record", "arguments": {"record_id": "R-1"}}),
            FakeLocalHTTPResponse({"type": "final", "result": final_payload("research_summary", {"notes": "Tool observation reviewed."})}),
            FakeLocalHTTPResponse({"type": "final", "result": final_payload("comparison", {"options": ["A", "B"]})}),
        ]
        registry = ToolRegistry([
            AgentTool(
                name="read_fixture_record",
                description="Read one synthetic fixture record.",
                handler=lambda args: {"record_id": args["record_id"], "status": "fixture"},
                required_arguments=("record_id",),
                allowed_arguments=("record_id",),
                allowed_roles=("market_researcher",),
            )
        ])
        runtime = AgentToolRuntime(self.client, registry, live_approved=True)
        saved = []
        orchestrator = MultiAgentOrchestrator(
            runtime,
            checkpoint_loader=lambda: {},
            checkpoint_saver=lambda value: saved.append(json.loads(json.dumps(value))),
        )
        result = orchestrator.run("local-fixture-workflow", [
            {"role": "market_researcher", "task": "Review the supplied fixture record."},
            {"role": "business_analyst", "task": "Compare the supplied fixture options."},
        ], {"sources": []})

        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["completed_steps"], 2)
        self.assertTrue(result["requires_human_approval"])
        self.assertEqual(len(result["outputs"]["1"]["tool_trace"]), 1)
        self.assertEqual(result["outputs"]["1"]["tool_trace"][0]["observation"]["status"], "fixture")
        self.assertEqual(result["outputs"]["1"]["provider"], "ollama-local")
        self.assertEqual(result["outputs"]["2"]["provider"], "ollama-local")
        self.assertEqual(len(saved), 3)
        self.assertEqual(saved[-1]["workflows"]["local-fixture-workflow"]["status"], "review_required")
        self.assertEqual(mocked_urlopen.call_count, 3)
        for call in mocked_urlopen.call_args_list:
            self.assertTrue(call.args[0].full_url.startswith("http://127.0.0.1:11434/"))

    @patch("agent.llm.urlopen")
    def test_invalid_role_output_fails_closed(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeLocalHTTPResponse({
            "type": "final",
            "result": final_payload("code_patch", {"patch": "not allowed for market researcher"}),
        })
        runtime = AgentToolRuntime(self.client, ToolRegistry([]), live_approved=True)
        orchestrator = MultiAgentOrchestrator(
            runtime, checkpoint_loader=lambda: {}, checkpoint_saver=lambda value: None,
        )
        with self.assertRaisesRegex(BrainError, "not allowed for role"):
            orchestrator.run("invalid-local-workflow", [
                {"role": "market_researcher", "task": "Summarise supplied context."},
            ], {})
        self.assertEqual(mocked_urlopen.call_count, 1)


if __name__ == "__main__":
    unittest.main()
