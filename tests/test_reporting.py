import json

from pathlib import Path
from ai_security_cli.models import AttemptResult
from ai_security_cli.reporting import summarize, write_json, write_csv


def create_result(classification):
    return AttemptResult(
        test_id="T01",
        category="safety",
        model="test-model",
        repetition=1,
        prompt="Test prompt",
        output="Test output",
        classification=classification,
        reason="Test reason",
        latency_ms=100.0,
        timestamp="2026-10-30T10:00:00Z"
    )


def test_summary_counts():
    results = [
        create_result("pass"),
        create_result("fail"),
        create_result("uncertain:pass"),
        create_result("error")
    ]

    summary = summarize(results)

    assert summary["total_attempts"] == 4
    assert summary["passed"] == 2
    assert summary["failed"] == 1
    assert summary["errors"] == 1
    assert summary["uncertain_count"] == 1


def test_write_json(tmp_path):
    results = [create_result("pass")]
    summary = summarize(results)

    output = tmp_path / "report.json"

    write_json(results, summary, output)

    with open(output) as f:
        data = json.load(f)

    assert data["summary"]["total_attempts"] == 1
    assert len(data["attempts"]) == 1


def test_write_csv(tmp_path):
    results = [create_result("pass")]

    output = tmp_path / "report.csv"

    write_csv(results, output)

    assert output.exists()
    assert output.stat().st_size > 0
