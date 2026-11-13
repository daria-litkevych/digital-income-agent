import unittest
from pathlib import Path

from agent.developer import execute_developer_task


class DeveloperProposalTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.original = (self.root / "agent" / "product_designer.py").read_text(encoding="utf-8")

    def test_proposal_runs_allowlisted_tests_and_never_modifies_repository(self):
        proposed = self.original + "\n# proposal-only test marker\n"
        result = execute_developer_task({
            "target_path": "agent/product_designer.py",
            "proposed_content": proposed,
            "test_module": "tests.test_product_designer",
        }, self.root)
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["artifact"]["repository_modified"])
        self.assertTrue(result["artifact"]["test_plan"]["result"]["passed"])
        self.assertIn("proposal-only test marker", result["artifact"]["code_patch"])
        self.assertEqual((self.root / "agent" / "product_designer.py").read_text(encoding="utf-8"), self.original)

    def test_unallowlisted_path_is_rejected(self):
        result = execute_developer_task({
            "target_path": "../../README.md",
            "proposed_content": "bad",
            "test_module": "tests.test_product_designer",
        }, self.root)
        self.assertTrue(result["blocked"])
        self.assertIn("allowlist", result["summary"])

    def test_unallowlisted_test_is_rejected(self):
        result = execute_developer_task({
            "target_path": "agent/product_designer.py",
            "proposed_content": self.original,
            "test_module": "os",
        }, self.root)
        self.assertTrue(result["blocked"])
        self.assertIn("allowlist", result["summary"])


if __name__ == "__main__":
    unittest.main()
