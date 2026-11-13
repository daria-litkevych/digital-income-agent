import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.autonomous_studio import LiveStudioApprovalError, build_local_studio


class LocalStudioCompositionTests(unittest.TestCase):
    def test_local_studio_requires_explicit_host_approval(self):
        with self.assertRaisesRegex(LiveStudioApprovalError, "Human approval"):
            build_local_studio(Path(__file__).resolve().parents[1], checkpoint_loader=dict, checkpoint_saver=lambda value: None)

    def test_local_studio_requires_explicit_local_opt_in(self):
        with self.assertRaisesRegex(LiveStudioApprovalError, "not explicitly true"):
            build_local_studio(
                Path(__file__).resolve().parents[1],
                checkpoint_loader=dict,
                checkpoint_saver=lambda value: None,
                approval_confirmed=True,
                env={"STUDIO_LOCAL_LLM_ENABLED": "false"},
            )

    def test_factory_construction_makes_no_network_call_or_paid_request(self):
        root = Path(__file__).resolve().parents[1]
        with patch("agent.llm.urlopen") as mocked_urlopen:
            studio = build_local_studio(
                root,
                checkpoint_loader=dict,
                checkpoint_saver=lambda value: None,
                approval_confirmed=True,
                env={
                    "STUDIO_LOCAL_LLM_ENABLED": "true",
                    "STUDIO_LOCAL_LLM_MODEL": "installed-test-model",
                    "STUDIO_LOCAL_LLM_BASE_URL": "http://127.0.0.1:11434",
                },
            )
            try:
                mocked_urlopen.assert_not_called()
                self.assertEqual(studio.orchestrator.runtime.client.settings.model, "installed-test-model")
                self.assertEqual(studio.orchestrator.runtime.client.settings.base_url, "http://127.0.0.1:11434")
            finally:
                studio.close()


if __name__ == "__main__":
    unittest.main()
