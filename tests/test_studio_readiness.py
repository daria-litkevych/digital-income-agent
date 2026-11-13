import unittest
from pathlib import Path

from agent.studio_readiness import evaluate


class StudioReadinessTests(unittest.TestCase):
    def test_current_studio_passes_readiness_audit_without_claiming_live_model_use(self):
        root = Path(__file__).resolve().parents[1]
        result = evaluate(root)
        self.assertTrue(result["ok"], result["metrics"])
        self.assertEqual(result["metrics"]["passed"], result["metrics"]["total"])
        self.assertIn("No model is installed", result["artifact"]["limitations"][0])
        self.assertIn("Install and start", result["next_action"])

    def test_missing_project_plan_fails_closed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            result = evaluate(Path(folder))
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])


if __name__ == "__main__":
    unittest.main()
