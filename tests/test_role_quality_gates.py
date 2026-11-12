"""Cross-role quality gates for the specialist registry.

These tests verify role contracts and fail-closed behaviour. They do not claim
that a language model's reasoning quality has been benchmarked.
"""
import json
import unittest

from agent.brain import AgentBrain, BrainError, ROLE_REGISTRY


class FixtureClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def generate(self, request):
        from agent.llm import LLMResponse
        self.calls += 1
        return LLMResponse(
            text=json.dumps(self.payload), model="fixture-model",
            provider="fixture", input_tokens=1, output_tokens=1,
            estimated_cost_usd=0.0, is_mock=False,
        )


def valid_payload(section):
    return {
        "status": "draft",
        "summary": "A fixture-only specialist draft.",
        "artifact": {section: {"fixture": True}},
        "evidence": [],
        "assumptions": ["This is synthetic test data."],
        "risks": ["No real research or model quality is measured."],
        "confidence": "low",
        "requires_human_approval": True,
    }


class CrossRoleQualityGates(unittest.TestCase):
    def test_every_allowed_artifact_section_is_accepted_only_by_its_role(self):
        for role, spec in ROLE_REGISTRY.items():
            for section in spec.allowed_outputs:
                with self.subTest(role=role, section=section):
                    client = FixtureClient(valid_payload(section))
                    result = AgentBrain(client, live_approved=True).dispatch(
                        role, "Prepare the requested internal draft.", {}
                    )
                    self.assertIn(section, result["artifact"])
                    self.assertEqual(client.calls, 1)
                    self.assertTrue(result["requires_human_approval"])

    def test_every_role_rejects_an_artifact_owned_by_another_role(self):
        for role, spec in ROLE_REGISTRY.items():
            foreign = next(
                section
                for other_role, other_spec in ROLE_REGISTRY.items()
                if other_role != role
                for section in other_spec.allowed_outputs
                if section not in spec.allowed_outputs
            )
            with self.subTest(role=role, foreign_section=foreign):
                client = FixtureClient(valid_payload(foreign))
                with self.assertRaisesRegex(BrainError, "not allowed for role"):
                    AgentBrain(client, live_approved=True).dispatch(
                        role, "Prepare the requested internal draft.", {}
                    )

    def test_evidence_must_reference_a_url_present_in_supplied_context(self):
        payload = valid_payload("research_summary")
        payload["evidence"] = [{"claim": "synthetic claim", "source": "https://not-provided.example"}]
        client = FixtureClient(payload)
        with self.assertRaisesRegex(BrainError, "not supplied in task context"):
            AgentBrain(client, live_approved=True).dispatch(
                "market_researcher", "Summarise supplied sources.",
                {"sources": ["https://provided.example/source"]}
            )

    def test_live_capable_client_is_not_called_without_approval(self):
        client = FixtureClient(valid_payload("task_plan"))
        with self.assertRaisesRegex(BrainError, "not approved"):
            AgentBrain(client, live_approved=False).dispatch(
                "project_manager", "Prepare an internal task plan.", {}
            )
        self.assertEqual(client.calls, 0)

    def test_external_side_effect_requests_are_rejected_before_provider_call(self):
        for role in ROLE_REGISTRY:
            client = FixtureClient(valid_payload(ROLE_REGISTRY[role].allowed_outputs[0]))
            with self.subTest(role=role):
                with self.assertRaisesRegex(BrainError, "external side effect"):
                    AgentBrain(client, live_approved=True).dispatch(
                        role, "Publish this listing now.", {}
                    )
                self.assertEqual(client.calls, 0)

    def test_draft_without_artifact_is_rejected(self):
        payload = valid_payload("task_plan")
        payload["artifact"] = {}
        client = FixtureClient(payload)
        with self.assertRaisesRegex(BrainError, "must contain"):
            AgentBrain(client, live_approved=True).dispatch(
                "project_manager", "Prepare an internal task plan.", {}
            )


if __name__ == "__main__":
    unittest.main()
