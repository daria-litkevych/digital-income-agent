"""Provider-free Analytics specialist for supplied product metrics.

Computes transparent descriptive metrics only. It does not connect to analytics
accounts, infer causality, track users or fabricate missing denominators.
"""
from math import isfinite
from typing import Any


class MetricsInputError(ValueError):
    pass


def analyse_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise MetricsInputError("Metrics input must be an object.")
    required = ("sessions", "conversions", "gross_revenue", "refunds", "active_users")
    missing = [key for key in required if key not in metrics]
    if missing:
        raise MetricsInputError("Metrics input is missing: " + ", ".join(missing))
    values = {}
    for key in required:
        value = metrics[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
            raise MetricsInputError(f"{key} must be a finite non-negative number.")
        values[key] = value
    if values["refunds"] > values["conversions"]:
        raise MetricsInputError("refunds cannot exceed conversions in this aggregate input.")
    currency = metrics.get("currency", "unspecified currency")
    if not isinstance(currency, str) or not currency.strip():
        raise MetricsInputError("currency must be a non-empty string.")

    conversion_rate = values["conversions"] / values["sessions"] if values["sessions"] else None
    refund_rate = values["refunds"] / values["conversions"] if values["conversions"] else None
    net_revenue = values["gross_revenue"] - metrics.get("refund_amount", 0)
    refund_amount = metrics.get("refund_amount", 0)
    if isinstance(refund_amount, bool) or not isinstance(refund_amount, (int, float)) or not isfinite(refund_amount) or refund_amount < 0:
        raise MetricsInputError("refund_amount must be a finite non-negative number.")
    net_revenue = values["gross_revenue"] - refund_amount
    if net_revenue < 0:
        raise MetricsInputError("refund_amount cannot exceed gross_revenue.")

    return {
        "metrics_report": {
            "sessions": values["sessions"],
            "conversions": values["conversions"],
            "conversion_rate": conversion_rate,
            "refunds": values["refunds"],
            "refund_rate": refund_rate,
            "gross_revenue": values["gross_revenue"],
            "refund_amount": refund_amount,
            "net_revenue": net_revenue,
            "currency": currency,
            "active_users": values["active_users"],
            "calculation_notes": [
                "Rates use only the supplied aggregate denominators.",
                "A rate is null when its denominator is zero.",
                "Descriptive metrics do not establish causality or representativeness.",
            ],
        },
        "experiment_recommendation": {
            "next_measurement": "Collect the same metrics over a comparable period and segment only where sample sizes remain visible.",
            "guardrail": "Do not interpret a change as causal without a controlled experiment or other credible design.",
        },
        "decision_memo": {
            "status": "insufficient_data" if not values["sessions"] else "descriptive_only",
            "recommendation": "Use as a baseline; do not scale, retire or change pricing from this aggregate alone.",
            "missing_context": ["time window", "traffic source", "sample size by segment", "acquisition and operating costs"],
        },
    }


def execute_analytics_task(task: dict[str, Any]) -> dict[str, Any]:
    try:
        artifact = analyse_metrics(task.get("supplied_metrics"))
    except MetricsInputError as error:
        return {"ok": False, "blocked": True, "summary": str(error), "next_action": "Supply finite non-negative aggregate metrics with explicit denominators and currency."}
    return {
        "ok": True,
        "summary": "Analysed only the supplied aggregate metrics; missing denominators remain null and no causal conclusion is claimed.",
        "artifact": artifact,
        "metrics": {"conversion_rate_available": artifact["metrics_report"]["conversion_rate"] is not None, "refund_rate_available": artifact["metrics_report"]["refund_rate"] is not None},
    }


def evaluate(repository_root) -> dict[str, Any]:
    from pathlib import Path
    root = Path(repository_root)
    if not (root / "tests" / "test_analytics.py").is_file():
        return {"ok": False, "blocked": True, "summary": "Analytics specialist tests are missing.", "next_action": "Restore the aggregate-metrics analytics tests."}
    fixture = {"sessions": 100, "conversions": 5, "gross_revenue": 100, "refunds": 1, "refund_amount": 10, "active_users": 20, "currency": "EUR"}
    result = execute_analytics_task({"supplied_metrics": fixture})
    passed = (
        result.get("ok") is True
        and result["artifact"]["metrics_report"]["conversion_rate"] == 0.05
        and result["artifact"]["metrics_report"]["refund_rate"] == 0.2
        and result["artifact"]["metrics_report"]["net_revenue"] == 90
        and result["artifact"]["decision_memo"]["status"] == "descriptive_only"
    )
    return {
        "ok": passed, "blocked": not passed,
        "summary": "Analytics now calculates transparent descriptive metrics from supplied data, preserves zero-denominator gaps and avoids causal claims." if passed else "Analytics capability evaluation failed.",
        "metrics": {"fixture_passed": passed},
        "artifact": {"module": "agent/analytics.py", "tests": "tests/test_analytics.py", "mode": "supplied aggregate data only; no external tracking"},
        "next_action": "Connect only reviewed, user-approved metrics sources if and when a real product requires them.",
    }
