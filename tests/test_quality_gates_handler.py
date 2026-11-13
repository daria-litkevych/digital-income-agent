import tempfile
import unittest
from pathlib import Path

from agent.quality_gates import evaluate


class QualityGateHandlerTests(unittest.TestCase):
    def test_current_repository_passes_cross_role_contract_audit(self):
        root = Path(__file__).resolve().parents[1]
        result = evaluate(root)
        self.assertTrue(result["ok"], result["metrics"])
        self.assertEqual(result["metrics"]["registered_roles"], 9)
        self.assertEqual(result["metrics"]["passed"], result["metrics"]["total"])
        self.assertIn("not semantic model-quality", result["summary"])

    def test_missing_prerequisite_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            result = evaluate(Path(directory))
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])
        self.assertIn("missing", result["summary"].lower())


if __name__ == "__main__":
    unittest.main()
