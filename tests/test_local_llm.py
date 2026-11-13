import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.llm import LLMRequest, LocalLLMSettings, LocalOllamaClient


class FakeLocalResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")
        self.requested_size = None
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size=-1):
        self.requested_size = size
        return self.body if size < 0 else self.body[:size]


class LocalLLMTests(unittest.TestCase):
    def settings(self, **overrides):
        values = {"enabled": True, "base_url": "http://127.0.0.1:11434", "model": "installed-test-model"}
        values.update(overrides)
        return LocalLLMSettings(**values)

    def test_local_model_is_disabled_by_default(self):
        with self.assertRaisesRegex(RuntimeError, "disabled"):
            LocalLLMSettings().validate()

    def test_remote_hosts_and_non_loopback_addresses_are_rejected(self):
        for url in ("http://192.168.1.10:11434", "https://127.0.0.1:11434", "http://localhost:11434"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    self.settings(base_url=url).validate()

    def test_missing_model_is_rejected_without_downloading_anything(self):
        with self.assertRaisesRegex(ValueError, "never downloaded"):
            self.settings(model="").validate()

    @patch("agent.llm.urlopen")
    def test_local_client_calls_loopback_ollama_and_reports_zero_cost(self, mocked_urlopen):
        response = FakeLocalResponse({
            "message": {"content": "A local specialist draft"},
            "prompt_eval_count": 120,
            "eval_count": 40,
        })
        mocked_urlopen.return_value = response
        client = LocalOllamaClient(self.settings())
        result = client.generate(LLMRequest(
            task="design", system="You are a designer", user="Prepare a draft", max_output_tokens=100
        ))
        request = mocked_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertEqual(result.provider, "ollama-local")
        self.assertFalse(result.is_mock)
        self.assertEqual(result.estimated_cost_usd, 0.0)
        self.assertEqual(result.input_tokens, 120)
        self.assertGreater(response.requested_size, 0)

    @patch("agent.llm.urlopen")
    def test_oversized_response_is_rejected(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeLocalResponse({
            "message": {"content": "x" * 3000}, "prompt_eval_count": 1, "eval_count": 1
        })
        client = LocalOllamaClient(self.settings(max_response_bytes=1024))
        with self.assertRaisesRegex(RuntimeError, "size limit"):
            client.generate(LLMRequest(task="test", system="s", user="u", max_output_tokens=10))

    def test_input_and_output_limits_are_enforced_before_network(self):
        with patch("agent.llm.urlopen") as mocked_urlopen:
            client = LocalOllamaClient(self.settings(max_input_characters=5))
            with self.assertRaisesRegex(ValueError, "input limit"):
                client.generate(LLMRequest(task="test", system="", user="too long", max_output_tokens=2))
            mocked_urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
