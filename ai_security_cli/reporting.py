"""Summary statistics and JSON/CSV report export."""

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .models import AttemptResult


def summarize(results: list[AttemptResult]) -> dict:
    """Compute aggregate pass/fail/error/uncertain counts and latency stats."""
    total = len(results)
    fails = sum(1 for r in results if r.classification.endswith("fail"))
    passes = sum(1 for r in results if r.classification.endswith("pass"))
    errors = sum(1 for r in results if r.classification == "error")
    uncertain = sum(1 for r in results if r.classification.startswith("uncertain"))
    latencies = [r.latency_ms for r in results if r.latency_ms > 0]

    by_test: dict[str, dict] = {}
    for r in results:
        by_test.setdefault(r.test_id, {"pass": 0, "fail": 0, "error": 0, "uncertain": 0})
        key = "error" if r.classification == "error" else (
            "fail" if r.classification.endswith("fail") else "pass"
        )
        by_test[r.test_id][key] += 1
        if r.classification.startswith("uncertain"):
            by_test[r.test_id]["uncertain"] += 1

    return {
        "total_attempts": total,
        "passed": passes,
        "failed": fails,
        "errors": errors,
        "uncertain_count": uncertain,
        "pass_rate_pct": round(100 * passes / total, 2) if total else 0,
        "fail_rate_pct": round(100 * fails / total, 2) if total else 0,
        "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else None,
        "max_latency_ms": round(max(latencies), 1) if latencies else None,
        "by_test": by_test,
    }


def write_json(results: list[AttemptResult], summary: dict, out_path: Path) -> None:
    payload = {"summary": summary, "attempts": [asdict(r) for r in results]}
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)


def write_csv(results: list[AttemptResult], out_path: Path) -> None:
    fieldnames = ["test_id", "category", "model", "repetition", "classification",
                  "reason", "latency_ms", "timestamp", "error", "prompt", "output"]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(asdict(r))
