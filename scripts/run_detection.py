#!/usr/bin/env python
"""
FlakeGuard Detection CLI Entry Point.

Usage:
    python scripts/run_detection.py [--repo sample-repo] [--runs 10] [--seed 42] [--batch-size 3] [--json output.json]
"""
import argparse
import asyncio
import json
from pathlib import Path
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.harness.analyzer import TestAnalyzer
from backend.harness.executor import TestExecutor
from backend.harness.runner import TestRunner


async def main():
    parser = argparse.ArgumentParser(description="FlakeGuard flaky test detection harness")
    parser.add_argument("--repo", default="sample-repo", help="Path to repository to analyze")
    parser.add_argument("--runs", type=int, default=10, help="Number of test runs (default: 10)")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed for ordering and chaos (default: 42)")
    parser.add_argument("--batch-size", type=int, default=3, help="Batch size for early stopping (default: 3)")
    parser.add_argument("--json", dest="json_output", default=None, help="Optional output JSON path")
    parser.add_argument("--pattern", default=None, help="Optional pytest pattern filter (-k)")

    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        return

    print("=" * 80)
    print("FlakeGuard Flaky Test Detection Harness")
    print(f"Repository: {repo_path}")
    print(f"Planned runs: {args.runs} | Batch size: {args.batch_size} | Base seed: {args.seed}")
    print("=" * 80)

    runner = TestRunner(repo_path)
    analyzer = TestAnalyzer()
    executor = TestExecutor(runner, analyzer)

    start_time = time.perf_counter()

    runs = await executor.execute_multiple_runs(
        num_runs=args.runs,
        batch_size=args.batch_size,
        base_seed=args.seed,
        test_pattern=args.pattern,
    )
    # Note: analyze_runs is SYNCHRONOUS
    detection = analyzer.analyze_runs(runs)
    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 80)
    print("DETECTION RESULTS")
    print("=" * 80)
    print(f"Total test runs completed: {detection.total_test_runs}")
    print(f"Total unique tests: {detection.total_unique_tests}")
    print(f"Flaky tests flagged: {len(detection.flaky_tests)}")
    print(f"Stable tests: {len(detection.stable_tests)}")
    print(f"Elapsed time: {elapsed:.2f}s")
    print("-" * 80)

    # Flaky tests table
    if detection.flaky_tests:
        print("\nFLAGGED FLAKY TESTS:")
        print(f"{'Test Name':<50} {'Score':>7} {'Conf':>7} {'Pass/Fail':>11} {'Flagged Run':>12}")
        print("-" * 92)
        for t in detection.flaky_tests:
            pf_str = f"{t.pass_count}P / {t.fail_count}F"
            flagged_str = f"Run #{t.first_flagged_run}" if t.first_flagged_run else "N/A"
            # Truncate long test names for table display if needed
            short_name = t.test_name if len(t.test_name) <= 50 else "..." + t.test_name[-47:]
            print(f"{short_name:<50} {t.flakiness_score:>7.2f} {t.confidence:>7.4f} {pf_str:>11} {flagged_str:>12}")
    else:
        print("\nNo tests met the flaky threshold (>=3 passes AND >=3 failures).")

    # Rejected tests table
    if detection.rejected_tests:
        print("\nREJECTED TESTS (Zero-False-Positive Proof):")
        print(f"{'Test Name':<55} {'Reason':<30} {'Pass/Fail':>10}")
        print("-" * 98)
        for r in detection.rejected_tests:
            name = str(r.get("test_name", ""))
            short_name = name if len(name) <= 55 else "..." + name[-52:]
            reason = str(r.get("reason", ""))
            pf = f"{r.get('pass_count', 0)}P / {r.get('fail_count', 0)}F"
            print(f"{short_name:<55} {reason:<30} {pf:>10}")

    if args.json_output:
        out_path = Path(args.json_output)
        summary_data = analyzer.summary(detection)
        output_payload = {
            "summary": summary_data,
            "detection": detection.model_dump(mode="json"),
            "elapsed_seconds": round(elapsed, 3),
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        print(f"\nSaved JSON results to: {out_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
