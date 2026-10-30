"""Command-line entry point. Wires together loader, runner, scoring,
and reporting modules behind the `sectest` command.

Subcommands:
    sectest run     — run a test suite against a model, export JSON/CSV
    sectest replay  — re-run only the test IDs that failed/errored in a
                       prior JSON report (regression-style replay)
"""

import argparse
import json
import sys
from pathlib import Path

from .loader import load_cases
from .reporting import summarize, write_csv, write_json
from .runner import run_suite


def cmd_run(args: argparse.Namespace) -> None:
    cases = load_cases(args.cases)
    if args.test_id:
        cases = [c for c in cases if c.id == args.test_id]
        if not cases:
            print(f"No test case with id '{args.test_id}' found.", file=sys.stderr)
            sys.exit(1)

    print(f"Loaded {len(cases)} test case(s) from {args.cases}")
    print(f"Target model: {args.model} | repeat: {args.repeat} | "
          f"timeout: {args.timeout}s | retries: {args.retries}")

    results = run_suite(cases, args.model, args.repeat, args.timeout,
                         args.retries, verbose=not args.quiet)
    summary = summarize(results)

    out_base = Path(args.output)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    json_path = out_base.with_suffix(".json")
    csv_path = out_base.with_suffix(".csv")
    write_json(results, summary, json_path)
    write_csv(results, csv_path)

    print("\n--- Summary ---")
    print(f"Total attempts: {summary['total_attempts']}")
    print(f"Passed: {summary['passed']} ({summary['pass_rate_pct']}%)")
    print(f"Failed: {summary['failed']} ({summary['fail_rate_pct']}%)")
    print(f"Errors: {summary['errors']}")
    print(f"Flagged uncertain (needs manual review): {summary['uncertain_count']}")
    if summary["avg_latency_ms"]:
        print(f"Avg latency: {summary['avg_latency_ms']}ms | Max: {summary['max_latency_ms']}ms")
    print(f"\nWritten: {json_path}")
    print(f"Written: {csv_path}")


def cmd_replay(args: argparse.Namespace) -> None:
    with open(args.from_report) as f:
        prior = json.load(f)

    failed_ids = sorted({
        a["test_id"] for a in prior["attempts"]
        if a["classification"].endswith("fail") or a["classification"] == "error"
    })
    if not failed_ids:
        print("No failed/errored test IDs found in the prior report — nothing to replay.")
        return

    print(f"Replaying {len(failed_ids)} previously-failed test id(s): {failed_ids}")
    cases = [c for c in load_cases(args.cases) if c.id in failed_ids]

    results = run_suite(cases, args.model, args.repeat, args.timeout,
                         args.retries, verbose=not args.quiet)
    summary = summarize(results)

    out_base = Path(args.output)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    write_json(results, summary, out_base.with_suffix(".json"))
    write_csv(results, out_base.with_suffix(".csv"))

    print("\n--- Replay Summary ---")
    print(f"Still failing: {summary['failed'] + summary['errors']}/{summary['total_attempts']}")
    print(f"Now passing: {summary['passed']}/{summary['total_attempts']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sectest",
        description="A small, modular AI security evaluation CLI (Promptfoo/Garak-inspired) for local Ollama models."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run a test case suite against a model.")
    p_run.add_argument("--cases", required=True, help="Path to a YAML/JSON test case file.")
    p_run.add_argument("--model", required=True, help="Ollama model name, e.g. llama3.2")
    p_run.add_argument("--repeat", type=int, default=1, help="Repetitions per test case.")
    p_run.add_argument("--timeout", type=float, default=60.0, help="Per-request timeout (s).")
    p_run.add_argument("--retries", type=int, default=2, help="Retries per request on failure.")
    p_run.add_argument("--output", required=True, help="Output path prefix (writes .json and .csv).")
    p_run.add_argument("--test-id", dest="test_id", default=None, help="Run only this test id.")
    p_run.add_argument("--quiet", action="store_true", help="Suppress per-attempt progress output.")
    p_run.set_defaults(func=cmd_run)

    p_replay = sub.add_parser("replay", help="Re-run only the failed test IDs from a prior JSON report.")
    p_replay.add_argument("--from-report", required=True, help="Path to a prior run's JSON report.")
    p_replay.add_argument("--cases", required=True, help="Path to the original YAML/JSON test case file.")
    p_replay.add_argument("--model", required=True, help="Ollama model name.")
    p_replay.add_argument("--repeat", type=int, default=1)
    p_replay.add_argument("--timeout", type=float, default=60.0)
    p_replay.add_argument("--retries", type=int, default=2)
    p_replay.add_argument("--output", required=True, help="Output path prefix for the replay report.")
    p_replay.add_argument("--quiet", action="store_true")
    p_replay.set_defaults(func=cmd_replay)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
