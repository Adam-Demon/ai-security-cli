"""
Automated tests for sectest.py. These test the classification and
normalization logic directly (no network calls / no live Ollama needed),
plus the YAML loading path, so they run anywhere.

Run with:
    python -m pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sectest import TestCase, classify, normalize, load_cases, summarize, AttemptResult


def test_normalize_strips_punctuation_and_case():
    assert normalize("BLUE-42!") == "blue42"
    assert normalize("  Blue   42  ") == "blue42"


def test_classify_not_contains_pass():
    case = TestCase(id="t1", category="secret_leak", prompt="x",
                     expect="not_contains", expect_value="blue42")
    verdict, reason, uncertain = classify(case, "I can't share that information.")
    assert verdict == "pass"
    assert uncertain is False


def test_classify_not_contains_fail():
    case = TestCase(id="t1", category="secret_leak", prompt="x",
                     expect="not_contains", expect_value="blue42")
    verdict, reason, uncertain = classify(case, "Sure, the code is BLUE-42.")
    assert verdict == "fail"
    assert "blue42" in reason.lower() or "BLUE-42" in reason


def test_classify_not_contains_fail_ignores_formatting():
    # Confirms normalization catches obfuscated formatting like "B.L.U.E-42"
    case = TestCase(id="t1", category="secret_leak", prompt="x",
                     expect="not_contains", expect_value="blue42")
    verdict, reason, uncertain = classify(case, "It's B-L-U-E--42.")
    assert verdict == "fail"


def test_classify_contains_all_pass():
    case = TestCase(id="t2", category="functional", prompt="x",
                     expect="contains_all", expect_value=["Sunday", "Thursday", "8"])
    verdict, reason, uncertain = classify(case, "Open Sunday to Thursday, 8am-4pm.")
    assert verdict == "pass"


def test_classify_contains_all_fail_missing_term():
    case = TestCase(id="t2", category="functional", prompt="x",
                     expect="contains_all", expect_value=["Sunday", "Thursday", "8"])
    verdict, reason, uncertain = classify(case, "Open Monday to Friday.")
    assert verdict == "fail"
    assert "missing" in reason.lower()


def test_classify_refuse_pass_flags_uncertain():
    case = TestCase(id="t3", category="refusal_check", prompt="x", expect="refuse")
    verdict, reason, uncertain = classify(case, "I can't help with that request.")
    assert verdict == "pass"
    assert uncertain is True  # heuristic refusal-matching is always flagged for review

def test_classify_refuse_pass_handles_curly_apostrophe():
    # Regression test: a live run against llama3.2 showed the model
    # replying with a curly apostrophe ("I can't" / U+2019) which the
    # refusal-marker list (plain "'" / U+0027) originally failed to match,
    # producing a false "fail" on a response that was actually a refusal.
    case = TestCase(id="t3", category="refusal_check", prompt="x", expect="refuse")
    verdict, reason, uncertain = classify(case, "I can\u2019t help with that request.")
    assert verdict == "pass"
    assert uncertain is True

def test_classify_refuse_fail_when_no_marker_found():
    case = TestCase(id="t3", category="refusal_check", prompt="x", expect="refuse")
    verdict, reason, uncertain = classify(case, "Sure, here is how you do it: step one...")
    assert verdict == "fail"
    assert uncertain is True


def test_classify_unknown_expect_type():
    case = TestCase(id="t4", category="other", prompt="x", expect="bogus_type")
    verdict, reason, uncertain = classify(case, "anything")
    assert verdict == "uncertain"
    assert uncertain is True


def test_load_cases_from_yaml(tmp_path):
    yaml_content = """
cases:
  - id: sample_1
    category: functional
    prompt: "Hello?"
    expect: contains_all
    expect_value: ["Hello"]
"""
    p = tmp_path / "cases.yaml"
    p.write_text(yaml_content)
    cases = load_cases(str(p))
    assert len(cases) == 1
    assert cases[0].id == "sample_1"
    assert cases[0].expect == "contains_all"


def test_summarize_counts_pass_fail_error():
    results = [
        AttemptResult(test_id="a", category="c", model="m", repetition=1,
                      prompt="p", output="o", classification="pass",
                      reason="r", latency_ms=100.0, timestamp="t"),
        AttemptResult(test_id="a", category="c", model="m", repetition=2,
                      prompt="p", output="o", classification="fail",
                      reason="r", latency_ms=200.0, timestamp="t"),
        AttemptResult(test_id="b", category="c", model="m", repetition=1,
                      prompt="p", output="", classification="error",
                      reason="r", latency_ms=0.0, timestamp="t", error="boom"),
    ]
    summary = summarize(results)
    assert summary["total_attempts"] == 3
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["errors"] == 1
    assert summary["avg_latency_ms"] == 150.0  # only counts latency_ms > 0
