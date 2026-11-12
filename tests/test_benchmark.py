import json
import tempfile
import unittest
from pathlib import Path

from agent.benchmark import load_cases, run_benchmark
from agent.llm import OfflineMockClient


class BenchmarkTests(unittest.TestCase):
    def test_default_benchmark_is_offline_and_labelled(self):
        report = run_benchmark()
        self.assertEqual(report["run_type"], "offline_mock")
        self.assertEqual(report["dataset_type"], "synthetic_test_cases_not_market_evidence")
        self.assertEqual(len(report["results"]), 4)
        self.assertTrue(all(item["is_mock"] for item in report["results"]))
        self.assertTrue(all(item["manual_review"]["reviewed"] is False
                            for item in report["results"]))

    def test_rejects_dataset_without_synthetic_label(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text(json.dumps({"cases": [{"id": "x"}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "marked synthetic"):
                load_cases(path)


if __name__ == "__main__":
    unittest.main()
