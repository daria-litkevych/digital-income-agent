import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.llm import (
    LLMRequest, LLMSettings, OfflineMockClient, OpenAICompatibleClient,
    enforce_request_limits, estimate_cost_usd,
)
from agent.spend_ledger import SpendLedger, SpendLimitExceeded


def live_settings(**overrides):
    values = dict(
        enabled=True, provider="test-provider", base_url="https://api.example.test/v1",
        model="test-model", max_output_tokens=100, max_input_characters=1000,
        max_cost_per_call_usd=1.0, input_price_per_million_usd=0.2,
        output_price_per_million_usd=1.2,
    )
    values.update(overrides)
    return LLMSettings(**values)


class FakeHTTPResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.body


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
        with self.assertRaisesRegex(ValueError, "prices"):
            live_settings(input_price_per_million_usd=None).validate_for_live_use()

    def test_live_requires_https(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            live_settings(base_url="http://api.example.test/v1").validate_for_live_use()

    def test_client_requires_explicit_key(self):
        with self.assertRaisesRegex(ValueError, "API key"):
            OpenAICompatibleClient(live_settings(), "")

    def test_cost_estimate(self):
        self.assertAlmostEqual(estimate_cost_usd(1_000_000, 1_000_000, 0.2, 1.2), 1.4)

    def test_request_limits_enforce_per_call_cap(self):
        settings = live_settings(
            max_cost_per_call_usd=0.0001, input_price_per_million_usd=1.0,
            output_price_per_million_usd=2.0, max_output_tokens=1000,
        )
        request = LLMRequest(task="test", system="a" * 400, user="b" * 400, max_output_tokens=1000)
        with self.assertRaisesRegex(ValueError, "per-call cap"):
            enforce_request_limits(request, settings)

    def test_request_limits_enforce_prompt_size(self):
        settings = live_settings(max_input_characters=10)
        with self.assertRaisesRegex(ValueError, "characters"):
            enforce_request_limits(
                LLMRequest(task="test", system="", user="x" * 20, max_output_tokens=10),
                settings,
            )

    @patch("agent.llm.urlopen")
    def test_live_client_parses_response_and_reports_actual_usage(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeHTTPResponse({
            "choices": [{"message": {"content": "A careful test answer"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        })
        client = OpenAICompatibleClient(live_settings(), "test-secret")
        result = client.generate(LLMRequest(
            task="test", system="Be accurate", user="Summarise this public example",
            max_output_tokens=20,
        ))
        self.assertEqual(result.text, "A careful test answer")
        self.assertFalse(result.is_mock)
        self.assertEqual(result.input_tokens, 100)
        self.assertEqual(result.output_tokens, 50)
        self.assertAlmostEqual(result.estimated_cost_usd, 0.00008)
        sent_request = mocked_urlopen.call_args.args[0]
        self.assertEqual(sent_request.full_url, "https://api.example.test/v1/chat/completions")
        self.assertNotIn("test-secret", repr(sent_request.data))

    @patch("agent.llm.urlopen")
    def test_live_client_rejects_malformed_response(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeHTTPResponse({"unexpected": True})
        client = OpenAICompatibleClient(live_settings(), "test-secret")
        with self.assertRaisesRegex(RuntimeError, "unexpected response"):
            client.generate(LLMRequest(task="test", system="", user="Hello", max_output_tokens=10))

    @patch("agent.llm.urlopen")
    def test_live_client_reserves_and_settles_monthly_spend(self, mocked_urlopen):
        with tempfile.TemporaryDirectory() as folder:
            ledger = SpendLedger(Path(folder) / "ledger.sqlite3", 1.0)
            mocked_urlopen.return_value = FakeHTTPResponse({
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            })
            client = OpenAICompatibleClient(live_settings(), "test-secret", ledger)
            result = client.generate(
                LLMRequest(task="test", system="system", user="hello", max_output_tokens=20),
                request_id="test-success",
            )
            self.assertAlmostEqual(result.estimated_cost_usd, 0.00008)
            self.assertAlmostEqual(ledger.monthly_committed_usd(), 0.00008)

    @patch("agent.llm.urlopen")
    def test_monthly_limit_blocks_before_network_request(self, mocked_urlopen):
        with tempfile.TemporaryDirectory() as folder:
            ledger = SpendLedger(Path(folder) / "ledger.sqlite3", 0.000001)
            client = OpenAICompatibleClient(live_settings(), "test-secret", ledger)
            with self.assertRaises(SpendLimitExceeded):
                client.generate(
                    LLMRequest(task="test", system="s" * 100, user="u" * 100,
                               max_output_tokens=20),
                    request_id="over-budget",
                )
            mocked_urlopen.assert_not_called()

    @patch("agent.llm.urlopen")
    def test_failed_network_request_keeps_reservation(self, mocked_urlopen):
        from urllib.error import URLError
        mocked_urlopen.side_effect = URLError("offline")
        with tempfile.TemporaryDirectory() as folder:
            ledger = SpendLedger(Path(folder) / "ledger.sqlite3", 1.0)
            client = OpenAICompatibleClient(live_settings(), "test-secret", ledger)
            with self.assertRaisesRegex(RuntimeError, "request failed"):
                client.generate(
                    LLMRequest(task="test", system="system", user="hello",
                               max_output_tokens=20),
                    request_id="network-failure",
                )
            self.assertGreater(ledger.monthly_committed_usd(), 0)

if __name__ == "__main__":
    unittest.main()
