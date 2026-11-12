import tempfile
import unittest
from pathlib import Path

from agent.autonomous_studio import LiveStudioApprovalError, build_live_studio
from agent.engine import execute


class LiveStudioCompositionTests(unittest.TestCase):
    def test_ab011_acceptance_handler_checks_composition_root_and_tests(self):
        result = execute({"id": "AB-011", "role": "developer", "kind": "live_composition"}, {}, {})
        self.assertTrue(result["ok"], result.get("metrics"))
        self.assertTrue(all(result["metrics"]["checks"].values()))

    def test_no_approval_means_no_live_studio_construction(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(LiveStudioApprovalError, "Human approval"):
                build_live_studio(directory, checkpoint_loader=dict, checkpoint_saver=lambda state: None, env={})

    def test_disabled_live_flag_blocks_even_with_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(LiveStudioApprovalError, "not explicitly true"):
                build_live_studio(directory, checkpoint_loader=dict, checkpoint_saver=lambda state: None, approval_confirmed=True, env={"STUDIO_LIVE_ENABLED": "false"})

    def test_approved_configuration_constructs_without_sending_provider_request(self):
        env = {
            "STUDIO_LIVE_ENABLED": "true",
            "STUDIO_LLM_API_KEY": "fixture-not-a-real-key",
            "STUDIO_LLM_PROVIDER": "fixture-provider",
            "STUDIO_LLM_BASE_URL": "https://api.example.test/v1",
            "STUDIO_LLM_MODEL": "fixture-model",
            "STUDIO_LLM_MAX_COST_PER_CALL_USD": "0.01",
            "STUDIO_LLM_INPUT_PRICE_PER_MILLION_USD": "1.0",
            "STUDIO_LLM_OUTPUT_PRICE_PER_MILLION_USD": "2.0",
            "STUDIO_LLM_MONTHLY_CAP_USD": "1.00",
        }
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "agent").mkdir()
            studio = build_live_studio(
                directory, checkpoint_loader=dict, checkpoint_saver=lambda state: None,
                approval_confirmed=True, env=env,
            )
            try:
                self.assertIsNotNone(studio.orchestrator)
                self.assertIsNotNone(studio.workspace)
                self.assertTrue(Path(directory, "data", "llm_spend.sqlite").exists())
            finally:
                studio.close()


if __name__ == "__main__":
    unittest.main()