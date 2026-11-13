import unittest

from agent.analytics import MetricsInputError, analyse_metrics, execute_analytics_task


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.metrics = {
            "sessions": 100,
            "conversions": 5,
            "gross_revenue": 100,
            "refunds": 1,
            "refund_amount": 10,
            "active_users": 20,
            "currency": "EUR",
        }

    def test_computes_rates_and_net_revenue_from_supplied_values(self):
        result = analyse_metrics(self.metrics)
        report = result["metrics_report"]
        self.assertEqual(report["conversion_rate"], 0.05)
        self.assertEqual(report["refund_rate"], 0.2)
        self.assertEqual(report["net_revenue"], 90)
        self.assertEqual(report["currency"], "EUR")
        self.assertIn("causality", " ".join(report["calculation_notes"]))

    def test_zero_denominators_remain_null(self):
        result = analyse_metrics(dict(self.metrics, sessions=0, conversions=0, refunds=0))
        self.assertIsNone(result["metrics_report"]["conversion_rate"])
        self.assertIsNone(result["metrics_report"]["refund_rate"])
        self.assertEqual(result["decision_memo"]["status"], "insufficient_data")

    def test_negative_or_non_finite_values_are_rejected(self):
        for bad in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=bad):
                with self.assertRaises(MetricsInputError):
                    analyse_metrics(dict(self.metrics, sessions=bad))

    def test_invalid_refund_amount_is_rejected_before_arithmetic(self):
        with self.assertRaisesRegex(MetricsInputError, "refund_amount"):
            analyse_metrics(dict(self.metrics, refund_amount="not-a-number"))

    def test_inconsistent_refunds_are_rejected(self):
        with self.assertRaisesRegex(MetricsInputError, "refunds cannot exceed conversions"):
            analyse_metrics(dict(self.metrics, refunds=6))

    def test_missing_denominator_blocks_task(self):
        result = execute_analytics_task({"supplied_metrics": {"conversions": 2}})
        self.assertTrue(result["blocked"])
        self.assertIn("sessions", result["summary"])


if __name__ == "__main__":
    unittest.main()
