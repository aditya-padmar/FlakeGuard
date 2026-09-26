#!/usr/bin/env python
"""
Acceptance Gate Validation CLI Script.

Usage:
    python scripts/validate_harness.py [--repo sample-repo] [--runs 10] [--iterations 3] [--seed 42]
"""
import argparse
from pathlib import Path
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.harness.validate import validate


def main():
    parser = argparse.ArgumentParser(description="FlakeGuard Acceptance Gate Validator")
    parser.add_argument("--repo", default="sample-repo", help="Path to repo (default: sample-repo)")
    parser.add_argument("--runs", type=int, default=10, help="Runs per pass (default: 10)")
    parser.add_argument("--iterations", type=int, default=3, help="Number of independent iterations (default: 3)")
    parser.add_argument("--seed", type=int, default=42, help="Base seed (default: 42)")

    args = parser.parse_args()
    repo_path = Path(args.repo).resolve()

    print("=" * 80)
    print("FLAKEGUARD ACCEPTANCE GATE")
    print(f"Target Repository: {repo_path}")
    print(f"Iterations: {args.iterations} | Runs per pass: {args.runs} | Base seed: {args.seed}")
    print("=" * 80)

    val_res = validate(
        repo_path=repo_path,
        num_runs=args.runs,
        iterations=args.iterations,
        base_seed=args.seed,
    )

    print("\n" + "=" * 80)
    print("ACCEPTANCE GATE ITERATION SUMMARY")
    print("=" * 80)
    print(f"{'Iteration':<10} {'Seconds':<10} {'Flaky Found':<14} {'False Positives':<18} {'False Negatives':<18} {'Status':<8}")
    print("-" * 80)

    for it in val_res["iterations"]:
        flaky_count = len(it["flaky_found"])
        fp_count = len(it["false_positives"])
        fn_count = len(it["false_negatives"])
        status = "PASS" if it["passed"] else "FAIL"
        print(f"{it['iteration']:<10} {it['seconds']:<10.2f} {flaky_count:<14} {fp_count:<18} {fn_count:<18} {status:<8}")

    print("-" * 80)
    if val_res["passed"]:
        print("\n=======================================================")
        print("          >>> ACCEPTANCE GATE PASSED (3/3) <<<          ")
        print("=======================================================\n")
        sys.exit(0)
    else:
        print("\n=======================================================")
        print("          >>> ACCEPTANCE GATE FAILED <<<               ")
        print("=======================================================\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
