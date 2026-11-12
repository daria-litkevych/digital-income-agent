import json
import unittest
from dataclasses import dataclass

from agent.brain import AgentBrain, BrainError, ROLE_REGISTRY, build_offline_brain
from agent.llm import LLMResponse


class FakeClient:
    def __init__(self, text, *, is_mock=False):
        self.text = text
        self.is_mock = is_mock
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return LLMResponse(
            text=self.text, model="fake-model", provider="test",
            input_tokens=10, output_tokens=20, estimated_cost_usd=0.001,
            is_mock=self.is_mock,
        )


class AgentBrainTests(unittest.TestCase):
    def test_registry_covers_studio_specialists(self):
        expected = {
            "project_manager", "market_researcher", "business_analyst",
            "product_strategist", "product_designer", "developer",
            "quality_controller", "growth_launch", "analytics",
        }
        self.assertTrue(expected.issubset(ROLE_REGISTRY))

    def test_default_brain_is_offline_and_never_calls_paid_provider(self):
        brain = build_offline_brain()
        result = brain.dispatch("market_researcher", "Review supplied evidence", {"items": []})
        self.assertEqual(brain.mode, "offline")
        self.assertEqual(result["execution_mode"], "offline_mock")
        self.assertEqual(result["confidence"], "none")
        self.assertTrue(result["requires_human_approval"])

    def test_unknown_role_is_rejected(self):
        with self.assertRaisesRegex(BrainError, "Unknown"):
            build_offline_brain().dispatch("ceo", "Review", {})

    def test_external_side_effect_task_is_rejected(self):
        with self.assertRaisesRegex(BrainError, "external side effect"):
            build_offline_brain().dispatch("growth_launch", "Publish listing", {})

    def test_live_structured_response_is_validated(self):
        payload = {
            "status": "needs_evidence", "summary": "Need independent reviews.",
            "artifact": {"comparison": {}}, "evidence": [], "assumptions": ["No sales data"],
            "risks": ["Low confidence"], "confidence": "low",
            "requires_human_approval": True,
        }
        client = FakeClient(json.dumps(payload))
        brain = AgentBrain(client, live_approved=True)
        result = brain.dispatch("business_analyst", "Compare supplied alternatives", {"alternatives": []})
        self.assertEqual(result["execution_mode"], "live")
        self.assertEqual(result["model"], "fake-model")
        self.assertTrue(client.requests)

    def test_live_client_is_not_called_without_explicit_approval(self):
        client = FakeClient("{}")
        brain = AgentBrain(client, live_approved=False)
        with self.assertRaisesRegex(BrainError, "not approved"):
            brain.dispatch("market_researcher", "Summarise supplied sources", {})
        self.assertEqual(client.requests, [])

    def test_hallucinated_evidence_url_is_rejected(self):
        payload = {
            "status": "draft", "summary": "Found a source.",
            "artifact": {"research_summary": {}}, "evidence": [{"source": "https://invented.example/source"}],
            "assumptions": [], "risks": [], "confidence": "low",
            "requires_human_approval": True,
        }
        brain = AgentBrain(FakeClient(json.dumps(payload)), live_approved=True)
        with self.assertRaisesRegex(BrainError, "not supplied"):
            brain.dispatch("market_researcher", "Summarise supplied sources", {
                "sources": [{"url": "https://real.example/source"}]
            })

    def test_supplied_evidence_url_is_accepted(self):
        source = "https://real.example/source"
        payload = {
            "status": "draft", "summary": "Summary grounded in supplied source.",
            "artifact": {"research_summary": {}}, "evidence": [{"source": source}],
            "assumptions": [], "risks": [], "confidence": "medium",
            "requires_human_approval": True,
        }
        brain = AgentBrain(FakeClient(json.dumps(payload)), live_approved=True)
        result = brain.dispatch("market_researcher", "Summarise supplied sources", {
            "sources": [{"url": source}]
        })
        self.assertEqual(result["evidence"][0]["source"], source)

    def test_malformed_live_output_fails_closed(self):
        brain = AgentBrain(FakeClient("not json"), live_approved=True)
        with self.assertRaisesRegex(BrainError, "valid JSON"):
            brain.dispatch("market_researcher", "Summarise supplied sources", {})

    def test_missing_contract_fields_fail_closed(self):
        brain = AgentBrain(FakeClient(json.dumps({"status": "draft"})), live_approved=True)
        with self.assertRaisesRegex(BrainError, "missing required"):
            brain.dispatch("market_researcher", "Summarise supplied sources", {})


if __name__ == "__main__":
    unittest.main()
