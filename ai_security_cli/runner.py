"""Runs a loaded suite of TestCase objects against a model, repetition
by repetition, producing AttemptResult records."""

import time

from .models import AttemptResult, TestCase
from .ollama_client import call_ollama
from .scoring import classify


def run_suite(cases: list[TestCase], model: str, repeat: int, timeout: float,
              retries: int, verbose: bool = True) -> list[AttemptResult]:
    """Run every case `repeat` times against `model`, returning one
    AttemptResult per (case, repetition)."""
    results: list[AttemptResult] = []
    total = len(cases) * repeat
    done = 0

    for case in cases:
        for rep in range(1, repeat + 1):
            done += 1
            if verbose:
                print(f"[{done}/{total}] {case.id} (rep {rep}/{repeat})...", end=" ", flush=True)

            output, error, latency_ms = call_ollama(
                model, case.system_prompt, case.prompt, timeout, retries
            )
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

            if error:
                result = AttemptResult(
                    test_id=case.id, category=case.category, model=model,
                    repetition=rep, prompt=case.prompt, output="",
                    classification="error", reason=f"request failed: {error}",
                    latency_ms=0.0, timestamp=ts, error=error,
                )
                if verbose:
                    print("ERROR")
            else:
                verdict, reason, uncertain = classify(case, output)
                classification = f"uncertain:{verdict}" if uncertain else verdict
                result = AttemptResult(
                    test_id=case.id, category=case.category, model=model,
                    repetition=rep, prompt=case.prompt, output=output,
                    classification=classification, reason=reason,
                    latency_ms=round(latency_ms, 1), timestamp=ts,
                )
                if verbose:
                    print(f"{classification} ({latency_ms:.0f}ms) — {reason}")

            results.append(result)

    return results
