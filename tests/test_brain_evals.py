import json
import unittest
from pathlib import Path

from agent.brain import AgentBrain, ROLE_REGISTRY


class FixtureClient:
    def __init__(self, text):
        self.text = text
    def generate(self, request):
        from agent.llm import LLMResponse
        return LLMResponse(
            text=self.text, model="fixture-model", provider="fixture",
            input_tokens=1, output_tokens=1, estimated_cost_usd=0.0, is_mock=False,
        )


class AgentBrainEvaluationFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[1] / "benchmarks" / "agent_brain_cases.json"
        cls.fixtures = json.loads(path.read_text(encoding="utf-8"))["cases"]

    def test_every_registered_role_has_a_golden_contract_case(self):
        self.assertEqual({case["role"] for case in self.fixtures}, set(ROLE_REGISTRY))

    def test_each_role_accepts_its_expected_artifact_section(self):
        for case in self.fixtures:
            with self.subTest(role=case["role"]):
                payload = {
                    "status": case["expected_status"],
                    "summary": "Fixture-only contract response.",
                    "artifact": {case["required_artifact_key"]: {"fixture": True}},
                    "evidence": [],
                    "assumptions": ["Fixture is not real work."],
                    "risks": ["No model quality is measured by this fixture."],
                    "confidence": "low",
                    "requires_human_approval": True,
                }
                result = AgentBrain(
                    FixtureClient(json.dumps(payload)), live_approved=True
                ).dispatch(case["role"], case["task"], case["context"])
                self.assertIn(case["required_artifact_key"], result["artifact"])

    def test_role_cannot_return_another_specialists_artifact_section(self):
        payload = {
            "status": "draft", "summary": "Wrong role output.",
            "artifact": {"listing_draft": {"text": "not a researcher output"}},
            "evidence": [], "assumptions": [], "risks": [],
            "confidence": "low", "requires_human_approval": True,
        }
        with self.assertRaisesRegex(Exception, "not allowed for role"):
            AgentBrain(FixtureClient(json.dumps(payload)), live_approved=True).dispatch(
                "market_researcher", "Summarise supplied public sources.", {}
            )


if __name__ == "__main__":
    unittest.main()
