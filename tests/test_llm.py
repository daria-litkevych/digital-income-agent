import unittest

from agent.llm import (
    LLMRequest, LLMSettings, OfflineMockClient,
    enforce_request_limits, estimate_cost_usd,
)

class LLMInterfaceTests(unittest.TestCase):
    def test_offline_mock_is_explicitly_mock_and_free(self):
        result = OfflineMockClient().generate(
            LLMRequest(task="market scan", system="Be careful", user="Compare offers")
        )
        self.assertTrue(result.is_mock)
        self.assertEqual(result.estimated_cost_usd, 0)
        self.assertIn("MOCK RESPONSE", result.text)

    def test_mock_rejects_empty_prompt(self):
        with self.assertRaises(ValueError):
            OfflineMockClient().generate(LLMRequest(task="test", system="", user=" "))

    def test_live_is_disabled_by_default(self):
        with self.assertRaisesRegex(RuntimeError, "disabled"):
            LLMSettings().validate_for_live_use()

    def test_live_requires_verified_prices(self):
        settings = LLMSettings(
            enabled=True, provider="example", base_url="https://example.invalid/v1",
            model="example-model", max_cost_per_call_usd=0.01,
        )
        with self.assertRaisesRegex(ValueError, "prices"):
            settings.validate_for_live_use()

    def test_cost_estimate(self):
        self.assertAlmostEqual(estimate_cost_usd(1_000_000, 1_000_000, 0.2, 1.2), 1.4)

    def test_request_limits_enforce_per_call_cap(self):
        settings = LLMSettings(
            enabled=True, provider="example", base_url="https://example.invalid/v1",
            model="example-model", max_output_tokens=1000, max_input_characters=1000,
            max_cost_per_call_usd=0.0001,
            input_price_per_million_usd=1.0, output_price_per_million_usd=2.0,
        )
        request = LLMRequest(task="test", system="a" * 400, user="b" * 400, max_output_tokens=1000)
        with self.assertRaisesRegex(ValueError, "per-call cap"):
            enforce_request_limits(request, settings)

    def test_request_limits_enforce_prompt_size(self):
        settings = LLMSettings(
            enabled=True, provider="example", base_url="https://example.invalid/v1",
            model="example-model", max_output_tokens=100, max_input_characters=10,
            max_cost_per_call_usd=1, input_price_per_million_usd=0.1,
            output_price_per_million_usd=0.2,
        )
        with self.assertRaisesRegex(ValueError, "characters"):
            enforce_request_limits(
                LLMRequest(task="test", system="", user="x" * 20, max_output_tokens=10),
                settings,
            )

if __name__ == "__main__":
    unittest.main()
