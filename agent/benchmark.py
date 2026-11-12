"""Offline-first benchmark runner. Mock outputs are never research evidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from agent.llm import LLMRequest, OfflineMockClient


def load_cases(path: str | Path = "benchmarks/cases.json") -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("dataset_type") != "synthetic_test_cases_not_market_evidence":
        raise ValueError("Benchmark dataset must be explicitly marked synthetic")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Benchmark dataset contains no cases")
    ids = [case.get("id") for case in cases]
    if any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("Benchmark case IDs must be present and unique")
    return cases


def run_benchmark(client=None, cases_path: str | Path = "benchmarks/cases.json") -> dict:
    client = client or OfflineMockClient()
    results = []
    for case in load_cases(cases_path):
        response = client.generate(LLMRequest(
            task=case["task"], system=case["system"], user=case["user"],
            max_output_tokens=300,
        ))
        results.append({
            "case_id": case["id"],
            "task": case["task"],
            "response": response.text,
            "provider": response.provider,
            "model": response.model,
            "is_mock": response.is_mock,
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "estimated_cost_usd": response.estimated_cost_usd,
            "manual_review": {
                "scores": None,
                "expected_behaviours": case["expected_behaviours"],
                "risk": case["risk"],
                "reviewed": False
            }
        })
    is_mock = all(item["is_mock"] for item in results)
    return {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_type": "synthetic_test_cases_not_market_evidence",
        "run_type": "offline_mock" if is_mock else "model_evaluation",
        "warning": "Benchmark output is not customer evidence or market research.",
        "results": results
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports/benchmark-latest.json")
    args = parser.parse_args()
    report = run_benchmark()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"Wrote {report['run_type']} benchmark: {len(report['results'])} cases")
